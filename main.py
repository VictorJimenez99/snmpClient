import time

import requests
from pysnmp.hlapi import *
import threading


def get_oid_value(ip, oid):
    engine = SnmpEngine()

    user_data = UsmUserData(userName=b"snmp_admin",
                            authKey=b"qwertyui",
                            privKey=b"qwertyui",
                            privProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 2, 2),
                            authProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 1, 3))
    iterator = getCmd(
        engine, user_data,
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    error_indication, error_status, error_index, var_binds = next(iterator)
    if error_indication:
        print(f"errorIndication: {error_indication}")

    elif error_status:
        print('%s at %s' % (error_status.prettyPrint(),
                            error_index and var_binds[int(error_index) - 1][0] or '?'))

    else:
        for varBind in var_binds:
            result = (' = '.join([x.prettyPrint() for x in varBind]))
            result = result.split(' = ')
            return result[1]


def set_oid_value(ip, oid, new_value):
    engine = SnmpEngine()

    user_data = UsmUserData(userName=b"snmp_admin",
                            authKey=b"qwertyui",
                            privKey=b"qwertyui",
                            privProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 2, 2),
                            authProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 1, 3))
    command = setCmd(
        engine, user_data,
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid), new_value)
    )

    next(command)


server_url = "http://localhost:5000/"

url_get_needs_read = "http://localhost:5000/snmp/get_needs_read"
url_get_needs_update = "http://localhost:5000/snmp/get_needs_update"
url_set_snmp = "http://localhost:5000/router/set_snmp_drop_update"

sys_description_oid = '1.3.6.1.2.1.1.1.0'
sys_location_oid = '1.3.6.1.2.1.1.6.0'
sys_contact_oid = '1.3.6.1.2.1.1.4.0'
sys_name_oid = '1.3.6.1.4.1.9.2.1.3.0'
setter_sys_name_oid = '1.3.6.1.2.1.1.5.0'


def get_snmp_info(_router_info: dict):
    sys_name_value = get_oid_value(_router_info.get("router_ip"), sys_name_oid)
    sys_contact_value = get_oid_value(_router_info.get("router_ip"), sys_contact_oid)
    sys_location_value = get_oid_value(_router_info.get("router_ip"), sys_location_oid)
    return {"sys_name": sys_name_value,
            "sys_contact": sys_contact_value,
            "sys_location": sys_location_value}


def thread_update():
    while True:
        print("loop_start_update")
        sess = requests.Session()
        credentials_json = {"name": "root", "password": "root"}
        # payload_req = {'json_payload': credentials_json}
        login_request = sess.post(f"{server_url}create_session",
                                  json=credentials_json)
        print(f"request: {login_request}")

        response_ss = sess.get(url_get_needs_update)
        if response_ss.status_code != 200:
            print("error sleeping for 10s")
            time.sleep(10)
            continue
        json_ret = response_ss.json()

        list_needs_read = json_ret.get("list")
        sleep_time = int(json_ret.get("sleep_time"))

        for router_info in list_needs_read:
            new_values = get_snmp_info(router_info)
            print(new_values)

        print(f"sleeping for: {sleep_time}s")
        time.sleep(sleep_time)


def thread_read():
    while True:
        print("loop_start_read")
        sess = requests.Session()
        credentials_json = {"name": "root", "password": "root"}
        # payload_req = {'json_payload': credentials_json}
        login_request = sess.post(f"{server_url}create_session",
                                  json=credentials_json)
        print(f"request: {login_request}")

        response_ss = sess.get(url_get_needs_read)
        if response_ss.status_code != 200:
            print("error sleeping for 10s")
            time.sleep(10)
            continue
        json_ret = response_ss.json()

        list_needs_read = json_ret.get("list")
        sleep_time = int(json_ret.get("sleep_time"))

        for router_info in list_needs_read:
            new_values = get_snmp_info(router_info)
            print(f"new_values for: {router_info}: {new_values}")
            for (new_val_key, new_val_val) in new_values.items():
                json_object = {"router_name": router_info.get("router_name"),
                               "snmp_key": new_val_key,
                               "snmp_new_value": new_val_val}
                update_result = sess.post(url_set_snmp, json=json_object)
                print(update_result.text)

        print(f"sleeping for: {sleep_time}s")
        time.sleep(sleep_time)


if __name__ == '__main__':
    thread_read_h = threading.Thread(target=thread_read, args=" ")
    thread_update_h = threading.Thread(target=thread_update, args=" ")

    thread_read_h.start()
    thread_update_h.start()

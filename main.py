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
url_get_system_snmp = "http://localhost:5000/router/get_snmp"

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


def cprint(sw, message):
    if sw:
        print(message)


def thread_update(debug):
    while True:
        cprint(debug, "update: loop_start_update")
        sess = requests.Session()
        credentials_json = {"name": "root", "password": "root"}
        # payload_req = {'json_payload': credentials_json}
        login_request = sess.post(f"{server_url}create_session",
                                  json=credentials_json)
        cprint(debug, f"update: request: {login_request}")

        response_ss = sess.get(url_get_needs_update)
        if response_ss.status_code != 200:
            cprint(debug, "update: error sleeping for 10s")
            time.sleep(10)
            continue
        json_ret = response_ss.json()

        list_needs_update = json_ret.get("list")
        sleep_time = int(json_ret.get("sleep_time"))
        cprint(debug, list_needs_update)

        for router_info in list_needs_update:
            old_values = get_snmp_info(router_info)
            new_values: dict = sess.get(url_get_system_snmp,
                                        json={"router_name": router_info.get("router_name")}).json()
            cprint(debug, f"update: {old_values} with: {new_values}")
            old_sys_name = old_values.get("sys_name")
            new_sys_name = new_values.get("sys_name")
            old_sys_location = old_values.get("sys_location")
            new_sys_location = new_values.get("sys_location")
            old_sys_contact = old_values.get("sys_contact")
            new_sys_contact = new_values.get("sys_contact")
            if old_sys_name != new_sys_name:
                set_oid_value(router_info.get("router_ip"), setter_sys_name_oid, new_sys_name)
                json_object = {"router_name": router_info.get("router_name"),
                               "snmp_key": "sys_name",
                               "snmp_new_value": new_sys_name}
                update_result = sess.post(url_set_snmp, json=json_object)
                cprint(debug, f"update: {update_result.text}")
            if old_sys_contact != new_sys_contact:
                set_oid_value(router_info.get("router_ip"), sys_contact_oid, new_sys_contact)
                json_object = {"router_name": router_info.get("router_name"),
                               "snmp_key": "sys_contact",
                               "snmp_new_value": new_sys_contact}
                update_result = sess.post(url_set_snmp, json=json_object)
                cprint(debug, f"update: {update_result.text}")
            if old_sys_location != new_sys_location:
                set_oid_value(router_info.get("router_ip"), sys_location_oid, new_sys_location)
                json_object = {"router_name": router_info.get("router_name"),
                               "snmp_key": "sys_location",
                               "snmp_new_value": new_sys_location}
                update_result = sess.post(url_set_snmp, json=json_object)
                cprint(debug, f"update: {update_result.text}")

        cprint(debug, f"update: sleeping for: {sleep_time}s")
        time.sleep(sleep_time)


def thread_read(debug):
    while True:
        cprint(debug, "read: loop_start_read")
        sess = requests.Session()
        credentials_json = {"name": "root", "password": "root"}
        # payload_req = {'json_payload': credentials_json}
        login_request = sess.post(f"{server_url}create_session",
                                  json=credentials_json)
        cprint(debug, f"read: request: {login_request}")

        response_ss = sess.get(url_get_needs_read)
        if response_ss.status_code != 200:
            cprint(debug, "read: error sleeping for 10s")
            time.sleep(10)
            continue
        json_ret = response_ss.json()

        list_needs_read = json_ret.get("list")
        sleep_time = int(json_ret.get("sleep_time"))

        for router_info in list_needs_read:
            new_values = get_snmp_info(router_info)
            # print(f"read: new_values for: {router_info}: {new_values}")
            for (new_val_key, new_val_val) in new_values.items():
                json_object = {"router_name": router_info.get("router_name"),
                               "snmp_key": new_val_key,
                               "snmp_new_value": new_val_val}
                update_result = sess.post(url_set_snmp, json=json_object)
                cprint(debug, f"read: {update_result.text}")

        cprint(debug, f"read: sleeping for: {sleep_time}s")
        time.sleep(sleep_time)


def out_pkt_get_oid_from_if_name(interface_name):
    leading_values = "1.3.6.1.2.1.2.2.1.17."
    if interface_name == "FastEthernet0/0":
        return leading_values + "1"
    if interface_name == "FastEthernet1/0":
        return leading_values + "2"
    if interface_name == "FastEthernet1/1":
        return leading_values + "3"
    if interface_name == "FastEthernet2/0":
        return leading_values + "4"
    if interface_name == "FastEthernet2/1":
        return leading_values + "5"
    if interface_name == "Ethernet3/0":
        return leading_values + "6"
    if interface_name == "Ethernet3/1":
        return leading_values + "7"
    if interface_name == "FastEthernet3/2":
        return leading_values + "8"
    if interface_name == "FastEthernet3/3":
        return leading_values + "9"


def in_pkt_get_oid_from_if_name(interface_name):
    leading_values = "1.3.6.1.2.1.2.2.1.11."
    if interface_name == "FastEthernet0/0":
        return leading_values + "1"
    if interface_name == "FastEthernet1/0":
        return leading_values + "2"
    if interface_name == "FastEthernet1/1":
        return leading_values + "3"
    if interface_name == "FastEthernet2/0":
        return leading_values + "4"
    if interface_name == "FastEthernet2/1":
        return leading_values + "5"
    if interface_name == "Ethernet3/0":
        return leading_values + "6"
    if interface_name == "Ethernet3/1":
        return leading_values + "7"
    if interface_name == "Ethernet3/2":
        return leading_values + "8"
    if interface_name == "Ethernet3/3":
        return leading_values + "9"


def thread_packages(debug):
    cprint(debug, "Hola")
    val = get_oid_value("10.1.0.254", out_pkt_get_oid_from_if_name("FastEthernet0/0"))
    cprint(debug, val)


if __name__ == '__main__':
    thread_read_h = threading.Thread(target=thread_read, args=[False])
    thread_update_h = threading.Thread(target=thread_update, args=[False])
    thread_packages_h = threading.Thread(target=thread_packages, args=[True])

    thread_read_h.start()
    thread_update_h.start()
    thread_packages_h.start()

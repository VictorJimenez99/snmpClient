from pysnmp.hlapi import *


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
            print(' = '.join([x.prettyPrint() for x in varBind]))


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


if __name__ == '__main__':
    sys_description = '1.3.6.1.2.1.1.1.0'
    sys_location = '1.3.6.1.2.1.1.6.0'
    sys_contact = '1.3.6.1.2.1.1.4.0'
    sys_name = "1.3.6.1.4.1.9.2.1.3.0"

    get_oid_value("10.1.0.254", sys_name)
    get_oid_value("10.1.0.254", sys_location)
    get_oid_value("10.1.0.254", sys_description)
    get_oid_value("10.1.0.254", sys_contact)

    set_oid_value("10.1.0.254", sys_name, "R41")
    get_oid_value("10.1.0.254", sys_name)

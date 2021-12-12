from pysnmp.hlapi import *


def get_oid_value(ip, oid):
    engine = SnmpEngine()

    user_data = UsmUserData(userName=b"snmp_admin",
                            authKey=b"qwertyui",
                            privKey=b"qwertyui",
                            privProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 2, 2),
                            authProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 1, 3))
    print(user_data)
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


if __name__ == '__main__':
    get_oid_value("10.1.0.254", "1.3.6.1.2.1.2.2")

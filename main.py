from pysnmp.hlapi import *

if __name__ == '__main__':
    engine = SnmpEngine()
    user_data=UsmUserData(userName=b"snmp_admin",
                          authKey=b"qwertyui",
                          privKey=b"qwertyui",
                          privProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 2, 2),
                          authProtocol=(1, 3, 6, 1, 6, 3, 10, 1, 1, 3))
    print(user_data)
    iterator = getCmd(
        engine, user_data,
        UdpTransportTarget(('10.1.0.254', 161)),
        ContextData(),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.9.2.1.3.0"))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(f"errorIndication: {errorIndication}")

    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))

    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))

from pysnmp.hlapi import *

if __name__ == '__main__':
    iterator = getCmd(
        SnmpEngine(),
        UsmUserData(userName=b"admin_snmp", authKey=b"admin", privKey=b"admin", authProtocol=usmHMACMD5AuthProtocol),
        UdpTransportTarget(('10.1.0.254', 161)),
        ContextData(),
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(f"errorIndicationaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: {errorIndication}")

    elif errorStatus:
        print('aaaaaaaaaaaaaaaaaaaaaaasssssssssssssssssssssssssssssssssssssssss%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))

    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))

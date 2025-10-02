from pysnmp.hlapi import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    getCmd,
)
import sys

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
community = sys.argv[2] if len(sys.argv) > 2 else "public"

# sysName.0 = 1.3.6.1.2.1.1.5.0
iterator = getCmd(
    SnmpEngine(),
    CommunityData(community, mpModel=1),  # SNMPv2c
    UdpTransportTarget((host, 161), timeout=2, retries=2),
    ContextData(),
    ObjectType(ObjectIdentity("1.3.6.1.2.1.1.5.0")),
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

if errorIndication:
    print(f"SNMP hiba: {errorIndication}")
elif errorStatus:
    print(f"SNMP hiba: {errorStatus.prettyPrint()} at {errorIndex}")
else:
    for vb in varBinds:
        print(f"Eredmény: {vb.prettyPrint()}")

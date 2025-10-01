from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, getCmd, nextCmd
)
import sys
from datetime import timedelta

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
COMM = sys.argv[2] if len(sys.argv) > 2 else "public"

def snmp_get(oid: str):
    it = getCmd(
        SnmpEngine(),
        CommunityData(COMM, mpModel=1),
        UdpTransportTarget((HOST, 161), timeout=2, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    errInd, errStat, errIdx, varBinds = next(it)
    if errInd:
        return None
    if errStat:
        return None
    return varBinds[0][1]

def snmp_walk(prefix_oid: str):
    for (errInd, errStat, errIdx, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(COMM, mpModel=1),
        UdpTransportTarget((HOST, 161), timeout=2, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity(prefix_oid)),
        lexicographicMode=False
    ):
        if errInd or errStat:
            return
        for oid, val in varBinds:
            yield str(oid), val

def human_uptime(timeticks):
    if timeticks is None:
        return "n/a"
    ticks = int(timeticks)
    seconds = ticks // 100
    return str(timedelta(seconds=seconds))

def to_float(val):
    try:
        return float(str(val).strip('"'))
    except Exception:
        return None

def to_int(val):
    try:
        return int(str(val))
    except Exception:
        return None

def kib_to_mib(kib):
    try:
        return float(kib) / 1024.0
    except Exception:
        return 0.0

def main():
    sys_name   = snmp_get("1.3.6.1.2.1.1.5.0")      # sysName.0
    sys_uptime = snmp_get("1.3.6.1.2.1.1.3.0")      # sysUpTime.0

    la1  = to_float(snmp_get("1.3.6.1.4.1.2021.10.1.3.1"))
    la5  = to_float(snmp_get("1.3.6.1.4.1.2021.10.1.3.2"))
    la15 = to_float(snmp_get("1.3.6.1.4.1.2021.10.1.3.3"))

    mem_total_kib = to_int(snmp_get("1.3.6.1.4.1.2021.4.5.0"))
    mem_avail_kib = to_int(snmp_get("1.3.6.1.4.1.2021.4.6.0"))
    mem_used_kib  = (mem_total_kib - mem_avail_kib) if (mem_total_kib and mem_avail_kib) else None
    mem_used_pct  = (mem_used_kib / mem_total_kib * 100.0) if (mem_total_kib and mem_used_kib is not None) else None

    # dskTable: find "/" index
    root_idx = None
    for oid, val in snmp_walk("1.3.6.1.4.1.2021.9.1.2") or []:
        if str(val).strip('"') == "/":
            root_idx = oid.split('.')[-1]
            break

    if root_idx:
        d_total_kib = to_int(snmp_get(f"1.3.6.1.4.1.2021.9.1.6.{root_idx}"))
        d_used_kib  = to_int(snmp_get(f"1.3.6.1.4.1.2021.9.1.8.{root_idx}"))
        d_pct       = to_int(snmp_get(f"1.3.6.1.4.1.2021.9.1.9.{root_idx}"))
    else:
        d_total_kib = d_used_kib = d_pct = None

    print("\nSNMP MINI-DASHBOARD\n====================")
    print(f"Host:        {HOST}")
    print(f"Device:      {str(sys_name) if sys_name is not None else 'n/a'}")
    print(f"Uptime:      {human_uptime(sys_uptime)}\n")

    la_str = " / ".join([
        f"1m: {la1:.2f}" if la1 is not None else "1m: n/a",
        f"5m: {la5:.2f}" if la5 is not None else "5m: n/a",
        f"15m: {la15:.2f}" if la15 is not None else "15m: n/a",
    ])
    print(f"Load avg:    {la_str}")

    if mem_total_kib and mem_used_kib is not None and mem_used_pct is not None:
        print("Memory:      used: {:.1f} MiB / {:.1f} MiB ({:.1f}%)".format(
            kib_to_mib(mem_used_kib), kib_to_mib(mem_total_kib), mem_used_pct))
    else:
        print("Memory:      n/a")

    if d_total_kib and d_used_kib is not None and d_pct is not None:
        print("Disk:        /: {:.1f} / {:.1f} MiB ({}%)".format(
            kib_to_mib(d_used_kib), kib_to_mib(d_total_kib), d_pct))
    else:
        print("Disk:        n/a\n")

if __name__ == "__main__":
    main()

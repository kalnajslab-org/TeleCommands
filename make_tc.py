#!/usr/bin/env python3
"""Make one Strateole-2 telecommand file without the GUI (same framing and CRC as TCMessage.py).

Usage:  make_tc.py <Instrument> <TC name or code> [param ...] [-o DIR]
        make_tc.py RATS 76                 -> RATS_76_20261007-071530.tc  containing START76;<crc>END
        make_tc.py RATS RatsSetEcuTemp -20 -> "66,-20;"
        make_tc.py MCB RetractRevs 2       -> "4,2;"
        make_tc.py --list RATS             -> the TCs the CSV knows for that instrument
The TC database is TC_Parameters.csv next to this script (Instrument, name, number of
parameters, code, default, min, max, notes); parameters are range-checked like the GUI.
The file is the operational CCMZ format (START + "<code>[,p...];" + CRC-16/CCITT big-endian + END);
the Zephyr simulator and the OBCZ AIT page take the bare "<code>[,p...];" text instead.
"""
import argparse, csv, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "TC_Parameters.csv")


def crc16_ccitt(crc, data):            # verbatim from TCMessage.py
    msb = crc >> 8
    lsb = crc & 255
    for c in data:
        x = c ^ msb
        x ^= (x >> 4)
        msb = (lsb ^ (x >> 3) ^ (x << 4)) & 255
        lsb = (x ^ (x << 5)) & 255
    return (msb << 8) + lsb


def make_tc_file(filename, command):   # verbatim framing from TCMessage.MakeTCFile
    payload = command.encode("ASCII")
    crc = crc16_ccitt(0x1021, payload)
    with open(filename, "wb") as f:
        f.write(b"START")
        f.write(payload)
        f.write(crc.to_bytes(2, byteorder="big", signed=False))
        f.write(b"END")
    return crc


def load(instrument):
    rows = []
    with open(CSV, encoding="utf8") as f:
        for r in csv.DictReader(f):
            if r["Instrument"] == instrument and r["Parameter"]:
                rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("instrument", nargs="?")
    ap.add_argument("tc", nargs="?", help="TC name from the CSV or its numeric code")
    ap.add_argument("params", nargs="*")
    ap.add_argument("-o", "--out", default=".", help="directory for the .tc file (default: current)")
    ap.add_argument("--list", metavar="INSTRUMENT", help="list the TCs for an instrument and exit")
    a = ap.parse_args()
    if a.list:
        for r in load(a.list):
            print(f"{r['Enum']:>4}  {r['Parameter']:24} params={r['Values']}  range {r['Min_val']}..{r['Max_val']}  {r['Notes']}")
        return
    if not (a.instrument and a.tc):
        ap.error("instrument and TC are required")
    rows = load(a.instrument)
    if not rows:
        sys.exit(f"no instrument {a.instrument!r} in {CSV} (try --list)")
    row = next((r for r in rows if r["Parameter"] == a.tc or r["Enum"] == a.tc), None)
    if row is None:
        sys.exit(f"no TC {a.tc!r} for {a.instrument}; use --list {a.instrument}")
    n = int(row["Values"])
    if len(a.params) != n:
        sys.exit(f"{row['Parameter']} (code {row['Enum']}) takes {n} parameter(s), got {len(a.params)}")
    lo, hi = float(row["Min_val"]), float(row["Max_val"])
    for p in a.params:
        try:
            v = float(p)
        except ValueError:
            sys.exit(f"parameter {p!r} is not a number")
        if n and not (lo <= v <= hi):
            sys.exit(f"{p} is outside the CSV range {lo:g}..{hi:g} for {row['Parameter']}")
    command = row["Enum"] + ("," + ",".join(a.params) if a.params else "") + ";"
    # name carries the command, so files made in the same second do not overwrite each other
    # (the GUI names files <Instrument><timestamp>.tc; the CCMZ does not read the name)
    tag = row["Enum"] + ("_" + "_".join(a.params) if a.params else "")
    filename = os.path.join(a.out, f"{a.instrument}_{tag}_{time.strftime('%Y%m%d-%H%M%S')}.tc")
    crc = make_tc_file(filename, command)
    print(f"{filename}: {command}  crc 0x{crc:04x}  ({row['Notes']})")


if __name__ == "__main__":
    main()

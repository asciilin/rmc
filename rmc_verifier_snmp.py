import subprocess
import time
import re

IP = "10.225.70.178"
RO_COMM = "public"
RW_COMM = "private1"
EXPECTED_MODEL = "SRC-0800"
EXPECTED_FW = "4.2.0.5-50274"
EXPECTED_SN = "24L5200076"
REACHABILITY_MAX_MS = 200

OIDS = {
    "pduModel": ".1.3.6.1.4.1.13742.6.3.2.1.1.3.1",
    "boardFirmwareVersion": ".1.3.6.1.4.1.13742.6.3.2.3.1.6.1.1.1",
    "pduSerialNumber": ".1.3.6.1.4.1.13742.6.3.2.1.1.4.1",
    "unitDeviceCapabilities": ".1.3.6.1.4.1.13742.6.3.2.2.1.35.1",
    "measurementsUnitSensorIsAvailable": ".1.3.6.1.4.1.13742.6.5.1.3.1.2.1",
    "externalSensorType": ".1.3.6.1.4.1.13742.6.3.6.3.1.2.1",
    "measurementsExternalSensorIsAvailable": ".1.3.6.1.4.1.13742.6.5.5.3.1.2.1",
    "measurementsUnitSensorState": ".1.3.6.1.4.1.13742.6.5.1.3.1.3.1",
    "measurementsExternalSensorState": ".1.3.6.1.4.1.13742.6.5.5.3.1.3.1",
    "measurementsUnitSensorValue": ".1.3.6.1.4.1.13742.6.5.1.3.1.4.1",
    "unitSensorMinimum": ".1.3.6.1.4.1.13742.6.3.2.5.1.12.1",
    "unitSensorMaximum": ".1.3.6.1.4.1.13742.6.3.2.5.1.11.1",
    "measurementsExternalSensorValue": ".1.3.6.1.4.1.13742.6.5.5.3.1.4.1",
    "externalSensorMinimum": ".1.3.6.1.4.1.13742.6.3.6.3.1.22.1",
    "externalSensorMaximum": ".1.3.6.1.4.1.13742.6.3.6.3.1.21.1",
    "hwFailureTable": ".1.3.6.1.4.1.13742.6.10.3.1",
    "reliabilityDataTable": ".1.3.6.1.4.1.13742.6.10.1.2",
}

# 感測器名稱對應（自行補充）
sensor_name_dict = {
    "temperature": "溫度感測器",
    "humidity": "濕度感測器",
    # 依實際感測器型別補充
}

def snmpget(oid, community=RO_COMM):
    cmd = ["snmpget", "-v2c", "-c", community, IP, oid]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if result.returncode != 0 or "No Such" in result.stdout:
        return None
    return result.stdout.strip()

def snmpwalk(oid, community=RO_COMM):
    cmd = ["snmpwalk", "-v2c", "-c", community, IP, oid]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def get_external_sensor_info():
    """index（如 1.1）: (type, name)"""
    lines = snmpwalk(OIDS["externalSensorType"])
    info = {}
    for line in lines:
        m = re.match(r'.*::externalSensorType\.(\d+\.\d+)\s+= INTEGER: (\w+)', line)
        if m:
            idx, typ = m.group(1), m.group(2)
            name = sensor_name_dict.get(typ, typ)
            info[idx] = (typ, name)
    return info

def check_identification():
    print("[1] Identification: ", end="")
    model = snmpget(OIDS["pduModel"])
    fw = snmpget(OIDS["boardFirmwareVersion"])
    sn = snmpget(OIDS["pduSerialNumber"])
    if model is None or fw is None or sn is None:
        print("FAIL (SNMP error)")
        return False
    if EXPECTED_MODEL not in model:
        print(f"FAIL (model mismatch: {model})")
        return False
    if EXPECTED_FW not in fw:
        print(f"FAIL (fw mismatch: {fw})")
        return False
    if EXPECTED_SN not in sn:
        print(f"FAIL (sn mismatch: {sn})")
        return False
    print("PASS")
    return True

def check_reachability():
    print("[2] Reachability: ", end="")
    start = time.perf_counter()
    resp = snmpget(OIDS["pduModel"])
    elapsed = (time.perf_counter() - start) * 1000
    if resp is None:
        print("FAIL (no response)")
        return False
    print(f"PASS ({elapsed:.1f} ms)")
    return elapsed < REACHABILITY_MAX_MS

def check_unit_sensor_presence():
    present = False
    available = snmpwalk(OIDS["measurementsUnitSensorIsAvailable"])
    print("[3a] Unit sensor presence:")
    if not available:
        print("    FAIL (SNMP error)")
        print("[3a] Unit sensor presence: FAIL")
        return False
    for line in available:
        # 例: PDU2-MIB::measurementsUnitSensorIsAvailable.1.i1smpsStatus = INTEGER: true(1)
        m = re.match(r'.*::measurementsUnitSensorIsAvailable\.(\d+)\.(\w+)\s+=\s+INTEGER: (\w+)\((\d+)\)', line)
        if m:
            unit_idx, sensor_name, val, val_num = m.groups()
            # 你可加對照表 unit_sensor_name_dict 轉中文
            status = "OK" if val in ["true", "1"] or val_num == "1" else "Not Present"
            print(f"    Unit {unit_idx} Sensor ({sensor_name}): {status}")
            if status == "OK":
                present = True
    if present:
        print("[3a] Unit sensor presence: PASS")
        return True
    else:
        print("[3a] Unit sensor presence: FAIL (no unit sensor present)")
        return False

def check_external_sensor_presence():
    ext_info = get_external_sensor_info()
    present = True
    found_any = False
    print("[3b] External sensor presence:")
    for idx, (typ, name) in ext_info.items():
        # 拆出 idx 的第二段
        sub_idx = idx.split(".")[1]
        oid_query = OIDS["measurementsExternalSensorIsAvailable"] + f".{sub_idx}"
        avail = snmpget(oid_query)
        found_any = True
        # debug print
        # print(f"    DEBUG: idx={idx}, query={oid_query}, result={repr(avail)}")
        if avail is not None and ("true(1)" in avail or "INTEGER: 1" in avail or "INTEGER: true(1)" in avail):
            status = "OK"
        else:
            status = "Not Present"
            present = False
        print(f"    Sensor {idx} ({name}): {status}")
    if not ext_info or not found_any:
        print("[3b] External sensor presence: PASS (no external sensor)")
        return True
    if present:
        print("[3b] External sensor presence: PASS")
        return True
    else:
        print("[3b] External sensor presence: FAIL")
        return False

def check_sensor_state():
    print("[4] Sensor state: ", end="")
    ext_info = get_external_sensor_info()
    unit_states = snmpwalk(OIDS["measurementsUnitSensorState"])
    ext_states = snmpwalk(OIDS["measurementsExternalSensorState"])

    def ok(line):
        return any(x in line for x in ("INTEGER: 12", "ok(12)", "INTEGER: 4", "normal(4)"))

    bad_lines = []

    # 處理 unit sensors
    for line in unit_states:
        if not ok(line):
            m = re.match(r'.*::measurementsUnitSensorState\.(\d+)\.(\w+)\s+=\s+(.*)', line)
            sensor_info = line.split("=")[0].strip()
            sensor_status = line.split("=")[1].strip()
            value_display = ""
            if m:
                unit_idx, sensor_name, state_str = m.groups()
                value_oid = OIDS["measurementsUnitSensorValue"] + f".{unit_idx}.{sensor_name}"
                print(f"    DEBUG: snmpget({value_oid})")
                value = snmpget(value_oid)
                print(f"    DEBUG: SNMP reply = {repr(value)}")
                if value is not None:
                    val_num = re.search(r'INTEGER:\s*(-?\d+)', value)
                    value_display = f" [Value: {val_num.group(1)}]" if val_num else ""
            bad_lines.append(f"{sensor_info}: {sensor_status}{value_display}")

    # 處理 external sensors
    for line in ext_states:
        if not ok(line):
            m = re.match(r'.*::measurementsExternalSensorState\.(\d+\.\d+)\s+=\s+(.*)', line)
            if m:
                idx, sensor_status = m.group(1), m.group(2)
                typ, name = ext_info.get(idx, ("Unknown", "UnknownSensor"))
                # 只加 "1.1" 的第二碼（例如 1.1 → .1）
                value_oid = OIDS["measurementsExternalSensorValue"] + f".{idx.split('.')[1]}"
             #   print(f"    DEBUG: snmpget({value_oid})")
                value = snmpget(value_oid)
             #   print(f"    DEBUG: SNMP reply = {repr(value)}")
                value_display = ""
                if value is not None:
                    val_num = re.search(r'INTEGER:\s*(-?\d+)', value)
                    value_display = f" [Value: {val_num.group(1)}]" if val_num else ""
                bad_lines.append(f"ExternalSensor.{idx} ({name}): {sensor_status}{value_display}")
            else:
                bad_lines.append(line)

    if bad_lines:
        print("FAIL (下列感測器異常:)")
        for line in bad_lines:
            print("    " + line)
        return False
    print("PASS")
    return True

def check_reading_sanity():
    print("[5] Reading sanity: ", end="")
    ok = True

    # 處理 unit sensor
    values = snmpwalk(OIDS["measurementsUnitSensorValue"])
    mins = snmpwalk(OIDS["unitSensorMinimum"])
    maxs = snmpwalk(OIDS["unitSensorMaximum"])

    def extract_index_and_num(line):
        m = re.match(r'.*\.(\d+)\.(\w+)\s*=\s*\w+: *(-?\d+)', line)
        if m:
            idx = f"{m.group(1)}.{m.group(2)}"
            num = int(m.group(3))
            return idx, num
        return None, None

    unit_sensor_map = {}
    for line in values:
        idx, v = extract_index_and_num(line)
        if idx:
            unit_sensor_map[idx] = {"value": v}
    for line in mins:
        idx, v = extract_index_and_num(line)
        if idx and idx in unit_sensor_map:
            unit_sensor_map[idx]["min"] = v
    for line in maxs:
        idx, v = extract_index_and_num(line)
        if idx and idx in unit_sensor_map:
            unit_sensor_map[idx]["max"] = v

    for idx, d in unit_sensor_map.items():
        value, minv, maxv = d.get("value"), d.get("min"), d.get("max")
        print(f"\n    UnitSensor.{idx}: value={value}, min={minv}, max={maxv}", end="")
        if value is None or minv is None or maxv is None or not (minv <= value <= maxv):
            ok = False
            print("  [OUT OF RANGE]", end="")

    # External sensor: 顯示 Sensor 1.1 (溫度感測器)
    ext_info = get_external_sensor_info()

    ext_values = snmpwalk(OIDS["measurementsExternalSensorValue"])
    ext_mins = snmpwalk(OIDS["externalSensorMinimum"])
    ext_maxs = snmpwalk(OIDS["externalSensorMaximum"])

    ext_sensor_map = {}
    for line in ext_values:
        m = re.match(r'.*\.(\d+\.\d+)\s*=\s*\w+: *(-?\d+)', line)
        if m:
            idx = m.group(1)
            v = int(m.group(2))
            ext_sensor_map[idx] = {"value": v}
    for line in ext_mins:
        m = re.match(r'.*\.(\d+\.\d+)\s*=\s*\w+: *(-?\d+)', line)
        if m:
            idx, v = m.group(1), int(m.group(2))
            if idx in ext_sensor_map:
                ext_sensor_map[idx]["min"] = v
    for line in ext_maxs:
        m = re.match(r'.*\.(\d+\.\d+)\s*=\s*\w+: *(-?\d+)', line)
        if m:
            idx, v = m.group(1), int(m.group(2))
            if idx in ext_sensor_map:
                ext_sensor_map[idx]["max"] = v

    for idx, d in ext_sensor_map.items():
        value, minv, maxv = d.get("value"), d.get("min"), d.get("max")
        typ, name = ext_info.get(idx, ("Unknown", "UnknownSensor"))
        print(f"\n    Sensor {idx} ({name}): value={value}, min={minv}, max={maxv}", end="")
        if value is None or minv is None or maxv is None or not (minv <= value <= maxv):
            ok = False
            print("  [OUT OF RANGE]", end="")

    print("\n[5] Reading sanity: " + ("PASS" if ok else "FAIL"))
    return ok



def check_hw_failure_table():
    print("[7] HW-failure table: ", end="")
    entries = snmpwalk(OIDS["hwFailureTable"])
    if entries and not all("No Such" in e for e in entries):
        print("FAIL (failures present)")
        return False
    print("PASS")
    return True

def check_reliability_counters():
    print("[8] Reliability counters: ", end="")
    table = snmpwalk(OIDS["reliabilityDataTable"], community=RW_COMM)
    if not table:
        print("FAIL (no data)")
        return False
    ok = True
    for line in table:
        if ("reliabilityDataValue" in line or "reliabilityDataWorstValue" in line) and "Gauge32" in line:
            m = re.search(r'Gauge32: (\d+)', line)
            if m:
                num = int(m.group(1))
                if num < 99:
                    print(f"    Value {num} below 99: {line}")
                    ok = False
    print("PASS" if ok else "FAIL")
    return ok

def main():
    test_items = [
        ("[1] Identification", check_identification),
        ("[2] Reachability", check_reachability),
        ("[3a] Unit sensor presence", check_unit_sensor_presence),
        ("[3b] External sensor presence", check_external_sensor_presence),
        ("[4] Sensor state", check_sensor_state),
        ("[5] Reading sanity", check_reading_sanity),
        ("[7] HW-failure table", check_hw_failure_table),
        ("[8] Reliability counters", check_reliability_counters),
    ]
    results = []
    for name, func in test_items:
        result = func()
        results.append((name, result))

    all_pass = all(x[1] for x in results)
    print("\nFinal result:", "PASS" if all_pass else "FAIL")
    if not all_pass:
        failed = [x[0] for x in results if not x[1]]
        print("以下測項 FAIL：")
        for f in failed:
            print(f"  {f}")

if __name__ == "__main__":
    main()
    
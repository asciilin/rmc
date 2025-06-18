
# SNMP Verification Tool for PDU2-MIB

This tool provides a structured checklist for verifying SNMP implementation and device health/status on Raritan (or similar) PDUs using the PDU2-MIB schema. The tests ensure your Device Under Test (DUT) is reachable, sensors are present and healthy, values are sane, and system health counters report no issues.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Checklist Steps](#checklist-steps)
- [Example Usage](#example-usage)
- [Expected Output](#expected-output)
- [Troubleshooting](#troubleshooting)
- [Contact](#contact)

---

## Overview

This SNMP verification checklist covers:

1. Device Identification (model, firmware, serial)
2. Network Reachability (latency)
3. Sensor Presence (unit/external sensors)
4. Sensor State (normal/ok status)
5. Sensor Reading Sanity (in-range)
6. Min/Max Reset Validation
7. HW-Failure Table Check
8. Reliability Counters Review

Each step includes:
- Test objective
- SNMP commands to run
- Expected/pass criteria
- Example outputs

---

## Prerequisites

- Access to the DUT’s SNMP agent and network
- PDU2-MIB installed and accessible to SNMP tools (e.g., `snmpget`, `snmpwalk`, `snmpset`)
- SNMP v2c credentials (`public` for read, `private1` for write/set)
- Standard Linux command line (bash/zsh/etc.)

---

## Checklist Steps

### 1. Identification

**Objective:** Confirm device model, firmware, and serial number match the approved release.

**Commands:**
```bash
snmpget -v2c -c public <DUT_IP> PDU2-MIB::pduModel.1
snmpget -v2c -c public <DUT_IP> PDU2-MIB::boardFirmwareVersion.1.1.1
snmpget -v2c -c public <DUT_IP> PDU2-MIB::pduSerialNumber.1
```
**Pass:** Output values must match your release manifest.

---

### 2. Reachability

**Objective:** Verify network latency is under 200 ms.

**Command:**
```bash
time snmpget -v2c -c public <DUT_IP> PDU2-MIB::pduCount.0
```
**Pass:** `real` time < 0.2s (200ms).

---

### 3. Sensor Presence

#### 3-a. Unit Sensor Capability
**Objective:** At least one unit sensor supported.

**Command:**
```bash
snmpget -v2c -c public <DUT_IP> PDU2-MIB::unitDeviceCapabilities.1
```
**Pass:** At least one capability bit is set.

#### 3-a-2. Unit Sensor Presence
**Objective:** Every advertised unit sensor is available.

**Command:**
```bash
snmpwalk -v2c -c public <DUT_IP> PDU2-MIB::measurementsUnitSensorIsAvailable.1
```
**Pass:** Each relevant index returns `INTEGER: true(1)`.

#### 3-b. External Sensors
**Objective:** Detect and verify external sensors (e.g., temperature/humidity probes).

**Command:**
```bash
snmpwalk -v2c -c public <DUT_IP> PDU2-MIB::externalSensorType
snmpget -v2c -c public <DUT_IP> PDU2-MIB::measurementsExternalSensorIsAvailable.1.1
snmpget -v2c -c public <DUT_IP> PDU2-MIB::measurementsExternalSensorIsAvailable.1.2
```
**Pass:** At least one sensor is present, and all discovered sensors are available.

---

### 4. Sensor State

**Objective:** All sensors report a normal or OK state.

**Commands:**
```bash
# For built-in/unit sensors
snmpwalk -v2c -c public <DUT_IP> PDU2-MIB::measurementsUnitSensorState.1

# For external sensors
snmpwalk -v2c -c public <DUT_IP> PDU2-MIB::measurementsExternalSensorState.1
```
**Pass:** All entries = `ok(12)` (unit) or `normal(4)` (external).

---

### 5. Reading Sanity

**Objective:** Each sensor value is within its min/max range.

**Commands:**  
(Replace X with the relevant sensor index)
```bash
# Unit sensors
snmpget -v2c -c public <DUT_IP> PDU2-MIB::measurementsUnitSensorValue.1.X
snmpget -v2c -c public <DUT_IP> PDU2-MIB::unitSensorMinimum.1.X
snmpget -v2c -c public <DUT_IP> PDU2-MIB::unitSensorMaximum.1.X

# External sensors
snmpget -v2c -c public <DUT_IP> PDU2-MIB::measurementsExternalSensorValue.1.X
snmpget -v2c -c public <DUT_IP> PDU2-MIB::externalSensorMinimum.1.X
snmpget -v2c -c public <DUT_IP> PDU2-MIB::externalSensorMaximum.1.X
```
**Pass:** Value present and `Min ≤ Value ≤ Max`.

---

### 6. Min/Max Reset

**Objective:** Verify min/max reset functionality and validity.

**Commands:**  
(Replace X with the relevant sensor index)
```bash
snmpset -v2c -c private1 <DUT_IP> PDU2-MIB::externalSensorResetMinMax.1.X i 1
snmpget -v2c -c private1 <DUT_IP> PDU2-MIB::measurementsExternalSensorMinMaxValid.1.X
```
**Pass:** Set command accepted; validity remains true; min/max values reset then update over time.

---

### 7. HW-Failure Table

**Objective:** Confirm no asserted hardware failures.

**Command:**
```bash
snmpwalk -v2c -c public <DUT_IP> PDU2-MIB::hwFailureTable
```
**Pass:** Table is empty (SRC-0800 not supported).

---

### 8. Reliability Counters

**Objective:** Check health metrics like POH, checksum errors, fuse trips.

**Command:**
```bash
snmpwalk -v2c -c private1 <DUT_IP> PDU2-MIB::reliabilityDataTable
```
**Pass:** All DataValue ≥ 99, DataFlags = `00 00 00 00`, and no unexpected non-zero error bytes.

---

## Example Usage

Run each step in sequence as described above, replacing `<DUT_IP>` with your device's IP address.

---

## Expected Output

Sample OK outputs are included in the checklist (see above). For full details, refer to the "Example OK Output" column in the test table.

---

## Troubleshooting

- **Command not found:** Ensure `snmpget`, `snmpwalk`, and `snmpset` are installed (usually in `snmp` or `net-snmp` package).
- **Timeouts or unreachable device:** Verify network and SNMP settings on the DUT.
- **OID not found:** Ensure the PDU2-MIB file is loaded and present in your SNMP configuration.

---

## Contact

For issues, questions, or contributions, please contact the tool maintainer or open an issue in your project repository.

---

**Note:**  
- Modify command-line examples if your SNMP credentials or MIB paths differ.
- Always follow your organization’s security and change management policies when running verification steps on production hardware.

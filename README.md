# RMC Verifier SNMP

**RMC Verifier SNMP** is a Python tool specifically designed to verify RMC (Rack Management Controller) devices and their connected sensors via SNMP commands.  
It helps manufacturing and QA engineers quickly validate hardware identity and sensor functionality, ensuring devices meet expected release criteria.

---

## Features

- Verifies RMC device information (model, firmware version, serial number)
- Checks network reachability and SNMP communication
- Reads and validates sensor values (e.g., temperature, humidity)
- Outputs clear pass/fail results for each checklist step
- Easily customizable for additional SNMP OIDs or devices

---

## Requirements

- Python 3.7 or higher  
- SNMP command-line tools (`snmpget`, `snmpwalk`) **or** Python SNMP libraries (e.g., `pysnmp`)  
- **SRC/RMC MIB file**: `PDU2_MIB_4.3.0_51180.txt`

  **Download MIB here:**  
  [PDU2_MIB_4.3.0_51180.txt](https://cdn1.raritan.com/download/src-g2/4.3.0/PDU2_MIB_4.3.0_51180.txt)

  > *Place this MIB file alongside the script or in your SNMP tool's MIB directory.*

---

## Usage

1. **Download and prepare the MIB file**  
   Download `PDU2_MIB_4.3.0_51180.txt` from the link above and ensure it’s accessible to your SNMP tools.

2. **Configure your SNMP environment**  
   For command-line tools, set the MIB directory or use the `-m` option. Example (Linux):
   ```bash
   export MIBS=+PDU2_MIB_4.3.0_51180
   snmpget -v2c -c public -m PDU2_MIB_4.3.0_51180 10.0.0.1 PDU2-MIB::pduModel.1

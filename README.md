# RC Bridge - BLE to MQTT Gateway

A lightweight firmware for ESP32 that bridges Bluetooth Low Energy (BLE) devices with MQTT brokers. Originally developed for **Roger Chargers** (Electric Unicycle charging devices), this gateway can work with **any BLE device** if you know its communication protocol.

## Features

✨ **Core Functionality**
- BLE device discovery and bidirectional communication
- MQTT publish/subscribe for commands and responses
- Base64-encoded data transmission for reliability
- **Over-The-Air (OTA) firmware updates** with SHA256 verification
- WiFi and MQTT automatic reconnection

🛠️ **User-Friendly**
- **Setup Mode**: BLE-based configuration (no serial needed)
- **Gateway Mode**: Automatic operation once configured
- Factory reset via button (5-second hold)
- RGB LED status indicators for immediate feedback
- Detailed logging for troubleshooting

🔒 **Reliable**
- FreeRTOS task management for stable concurrent operations
- MQTT Last Will and Testament for offline detection
- Stream timeout protection during OTA downloads
- Message queuing when MQTT is disconnected
- Comprehensive error handling

## Hardware Requirements

- **Microcontroller**: ESP32 (tested on M5Stack Atom)
- **Connectivity**: Built-in WiFi and BLE
- **Button**: GPIO 39 for factory reset (optional, can be reset remotely)
- **Storage**: 4MB Flash minimum (OTA requires 2x firmware space)
- **Power**: 5V USB or battery

## Firmware Files

This repository contains pre-compiled firmware binaries:

- **`firmware.bin`** - Latest firmware binary (ready to flash)
- **`manifest.json`** - Metadata for OTA updates
  - Current version
  - Download URL
  - SHA256 checksum (for verification)
  - Update description


## Getting Started

### 1. Initial Firmware Flash

**Option A: Using PlatformIO (Recommended)**

1. Install [PlatformIO](https://platformio.org/)
2. Clone the source repository: `git clone https://github.com/blkfribourg/RCBridge.git`
3. Download `firmware.bin` from this repository
4. Flash via PlatformIO:
   ```bash
   platformio run -e esp32-custom --target upload
   ```

**Option B: Using ESP Flash Tool (GUI)**

1. Download [ESP Flash Download Tool](https://www.espressif.com/en/support/download/other-tools)
2. Download `firmware.bin` from this repository
3. Use the tool to flash at address `0x10000`

**Option C: Using esptool.py (Command Line)**

```bash
pip install esptool
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x10000 firmware.bin
```

### 2. Configuration

#### Option A: Via BLE Setup Mode (Recommended for first-time setup)

1. Upload the firmware without config file:
   ```bash
   pio run --target upload
   ```

2. Device will start in **BLE Setup Mode** (blue screen)

3. Connect to the device via BLE (name: `rc-bridge-setup-AABBCC` where AABBCC is the last 3 bytes of the device's MAC address)

4. Prepare your configuration JSON (see example below)

5. Send the configuration to the device via BLE characteristics

**How to send configuration via BLE:**

You can use any BLE app or write a script. Here's how the process works:

1. **Connect** to the device by name
2. **Find the service** `00001234-0000-1000-8000-00805f9b34fb`
3. **Write your JSON config** to characteristic `00001235-0000-1000-8000-00805f9b34fb` (config_write)
4. **Commit the config** by writing any value to characteristic `00001238-0000-1000-8000-00805f9b34fb` (commit)
5. **Read status** from characteristic `00001236-0000-1000-8000-00805f9b34fb` (config_status) to verify success
6. **Restart the device** by writing any value to characteristic `00001239-0000-1000-8000-00805f9b34fb` (restart)

**BLE Configuration Service UUIDs:**

| Characteristic | UUID | Purpose | Type |
|---|---|---|---|
| Service | `00001234-0000-1000-8000-00805f9b34fb` | Configuration service | N/A |
| Config Write | `00001235-0000-1000-8000-00805f9b34fb` | Write your JSON config here | Write |
| Config Status | `00001236-0000-1000-8000-00805f9b34fb` | Read status updates | Notify |
| Device Info | `00001237-0000-1000-8000-00805f9b34fb` | Device information | Read |
| Commit | `00001238-0000-1000-8000-00805f9b34fb` | Write to save config | Write |
| Restart | `00001239-0000-1000-8000-00805f9b34fb` | Write to reboot device | Write |

**Example Configuration JSON:**

```json
{
  "wifi": {
    "ssid": "YourWiFiSSID",
    "password": "YourWiFiPassword"
  },
  "mqtt": {
    "host": "your-broker.hivemq.cloud",
    "port": 8883,
    "username": "your-username",
    "password": "your-password",
    "client_id": "rc-bridge-001",
    "use_tls": true,
    "ca_cert": ""
  },
  "device": {
    "cmd_topic": "devices/rc-bridge-001/cmd",
    "resp_topic": "devices/rc-bridge-001/resp",
    "status_topic": "devices/rc-bridge-001/status",
    "heartbeat_topic": "devices/rc-bridge-001/heartbeat"
  },
  "ble": {
    "target_name": "RogerCharger",
    "target_address": "",
    "service_uuid": "6E400001-B5A3-F393-E0A9-E50E24DCCA9E",
    "char_uuid_write": "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",
    "char_uuid_notify": "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",
    "mtu": 256
  },
  "logging": {
    "level": "INFO"
  }
}
```

**Easy Setup with Python Script:**

The easiest way to configure your device is with the included Python script:

1. Install requirements:
   ```bash
   pip install bleak
   ```

2. Run the configuration script:
   ```bash
   python3 configure_ble.py
   ```

3. Follow the interactive prompts to enter:
   - WiFi SSID and password
   - MQTT broker details
   - Target BLE device name

4. The script will:
   - Find your RC Bridge device
   - Send the configuration over BLE
   - Save it to the device
   - Optionally restart the device into gateway mode

**Alternative 1: Manual JSON Upload via BLE App**

If you prefer using a BLE app like nRF Connect:

1. Connect to the device by name (`rc-bridge-setup-AABBCC`)
2. Find service `00001234-0000-1000-8000-00805f9b34fb`
3. Copy the example JSON configuration below and edit it with your settings
4. Write the JSON to characteristic `00001235-0000-1000-8000-00805f9b34fb` (config_write)
5. Write any value to characteristic `00001238-0000-1000-8000-00805f9b34fb` (commit)
6. Check characteristic `00001236-0000-1000-8000-00805f9b34fb` (config_status) for status - look for "committed" = success
7. Write any value to characteristic `00001239-0000-1000-8000-00805f9b34fb` (restart) to reboot

**Alternative 2: Manual Text/JSON File Method**

1. Create a file named `config.json` with the example JSON below (edit with your settings)
2. Use any BLE terminal or app to send the contents to the device
3. Follow steps 4-7 above

**Compact JSON Format (for BLE transmission):**

To save space when sending via BLE, use this compact format (no spaces):

```
{"wifi":{"ssid":"YourWiFiSSID","password":"YourPassword"},"mqtt":{"host":"broker.hivemq.cloud","port":8883,"username":"user","password":"pass","client_id":"rc-bridge-001","use_tls":true,"ca_cert":""},"device":{"cmd_topic":"devices/rc-bridge-001/cmd","resp_topic":"devices/rc-bridge-001/resp","status_topic":"devices/rc-bridge-001/status","heartbeat_topic":"devices/rc-bridge-001/heartbeat"},"ble":{"target_name":"RogerCharger","target_address":"","service_uuid":"6E400001-B5A3-F393-E0A9-E50E24DCCA9E","char_uuid_write":"6E400002-B5A3-F393-E0A9-E50E24DCCA9E","char_uuid_notify":"6E400003-B5A3-F393-E0A9-E50E24DCCA9E","mtu":256},"logging":{"level":"INFO"}}
```

### 3. Firmware Updates (OTA - Over-The-Air)

Once the device is connected to MQTT, you can update firmware without physical access!

**Check for Updates**

Send a command to the admin topic:

```bash
mosquitto_pub -h <broker> -p 8883 -u <username> -P <password> \
  -t "devices/<device-id>/admin" \
  -m "ota_check"
```

Device will respond on the status topic with available version or "up to date".

**Install Update**

```bash
mosquitto_pub -h <broker> -p 8883 -u <username> -P <password> \
  -t "devices/<device-id>/admin" \
  -m "ota_update"
```

The device will:
1. Download firmware from `https://raw.githubusercontent.com/blkfribourg/RCBridge-Firmware/main/firmware.bin`
2. Verify SHA256 checksum (from `manifest.json`)
3. Flash to OTA partition
4. **Reboot with new firmware**

**Status During Update**

- RGB LED shows **blue pulsing** while downloading
- Watch device logs (serial monitor) for progress
- If update fails, device returns to previous version and enters **red error state**

**Update Manifest**

The device reads update info from `manifest.json`:

```json
{
  "version": "1.0.1",
  "description": "Firmware update",
  "url": "https://raw.githubusercontent.com/blkfribourg/RCBridge-Firmware/main/firmware.bin",
  "sha256": "92c7059222fbf98b04980996425bec8077c8aef9309fde27c1ad7cc87a0fbd70"
}
```

This file is **automatically updated** by GitHub Actions when new firmware is released.

### 4. TLS/SSL and CA Certificate

The firmware supports TLS connections to secure MQTT brokers. Here's how to handle certificates:

**If you have a CA certificate** (e.g., AWS IoT Core, paid HiveMQ tier):

1. Download your broker's CA certificate (usually a `.pem` file)
2. Save as `data/certs/ca.pem`
3. Upload to LittleFS: `pio run --target uploadfs`
4. Enable in configuration: `"use_tls": true` and `"ca_cert": "/certs/ca.pem"`

**If your broker doesn't provide a certificate** (e.g., HiveMQ free tier):

The firmware automatically falls back to **insecure TLS** mode (certificate verification disabled). The connection is still encrypted, just without server verification.

### 5. MQTT Broker Setup

#### HiveMQ Cloud (Recommended)

1. Create a free account at [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)

2. Create a cluster and note:
   - Broker URL (e.g., `abc123.s1.eu.hivemq.cloud`)
   - Port: `8883` (TLS)
   - Username/password

3. Download the CA certificate from cluster settings

4. Update `config.json` with your HiveMQ credentials

#### Other MQTT Brokers

The gateway is compatible with any standard MQTT broker supporting:
- MQTT v3.1.1
- TLS/SSL (port 8883)
- Username/password authentication
- Last Will Testament (LWT)

Tested with:
- HiveMQ Cloud
- AWS IoT Core (requires device certificates)
- Mosquitto (with TLS configured)
- Azure IoT Hub (requires connection string conversion)

## Usage

### Gateway Operation

Once configured, the device will:

1. **Connect to WiFi** → Green status on display
2. **Connect to MQTT** → Subscribe to `cmd_topic`, publish `online` to `status_topic`
3. **Connect to BLE peripheral** → Negotiate MTU, subscribe to notifications
4. **Bridge data**:
   - MQTT → BLE: Receive base64 from `cmd_topic`, decode, forward to BLE
   - BLE → MQTT: Receive notifications, encode to base64, publish to `resp_topic`

### Sending Commands (MQTT → BLE)

Publish base64-encoded data to the command topic:

```bash
# Example: Send "Hello" to BLE device
echo -n "Hello" | base64  # SGVsbG8=
mosquitto_pub -h your-broker.hivemq.cloud -p 8883 --cafile ca.pem \
  -u username -P password \
  -t "devices/esp32-gateway-001/cmd" \
  -m "SGVsbG8="
```

### Receiving Responses (BLE → MQTT)

Subscribe to the response topic:

```bash
mosquitto_sub -h your-broker.hivemq.cloud -p 8883 --cafile ca.pem \
  -u username -P password \
  -t "devices/esp32-gateway-001/resp" \
  -v
```

Data will be base64-encoded. Decode with:

```bash
echo "SGVsbG8gV29ybGQ=" | base64 -d
```

### Status Monitoring

Subscribe to status topic for heartbeats:

```bash
mosquitto_sub -h your-broker.hivemq.cloud -p 8883 --cafile ca.pem \
  -u username -P password \
  -t "devices/esp32-gateway-001/status" \
  -v
```

Heartbeat includes:
```json
{
  "status": "online",
  "uptime": 12345,
  "free_heap": 123456,
  "wifi_rssi": -45
}
```

### Factory Reset

**Method 1: Button**
- Press and hold BtnA (GPIO 39) for 5+ seconds
- Display will show "FACTORY RESET"
- Device deletes config and reboots into BLE setup mode

**Method 2: MQTT Admin Command**
```bash
mosquitto_pub -h your-broker.hivemq.cloud -p 8883 --cafile ca.pem \
  -u username -P password \
  -t "devices/esp32-gateway-001/admin" \
  -m "reset"
```

## Logging

Log levels: `DEBUG`, `INFO`, `WARN`, `ERROR`, `NONE`

Configure in `config.json`:
```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

View logs via Serial Monitor:
```bash
pio device monitor -b 115200
```

## Troubleshooting

### WiFi won't connect
- Check SSID and password in config
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check serial logs for error messages

### MQTT connection fails
- Verify broker URL, port, username, password
- Check TLS certificate is valid
- Test broker with `mosquitto_pub`/`mosquitto_sub`
- Ensure firewall allows port 8883

### BLE device not found
- Verify `target_name` matches exactly
- Ensure BLE device is advertising
- Try using `target_address` instead of name
- Check BLE device is in range (<10m)

### MTU negotiation issues
- Some BLE devices don't support MTU > 23
- Check logs for negotiated MTU
- Adjust `max_payload_bytes` accordingly

### Message queue full
- MQTT disconnected for too long
- Increase `MAX_QUEUE_SIZE` in `mqtt_client.h`
- Check MQTT reconnection logic

## Advanced Configuration

### Custom BLE Service UUIDs

The default UUIDs are for Nordic UART Service (NUS). For custom services:

```json
{
  "ble": {
    "service_uuid": "12345678-1234-1234-1234-123456789abc",
    "char_uuid_write": "12345678-1234-1234-1234-123456789abd",
    "char_uuid_notify": "12345678-1234-1234-1234-123456789abe"
  }
}
```

### Payload Size Optimization

Maximum payload = MTU - 3 bytes (ATT overhead)

Example with MTU 256:
- `max_payload_bytes`: 253
- After base64 encoding: ~337 bytes MQTT payload

Adjust `mtu` in config:
```json
{
  "ble": {
    "mtu": 512
  }
}
```

### Reconnection Tuning

Edit constants in source files:
- `wifi_manager.cpp`: `BASE_RECONNECT_INTERVAL`, `MAX_RECONNECT_INTERVAL`
- `mqtt_client.cpp`: `BASE_RECONNECT_INTERVAL`, `MAX_RECONNECT_INTERVAL`

## LED Status Indicators

The RGB LED on the device shows status via color and animation:

| Mode | LED State | Meaning |
|------|-----------|---------|
| **Setup** | 🔷 Cyan pulsing | Waiting for BLE configuration (power on, no config) |
| **Normal** | 🟢 Green solid | Fully operational - all systems connected |
| **Errors** | 🔴 Red blinking | Connection errors (WiFi/MQTT/BLE down) |
| **OTA Download** | 🔵 Blue pulsing | Downloading firmware update |
| **OTA Success** | 🟢 Green rapid blink | Update successful (rebooting) |
| **OTA Failed** | 🔴 Red rapid blink | Update failed (check logs) |
| **Factory Reset** | ⚪ White rapid blink | Factory reset in progress |

**Note**: When in normal gateway mode with some errors, the LED will show a red blinking pattern indicating which system failed (WiFi/MQTT/BLE).

## Admin Commands (MQTT)

Send these to `devices/<device-id>/admin` topic:

| Command | Purpose |
|---------|---------|
| `ota_check` | Check for new firmware version |
| `ota_update` | Download and install new firmware |
| `reset` | Factory reset (erase config and reboot to setup mode) |

## Troubleshooting

### Device won't connect to WiFi
- Check SSID and password in BLE configuration
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Red LED indicates WiFi error

### BLE device not found
- Verify target device is powered on and advertising
- Check BLE device name spelling exactly
- Try using BLE device MAC address instead of name
- Red LED indicates BLE connection error

### OTA update fails
- Check WiFi and MQTT are connected (green LED)
- Verify firmware.bin is accessible from GitHub
- Check SHA256 mismatch errors in logs
- If stuck, hold reset button 5 seconds to recover

### MQTT messages not working
- Verify broker address, port, and credentials
- Check topic names match your configuration
- Confirm green LED (MQTT connected)
- Test MQTT connection with `mosquitto_pub`/`mosquitto_sub`

## Support

- Check logs via serial monitor (115200 baud): `pio device monitor`
- Verify WiFi/MQTT/BLE status with LED indicators
- Send `ota_check` to see detailed firmware version info
- Review MQTT broker logs for connection issues

## Dependencies

This firmware uses:
- [NimBLE-Arduino](https://github.com/h2zero/NimBLE-Arduino) - Bluetooth Low Energy
- [PubSubClient](https://github.com/knolleary/pubsubclient) - MQTT protocol
- [ArduinoJson](https://arduinojson.org/) - JSON configuration
- [FastLED](https://github.com/FastLED/FastLED) - RGB LED control

Built with [PlatformIO](https://platformio.org/) and Arduino framework.

---

**Project**: RC Bridge - BLE to MQTT Gateway
**Use Case**: Roger Chargers (Electric Unicycle), extensible to any BLE device
**Target**: M5Stack Atom (ESP32)
**License**: See source repository
**Status**: Active - Automatic firmware releases via GitHub Actions

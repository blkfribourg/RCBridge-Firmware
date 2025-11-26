#!/usr/bin/env python3
"""
RC Bridge BLE Configuration Script

This script configures an RC Bridge device via BLE without needing to upload firmware.
It connects to the device in setup mode and sends the configuration over BLE.

Requirements:
    pip install bleak

Usage:
    python3 configure_ble.py
"""

import asyncio
import json
import sys
from bleak import BleakClient, BleakScanner

# BLE Service and Characteristic UUIDs
CONFIG_SERVICE_UUID = "00001234-0000-1000-8000-00805f9b34fb"
CONFIG_WRITE_UUID = "00001235-0000-1000-8000-00805f9b34fb"
CONFIG_STATUS_UUID = "00001236-0000-1000-8000-00805f9b34fb"
DEVICE_INFO_UUID = "00001237-0000-1000-8000-00805f9b34fb"
COMMIT_UUID = "00001238-0000-1000-8000-00805f9b34fb"
RESTART_UUID = "00001239-0000-1000-8000-00805f9b34fb"

# Default configuration template
DEFAULT_CONFIG = {
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
        "use_tls": True,
        "ca_cert": ""
    },
    "device": {
        "cmd_topic": "devices/rc-bridge-001/cmd",
        "resp_topic": "devices/rc-bridge-001/resp",
        "status_topic": "devices/rc-bridge-001/status",
        "heartbeat_topic": "devices/rc-bridge-001/heartbeat"
    },
    "ble": {
        "target_name": "YourRogerChargerName",
        "target_address": "",
        "service_uuid": "0000FFE1-0000-1000-8000-00805F9B34FB",
        "char_uuid_write": "0000FFE3-0000-1000-8000-00805F9B34FB",
        "char_uuid_notify": "0000FFE2-0000-1000-8000-00805F9B34FB",
        "mtu": 256
    },
    "logging": {
        "level": "INFO"
    }
}


async def find_device(device_name_prefix="rc-bridge-setup"):
    """Scan for RC Bridge devices in setup mode"""
    print(f"Scanning for BLE devices with name starting with '{device_name_prefix}'...")
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name and device.name.startswith(device_name_prefix):
            print(f"✓ Found device: {device.name} ({device.address})")
            return device

    print("✗ No RC Bridge device found in setup mode")
    print("  Make sure your device is:")
    print("    1. Powered on")
    print("    2. In setup mode (no config yet, or factory reset)")
    print("    3. Within Bluetooth range")
    return None


async def configure_device(device_address, config):
    """Send configuration to device via BLE"""
    print(f"\nConnecting to {device_address}...")

    async with BleakClient(device_address) as client:
        print("✓ Connected to device")

        # Read device info
        try:
            device_info = await client.read_gatt_char(DEVICE_INFO_UUID)
            print(f"  Device info: {device_info.decode()}")
        except Exception as e:
            print(f"  (Could not read device info: {e})")

        # Prepare JSON config
        config_json = json.dumps(config, separators=(',', ':'))
        print(f"\nSending configuration ({len(config_json)} bytes)...")
        print(f"Configuration:\n{json.dumps(config, indent=2)}")

        # Write config in chunks (BLE has MTU limits, usually 20-512 bytes)
        chunk_size = 512
        for i in range(0, len(config_json), chunk_size):
            chunk = config_json[i:i+chunk_size]
            print(f"  Writing chunk {i//chunk_size + 1} ({len(chunk)} bytes)...", end="", flush=True)
            await client.write_gatt_char(CONFIG_WRITE_UUID, chunk.encode())
            print(" ✓")

        # Commit configuration
        print("\nCommitting configuration...")
        await client.write_gatt_char(COMMIT_UUID, b"\x01")

        # Wait a moment and read status
        await asyncio.sleep(0.5)
        try:
            status = await client.read_gatt_char(CONFIG_STATUS_UUID)
            status_text = status.decode('utf-8', errors='ignore')
            print(f"Device status: {status_text}")

            if "committed" in status_text.lower() or "ok" in status_text.lower():
                print("✓ Configuration saved successfully!")

                # Ask user if they want to restart
                response = input("\nRestart device now? (y/n): ").strip().lower()
                if response == 'y':
                    print("Restarting device...")
                    await client.write_gatt_char(RESTART_UUID, b"\x01")
                    print("Device is rebooting into gateway mode!")
                    print("\nNext steps:")
                    print("  1. Wait for device to reboot (~5 seconds)")
                    print("  2. Device should connect to WiFi and MQTT automatically")
                    print("  3. Check device LED status:")
                    print("     - 🟢 Green = Connected and ready")
                    print("     - 🔴 Red = Connection error (check WiFi/MQTT settings)")
                else:
                    print("Device not restarted. Configuration is saved.")
            else:
                print("✗ Configuration may not have been saved (unexpected status)")
        except Exception as e:
            print(f"✗ Error reading status: {e}")
            print("Configuration may still have been saved. Try restarting the device.")


def edit_config_interactive():
    """Interactive configuration editor"""
    config = DEFAULT_CONFIG.copy()

    print("=" * 60)
    print("RC Bridge BLE Configuration")
    print("=" * 60)

    # WiFi setup
    print("\n[WiFi Configuration]")
    config["wifi"]["ssid"] = input(f"WiFi SSID [{config['wifi']['ssid']}]: ") or config["wifi"]["ssid"]
    config["wifi"]["password"] = input(f"WiFi Password [{config['wifi']['password']}]: ") or config["wifi"]["password"]

    # MQTT setup
    print("\n[MQTT Configuration]")
    config["mqtt"]["host"] = input(f"MQTT Host [{config['mqtt']['host']}]: ") or config["mqtt"]["host"]
    config["mqtt"]["port"] = int(input(f"MQTT Port [{config['mqtt']['port']}]: ") or config["mqtt"]["port"])
    config["mqtt"]["username"] = input(f"MQTT Username [{config['mqtt']['username']}]: ") or config["mqtt"]["username"]
    config["mqtt"]["password"] = input(f"MQTT Password [{config['mqtt']['password']}]: ") or config["mqtt"]["password"]
    config["mqtt"]["client_id"] = input(f"Client ID [{config['mqtt']['client_id']}]: ") or config["mqtt"]["client_id"]

    # Device setup
    print("\n[Device Configuration]")
    device_id = input(f"Device ID [{config['mqtt']['client_id']}]: ") or config['mqtt']['client_id']
    config["device"]["cmd_topic"] = f"devices/{device_id}/cmd"
    config["device"]["resp_topic"] = f"devices/{device_id}/resp"
    config["device"]["status_topic"] = f"devices/{device_id}/status"
    config["device"]["heartbeat_topic"] = f"devices/{device_id}/heartbeat"
    print(f"  Topics will use prefix: devices/{device_id}/")

    # BLE Target setup
    print("\n[BLE Target Device]")
    config["ble"]["target_name"] = input(f"Target BLE Device Name [{config['ble']['target_name']}]: ") or config["ble"]["target_name"]

    return config


async def main():
    """Main entry point"""
    try:
        # Find device
        device = await find_device()
        if not device:
            sys.exit(1)

        # Ask user for configuration
        print("\nConfiguration options:")
        print("1. Interactive setup (edit each field)")
        print("2. Use default config (edit later via MQTT)")
        choice = input("Choose option (1-2): ").strip()

        if choice == "1":
            config = edit_config_interactive()
        else:
            config = DEFAULT_CONFIG.copy()

        # Send configuration
        await configure_device(device.address, config)

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("RC Bridge BLE Configuration Tool")
    print("=" * 60)

    # Check if bleak is installed
    try:
        import bleak
    except ImportError:
        print("Error: 'bleak' library not found")
        print("Install it with: pip install bleak")
        sys.exit(1)

    # Run async main
    asyncio.run(main())

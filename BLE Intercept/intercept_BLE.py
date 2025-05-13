import asyncio
import struct
from bleak import BleakClient, discover

# --- Configuration ---
# Replace with the actual address of your ESP32 device.
# You can find this by scanning for devices using a BLE scanner app or a simple bleak scanning script.
# Example: 'XX:XX:XX:XX:XX:XX'

# DEVICE_ADDRESS = "34:85:18:F8:27:CA"
DEVICE_ADDRESS = "34:85:18:F8:26:CE"

# Replace with the actual Service UUID your ESP32 is using for sensor data.
# This UUID is defined in your ESP32's BLE server code (likely in HF.h or related files).
# Example: "19B10000-E8F2-537E-4F6C-D104768A1214"
SERVICE_UUID = "9f3c872e-2f1b-4c58-bc2a-5a2e2f48f519"

# Replace with the actual Characteristic UUID where the FSR, POT, and TOF data is written.
# This UUID is also defined in your ESP32's BLE server code.
# Example: "19B10001-E8F2-537E-4F6C-D104768A1214"
CHARACTERISTIC_UUID = "2d8e1b65-9d11-43ea-b0f5-c51cb352ddfa"

# --- Notification Callback Function ---
# This function is called whenever the ESP32 sends a notification
def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print(f"Notification from {sender}: {data}")

    # --- Data Decoding ---
    # Assuming the ESP32 sends the three float values (FSR, POT, TOF)
    # packed together as binary data (3 floats, typically 4 bytes each).
    # The '<fff' format string means:
    # '<' : Little-endian byte order (common for ESP32)
    # 'fff': Three single-precision floating-point numbers
    # If your ESP32 sends the data as a string, you will need to decode it differently.
    try:
        # Unpack the bytes into three floats
        fsr_value, pot_value, tof_value = struct.unpack('<fff', data)
        print(f"Decoded Values:")
        print(f"  FSR: {fsr_value}")
        print(f"  POT: {pot_value}")
        print(f"  TOF: {tof_value}")
    except struct.error as e:
        print(f"Error unpacking data: {e}")
        print("Please check if the data format sent by the ESP32 matches the struct.unpack format ('<fff').")
        print("If your ESP32 sends data as a string, you'll need to decode it as a string instead of using struct.unpack.")
    print("-" * 20) # Separator for clarity


# --- Async Function to Connect and Read Continuously ---
async def run(address, characteristic_uuid):
    print(f"Attempting to connect to {address}...")
    async with BleakClient(address) as client:
        if client.is_connected:
            print(f"Connected to {address}")

            # Start subscribing to notifications from the characteristic
            # The notification_handler function will be called whenever data is sent
            print(f"Subscribing to notifications from characteristic {characteristic_uuid}...")
            await client.start_notify(characteristic_uuid, notification_handler)
            print("Subscribed. Waiting for data...")

            # Keep the connection alive and listen for notifications
            # This loop will run indefinitely until interrupted (e.g., Ctrl+C)
            while True:
                await asyncio.sleep(1) # Keep the async loop running

        else:
            print(f"Failed to connect to {address}")

# --- Main Execution ---
if __name__ == "__main__":
    if DEVICE_ADDRESS == "YOUR_ESP32_BLE_ADDRESS" or SERVICE_UUID == "YOUR_SERVICE_UUID" or CHARACTERISTIC_UUID == "YOUR_CHARACTERISTIC_UUID":
        print("Please update DEVICE_ADDRESS, SERVICE_UUID, and CHARACTERISTIC_UUID in the script.")
    else:
        try:
            # The run function now handles the continuous reading via notifications
            asyncio.run(run(DEVICE_ADDRESS, CHARACTERISTIC_UUID))
        except KeyboardInterrupt:
            print("Script interrupted by user.")
        except Exception as e:
            print(f"An error occurred: {e}")


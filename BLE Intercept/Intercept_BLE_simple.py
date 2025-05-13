import asyncio
import struct
import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner
from collections import deque
import time

# Configuration
DEVICE_NAME = "ReCover"
CHARACTERISTIC_UUID = "2d8e1b65-9d11-43ea-b0f5-c51cb352ddfa"
BUFFER_SIZE = 100

# Data Buffers
timestamps = deque(maxlen=BUFFER_SIZE)
fsr_values = deque(maxlen=BUFFER_SIZE)
pot_values = deque(maxlen=BUFFER_SIZE)
tof_values = deque(maxlen=BUFFER_SIZE)

# Initial values
timestamps.append(0)
fsr_values.append(0)
pot_values.append(0)
tof_values.append(0)

start_time = None

# Plot Setup
plt.ion()
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
fig.tight_layout(pad=3.0)
plt.subplots_adjust(hspace=0.4)

# Axis setup
ax1.set_ylabel('FSR (0-4095)')
ax1.set_ylim(0, 4095)

ax2.set_ylabel('POT (0-4095)')
ax2.set_ylim(0, 4095)

ax3.set_ylabel('TOF (mm)')
ax3.set_ylim(0, 100)
ax3.set_xlabel('Time (samples)')

# Notification handler
def notification_handler(sender, data):
    global start_time
    if start_time is None:
        start_time = time.time()
    try:
        # Unpack data (3 floats)
        fsr, pot, tof = struct.unpack('<fff', data)

        # Convert TOF to mm (assuming it's originally in mm)
        tof_mm = min(tof, 100.0)  # Clamp to 100mm max

        # Update buffers
        timestamps.append(timestamps[-1] + 1)
        fsr_values.append(min(fsr, 4095))
        pot_values.append(min(pot, 4095))
        tof_values.append(tof_mm)

        # Update plot
        ax1.cla()
        ax2.cla()
        ax3.cla()

        ax1.plot(timestamps, fsr_values, color='red')
        ax1.set_ylabel('FSR (0-4095)')
        ax1.set_ylim(0, 4095)
        ax1.grid(True)

        ax2.plot(timestamps, pot_values, color='green')
        ax2.set_ylabel('POT (0-4095)')
        ax2.set_ylim(0, 4095)
        ax2.grid(True)

        ax3.plot(timestamps, tof_values, color='blue')
        ax3.set_ylabel('TOF (mm)')
        ax3.set_ylim(0, 100)
        ax3.set_xlabel('Time (samples)')
        ax3.grid(True)

        plt.pause(0.01)

        print(f"FSR={fsr:.1f}, POT={pot:.1f}, TOF={tof_mm:.1f}mm")

    except struct.error as e:
        print(f"Data unpacking error: {e} | Raw: {data}")

# BLE connection loop
async def connect_and_listen():
    print(f"Scanning for device: {DEVICE_NAME}")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name == DEVICE_NAME if d.name else False
    )

    if device is None:
        print("Device not found.")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name}")
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("Disconnecting...")
            await client.stop_notify(CHARACTERISTIC_UUID)

# Run main loop
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(connect_and_listen())

    except Exception as e:
        print(f"Error: {e}")

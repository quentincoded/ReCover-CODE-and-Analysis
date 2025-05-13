import asyncio
from bleak import BleakClient
import matplotlib.pyplot as plt
from collections import deque
import struct

# ESP32_ADDRESS = "34:85:18:F8:27:DA"  # Change to your ESP32 BLE address
ESP32_ADDRESS = "32:85:18:f8:27:CA"
# CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # sensor test
CHARACTERISTIC_UUID = "A2d8e1b65-9d11-43ea-b0f5-c51cb352ddfa"  # ReCoverRun game

# Live plotting setup
window_size = 100
adc0_values = deque(maxlen=window_size)
adc1_values = deque(maxlen=window_size)
time_values = deque(maxlen=window_size)
time_values.append(0)
adc0_values.append(0)
adc1_values.append(0)


async def notification_handler(sender, data):
    """Handles incoming BLE data from ESP32."""
    try:
        # print(data)
        # print(data.decode())
        # decoded_data = data.decode("utf-8")  # Convert bytes to string
        # print(decoded_data)
        # adc0, adc1 = map(int, decoded_data.split(","))  # Convert to integers

        adc0, adc1 = struct.unpack("<HH", data)

        # Convert back to original values (assuming *10 scaling factor)
        fsr_mean = adc0 / 10.0
        pot_mean = adc1 / 10.0

        # Append new data to deques
        time_values.append(time_values[-1] + 1)
        adc0_values.append(fsr_mean)
        adc1_values.append(pot_mean)

        # Update the plot
        plt.cla()
        # plt.plot(time_values, adc0_values, label="ADC0 (Force Grip FSR)", color="blue")
        plt.plot(time_values, adc0_values, label="ADC0 (FSR)", color="blue")
        plt.plot(time_values, adc1_values, label="ADC4 (Potentiometer)", color="red")
        plt.xlabel("Time (samples)")
        plt.ylabel("ADC Value")
        plt.ylim(0, 4096)
        plt.legend()
        plt.pause(0.01)

        print(f"Received: ADC0={adc0}, ADC1={adc1}")

    except Exception as e:
        print(f"Error parsing data: {e}")


async def connect_and_listen():
    """Connects to ESP32 and listens for BLE notifications."""
    async with BleakClient(ESP32_ADDRESS) as client:
        print("Connected to ESP32! Listening for ADC data...")
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        # Keep the loop running to receive data
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("Disconnecting...")
            await client.stop_notify(CHARACTERISTIC_UUID)


# Run the asyncio event loop
if __name__ == "__main__":
    plt.ion()  # Enable interactive mode for real-time plotting
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_and_listen())

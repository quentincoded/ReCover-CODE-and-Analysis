import asyncio
import struct
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from bleak import BleakClient, BleakScanner
from collections import deque
import numpy as np
import warnings

# Suppress the specific warning about cache_frame_data
warnings.filterwarnings("ignore", category=UserWarning, 
                        message=".*frames=None.*cache_frame_data=True.*")

# --- Configuration ---
DEVICE_NAME = "ReCover"  # Name of your ESP32 BLE device

# UUID for the characteristic that sends sensor data
CHARACTERISTIC_UUID = "2d8e1b65-9d11-43ea-b0f5-c51cb352ddfa"

# Buffer size for plotting (how many data points to keep)
BUFFER_SIZE = 100

# Initialize the data buffers (deques are efficient for this purpose)
timestamps = deque(maxlen=BUFFER_SIZE)
fsr_values = deque(maxlen=BUFFER_SIZE)
pot_values = deque(maxlen=BUFFER_SIZE)
tof_values = deque(maxlen=BUFFER_SIZE)

# Initialize the figure and axes globally
fig = plt.figure(figsize=(12, 8))
ax1 = fig.add_subplot(3, 1, 1)
ax2 = fig.add_subplot(3, 1, 2)
ax3 = fig.add_subplot(3, 1, 3)

# Setup plot style
plt.style.use('dark_background')
fig.tight_layout(pad=3.0)
plt.subplots_adjust(hspace=0.3)

# Setup the three axes
ax1.set_ylabel('FSR (0-4095)')
ax1.set_title('Force Sensitive Resistor')
ax1.set_ylim(0, 4095)
ax1.grid(True, alpha=0.3)

ax2.set_ylabel('POT (0-4095)')
ax2.set_title('Potentiometer')
ax2.set_ylim(0, 4095)
ax2.grid(True, alpha=0.3)

ax3.set_ylabel('TOF (cm)')
ax3.set_title('Time of Flight Distance (cm)')
ax3.set_ylim(0, 50)  # 0-50cm range
ax3.grid(True, alpha=0.3)
ax3.set_xlabel('Time (s)')

# Initialize lines for each plot
line1, = ax1.plot([], [], 'r-', linewidth=2)
line2, = ax2.plot([], [], 'g-', linewidth=2)
line3, = ax3.plot([], [], 'b-', linewidth=2)

# Add legend to each plot
ax1.legend(['FSR'], loc='upper right')
ax2.legend(['POT'], loc='upper right')
ax3.legend(['TOF'], loc='upper right')

# Status text for connection info
connection_status = fig.text(0.02, 0.02, "Searching for device...", fontsize=10)

# Variables to control animation and BLE connection
connected = False
client = None
start_time = None
animation_running = True

# --- Notification Callback Function ---
def notification_handler(sender, data):
    global start_time
    
    # If this is the first data point, initialize the start time
    if start_time is None:
        start_time = time.time()
    
    current_time = time.time() - start_time
    
    try:
        # Unpack the bytes into three floats (FSR, POT, TOF)
        fsr_value, pot_value, tof_value = struct.unpack('<fff', data)
        
        # Convert TOF value to cm if it's in mm
        tof_value_cm = tof_value  # Assuming the value is already in cm based on your code
        
        # Append the new data to the buffers
        timestamps.append(current_time)
        fsr_values.append(min(fsr_value, 4095))  # Cap at 4095 to match ADC range
        pot_values.append(min(pot_value, 4095))  # Cap at 4095 to match ADC range
        tof_values.append(min(tof_value_cm, 50))  # Cap at 30cm
        
        # Print the values (optional)
        print(f"Time: {current_time:.2f}s, FSR: {fsr_value:.1f}, POT: {pot_value:.1f}, TOF: {tof_value_cm:.2f}cm")
        
    except struct.error as e:
        print(f"Error unpacking data: {e}")
        print(f"Raw data received: {data.hex()}")

# --- Function to update the plot ---
def update_plot(frame):
    if not animation_running:
        return []
    
    # Update the status text
    if connected:
        connection_status.set_text(f"Connected to {DEVICE_NAME}")
    else:
        connection_status.set_text("Searching for device...")
    
    # If no data yet, don't update the lines
    if len(timestamps) == 0:
        return [line1, line2, line3, connection_status]
    
    # Update the data for each line
    line1.set_data(list(timestamps), list(fsr_values))
    line2.set_data(list(timestamps), list(pot_values))
    line3.set_data(list(timestamps), list(tof_values))
    
    # Adjust x-axis limits to show the most recent data
    for ax in [ax1, ax2, ax3]:
        ax.set_xlim(max(0, timestamps[-1] - 10), timestamps[-1] + 0.5)
    
    return [line1, line2, line3, connection_status]

# --- Function to handle plot closure ---
def on_close(event):
    global animation_running
    print("Figure closed. Stopping animation and BLE connection.")
    animation_running = False
    plt.close('all')  # Force close any remaining plots

# --- Async Function to Connect to Device ---
async def connect_and_read():
    global connected, client
    
    print(f"Scanning for BLE device named '{DEVICE_NAME}'...")
    
    while animation_running:
        try:
            # Scan for the device by name
            device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name == DEVICE_NAME if d.name else False,
                timeout=5.0
            )
            
            if device is None:
                print(f"Device '{DEVICE_NAME}' not found. Retrying...")
                await asyncio.sleep(2)
                continue
            
            print(f"Found device: {device.name} ({device.address})")
            
            # Connect to the device
            client = BleakClient(device, timeout=10.0)
            await client.connect()
            
            if client.is_connected:
                print(f"Connected to {device.name}")
                connected = True
                
                # Subscribe to notifications
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                print("Subscribed to notifications. Waiting for data...")
                
                # Keep the connection alive
                while connected and animation_running:
                    await asyncio.sleep(0.01)
                
                # If we exited the loop but client is still connected, disconnect
                if client.is_connected:
                    await client.stop_notify(CHARACTERISTIC_UUID)
                    await client.disconnect()
                    print("Disconnected from device")
            else:
                print("Failed to connect to device")
                await asyncio.sleep(2)
            
        except Exception as e:
            print(f"BLE Error: {str(e)}")
            connected = False
            
            # If client exists and might be connected, try to disconnect
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
            
            await asyncio.sleep(2)  # Wait before retrying
            
    print("BLE connection task stopped")

# --- Main Function ---
async def main():
    # Register close event
    fig.canvas.mpl_connect('close_event', on_close)
    
    # Start the BLE connection task
    ble_task = asyncio.create_task(connect_and_read())
    
    # Create the animation with explicit save_count
    ani = FuncAnimation(
    fig, 
    update_plot, 
    frames=None,
    interval=50, 
    blit=False,  # <-- Changed from True to False
    save_count=100,
    cache_frame_data=False
)
    
    # Use a separate thread for the animation to avoid blocking the asyncio loop
    plt.show(block=False)
    
    # Keep the main loop running until animation is stopped
    while animation_running:
        await asyncio.sleep(0.01)
        plt.pause(0.001)  # Allow matplotlib to process events
    
    # Wait for BLE task to complete
    await ble_task
    print("Program completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user")
        animation_running = False
    except Exception as e:
        print(f"An error occurred: {e}")
        animation_running = False
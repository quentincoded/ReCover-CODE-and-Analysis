import asyncio
import struct
import time
import pandas as pd
import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner
import numpy as np
from scipy.optimize import curve_fit

# --- Configuration ---
DEVICE_NAME = "ReCover"  # Name of your ESP32 BLE device

# UUID for the characteristic that sends sensor data
CHARACTERISTIC_UUID = "2d8e1b65-9d11-43ea-b0f5-c51cb352ddfa"

# Calibration specific settings
NUM_DATAPOINTS_PER_WEIGHT = 5 # Number of readings to take for each weight (between 3 and 7)
STABILIZATION_DELAY = 2     # Seconds to wait for readings to stabilize after applying weight

# --- Global Data Buffer for Calibration ---
calibration_data = [] # List of dictionaries to store collected calibration data

# --- Global Control Flags and Objects ---
connected = False
client = None
current_calibration_samples = [] # Temporary buffer for samples during a single weight measurement

# --- Functions for Curve Fitting ---
# Define a polynomial function (e.g., quadratic) for fitting
def quadratic_func(x, a, b, c):
    return a * x**2 + b * x + c

# --- Notification Callback Function ---
# This function is called every time the ESP32 sends a BLE notification
def notification_handler(sender, data):
    global current_calibration_samples

    try:
        # Unpack the bytes into three floats (FSR, POT, TOF)
        # ESP32 sends FSR, POT, TOF as floats
        fsr_value, pot_value, tof_value_mm = struct.unpack('<fff', data)

        # In calibration mode, collect samples to a temporary buffer
        current_calibration_samples.append({
            "fsr_value": fsr_value,
            "tof_distance_mm": tof_value_mm
        })
        print(f"Calibrating: FSR={fsr_value:.1f}, ToF={tof_value_mm:.2f}mm (Sample {len(current_calibration_samples)})")

    except struct.error as e:
        print(f"Error unpacking data: {e}")
        print(f"Raw data received: {data.hex()}")
    except Exception as e:
        print(f"An unexpected error occurred in notification_handler: {e}")

# --- Async Function to Connect to Device ---
async def connect_to_device():
    global connected, client

    if client and client.is_connected:
        return True # Already connected

    print(f"Scanning for BLE device named '{DEVICE_NAME}'...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name == DEVICE_NAME if d.name else False,
        timeout=10.0 # Increased timeout for initial scan
    )

    if device is None:
        print(f"Device '{DEVICE_NAME}' not found.")
        return False

    print(f"Found device: {device.name} ({device.address})")

    try:
        client = BleakClient(device, timeout=20.0) # Increased timeout for connection
        await client.connect()

        if client.is_connected:
            print(f"Connected to {device.name}")
            connected = True
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            print("Subscribed to notifications.")
            return True
        else:
            print("Failed to connect to device.")
            return False
    except Exception as e:
        print(f"BLE Connection Error: {str(e)}")
        connected = False
        if client:
            try:
                await client.disconnect()
            except:
                pass
        return False

async def disconnect_from_device():
    global connected, client
    if client and client.is_connected:
        try:
            await client.stop_notify(CHARACTERISTIC_UUID)
            await client.disconnect()
            print("Disconnected from device.")
        except Exception as e:
            print(f"Error during BLE disconnect: {e}")
        finally:
            connected = False
            client = None

# --- Calibration Mode Function ---
async def run_calibration_mode():
    global current_calibration_samples, calibration_data

    print("\n--- Starting Calibration Data Collection ---")
    print("Please follow the prompts to collect data for different weights.")

    # Ensure connection before starting calibration
    if not await connect_to_device():
        print("Failed to connect to device. Cannot start calibration.")
        return

    while True:
        try:
            weight_input = input("\nEnter the applied weight in grams (e.g., 0, 50, 100) or 'd' when done: ")
            if weight_input.lower() == 'd':
                break

            try:
                current_weight = float(weight_input)
                if current_weight < 0:
                    print("Weight cannot be negative. Please enter a positive value or 0.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number or 'd'.")
                continue

            print(f"\n--- Collecting {NUM_DATAPOINTS_PER_WEIGHT} data points for {current_weight}g ---")
            print(f"Apply {current_weight}g to the elastic band and ensure it's stable.")
            print(f"Waiting {STABILIZATION_DELAY} seconds for stabilization...")
            await asyncio.sleep(STABILIZATION_DELAY)

            current_calibration_samples = [] # Clear buffer for new weight
            samples_collected = 0
            start_sample_time = time.time()

            while samples_collected < NUM_DATAPOINTS_PER_WEIGHT:
                # The notification_handler will automatically append to current_calibration_samples
                # We just need to wait for enough samples
                await asyncio.sleep(0.1) # Wait for a short period for a notification
                if len(current_calibration_samples) > samples_collected:
                    print(f"  Collected sample {len(current_calibration_samples)}/{NUM_DATAPOINTS_PER_WEIGHT}")
                    samples_collected = len(current_calibration_samples)
                # Add a timeout to prevent infinite waiting if data stops
                if time.time() - start_sample_time > 10: # 10 second timeout
                    print("  Timeout: Not enough samples received. Check ESP32 output.")
                    break

            if samples_collected > 0:
                # Add collected samples to the main calibration_data list
                for sample in current_calibration_samples:
                    calibration_data.append({
                        "weight_g": current_weight,
                        "fsr_value": sample["fsr_value"],
                        "tof_distance_mm": sample["tof_distance_mm"]
                    })
                print(f"  Successfully collected {samples_collected} samples for {current_weight}g.")
            else:
                print(f"  No valid data collected for {current_weight}g. Please re-check setup.")

        except KeyboardInterrupt:
            print("\nCalibration interrupted by user.")
            break
        except Exception as e:
            print(f"An error occurred during calibration step: {e}")

    print("\n--- Calibration Data Collection Complete ---")

    await disconnect_from_device() # Disconnect after calibration

    if calibration_data:
        df = pd.DataFrame(calibration_data)
        print("\nCollected Calibration Data:")
        print(df)

        # Save data to CSV
        output_filename = "calibration_data_ble.csv"
        df.to_csv(output_filename, index=False)
        print(f"\nData saved to {output_filename}")

        # --- Plotting ---
        print("\nGenerating plots...")

        plt.style.use('seaborn-v0_8-darkgrid') # Modern and clean style
        # plt.rcParams['font.family'] = 'Inter' # Set font to Inter

        # Plot 1: FSR vs. Weight0
        plt.figure(figsize=(10, 6))
        plt.scatter(df['weight_g'], df['fsr_value'], color='blue', label='Data Points', alpha=0.7)
        plt.title('FSR Value vs. Applied Weight', fontsize=16)
        plt.xlabel('Applied Weight (g)', fontsize=12)
        plt.ylabel('FSR Analog Value (0-4095)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)

        try:
            popt_fsr, pcov_fsr = curve_fit(quadratic_func, df['weight_g'], df['fsr_value'])
            x_fit_fsr = np.linspace(df['weight_g'].min(), df['weight_g'].max(), 100)
            y_fit_fsr = quadratic_func(x_fit_fsr, *popt_fsr)
            r_squared_fsr = np.corrcoef(df["fsr_value"], quadratic_func(df["weight_g"], *popt_fsr))[0, 1]**2
            plt.plot(x_fit_fsr, y_fit_fsr, color='red', linestyle='--', label=f'Quadratic Fit ($R^2$: {r_squared_fsr:.2f})')
            print(f"FSR vs. Weight Quadratic Fit: a={popt_fsr[0]:.4e}, b={popt_fsr[1]:.4e}, c={popt_fsr[2]:.4e}, R^2={r_squared_fsr:.2f}")
        except RuntimeError:
            print("Could not fit quadratic curve for FSR vs. Weight. Plotting without fit.")
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Plot 2: ToF Distance vs. Weight
        plt.figure(figsize=(10, 6))
        plt.scatter(df['weight_g'], df['tof_distance_mm'], color='green', label='Data Points', alpha=0.7)
        plt.title('ToF Distance vs. Applied Weight', fontsize=16)
        plt.xlabel('Applied Weight (g)', fontsize=12)
        plt.ylabel('ToF Distance (mm)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)

        try:
            popt_tof, pcov_tof = curve_fit(quadratic_func, df['weight_g'], df['tof_distance_mm'])
            x_fit_tof = np.linspace(df['weight_g'].min(), df['weight_g'].max(), 100)
            y_fit_tof = quadratic_func(x_fit_tof, *popt_tof)
            r_squared_tof = np.corrcoef(df["tof_distance_mm"], quadratic_func(df["weight_g"], *popt_tof))[0, 1]**2
            plt.plot(x_fit_tof, y_fit_tof, color='orange', linestyle='--', label=f'Quadratic Fit ($R^2$: {r_squared_tof:.2f})')
            print(f"ToF vs. Weight Quadratic Fit: a={popt_tof[0]:.4e}, b={popt_tof[1]:.4e}, c={popt_tof[2]:.4e}, R^2={r_squared_tof:.2f}")
        except RuntimeError:
            print("Could not fit quadratic curve for ToF vs. Weight. Plotting without fit.")
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Plot 3: FSR vs. ToF
        plt.figure(figsize=(10, 6))
        plt.scatter(df['tof_distance_mm'], df['fsr_value'], color='purple', label='Data Points', alpha=0.7)
        plt.title('FSR Value vs. ToF Distance', fontsize=16)
        plt.xlabel('ToF Distance (mm)', fontsize=12)
        plt.ylabel('FSR Analog Value (0-4095)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)

        try:
            popt_fsr_tof, pcov_fsr_tof = curve_fit(quadratic_func, df['tof_distance_mm'], df['fsr_value'])
            x_fit_fsr_tof = np.linspace(df['tof_distance_mm'].min(), df['tof_distance_mm'].max(), 100)
            y_fit_fsr_tof = quadratic_func(x_fit_fsr_tof, *popt_fsr_tof)
            r_squared_fsr_tof = np.corrcoef(df["fsr_value"], quadratic_func(df["tof_distance_mm"], *popt_fsr_tof))[0, 1]**2
            plt.plot(x_fit_fsr_tof, y_fit_fsr_tof, color='brown', linestyle='--', label=f'Quadratic Fit ($R^2$: {r_squared_fsr_tof:.2f})')
            print(f"FSR vs. ToF Quadratic Fit: a={popt_fsr_tof[0]:.4e}, b={popt_fsr_tof[1]:.4e}, c={popt_fsr_tof[2]:.4e}, R^2={r_squared_fsr_tof:.2f}")
        except RuntimeError:
            print("Could not fit quadratic curve for FSR vs. ToF. Plotting without fit.")
        plt.legend()
        plt.tight_layout()
        plt.show()

    else:
        print("No calibration data collected for plotting.")

# --- Main Function to run calibration ---
async def main():
    await run_calibration_mode()
    print("Program finished.")

if __name__ == "__main__":
    try:
        print("Starting BLE Calibration Script...")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")

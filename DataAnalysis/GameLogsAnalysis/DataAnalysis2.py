import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_sensor_data_subplots(csv_file):
    """
    Plots FSR vs time, POT vs time, and ToF vs time from sensor data
    in a single figure with three subplots.
    Boundaries are dynamically filled from 'Calibration data' and plotted as red lines.
    'SensorData' is plotted with default markers.

    Args:
        csv_file (str): Path to the CSV file containing the sensor data.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    # Ensure necessary columns exist, including 'Timestamp'
    required_columns = ['LogType', 'Timestamp', 'FSR', 'POT', 'ToF', 'MinPot', 'MaxPot', 'MinFsr', 'MaxFsr', 'MinTof', 'MaxTof']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: The CSV file must contain all of the following columns: {required_columns}")
        return

    # Convert 'Timestamp' to datetime objects for proper time-series plotting
    try:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    except Exception as e:
        print(f"Warning: Could not convert 'Timestamp' column to datetime. Plotting as-is. Error: {e}")

    # Sort by Timestamp to ensure correct forward fill of calibration data
    df = df.sort_values(by='Timestamp').reset_index(drop=True)

    # Define columns that hold calibration boundary values
    calibration_value_cols = ['MinFsr', 'MaxFsr', 'MinPot', 'MaxPot', 'MinTof', 'MaxTof']
    
    # Create new columns for propagated calibration values
    # Initialize them by setting non-calibration rows to NaN for these specific columns
    for col in calibration_value_cols:
        df[f'Propagated_{col}'] = df.apply(
            lambda row: row[col] if row['LogType'] == 'CalibrationData' else pd.NA, axis=1
        )
    
    # Forward fill the propagated calibration columns.
    # This will carry forward the last seen calibration value until a new one appears.
    df[[f'Propagated_{col}' for col in calibration_value_cols]] = df[[f'Propagated_{col}' for col in calibration_value_cols]].ffill()

    # Filter SensorData for plotting (it now implicitly carries the propagated calibration values)
    Sensor_df = df[df['LogType'] == 'SensorData'].copy()

    # Create a figure with 3 rows and 1 column for subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("FSR vs Time", "POT vs Time", "ToF vs Time")
    )

    # --- Subplot 1: FSR vs Time ---
    # Plot SensorData
    if not Sensor_df.empty:
        fig.add_trace(go.Scatter(
            x=Sensor_df['Timestamp'],
            y=Sensor_df['FSR'],
            mode='markers',
            name='SensorData (FSR)',
            marker=dict(size=5, opacity=0.7)
        ), row=1, col=1)

        # Plot Propagated Calibration Boundaries (lines for min/max FSR)
        # Only plot if there's any propagated data (i.e., if calibration data was found at all)
        if df['Propagated_MinFsr'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Timestamp'], # Use full timestamp range for boundary lines
                y=df['Propagated_MinFsr'],
                mode='lines',
                name='Min FSR Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False # Don't show legend for boundary lines to keep it clean
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df['Timestamp'],
                y=df['Propagated_MaxFsr'],
                mode='lines',
                name='Max FSR Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False
            ), row=1, col=1)
    
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_yaxes(title_text="FSR", row=1, col=1)


    # --- Subplot 2: POT vs Time ---
    # Plot SensorData
    if not Sensor_df.empty:
        fig.add_trace(go.Scatter(
            x=Sensor_df['Timestamp'],
            y=Sensor_df['POT'],
            mode='markers',
            name='SensorData (POT)',
            marker=dict(size=5, opacity=0.7)
        ), row=2, col=1)

        # Plot Propagated Calibration Boundaries (lines for min/max POT)
        if df['Propagated_MinPot'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Timestamp'],
                y=df['Propagated_MinPot'],
                mode='lines',
                name='Min POT Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=df['Timestamp'],
                y=df['Propagated_MaxPot'],
                mode='lines',
                name='Max POT Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False
            ), row=2, col=1)

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="POT", row=2, col=1)


    # --- Subplot 3: ToF vs Time ---
    # Plot SensorData
    if not Sensor_df.empty:
        fig.add_trace(go.Scatter(
            x=Sensor_df['Timestamp'],
            y=Sensor_df['ToF'],
            mode='markers',
            name='SensorData (ToF)',
            marker=dict(size=5, opacity=0.7)
        ), row=3, col=1)

        # Plot Propagated Calibration Boundaries (lines for min/max ToF)
        if df['Propagated_MinTof'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Timestamp'],
                y=df['Propagated_MinTof'],
                mode='lines',
                name='Min ToF Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False
            ), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=df['Timestamp'],
                y=df['Propagated_MaxTof'],
                mode='lines',
                name='Max ToF Boundary',
                line=dict(color="Red", width=2, dash="dash"),
                showlegend=False
            ), row=3, col=1)

    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="ToF", row=3, col=1)

    # Update overall layout
    fig.update_layout(
        title_text="Sensor Data Analysis over Time",
        showlegend=True,
        height=900, # Adjusted height for 3 rows
        width=900 # Adjusted width
    )

    fig.write_html("sensor_data_time_series_subplots_plot.html")
    print("Saved combined time-series plot to sensor_data_time_series_subplots_plot.html")

# To run the script, save the above code as a .py file (e.g., plot_data_time_series.py)
# and then call the function with your CSV file:
# plot_sensor_data_subplots('test2.csv')
if __name__ == "__main__":
    # Example usage
    plot_sensor_data_subplots('test2.csv')  # Replace with your actual CSV file path    
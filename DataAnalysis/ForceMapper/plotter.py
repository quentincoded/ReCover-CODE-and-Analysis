import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Define the path to the CSV file
csv_file_path = 'DataAnalysis/ForceMapper/Real_calibration_data_ble.csv'

# Define the output directory where the HTML plots will be saved
# You can change this path to any directory you prefer.
output_directory = 'DataAnalysis/ForceMapper' # Example: 'C:/Users/YourUser/Documents/MyPlots' or './Plots'

# Create the output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
    print(f"Created output directory: {output_directory}")

# Check if the CSV file exists
if not os.path.exists(csv_file_path):
    print(f"Error: The file '{csv_file_path}' was not found.")
    print("Please ensure 'Real_calibration_data_ble.csv' is in the specified directory.")
    exit()

# Read the CSV file into a pandas DataFrame
try:
    df = pd.read_csv(csv_file_path)
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit()

# Extract the relevant columns from the DataFrame
try:
    fsr = df['fsr_value'].values
    tof = df['tof_distance_mm'].values
    weight = df['weight_g'].values
except KeyError as e:
    print(f"Error: Missing expected column in CSV file: {e}")
    print("Please ensure your CSV has 'fsr_value', 'tof_distance_mm', and 'weight_g' columns.")
    exit()

# --- Quadratic Fit Calculations ---

# 1. Quadratic Fit for FSR vs. Weight
poly_fsr_weight_coeffs = np.polyfit(weight, fsr, 2)
fsr_weight_fit_line_func = np.poly1d(poly_fsr_weight_coeffs)
weight_for_fit = np.linspace(min(weight), max(weight), 100)
fsr_fit_values = fsr_weight_fit_line_func(weight_for_fit)

# 2. Quadratic Fit for ToF vs. Weight
poly_tof_weight_coeffs = np.polyfit(weight, tof, 2)
tof_weight_fit_line_func = np.poly1d(poly_tof_weight_coeffs)
tof_fit_values = tof_weight_fit_line_func(weight_for_fit)

# 3. Quadratic Fit for ToF vs. FSR (axes switched)
poly_tof_fsr_coeffs = np.polyfit(tof, fsr, 2)
tof_fsr_fit_line_func = np.poly1d(poly_tof_fsr_coeffs)
tof_for_fit = np.linspace(min(tof), max(tof), 100)
fsr_tof_fit_values = tof_fsr_fit_line_func(tof_for_fit)


# --- Create Plotly Figure 1: FSR and ToF vs. Weight ---

fig1 = make_subplots(specs=[[{"secondary_y": True}]])

fig1.add_trace(
    go.Scatter(x=weight, y=fsr, mode='markers', name='FSR Data',
               marker=dict(color='#4299e1', size=8, opacity=0.8)),
    secondary_y=False,
)

fig1.add_trace(
    go.Scatter(x=weight_for_fit, y=fsr_fit_values, mode='lines', name='FSR Quadratic Fit',
               line=dict(color='#2b6cb0', width=2, dash='dash')),
    secondary_y=False,
)

fig1.add_trace(
    go.Scatter(x=weight, y=tof, mode='markers', name='ToF Data',
               marker=dict(color='#f56565', size=8, opacity=0.8)),
    secondary_y=True,
)

fig1.add_trace(
    go.Scatter(x=weight_for_fit, y=tof_fit_values, mode='lines', name='ToF Quadratic Fit',
               line=dict(color='#c53030', width=2, dash='dash')),
    secondary_y=True,
)

fig1.update_layout(
    title_text='FSR and ToF vs. Weight with Quadratic Fits',
    xaxis_title='Weight',
    hovermode='x unified',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)', bordercolor='#ccc', borderwidth=1),
    margin=dict(l=60, r=60, t=70, b=60),
    plot_bgcolor='#fcfcfc',
    paper_bgcolor='#ffffff',
    font=dict(family='Inter, sans-serif')
)

fig1.update_yaxes(title_text='FSR Value', secondary_y=False, title_font=dict(color='#4299e1'), tickfont=dict(color='#4299e1'))
fig1.update_yaxes(title_text='ToF Value', secondary_y=True, title_font=dict(color='#f56565'), tickfont=dict(color='#f56565'))

# Construct the full path for the first output file
output_html_file1 = os.path.join(output_directory, 'fsr_tof_vs_weight_plot.html')
fig1.write_html(output_html_file1, auto_open=False)
print(f"Plot 1 saved to: {output_html_file1}")


# --- Create Plotly Figure 2: FSR vs. ToF (axes switched) ---

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(x=tof, y=fsr, mode='markers', name='ToF vs. FSR Data',
               marker=dict(color='#48bb78', size=8, opacity=0.8))
)

fig2.add_trace(
    go.Scatter(x=tof_for_fit, y=fsr_tof_fit_values, mode='lines', name='ToF vs. FSR Quadratic Fit',
               line=dict(color='#38a169', width=2, dash='dash'))
)

fig2.update_layout(
    title_text='ToF vs. FSR with Quadratic Fit',
    xaxis_title='ToF Value',
    yaxis_title='FSR Value',
    hovermode='closest',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)', bordercolor='#ccc', borderwidth=1),
    margin=dict(l=60, r=60, t=70, b=60),
    plot_bgcolor='#fcfcfc',
    paper_bgcolor='#ffffff',
    font=dict(family='Inter, sans-serif')
)

# Construct the full path for the second output file
output_html_file2 = os.path.join(output_directory, 'fsr_vs_tof_plot.html')
fig2.write_html(output_html_file2, auto_open=False)
print(f"Plot 2 saved to: {output_html_file2}")

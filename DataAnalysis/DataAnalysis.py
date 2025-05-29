import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Wichtig: Für separate Subplots
import numpy as np

def plot_sensor_data(csv_file_path):
    """
    Erstellt interaktive Plots von FSR, POT und ToF Werten aus einer CSV-Datei.
    Die Min/Max-Kalibrationswerte werden als rote Barrieren dargestellt.

    Args:
        csv_file_path (str): Der Pfad zur CSV-Datei.
    """
    try:
        df = pd.read_csv(csv_file_path)
        # Strippe Whitespace aus allen Spaltennamen
        df.columns = df.columns.str.strip()

        # Strippe Whitespace aus der ganzen DataFrame für alle object-Spalten (inkl. 'LogType')
        df = df.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    except FileNotFoundError:
        print(f"Fehler: Die Datei '{csv_file_path}' wurde nicht gefunden.")
        return
    except Exception as e:
        print(f"Fehler beim Lesen der CSV-Datei: {e}")
        return

    # Konvertiere 'Timestamp' Spalte in datetime Objekte
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Extrahiere Kalibrationsdaten
    # Überprüfe, ob die 'LogType'-Spalte existiert
    if 'LogType' not in df.columns:
        print("Fehler: 'LogType'-Spalte nicht in der CSV-Datei gefunden.")
        print("Stellen Sie sicher, dass die CSV-Datei die erwartete Struktur hat.")
        return

    # Entferne führende/nachfolgende Leerzeichen aus der 'LogType'-Spalte,
    # um Probleme bei der Filterung zu vermeiden
    df['LogType'] = df['LogType'].astype(str).str.strip()
    
    calibration_rows = df[df['LogType'] == 'CalibrationData']

    min_pot, max_pot = None, None
    min_fsr, max_fsr = None, None
    min_tof, max_tof = None, None

    if calibration_rows.empty:
        print("Warnung: Keine 'CalibrationData'-Zeilen in der CSV-Datei gefunden.")
        print("Stellen Sie sicher, dass die 'LogType'-Spalte 'CalibrationData' korrekt enthält (Groß-/Kleinschreibung und keine Leerzeichen).")
        print("Der Plot wird ohne Kalibrationsgrenzen erstellt.")
    else:
        calibration_data = calibration_rows.iloc[0] # Nehme die erste Zeile mit CalibrationData
        # Konvertiere Kalibrationswerte zu numerischen Werten, behandle Fehler mit NaN
        min_pot = pd.to_numeric(calibration_data['MinPot'], errors='coerce')
        max_pot = pd.to_numeric(calibration_data['MaxPot'], errors='coerce')
        min_fsr = pd.to_numeric(calibration_data['MinFsr'], errors='coerce')
        max_fsr = pd.to_numeric(calibration_data['MaxFsr'], errors='coerce')
        min_tof = pd.to_numeric(calibration_data['MinTof'], errors='coerce')
        max_tof = pd.to_numeric(calibration_data['MaxTof'], errors='coerce')

    # Filtere nur die SensorData für die Plots
    sensor_df = df[df['LogType'] == 'SensorData'].copy()

    # Stellen Sie sicher, dass die Sensorwerte numerisch sind
    sensor_df['FSR'] = pd.to_numeric(sensor_df['FSR'], errors='coerce')
    sensor_df['POT'] = pd.to_numeric(sensor_df['POT'], errors='coerce')
    sensor_df['ToF'] = pd.to_numeric(sensor_df['ToF'], errors='coerce')

    # Entferne Reihen mit NaN Werten in FSR, POT oder ToF, die durch 'coerce' entstehen könnten (falls nicht numerisch)
    sensor_df.dropna(subset=['FSR', 'POT', 'ToF'], inplace=True)

    if sensor_df.empty:
        print("Fehler: Keine 'SensorData'-Zeilen in der CSV-Datei gefunden, die geplottet werden können.")
        print("Stellen Sie sicher, dass die 'LogType'-Spalte 'SensorData' korrekt enthält und Sensorwerte numerisch sind.")
        return

    # Erstelle die Plots mit make_subplots für separate Achsen
    fig = make_subplots(rows=3, cols=1,
                        shared_xaxes=True, # X-Achse (Zeitstempel) wird geteilt
                        vertical_spacing=0.05, # Vertikaler Abstand zwischen den Subplots
                        subplot_titles=('FSR Values', 'POT Values', 'ToF Values')) # Titel für jeden Subplot

    # FSR Plot
    fig.add_trace(go.Scatter(x=sensor_df['Timestamp'], y=sensor_df['FSR'], mode='lines', name='FSR',
                             line=dict(color='blue')), row=1, col=1)
    # Füge horizontale Linien für Min/Max FSR hinzu, falls Werte vorhanden und nicht NaN
    if min_fsr is not None and max_fsr is not None and not np.isnan(min_fsr) and not np.isnan(max_fsr):
        fig.add_hline(y=min_fsr, line_dash="dot", line_color="red", annotation_text=f"Min FSR ({min_fsr:.2f})", annotation_position="top right", row=1, col=1)
        fig.add_hline(y=max_fsr, line_dash="dot", line_color="red", annotation_text=f"Max FSR ({max_fsr:.2f})", annotation_position="bottom right", row=1, col=1)

    # POT Plot
    fig.add_trace(go.Scatter(x=sensor_df['Timestamp'], y=sensor_df['POT'], mode='lines', name='POT',
                             line=dict(color='green')), row=2, col=1)
    # Füge horizontale Linien für Min/Max POT hinzu, falls Werte vorhanden und nicht NaN
    if min_pot is not None and max_pot is not None and not np.isnan(min_pot) and not np.isnan(max_pot):
        fig.add_hline(y=min_pot, line_dash="dot", line_color="red", annotation_text=f"Min POT ({min_pot:.2f})", annotation_position="top right", row=2, col=1)
        fig.add_hline(y=max_pot, line_dash="dot", line_color="red", annotation_text=f"Max POT ({max_pot:.2f})", annotation_position="bottom right", row=2, col=1)

    # ToF Plot
    fig.add_trace(go.Scatter(x=sensor_df['Timestamp'], y=sensor_df['ToF'], mode='lines', name='ToF',
                             line=dict(color='purple')), row=3, col=1)
    # Füge horizontale Linien für Min/Max ToF hinzu, falls Werte vorhanden und nicht NaN
    if min_tof is not None and max_tof is not None and not np.isnan(min_tof) and not np.isnan(max_tof):
        fig.add_hline(y=min_tof, line_dash="dot", line_color="red", annotation_text=f"Min ToF ({min_tof:.2f})", annotation_position="top right", row=3, col=1)
        fig.add_hline(y=max_tof, line_dash="dot", line_color="red", annotation_text=f"Max ToF ({max_tof:.2f})", annotation_position="bottom right", row=3, col=1)

    # Update layout für alle Subplots
    fig.update_layout(
        title_text="Sensorwerte (FSR, POT, ToF) mit Kalibrationsgrenzen",
        xaxis_title="Zeitstempel",
        height=900, # Höhe des gesamten Plots
        hovermode="x unified" # Verbessert die Interaktivität beim Hovern über alle Subplots
    )

    # Speichern des Plots als HTML-Datei
    output_html_file = "sensor_data_plot.html"
    fig.write_html(output_html_file)
    print(f"Der Plot wurde erfolgreich als '{output_html_file}' gespeichert.")
    print("Öffne die HTML-Datei in deinem Webbrowser, um den interaktiven Plot anzuzeigen.")

# --- Beispiel für die Nutzung des Skripts ---
# Dieser Teil wird nur ausgeführt, wenn das Skript direkt gestartet wird.
if __name__ == "__main__":
    csv_file = "test2.csv" # Hier wird der Dateiname deiner CSV-Datei festgelegt
    # create_dummy_csv(csv_file) # Diese Zeile ist auskommentiert, da du deine eigene Datei hast
    plot_sensor_data(csv_file)


import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from aws_download import download_directory  # renew_directory not used here
from datetime import datetime
from pytz import timezone

# Download data
download_directory('capwater', '', './capwater/')

# Load and merge capwater CSV files
folder_v = './capwater'
csv_files = [f for f in os.listdir(folder_v) if f.startswith('cap_')]

data_frames = []
for file in csv_files:
    file_path = os.path.join(folder_v, file)
    try:
        df = pd.read_csv(file_path)
        if df.empty or df.shape[1] == 0:
            print(f"Skipping empty file: {file_path}")
            continue
        data_frames.append(df)
    except pd.errors.EmptyDataError:
        print(f"Skipping empty file due to EmptyDataError: {file_path}")
        continue

if not data_frames:
    raise ValueError("No valid CSV files found to process.")

df_cap = pd.concat(data_frames)
df_cap['Timestamp'] = pd.to_datetime(df_cap['Timestamp'])


# Optional: Filter outliers if needed
# df_cap = df_cap[df_cap['Delta_pF'] <= 2000]  # Change threshold as needed

# Create subplots
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
    subplot_titles=('Delta pF', 'CH0 and CH1 (raw pF)'), row_heights=[0.3, 0.7]
)

# Plot Delta_pF
fig.add_trace(go.Scatter(
    x=df_cap['Timestamp'], y=df_cap['Delta_pF'],
    mode='markers', name='Delta_pF', marker=dict(color='red', size=4)
), row=1, col=1)

# Plot CH0_pF and CH1_pF
fig.add_trace(go.Scatter(
    x=df_cap['Timestamp'], y=df_cap['CH0_pF'],
    mode='markers', name='CH0_pF', line=dict(color='blue')
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=df_cap['Timestamp'], y=df_cap['CH1_pF'],
    mode='markers', name='CH1_pF', line=dict(color='green')
), row=2, col=1)

# Add daylight rectangles (7am–8pm)
all_dates = pd.to_datetime(df_cap['Timestamp']).dt.date.unique()
for day in all_dates:
    fig.add_vrect(
        x0=f"{day} 9:00:00", x1=f"{day} 18:00:00",
        fillcolor="yellow", opacity=0.2, layer="below", line_width=0
    )

fig.update_layout(
    # height=600, width=1400,
    title_text='Capacitive Sensor Data (Pothos)',
    showlegend=True
)

fig.update_xaxes(nticks=20, showticklabels=True)
fig.show()

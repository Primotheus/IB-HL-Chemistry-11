#!/usr/bin/env python3
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt

# locate files relative to this script
BASE = Path(__file__).resolve().parent
HEAT_CSV = BASE / "heatingcurve_lauricacid.csv"
COOL_CSV = BASE / "coolingcurve_lauricacid.csv"
OUT_DIR = BASE / "plots"
OUT_DIR.mkdir(exist_ok=True)

def find_time_temp_columns(df):
    # return (time_col, temp_col) using simple keyword matching
    cols = list(df.columns)
    time_col = None
    temp_col = None
    for c in cols:
        cl = c.lower()
        if 'time' in cl and time_col is None:
            time_col = c
        if ('temp' in cl or 'temperature' in cl) and temp_col is None:
            temp_col = c
    # fallback heuristics: first two numeric columns
    if time_col is None or temp_col is None:
        numeric = [c for c in cols if pd.to_numeric(df[c], errors='coerce').notna().any()]
        if len(numeric) >= 2:
            if time_col is None:
                time_col = numeric[0]
            if temp_col is None:
                temp_col = numeric[1]
    return time_col, temp_col


def load_curve(path, preferred_prefix=None):
    if not path.exists():
        print(f"Warning: file not found: {path}")
        return None
    df = pd.read_csv(path)

    # If a preferred_prefix is provided, try to use columns containing that prefix
    if preferred_prefix is not None:
        wl_col = None
        y_col = None
        for c in df.columns:
            cl = c.lower()
            if preferred_prefix.lower() in cl and 'time' in cl:
                wl_col = c
            if preferred_prefix.lower() in cl and ('temp' in cl or 'temperature' in cl):
                y_col = c
        if wl_col and y_col:
            tcol, ycol = wl_col, y_col
        else:
            tcol, ycol = find_time_temp_columns(df)
    else:
        tcol, ycol = find_time_temp_columns(df)

    if tcol is None or ycol is None:
        print(f"Could not identify time/temp columns in {path}. Columns: {list(df.columns)}")
        return None
    df = df[[tcol, ycol]].copy()
    df.columns = ['time', 'temp']
    df['time'] = pd.to_numeric(df['time'], errors='coerce')
    df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
    df = df.dropna(subset=['time', 'temp'])
    return df

# load both curves
# prefer Run 2 columns for the heating file if present
heat = load_curve(HEAT_CSV, preferred_prefix='Run 2')
cool = load_curve(COOL_CSV)

# plotting
if heat is None and cool is None:
    raise SystemExit('No data to plot.')

# prefer seaborn darkgrid if available, otherwise fall back
try:
    plt.style.use("seaborn-darkgrid")
except Exception:
    try:
        plt.style.use("seaborn")
    except Exception:
        plt.style.use("default")

# overlay plot
fig, ax = plt.subplots(figsize=(8,5))
if heat is not None:
    ax.plot(heat['time'], heat['temp'], label='Heating', color='crimson')
if cool is not None:
    ax.plot(cool['time'], cool['temp'], label='Cooling', color='royalblue')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('Lauric acid — Heating and Cooling curves')
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
over_path = OUT_DIR / 'lauric_heating_cooling_overlay.png'
fig.savefig(over_path, dpi=150)
plt.close(fig)
print(f"Saved overlay plot -> {over_path}")

# separate subplots
fig, axes = plt.subplots(2,1,figsize=(8,8), sharex=True)
if heat is not None:
    axes[0].plot(heat['time'], heat['temp'], color='crimson')
    axes[0].set_title('Heating curve')
    axes[0].set_ylabel('Temperature (°C)')
    axes[0].grid(alpha=0.3)
else:
    axes[0].text(0.5,0.5,'Heating data not found', ha='center')

if cool is not None:
    axes[1].plot(cool['time'], cool['temp'], color='royalblue')
    axes[1].set_title('Cooling curve')
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Temperature (°C)')
    axes[1].grid(alpha=0.3)
else:
    axes[1].text(0.5,0.5,'Cooling data not found', ha='center')

fig.tight_layout()
sep_path = OUT_DIR / 'lauric_heating_and_cooling_separate.png'
fig.savefig(sep_path, dpi=150)
plt.close(fig)
print(f"Saved separate plots -> {sep_path}")

# also save CSVs of cleaned data for reference
if heat is not None:
    hp = OUT_DIR / 'heating_cleaned.csv'
    heat.to_csv(hp, index=False)
    print(f"Saved cleaned heating data -> {hp}")
if cool is not None:
    cp = OUT_DIR / 'cooling_cleaned.csv'
    cool.to_csv(cp, index=False)
    print(f"Saved cleaned cooling data -> {cp}")

print('Done.')

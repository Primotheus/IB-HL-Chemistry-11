from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# locate data file (same folder as this script)
DATA_PATH = Path(__file__).resolve().parent / "temp.csv"
OUT_DIR = Path(__file__).resolve().parent / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_PATH.exists():
    raise SystemExit(f"Data file not found: {DATA_PATH}")

# read CSV
df = pd.read_csv(DATA_PATH)
# normalize column names (remove trailing colons/spaces)
df.columns = [c.strip().replace(':', '') for c in df.columns]
# ensure numeric
df[df.columns] = df[df.columns].apply(pd.to_numeric, errors='coerce')

time_col = df.columns[0]
solvents = ['Water', 'Acetone', 'Ethanol']

for sol in solvents:
    if sol not in df.columns:
        print(f"Warning: column '{sol}' not found in data; skipping")
        continue
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df[time_col], df[sol], marker='o', linestyle='-', color='tab:blue')
    ax.set_xlabel(f"{time_col}")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(sol)
    ax.grid(alpha=0.3)
    outpath = OUT_DIR / f"{sol.replace(' ', '_')}.png"
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {outpath}")

print('Done — 3 plots (one per solvent) saved to', OUT_DIR)

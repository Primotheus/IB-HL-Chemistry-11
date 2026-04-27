#!/usr/bin/env python3
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
FILES = [BASE / f for f in ("13C.csv", "23C.csv", "33C.csv")]
GROUPS_CSV = BASE / "groups.csv"
OUT = BASE / "plots"
OUT.mkdir(exist_ok=True)

# helper: find time-like column
def find_time_col(cols):
    for c in cols:
        cl = str(c).lower()
        if "time" in cl:
            return c
    # fallback to first column
    return cols[0] if cols else None

# load groups mapping if present
group_map = {}
if GROUPS_CSV.exists():
    try:
        gm = pd.read_csv(GROUPS_CSV, header=None)
        # If file has two columns (id, label), use them. Otherwise treat as single-column list.
        if gm.shape[1] >= 2:
            for _, row in gm.iterrows():
                raw_id = row.iloc[0]
                raw_label = row.iloc[1]
                # normalize id to string without decimals
                gid = None
                try:
                    gid = str(int(float(raw_id)))
                except Exception:
                    gid = str(raw_id).strip()
                # normalize label string, strip quotes/whitespace
                lab = '' if pd.isna(raw_label) else str(raw_label).strip().strip('"')
                if not lab:
                    lab = f"Group {gid}"
                group_map[gid] = lab
        else:
            # single column of labels; map 1..n
            for i, val in enumerate(gm.iloc[:,0].astype(str)):
                lab = val.strip().strip('"')
                key = str(i+1)
                group_map[key] = lab if lab and lab.lower() not in ('nan','none') else f"Group {key}"
    except Exception as e:
        print(f"Warning: could not read groups.csv: {e}")


# helper to map group ids/raw to labels using group_map
def map_label(row):
    try:
        gid = row['Group_id'] if 'Group_id' in row.index else None
        raw = row['Group_raw'] if 'Group_raw' in row.index else None
    except Exception:
        # row may be a plain value
        gid = None
        raw = str(row)
    if gid is not None and not (pd.isna(gid)):
        key = str(int(gid)) if (isinstance(gid, (int, np.integer)) or (isinstance(gid, float) and gid.is_integer())) else str(gid)
        if key in group_map:
            return group_map[key]
    if raw is not None:
        raw_s = str(raw).strip()
        if raw_s in group_map:
            return group_map[raw_s]
    return raw if raw is not None else str(row)

def to_long(df):
    # Normalize column names
    cols = [c.strip() for c in df.columns]
    df.columns = cols
    # If already long (has Group and Volume/Volume collected columns)
    lower = [c.lower() for c in cols]
    if ("group" in lower and ("volume" in " ".join(lower) or "gas" in " ".join(lower))):
        # try to identify time/volume/trial columns
        time_col = next((c for c in cols if 'time' in c.lower()), None)
        vol_col = next((c for c in cols if 'volume' in c.lower() or 'gas' in c.lower() or 'collected' in c.lower()), None)
        group_col = next((c for c in cols if 'group' in c.lower()), None)
        trial_col = next((c for c in cols if 'trial' in c.lower()), None)
        if time_col and vol_col and group_col:
            out = df.rename(columns={time_col: 'Time', vol_col: 'Volume', group_col: 'Group'})
            if trial_col:
                out = out.rename(columns={trial_col: 'Trial'})
                return out[['Group','Trial','Time','Volume']]
            return out[['Group','Time','Volume']]
    # Otherwise assume wide format: first column = time, other columns are groups
    time_col = find_time_col(cols)
    group_cols = [c for c in cols if c != time_col]
    long = df.melt(id_vars=[time_col], value_vars=group_cols, var_name='Group', value_name='Volume')
    long = long.rename(columns={time_col: 'Time'})
    return long


def split_overlapping_trials(df, group_col='Group_label', time_col='Time'):
    """Detect time resets or decreases within each group and assign incremental Trial numbers.
    Returns a DataFrame with a 'Trial' column (int).
    """
    rows = []
    for g, sub in df.groupby(group_col):
        # preserve original file order (index order) so time resets are detected correctly
        sub_orig = sub.sort_index().copy()
        trial = 1
        prev_t = None
        trial_ids = []
        for t in sub_orig[time_col].to_numpy():
            if prev_t is None:
                trial_ids.append(trial)
                prev_t = t
                continue
            try:
                # treat NaNs as no-change
                if np.isnan(t) or np.isnan(prev_t):
                    trial_ids.append(trial)
                # if time decreases relative to previous measurement, start a new trial
                elif t < prev_t - 1e-6:
                    trial += 1
                    trial_ids.append(trial)
                else:
                    trial_ids.append(trial)
                prev_t = t
            except Exception:
                trial_ids.append(trial)
                prev_t = t
        sub_orig = sub_orig.assign(Trial=trial_ids)
        rows.append(sub_orig)
    if not rows:
        return df
    out = pd.concat(rows, ignore_index=True)
    return out


def parse_and_plot(path):
    if not path.exists():
        print(f"File not found: {path}; skipping")
        return
    try:
        df_raw = pd.read_csv(path)
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return
    df_long = to_long(df_raw)
    # clean
    df_long['Time'] = pd.to_numeric(df_long['Time'], errors='coerce')
    df_long['Volume'] = pd.to_numeric(df_long['Volume'], errors='coerce')
    df_long = df_long.dropna(subset=['Time','Volume'])

    # Ensure we have Group_label before attempting to split trials
    df_long['Group_raw'] = df_long['Group'].astype(str).str.strip()
    df_long['Group_id'] = df_long['Group_raw'].apply(lambda s: (re.search(r"(\d+)", str(s)).group(1) if re.search(r"(\d+)", str(s)) else None))
    df_long['Group_label'] = df_long.apply(map_label, axis=1)

    # Split overlapping trials only when there is no Trial column in the input
    if 'Trial' not in df_long.columns:
        df_long = split_overlapping_trials(df_long, group_col='Group_label', time_col='Time')

    # keep Trial column if present; ensure it's string/numeric consistent
    if 'Trial' in df_long.columns:
        # coerce to int where possible, otherwise keep as string
        df_long['Trial'] = pd.to_numeric(df_long['Trial'], errors='coerce').where(lambda s: ~s.isna(), df_long['Trial'].astype(str))

    # If Trial exists, treat each (Group_label, Trial) pair as its own run to avoid overlaps
    delta_rows = []
    grouping_key = ['Group_label', 'Trial'] if 'Trial' in df_long.columns else ['Group_label']
    for keys, g in df_long.groupby(grouping_key):
        if isinstance(keys, tuple):
            g_label, trial = keys
            series_label = f"{g_label} (Trial {trial})"
        else:
            g_label = keys
            trial = None
            series_label = g_label
        g_sorted = g.sort_values('Time')
        volumes = g_sorted['Volume'].to_numpy()
        times = g_sorted['Time'].to_numpy()
        # find first valid initial
        if len(volumes) == 0:
            continue
        valid_idx = ~np.isnan(volumes)
        if not valid_idx.any():
            continue
        first_idx = np.where(valid_idx)[0][0]
        initial = volumes[first_idx]
        deltas = volumes - initial
        for t, v, d in zip(times, volumes, deltas):
            delta_rows.append({'Group_label': g_label, 'Trial': trial, 'Time': t, 'Volume': v, 'Volume_delta': d})

    if not delta_rows:
        print(f"No delta data computed for {path}")
        return

    delta_df = pd.DataFrame(delta_rows)
    # save cleaned delta CSV
    out_csv = OUT / f"{path.stem}_deltas.csv"
    delta_df.to_csv(out_csv, index=False)
    print(f"Saved deltas -> {out_csv}")

    # plotting: group-first, then trials within each group (distinct color per group, linestyle/marker per trial)
    plt.figure(figsize=(10,6))
    groups = list(delta_df['Group_label'].unique())
    cmap = plt.get_cmap('tab10')
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'D', 'v', '*', 'x']

    for i, group in enumerate(groups):
        color = cmap(i % 10)
        trials = list(delta_df.loc[delta_df['Group_label'] == group, 'Trial'].dropna().unique())
        # ensure deterministic ordering
        try:
            trials = sorted(trials, key=lambda x: float(x))
        except Exception:
            trials = sorted(trials, key=lambda x: str(x))
        if not trials:
            # no trial column values -> plot as single series
            sub = delta_df[delta_df['Group_label'] == group].sort_values('Time')
            plt.plot(sub['Time'], sub['Volume_delta'], marker='o', linestyle='-', color=color, label=str(group))
            continue
        for j, trial in enumerate(trials):
            sub = delta_df[(delta_df['Group_label'] == group) & (delta_df['Trial'] == trial)].sort_values('Time')
            if sub.empty:
                continue
            ls = linestyles[j % len(linestyles)]
            mk = markers[j % len(markers)]
            # Make a readable trial label
            trial_label = int(trial) if (pd.notna(trial) and float(trial).is_integer()) else trial
            label = f"{group} (Trial {trial_label})"
            plt.plot(sub['Time'], sub['Volume_delta'], marker=mk, linestyle=ls, color=color, label=label)

    plt.axhline(0, color='gray', linewidth=0.7)
    plt.xlabel('Time (s)')
    plt.ylabel('Volume change from initial (mL)')
    plt.title(f'Volume change from initial — {path.name}')
    plt.legend(ncol=2, fontsize='small')
    plt.grid(alpha=0.3)
    out_png = OUT / f"{path.stem}.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"Saved plot -> {out_png}")

# run for each file
for f in FILES:
    parse_and_plot(f)

print('All done. Plots and CSVs saved in', OUT)

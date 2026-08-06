"""Feature extraction from LGES StepEnd (step-summary) CSV."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cyclediag.io.stepemd_csv import cell_id_from_path, load_stepemd_csv


def _ah_from_capacity(val) -> float | None:
    if val is None or (isinstance(val, float) and not np.isfinite(val)):
        return None
    v = float(val)
    if abs(v) < 1e-12:
        return None
    # LGES StepEnd: values are typically mAh-scale (e.g. 70814) or Ah (70.8)
    if abs(v) > 200.0:
        return v / 1000.0
    return v


def _primary_charge_row(cyc: pd.DataFrame) -> pd.Series | None:
    chg = cyc[cyc["step_type"] == "charge"]
    if chg.empty:
        return None
    caps = pd.to_numeric(chg.get("charge_capacity", chg.get("capacity")), errors="coerce")
    if caps.notna().any():
        return chg.loc[caps.idxmax()]
    return chg.iloc[-1]


def _primary_discharge_row(cyc: pd.DataFrame) -> pd.Series | None:
    dchg = cyc[cyc["step_type"] == "discharge"]
    if dchg.empty:
        return None
    caps = pd.to_numeric(dchg.get("discharge_capacity"), errors="coerce")
    if caps.notna().any():
        return dchg.loc[caps.idxmax()]
    return dchg.iloc[-1]


def _rest_after(cyc: pd.DataFrame, after_step_no: int) -> pd.Series | None:
    rests = cyc[(cyc["step_type"] == "rest") & (cyc["step_no"] > after_step_no)]
    if rests.empty:
        return None
    return rests.iloc[0]


def extract_stepemd_cycle_row(cyc: pd.DataFrame, *, cell_id: str, filepath: str) -> dict | None:
    if cyc.empty or "cycle" not in cyc.columns:
        return None
    cycle = int(cyc["cycle"].iloc[0])
    chg = _primary_charge_row(cyc)
    dchg = _primary_discharge_row(cyc)
    if chg is None and dchg is None:
        return None

    row: dict = {
        "cell_id": cell_id,
        "file": filepath,
        "cycle": cycle,
        "feature_set": "vp_stepemd_cycle_v1",
    }

    temp_col = "temperature" if "temperature" in cyc.columns else None

    if chg is not None:
        row["chg_V_cutoff"] = float(chg["voltage"]) if pd.notna(chg.get("voltage")) else None
        row["chg_I_cutoff"] = float(chg["current"]) if pd.notna(chg.get("current")) else None
        row["chg_AvgV"] = float(chg.get("AvgVoltage", chg.get("voltage"))) if "AvgVoltage" in chg.index else None
        if row["chg_AvgV"] is not None and not np.isfinite(row["chg_AvgV"]):
            row["chg_AvgV"] = row["chg_V_cutoff"]
        row["chgCapa"] = _ah_from_capacity(chg.get("charge_capacity", chg.get("capacity")))
        row["chg_step_time_s"] = chg.get("step_time_s")
        row["impedance_chg"] = float(chg["Impedance"]) if "Impedance" in chg.index and pd.notna(chg["Impedance"]) else None
        if temp_col and pd.notna(chg.get(temp_col)):
            row["chg_temp_avg"] = float(chg[temp_col])
        rest_c = _rest_after(cyc, int(chg["step_no"]))
        if rest_c is not None:
            v_end = float(rest_c["voltage"]) if pd.notna(rest_c.get("voltage")) else None
            row["EoC_restV_init"] = v_end
            row["EoC_restV_end"] = v_end
            row["EoC_restV_60s"] = None
            row["EoC_restV_30m"] = v_end
            row["rest_after_chg_s"] = rest_c.get("step_time_s")

    if dchg is not None:
        row["dchg_V_cutoff"] = float(dchg["voltage"]) if pd.notna(dchg.get("voltage")) else None
        row["dchg_AvgV"] = float(dchg.get("AvgVoltage", dchg.get("voltage"))) if "AvgVoltage" in dchg.index else None
        if row.get("dchg_AvgV") is not None and not np.isfinite(row["dchg_AvgV"]):
            row["dchg_AvgV"] = row["dchg_V_cutoff"]
        row["dchgCapa"] = _ah_from_capacity(dchg.get("discharge_capacity"))
        row["dchg_step_time_s"] = dchg.get("step_time_s")
        row["impedance_dchg"] = float(dchg["Impedance"]) if "Impedance" in dchg.index and pd.notna(dchg["Impedance"]) else None
        if temp_col and pd.notna(dchg.get(temp_col)):
            row["dchg_temp_avg"] = float(dchg[temp_col])
        rest_d = _rest_after(cyc, int(dchg["step_no"]))
        if rest_d is not None:
            v_end = float(rest_d["voltage"]) if pd.notna(rest_d.get("voltage")) else None
            row["EoD_restV_init"] = row.get("dchg_V_cutoff")
            row["EoD_restV_end"] = v_end
            row["EoD_restV_60s"] = None
            row["EoD_restV_30m"] = v_end
            row["rest_after_dchg_s"] = rest_d.get("step_time_s")

    chg_ah = row.get("chgCapa")
    dchg_ah = row.get("dchgCapa")
    if chg_ah and dchg_ah and chg_ah > 0:
        row["CE"] = dchg_ah / chg_ah * 100.0

    if row.get("chg_AvgV") is not None and row.get("dchg_AvgV") is not None:
        row["V_hyst_proxy"] = row["chg_AvgV"] - row["dchg_AvgV"]
    zc = row.get("impedance_chg")
    zd = row.get("impedance_dchg")
    if zc and zd and zd > 0:
        row["impedance_ratio"] = zc / zd

    for k in ("EoC_restV_init", "EoC_restV_end", "EoD_restV_end"):
        v0 = row.get(k)
        v1 = row.get("EoC_restV_end" if "EoC" in k else "EoD_restV_end")
        if v0 is not None and v1 is not None and k.endswith("_init"):
            row[f"rest_drop_{k.split('_')[0].replace('Eo','')}".replace("C", "EoC").replace("D", "EoD")] = v0 - v1

    if row.get("EoC_restV_init") is not None and row.get("EoC_restV_end") is not None:
        row["rest_drop_EoC"] = row["EoC_restV_init"] - row["EoC_restV_end"]
    if row.get("EoD_restV_init") is not None and row.get("EoD_restV_end") is not None:
        row["rest_drop_EoD"] = row["EoD_restV_init"] - row["EoD_restV_end"]

    return row


def apply_stepemd_deltas(table: pd.DataFrame, *, baseline_cycle: int | None = None) -> pd.DataFrame:
    if table.empty:
        return table
    out = table.sort_values("cycle").copy()
    delta_cols = [
        "EoC_restV_30m", "EoC_restV_end", "EoD_restV_30m", "EoD_restV_end",
        "chgCapa", "dchgCapa",
    ]
    for col in delta_cols:
        out[f"delta_{col}"] = None

    groups = [("__all__", out)]
    if "cell_id" in out.columns:
        groups = [(n, g) for n, g in out.groupby("cell_id", sort=False)]

    for _, grp in groups:
        idx = grp.index
        base_cyc = baseline_cycle
        if base_cyc is None:
            good = grp[pd.to_numeric(grp["dchgCapa"], errors="coerce") > 1.0]
            base_cyc = int(good["cycle"].iloc[0]) if not good.empty else int(grp["cycle"].iloc[0])
        base = grp[grp["cycle"] == base_cyc]
        if base.empty:
            base = grp.head(1)
        base_row = base.iloc[0]
        base_dchg = base_row.get("dchgCapa")

        for col in delta_cols:
            b = base_row.get(col)
            if b is not None and np.isfinite(b):
                out.loc[idx, f"delta_{col}"] = grp[col] - b

        if base_dchg and np.isfinite(base_dchg) and base_dchg > 0:
            out.loc[idx, "SoHQ"] = pd.to_numeric(grp["dchgCapa"], errors="coerce") / base_dchg * 100.0

    # CE_rev: next cycle chg / this dchg
    if "cell_id" in out.columns:
        for _, grp in out.groupby("cell_id", sort=False):
            g = grp.sort_values("cycle")
            ce_rev = np.full(len(g), np.nan)
            dchg = pd.to_numeric(g["dchgCapa"], errors="coerce").to_numpy()
            chg = pd.to_numeric(g["chgCapa"], errors="coerce").to_numpy()
            for i in range(len(g) - 1):
                if np.isfinite(dchg[i]) and np.isfinite(chg[i + 1]) and dchg[i] > 0:
                    ce_rev[i] = chg[i + 1] / dchg[i] * 100.0
            out.loc[g.index, "CE_rev"] = ce_rev
    else:
        g = out.sort_values("cycle")
        ce_rev = np.full(len(g), np.nan)
        dchg = pd.to_numeric(g["dchgCapa"], errors="coerce").to_numpy()
        chg = pd.to_numeric(g["chgCapa"], errors="coerce").to_numpy()
        for i in range(len(g) - 1):
            if np.isfinite(dchg[i]) and np.isfinite(chg[i + 1]) and dchg[i] > 0:
                ce_rev[i] = chg[i + 1] / dchg[i] * 100.0
        out["CE_rev"] = ce_rev

    return out


def extract_stepemd_features_table(
    path: str | Path | None = None,
    *,
    step_df: pd.DataFrame | None = None,
    cycles: list[int] | None = None,
    encoding: str = "cp949",
) -> pd.DataFrame:
    if step_df is not None:
        df = step_df
        path = Path(path or ".")
    else:
        if path is None:
            raise ValueError("path or step_df required")
        path = Path(path)
        df = load_stepemd_csv(path, encoding=encoding)
    if "step_no" not in df.columns:
        df["step_no"] = np.arange(len(df))

    cell_id = cell_id_from_path(path)
    cycle_list = cycles or sorted(df["cycle"].dropna().unique().astype(int))
    rows = []
    for cyc in cycle_list:
        cyc_df = df[df["cycle"] == cyc]
        row = extract_stepemd_cycle_row(cyc_df, cell_id=cell_id, filepath=str(path))
        if row:
            rows.append(row)
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    return apply_stepemd_deltas(table)

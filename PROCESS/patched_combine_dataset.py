# -*- coding: utf-8 -*-
"""
Combine two datasets into a single dataframe to process
Combine hourly data into daily total precip
Three lightning categories:
1. No Lightning
2. Lightning with Precipitation
3. Dry Lightning

PATCH SUMMARY (2026-03-12):
- Do NOT require exact 850/700/500 hPa matches; use log-interp to those levels.
- Sort sounding by pressure (surface high p -> top low p); de-duplicate pressure rows.
- Scoped dropna on required thermo vars only (avoid losing rows due to optional fields).
- Use true near-surface level for parcel calcs (highest pressure, not T[0] by assumption).
- Compute RH from Td when missing; align quantities for below-cloud RH mask.
- Guard each index independently; failure in one (e.g., SWEAT due to missing winds) doesn't wipe others.
- Add concise diagnostics for p-range and level coverage.
"""

# %%
import json
import pandas as pd
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units
from context import utils_dir, download_dir

# define a cutoff value for dry or moist lightning [mm]
precip_cutoff = 2.54

# open the stations json file
with open(utils_dir + '/unique_ecozone_stations.json', 'r') as f:
    stations = json.load(f)
all_stations = stations.keys()


def next_day_hour_wx_lightning(precip_df, cldn_df, date):
    """Get precip/lightning from 12Z day0 to <12Z day1 (US 12Z launch window)."""
    date_dt = pd.to_datetime(date)
    next_day_dt = date_dt + pd.Timedelta(days=1)
    date_dt = date_dt.strftime("%Y-%m-%d")
    next_day_dt = next_day_dt.strftime("%Y-%m-%d")

    print(f"d0 = {date_dt}, d1 = {next_day_dt}")

    wx0 = precip_df[precip_df["Day"] == date_dt]
    strikes0 = cldn_df[cldn_df["Day"] == date_dt]
    wx1 = precip_df[precip_df["Day"] == next_day_dt]
    strikes1 = cldn_df[cldn_df["Day"] == next_day_dt]

    time_split = "12"  # string compare OK with zero-padded "Hour"

    wx0_12 = wx0[wx0["Hour"] >= time_split]
    wx1_12 = wx1[wx1["Hour"] < time_split]

    if strikes0.empty:
        strikes0_12 = pd.DataFrame()
    else:
        strikes0_12 = strikes0[strikes0["Hour"] >= time_split]
    if strikes1.empty:
        strikes1_12 = pd.DataFrame()
    else:
        strikes1_12 = strikes1[strikes1["Hour"] < time_split]

    wx_combined = pd.concat([wx0_12, wx1_12], ignore_index=True)
    strikes_combined = pd.concat([strikes0_12, strikes1_12], ignore_index=True)
    return wx_combined, strikes_combined


def get_thousand_temp(T, p):
    """Return the 1000 hPa temperature as a plain float (degC)."""
    target_p = 1000 * units.hPa
    try:
        if target_p in p:
            idx = np.where(p == target_p)[0][0]
            return T[idx].to('degC').magnitude
        else:
            interp_T = mpcalc.log_interp(target_p, p, T)
            return float(interp_T.to('degC').magnitude)
    except Exception:
        return np.nan

def get_T_Td_at_levels_direct_then_interp(p, T, Td, target_levels_hpa, tol_hpa=0.0):
    """
    Return T and Td at target isobaric levels (hPa) prioritizing direct
    values from the sounding. If a level is not present (within tol),
    fall back to log-interpolation for that level.

    Parameters
    ----------
    p, T, Td : pint.Quantity arrays (MetPy quantities)
        Pressure [hPa], temperature [degC], dewpoint [degC].
    target_levels_hpa : 1D array-like of numbers
        Target pressure levels in hPa (e.g., [850, 700, 500]).
    tol_hpa : float
        Optional tolerance for “exact match” (default 0.0 for strict match).
        If > 0, we will treat a level as present if |p - target| <= tol_hpa.

    Returns
    -------
    Ti, Tdi : pint.Quantity arrays
        Temperatures and dewpoints at the requested levels, in degC.
        Order matches target_levels_hpa.
    present_mask : np.ndarray of bool
        True where the value came directly from the sounding; False if interpolated.
    """
    targets = np.asarray(target_levels_hpa, dtype=float) * units.hPa
    Ti = np.empty(len(targets), dtype=float) * units.degC
    Tdi = np.empty(len(targets), dtype=float) * units.degC
    present_mask = np.zeros(len(targets), dtype=bool)

    # ensure pressure is monotonic (surface high p -> top low p) for interpolation
    # (our main routine already sorts, but we keep this defensive)
    sort_idx = np.argsort(p.magnitude)[::-1]
    p_sorted = p[sort_idx]
    T_sorted = T[sort_idx]
    Td_sorted = Td[sort_idx]

    for i, pt in enumerate(targets):
        # try direct (exact-within-tolerance) pick
        if tol_hpa == 0.0:
            # strict equality check
            direct_idx = np.where(p_sorted == pt)[0]
        else:
            # within tolerance
            direct_idx = np.where(np.abs((p_sorted - pt).to('hPa').magnitude) <= tol_hpa)[0]

        if direct_idx.size > 0:
            j = int(direct_idx[0])
            Ti[i] = T_sorted[j].to('degC')
            Tdi[i] = Td_sorted[j].to('degC')
            present_mask[i] = True
        else:
            # fallback: interpolate this single level
            try:
                Ti[i] = mpcalc.log_interp(pt, p_sorted, T_sorted).to('degC')
                Tdi[i] = mpcalc.log_interp(pt, p_sorted, Td_sorted).to('degC')
                present_mask[i] = False
            except Exception:
                # if interpolation fails (e.g., profile doesn't span), set NaN
                Ti[i] = np.nan * units.degC
                Tdi[i] = np.nan * units.degC
                present_mask[i] = False

    return Ti, Tdi, present_mask

def combine_year(station_select, year, precip_cutoff=precip_cutoff):
    """Combine datasets for a single station and year and write OUTPUT CSV."""
    # validate station
    if station_select in all_stations:
        print("station is valid...")
        station_info = stations[station_select]
        id = station_info["id"]
    else:
        raise ValueError("please ensure station_select is present in the stations file")

    print(f"Station id: {id}")

    # read inputs
    cldn = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_cldn_output.csv")
    precip = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_precip_output.csv")
    sounding = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_all_soundings.csv")

    # === SOUNDING PREP ===
    # drop rows only if key thermo fields are missing; do NOT drop due to optional fields
    req_thermo = ["time", "pressure", "temperature", "dewpoint"]
    missing_any = [c for c in req_thermo if c not in sounding.columns]
    if missing_any:
        print(f"Sounding missing required columns {missing_any} - all thermo indices will be NaN")

    if set(req_thermo).issubset(set(sounding.columns)):
        sounding = sounding.dropna(subset=req_thermo).copy()
        # coerce numerics for known numeric columns when present
        for c in ["pressure", "temperature", "dewpoint", "height", "speed", "direction", "pw", "rh"]:
            if c in sounding.columns:
                sounding[c] = pd.to_numeric(sounding[c], errors='coerce')
    else:
        # ensure 'time' exists to allow filtering; keep dataframe structure
        if "time" not in sounding.columns:
            sounding["time"] = pd.NaT

    # === EARLY EXIT if no precip ===
    if precip.empty:
        print(f"No precipitation data for station {id} in {year} - saving empty output")
        empty_predict = pd.DataFrame(columns=["Day", "no_lightning",
                                              "moist_lightning",
                                              "dry_lightning",
                                              "precip_total"])
        empty_predict.to_csv(f"./OUTPUT/{id}_{year}_lightning_prediction.csv", index=False)
        return

    # stamp Day/Hour onto precip & lightning
    for index, row in precip.iterrows():
        day = row["rep_date"][0:10]
        time = row["rep_date"][11:13]
        precip.loc[index, "Day"] = day
        precip.loc[index, "Hour"] = time

    for index, row in cldn.iterrows():
        day = row["rep_date"][0:10]
        time = row["rep_date"][11:13]
        cldn.loc[index, "Day"] = day
        cldn.loc[index, "Hour"] = time

    print(cldn.head())
    print(precip.head())
    print(sounding.head())

    # output frame
    lightning_predict = pd.DataFrame(columns=["Day", "no_lightning",
                                              "moist_lightning",
                                              "dry_lightning",
                                              "precip_total"])
    all_days = precip["Day"].unique()
    lightning_predict["Day"] = all_days

    if "Day" not in cldn.columns:
        cldn["Day"] = []
        cldn["Hour"] = []

    # === DAILY WX/LTG CLASSIFICATION ===
    for index, row in lightning_predict.iterrows():
        date = row["Day"]
        wx, strikes = next_day_hour_wx_lightning(precip, cldn, date)

        daily_precip = pd.to_numeric(wx["precip"], errors="coerce").sum()
        daily_precip = np.round(daily_precip, 2)
        lightning_predict.loc[index, "precip_total"] = daily_precip

        if strikes.empty:
            print("No Strikes Today: ", date, " - ", daily_precip)
            lightning_predict.loc[index, "no_lightning"] = 1
            lightning_predict.loc[index, "moist_lightning"] = 0
            lightning_predict.loc[index, "dry_lightning"] = 0
        else:
            print("Lightning Today: ", date, " - ", daily_precip)
            lightning_predict.loc[index, "no_lightning"] = 0
            if daily_precip > precip_cutoff:
                lightning_predict.loc[index, "moist_lightning"] = 1
                lightning_predict.loc[index, "dry_lightning"] = 0
            else:
                lightning_predict.loc[index, "moist_lightning"] = 0
                lightning_predict.loc[index, "dry_lightning"] = 1

    is_lightning = lightning_predict["no_lightning"] == 0
    print(lightning_predict[is_lightning])

    # === SOUNDING-BASED INDICES ===
    for index, row in lightning_predict.iterrows():
        sdate = row["Day"] + " 12:00:00"  # US stores times at 12Z

        # skip if key columns missing
        if not set(req_thermo).issubset(set(sounding.columns)):
            print(f"No sounding thermo columns available: {sdate}")
            continue

        daily_sounding = sounding[sounding["time"] == sdate].copy()
        if daily_sounding.empty:
            print(f"No sounding today: {sdate}")
            continue

        # keep essential columns to avoid losing rows to optional NaNs
        cols_needed = ["pressure", "temperature", "dewpoint", "height", "speed", "direction", "pw", "rh"]
        present = [c for c in cols_needed if c in daily_sounding.columns]
        daily = daily_sounding[present].copy()

        # force numeric
        for c in present:
            daily[c] = pd.to_numeric(daily[c], errors='coerce')

        # sort by pressure (surface high p -> top low p), drop exact duplicate pressures
        if "pressure" not in daily.columns:
            print(f"Pressure column missing for {sdate} - skipping indices")
            continue

        daily = daily.dropna(subset=["pressure", "temperature", "dewpoint"])
        if daily.empty:
            print(f"Thermo rows empty after cleaning: {sdate}")
            continue

        daily = daily.sort_values("pressure", ascending=False)
        daily = daily.drop_duplicates(subset="pressure", keep="first").reset_index(drop=True)

        # build quantities
        p = daily["pressure"].values * units.hPa
        T = daily["temperature"].values * units.degC
        Td = daily["dewpoint"].values * units.degC
        h = (daily["height"].values * units.m) if "height" in daily.columns else None

        # optional winds
        ws = wdir = None
        if "speed" in daily.columns and "direction" in daily.columns:
            if daily["speed"].notna().any() and daily["direction"].notna().any():
                ws = daily["speed"].values * units("m/s")
                wdir = daily["direction"].values * units.degree

        # RH (compute if missing)
        if "rh" in daily.columns and daily["rh"].notna().any():
            rhq = daily["rh"].values * units.percent
        else:
            rhq = mpcalc.relative_humidity_from_dewpoint(T, Td).to('percent')

        # DIAGNOSTIC: coverage
        try:
            pmax, pmin = p.max(), p.min()
        except Exception:
            print(f"Pressure array invalid for {sdate}")
            continue

        has_850 = pmax >= 850 * units.hPa
        has_700 = pmax >= 700 * units.hPa
        has_500 = pmin <= 500 * units.hPa
        print(
            f"{sdate}: p-range {pmax:~P} to {pmin:~P} | "
            f"has_850={bool(has_850)} has_700={bool(has_700)} has_500={bool(has_500)} "
            f"n_levels={len(p)}"
        )

        # Initialize outputs as NaN
        dTTd850 = np.nan
        dTTd700 = np.nan
        dT850_500 = np.nan
        T1000 = np.nan
        mucape = np.nan
        cape = np.nan
        totals = np.nan
        sweat = np.nan
        lcl = np.nan
        K_index = np.nan
        equil_lev = np.nan
        lifted = np.nan
        pw = np.nan
        sfc_rh = np.nan
        below_cloud_rh_mean = np.nan

        # Precipitable water if present
        if "pw" in daily.columns and daily["pw"].notna().any():
            pw = float(daily["pw"].dropna().iloc[0])

        # T1000 (best-effort)
        try:
            T1000 = get_thousand_temp(T, p)
        except Exception as e:
            print("T1000 calc failed:", e)

        # Surface index (highest pressure)
        surf_idx = int(np.argmax(p))

        # Parcel profile / LCL / EL / Lifted Index
        try:
            prof = mpcalc.parcel_profile(p, T[surf_idx], Td[surf_idx]).to('degC')
            lcl_p, lcl_T = mpcalc.lcl(p[surf_idx], T[surf_idx], Td[surf_idx])
            lcl = lcl_p.to('hPa').magnitude
            cape_val, cin_val = mpcalc.cape_cin(p, T, Td, prof)
            cape = cape_val.to('joule / kilogram').magnitude
            equil_lev = mpcalc.el(p, T, Td, prof)[0].to('hPa').magnitude
            # Lifted Index: environment at 500 hPa minus parcel T at 500 hPa
            lifted = mpcalc.lifted_index(p, T, prof)[0].magnitude
        except Exception as e:
            print("Parcel/LCL/CAPE/EL/LI calc issue:", e)

        # K-index & Total Totals & manual deltas using direct-then-interp retrieval
        try:
            targets_list = [850.0, 700.0, 500.0]
            # We can keep tol_hpa=0.0 for strict match, or relax slightly:
            Ti, Tdi, present_mask = get_T_Td_at_levels_direct_then_interp(
                p, T, Td, targets_list, tol_hpa=0.0
            )
            T850, T700, T500 = Ti.to('degC')
            Td850, Td700, Td500 = Tdi.to('degC')

            # Only compute manual deltas where both terms are valid
            if np.isfinite(T850.magnitude) and np.isfinite(Td850.magnitude):
                dTTd850 = (T850 - Td850).magnitude
            else:
                dTTd850 = np.nan

            if np.isfinite(T700.magnitude) and np.isfinite(Td700.magnitude):
                dTTd700 = (T700 - Td700).magnitude
            else:
                dTTd700 = np.nan

            if np.isfinite(T850.magnitude) and np.isfinite(T500.magnitude):
                dT850_500 = (T850 - T500).magnitude
            else:
                dT850_500 = np.nan

            # Diagnostic: which levels were direct vs interpolated
            level_labels = ["850", "700", "500"]
            diag_bits = [f"{lev}:{'direct' if b else 'interp'}" for lev, b in zip(level_labels, present_mask)]
            print("Level source -> " + ", ".join(diag_bits))

            # Canonical indices (MetPy will internally handle interpolation if the span exists)
            if has_850 and has_700 and has_500:
                try:
                    K_index = mpcalc.k_index(p, T, Td).magnitude
                except Exception as e:
                    print("K-index calc failed:", e)
                try:
                    totals = mpcalc.total_totals_index(p, T, Td).magnitude
                except Exception as e:
                    print("Total Totals calc failed:", e)
            else:
                print("Profile does not span 850–500 hPa; KI/TT set NaN.")
        except Exception as e:
            print("Direct-then-interp level retrieval failed:", e)        

        # SWEAT Index (needs winds)
        try:
            if (ws is not None) and (wdir is not None):
                sweat = mpcalc.sweat_index(p, T, Td, ws, wdir).magnitude
            else:
                print("Winds missing; SWEAT set NaN.")
        except Exception as e:
            print("SWEAT calc failed:", e)

        # Surface RH and below-cloud RH (pressure > LCL pressure)
        try:
            sfc_rh = rhq[surf_idx].to('percent').magnitude
            if not np.isnan(lcl):
                lcl_p_qty = lcl * units.hPa
                mask = p > lcl_p_qty
                below_cloud = rhq[mask]
                below_cloud_rh_mean = (np.nan if below_cloud.size == 0
                                       else np.nanmean(below_cloud.to('percent').magnitude))
        except Exception as e:
            print("RH/below-cloud calc failed:", e)

        # write to DF (use round where applicable)
        lightning_predict.loc[index, "dTTd850"] = np.round(dTTd850, 2)
        lightning_predict.loc[index, "dTTd700"] = np.round(dTTd700, 2)
        lightning_predict.loc[index, "dT850-500"] = np.round(dT850_500, 2)
        lightning_predict.loc[index, "T1000"] = np.round(T1000, 2)
        lightning_predict.loc[index, "mucape"] = np.round(mucape, 2)
        lightning_predict.loc[index, "cape"] = np.round(cape, 2)
        lightning_predict.loc[index, "total_totals"] = np.round(totals, 2)
        lightning_predict.loc[index, "sweat"] = np.round(sweat, 2)
        lightning_predict.loc[index, "lcl"] = np.round(lcl, 2)
        lightning_predict.loc[index, "K_index"] = np.round(K_index, 2)
        lightning_predict.loc[index, "el"] = np.round(equil_lev, 2)
        lightning_predict.loc[index, "lifted_index"] = np.round(lifted, 2)
        lightning_predict.loc[index, "pw"] = np.round(pw, 2)
        lightning_predict.loc[index, "sfc_rh"] = np.round(sfc_rh, 2)
        lightning_predict.loc[index, "below_cloud_rh"] = np.round(below_cloud_rh_mean, 2)

        print("Completed Sounding Calculations...")
        print(lightning_predict.head())

    # save
    lightning_predict.to_csv(f"./OUTPUT/{id}_{year}_lightning_prediction.csv", index=False)


if __name__ == "__main__":
    station_select = "The Pas"
    year = 2017
    combine_year(station_select, year)
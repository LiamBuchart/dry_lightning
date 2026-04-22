"""

    Combine two datasets into a single dataframe to process
    Combine hourly data into daily total precip
    Three lightning categories:
        1. No Lightning
        2. Lightning with Precipitation
        3. Dry Lightning

"""
#%%
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
    # get all output for the next 24hours from a dataframe 
    # extract precip and lightning in the same manner
    # sounding data is at 12z so get 12hours of data from d0 and 12 hours from d1

    # get datatime object of date and next day
    date_dt = pd.to_datetime(date)  #.strftime("%Y-%m-%d")
    next_day_dt = date_dt + pd.Timedelta(days=1)

    date_dt = date_dt.strftime("%Y-%m-%d")
    next_day_dt = next_day_dt.strftime("%Y-%m-%d")
    print(f"d0 = {date_dt}, d1 = {next_day_dt}")

    wx0 = precip_df[precip_df["Day"] == date_dt]
    strikes0 = cldn_df[cldn_df["Day"] == date_dt]
    wx1 = precip_df[precip_df["Day"] == next_day_dt]
    strikes1 = cldn_df[cldn_df["Day"] == next_day_dt]

    # now on dt need the time >= 12 and < 12 for the next day
    time_split = str(12)
    # ensure strikes0 is not empty 
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

    # combine the two dataframes
    wx_combined = pd.concat([wx0_12, wx1_12])
    strikes_combined = pd.concat([strikes0_12, strikes1_12])

    return wx_combined, strikes_combined

def get_thousand_temp(T, p, h):
    """Return the 1000 hPa temperature as a plain float (degC).

    The sounding arrays ``T`` and ``p`` are pint quantities.  If 1000 hPa is
    already present in ``p`` we simply grab the corresponding ``T`` value;
    otherwise we interpolate to the isobaric surface using MetPy.

    In both cases the units are stripped before returning so callers can
    safely insert the result into a pandas column without carrying a unit
    object.
    """
    target_p = 1000 * units.hPa
    if target_p in p:
        idx = np.where(p == target_p)[0][0]
        return T[idx].to('degC').magnitude
    else:
        # interpolate to 1000 hPa using metpy; result may be an array
        interp_T = mpcalc.log_interp(target_p, p, T)
        # ensure a scalar and strip units
        return float(interp_T.to('degC').magnitude)
    
# define a cutoff value for dry or moist lightning [mm]
def combine_year(station_select, year, precip_cutoff=precip_cutoff):
    """Combine datasets for a single station and year and write OUTPUT CSV."""
    # make sure the querying is done - plan to have this in main eventually
    if station_select in all_stations:
        print("station is valid...")
        station_info = stations[station_select]
        id = station_info["id"]
    else:
        raise ValueError("please ensure station_select is present in the stations file")

    # open all csvs
    print(f"Station id: {id}")
    cldn = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_cldn_output.csv")
    precip = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_precip_output.csv")
    sounding = pd.read_csv(f"{download_dir}/OUTPUT/{id}/{id}_{year}_all_soundings.csv")

    # remove nans from sounding
    sounding = sounding.dropna()

    # early exit if no precipitation data
    if precip.empty:
        print(f"No precipitation data for station {id} in {year} - saving empty output")
        empty_predict = pd.DataFrame(columns=["Day", "no_lightning", 
                                              "moist_lightning",
                                              "dry_lightning", 
                                              "precip_total"])
        empty_predict.to_csv(f"./OUTPUT/{id}_{year}_lightning_prediction.csv", index=False)
        return

    # build a daily dataframe which contains columns for the following 3 scenarios:
    # (1 = Yes, 0 = No)
    # No Lightning (1/0), Moist Lightning (1/0), Dry Lightning (1/0)
    for index, row in precip.iterrows():
        day = row["rep_date"][0:10]
        time = row["rep_date"][11:13]
        # add a column to the precip dataframe
        precip.loc[index, "Day"] = day
        precip.loc[index, "Hour"] = time

    # do the same for cldn
    for index, row in cldn.iterrows():
        day = row["rep_date"][0:10]
        time = row["rep_date"][11:13]
        # add a column for the day (no time)
        cldn.loc[index, "Day"] = day
        cldn.loc[index, "Hour"] = time

    # Checks
    print(cldn.head())
    print(precip.head())
    print(sounding.head())

    # empty dataframe to store lightning classifiers
    lightning_predict = pd.DataFrame(columns=["Day", "no_lightning", 
                                              "moist_lightning",
                                              "dry_lightning", 
                                              "precip_total"])

    # dates of the fire season we want to predict on 
    all_days = precip["Day"].unique()
    lightning_predict["Day"] = all_days 

    # if there is no "Day" column in cldn, add it manually - simply means things are empty
    if "Day" not in cldn.columns:
        cldn["Day"] = []
        cldn["Hour"] = []

    for index, row in lightning_predict.iterrows():
        date = row["Day"]
        # get all output for the for the specific date to fill in 
        # lightning_predict
        #wx = precip[precip["Day"] == date] # if you want same day 
        #strikes = cldn[cldn["Day"] == date] # if you want same day
        wx, strikes = next_day_hour_wx_lightning(precip, cldn, date)

        # get the daily total precipitation
        daily_precip = np.round(wx["precip"].sum(), 2)
        lightning_predict.loc[index, "precip_total"] = daily_precip

        # cldn data is the linchpin for the dataset
        if strikes.empty:
            # add 0 to the lightning column
            print("No Strikes Today: ", date, " - ", daily_precip)
            lightning_predict.loc[index, "no_lightning"] = 1
            lightning_predict.loc[index, "moist_lightning"] = 0
            lightning_predict.loc[index, "dry_lightning"] = 0

        else:
            # add 1 to the lightning column
            print("Lightning Today: ", date, " - ", daily_precip)
            lightning_predict.loc[index, "no_lightning"] = 0

            if daily_precip > precip_cutoff:
                # more precip that the cutoff (daily)
                lightning_predict.loc[index, "moist_lightning"] = 1
                lightning_predict.loc[index, "dry_lightning"] = 0

            else:
                # less precip than the cutoff
                lightning_predict.loc[index, "moist_lightning"] = 0
                lightning_predict.loc[index, "dry_lightning"] = 1

    is_lightning = lightning_predict["no_lightning"] == 0
    print(lightning_predict[is_lightning])

    # deal with the sounding data
    # similarly loop through lightning predict to get each individual date
    for index, row in lightning_predict.iterrows():
        sdate = row["Day"] + " 12:00:00"  # how us stores the times

        if "time" not in sounding.columns:  # for empty sounding data
            sounding["time"] = []

        daily_sounding = sounding[sounding["time"] == sdate]

        # perform calculations if the sounding is not empty
        if daily_sounding.empty:
            print(f"No sounding today: {sdate}")
        else:
            print(f"Successful sounding launch {sdate}")    

            # get the key variables
            p = np.array(daily_sounding["pressure"], dtype=float) * units.hPa
            T = np.asarray(daily_sounding["temperature"], dtype=float) * units.degC
            Td = np.asarray(daily_sounding["dewpoint"], dtype=float) * units.degC
            h = np.asarray(daily_sounding["height"], dtype=float) * units.m
            # might break here
            ws = np.asarray(daily_sounding["speed"], dtype=float) * units("m/s")
            wdir = np.asarray(daily_sounding["direction"], dtype=float) * units("degrees") 

            # some soundings do not have rh built in
            try: 
                rh = np.array(daily_sounding["rh"]) * units("%")
            except Exception as e:
                print("no rh just dewpoint: error - ", e) 
                rh = mpcalc.relative_humidity_from_dewpoint(T, Td).to('percent')

            # grab the percipitable water if available
            try:
                pw = np.array(daily_sounding["pw"])[0] 
            except:
                print("Precipitible water not calculated - make NaN")
                pw = np.nan

            ## calculate several indices
            # start with T - Td and Temp height changes
            r850 = daily_sounding[daily_sounding["pressure"] == 850.0]
            r700 = daily_sounding[daily_sounding["pressure"] == 700.0]
            r500 = daily_sounding[daily_sounding["pressure"] == 500.0]

            if r850.empty or r700.empty or r500.empty:
                print("One of the required levels is missing - skipping index calculations")
                continue
            else:
                dTTd850 = r850["temperature"] - r850["dewpoint"] 
                dTTd700 = r700["temperature"] - r700["dewpoint"]

                dT500850 = list(r850["temperature"])[0] - list(r500["temperature"])[0]

                # compute parcel profile temperature
                try:
                    T1000 = get_thousand_temp(T, p, h)
                    prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')
                    equil_lev = mpcalc.el(p, T, Td, prof)[0].magnitude
                    lifted = mpcalc.lifted_index(p, T, prof)[0].magnitude

                    # convective indices
                    mucape = mpcalc.most_unstable_cape_cin(p, T, Td)[0].magnitude
                    cape = mpcalc.cape_cin(p, T, Td, prof)[0].magnitude
                    sweat = mpcalc.sweat_index(p, T, Td, ws, wdir)[0].magnitude
                    totals = mpcalc.total_totals_index(p, T, Td).magnitude
                    lcl = mpcalc.lcl(p[0], T[0], Td[0])[0].magnitude
                    K_index = mpcalc.k_index(p, T, Td).magnitude

                    # calculate the average 'below-cloud' humidity (below LCL)
                    # lcl is in pressure units so find where pressure is greater than lcl
                    mask = np.asarray(p) > lcl
                    below_cloud_rh = list(rh[mask])
                except Exception as e: 
                    print("Issue with sounding format: ", e)
                    T1000 = np.nan
                    prof = np.nan
                    equil_lev = np.nan
                    lifted = np.nan

                    mucape = np.nan
                    cape = np.nan
                    sweat = np.nan
                    totals = np.nan
                    lcl = np.nan
                    K_index = np.nan

                    below_cloud_rh = np.nan

                # add things to the lightning predict dataframe
                lightning_predict.loc[index, "dTTd850"] = round(list(dTTd850)[0], 2)
                lightning_predict.loc[index, "dTTd700"] = round(list(dTTd700)[0], 2)
                lightning_predict.loc[index, "dT850-500"] = round(dT500850, 2)
                lightning_predict.loc[index, "T1000"] = round(T1000, 2)

                lightning_predict.loc[index, "mucape"] = round(mucape, 2)
                lightning_predict.loc[index, "cape"] = round(cape, 2)
                lightning_predict.loc[index, "total_totals"] = round(totals, 2)
                lightning_predict.loc[index, "sweat"] = round(sweat, 2)
                lightning_predict.loc[index, "lcl"] = round(lcl, 2)
                lightning_predict.loc[index, "K_index"] = round(K_index, 2)
                lightning_predict.loc[index, "el"] = round(equil_lev, 2)
                lightning_predict.loc[index, "lifted_index"] = round(lifted, 2)

                lightning_predict.loc[index, "pw"] = round(pw, 2)
                lightning_predict.loc[index, "sfc_rh"] = round(rh[0].magnitude, 2)
                lightning_predict.loc[index, "below_cloud_rh"] = round(np.mean(below_cloud_rh), 2)

    print("Completed Sounding Calculations...")

    print(lightning_predict.head())
    lightning_predict.to_csv(f"./OUTPUT/{id}_{year}_lightning_prediction.csv")


if __name__ == "__main__":
    station_select = "The Pas"
    year = 2017
    combine_year(station_select, year)

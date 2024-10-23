from ecmwfapi import ECMWFDataServer
from ecmwfapi.api import APIException
from fire import Fire
import numpy as np
import calendar
import pandas as pd
import os
import xarray as xr
import time

# Other dictionaries (var_dict, cf2pynio, long2short, areas) remain the same

def crop_to_nc(fn, lats, lons, var):
    ds = xr.open_mfdataset(fn, engine='pynio')[cf2pynio[var]].rename(long2short[var])
    ds = ds.rename({
        'initial_time0_hours': 'init_time',
        'forecast_time0': 'lead_time',
        'lat_0': 'lat',
        'lon_0': 'lon',
    })
    if 'ensemble0' in ds.coords:
        ds = ds.rename({'ensemble0': 'member'})
    ds = ds.sel(lat=slice(*lats), lon=slice(*lons))
    fn_nc = fn.rstrip('.grib') + '.nc'
    ds.to_netcdf(fn_nc)
    print('Saved to nc:', fn_nc)

def download_with_retries(server, request, fn, retries=3, delay=5):
    """
    Download data from ECMWF with a retry mechanism.
    """
    for attempt in range(retries):
        try:
            server.retrieve(request)
            return True
        except APIException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to download {fn} after {retries} attempts.")
                return False

def main(var, start_month, stop_month, dir, ensemble=False, members=50, lead_time=48, dt=6, level=None, check_exists=True,
         lats=[90, -90], lons=[0, 360], area='CONUS', delete_grib=True):
    """
    Downloads TIGGE files in monthly batches.
    """

    server = ECMWFDataServer()
    if area:
        lats, lons = areas[area]

    months = np.arange(start_month, stop_month, dtype='datetime64[M]')
    dir = f'{dir}/{var}{level if level else ""}{f"_ens{members}" if ensemble else ""}'
    os.makedirs(dir, exist_ok=True)

    for month in months:
        try:
            days = calendar.monthrange(pd.to_datetime(month).year, pd.to_datetime(month).month)[1]
            fn = f'{dir}/{month}.grib'
            fn_nc = fn.rstrip('.grib') + '.nc'
            print(fn)
            if check_exists and os.path.exists(fn_nc):
                print(fn_nc, 'exists')
                continue

            request = {
                "class": "ti",
                "dataset": "tigge",
                "date": f"{month}-01/to/{month}-{days}",
                "expver": "prod",
                "levtype": "sfc",
                "origin": "ecmf",
                "param": var_dict[var],
                "step": '/'.join(np.arange(0, lead_time+dt, dt).astype(str)),
                "time": "00:00:00/12:00:00",
                "type": "cf",
                "target": fn,
            }

            if level:
                request['levtype'] = 'pl'
                request['levelist'] = str(level)
            if ensemble:
                request['number'] = '/'.join(np.arange(1, members+1).astype(str))
                request['type'] = 'pf'

            success = download_with_retries(server, request, fn)
            
            if success:
                print('Converting to nc')
                crop_to_nc(fn, lats, lons, var)
                if delete_grib:
                    print('Deleting', fn)
                    os.remove(fn)

        except APIException as e:
            print(f'Damaged files for {month}-01/to/{month}-{days}: {e}')
    
if __name__ == '__main__':
    Fire(main)

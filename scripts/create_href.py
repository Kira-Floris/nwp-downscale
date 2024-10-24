from fire import Fire
import xarray as xr 
import numpy as np
import pandas as pd
from datetime import timedelta
import os
from tqdm import tqdm
import pprint

def add_zero_lead_time(da, check_exists=True):
    if da.lead_time[0] == np.timedelta64(0):
        return da
    else:
        da = xr.concat([
            (da.isel(lead_time=0)  * 0).assign_coords({
                    'lead_time': da.isel(lead_time=0).lead_time - np.timedelta64(6, 'h'),
                }).assign_coords({
                    'valid_time': da.isel(lead_time=0).valid_time.values - np.timedelta64(6, 'h'),
                }).drop('step'),
            da.drop('step')
        ], dim='lead_time')
        return da

nmmb_x2_dates = pd.to_datetime(np.arange(
        '2020-01-08T00:00:00.000000000', '2020-03-04T00:00:00.000000000', np.timedelta64(12, 'h'), dtype='datetime64[h]'
    )).union(
pd.to_datetime(np.arange(
        '2020-03-28T12:00:00.000000000', '2021-01-01T12:00:00.000000000', np.timedelta64(12, 'h'), dtype='datetime64[h]'
    )))

def main(start_date, stop_date, path, check_exists=True, in_version='', out_version=''):
    
    save_path = f'{path}/href{out_version}/4km/total_precipitation/'
    os.makedirs(save_path, exist_ok=True)
    
    init_dates = pd.to_datetime(np.arange(
        start_date, stop_date, np.timedelta64(12, 'h'), dtype='datetime64[h]'
    ))
    
    models = ['hiresw_conusarw', 'hiresw_conusnmmb', 'hiresw_conusnssl', 'nam_conusnest', 'hrrr']
    
    for date in tqdm(init_dates, disable=False):
        
        members = []
        names = []
        lag = 12
        previous_date = date - timedelta(hours=lag)
        current_date_str = f'{date.year}{str(date.month).zfill(2)}{str(date.day).zfill(2)}'
        previous_date_str = f'{previous_date.year}{str(previous_date.month).zfill(2)}{str(previous_date.day).zfill(2)}'
        
        save_fn = f'{save_path}{current_date_str}_{str(date.hour).zfill(2)}.nc'
        if not (check_exists and os.path.exists(save_fn)):
            try:
                for model in models:
                    current = add_zero_lead_time(
                        xr.open_dataarray(
                            f'{path}/{model}/4km{in_version}/total_precipitation/{current_date_str}_{str(date.hour).zfill(2)}.nc'
                        )
                    )
                    previous = add_zero_lead_time(
                        xr.open_dataarray(
                            f'{path}/{model}/4km{in_version}/total_precipitation/{previous_date_str}_{str(previous_date.hour).zfill(2)}.nc'
                        )
                    )
                    
#                     ## Account for HRRR total_precip
#                     if model == 'hrrr':
#                         current = current.diff('lead_time')
#                         previous = previous.diff('lead_time')
                    
                    # Cut off unused lead times
                    previous = previous.sel(lead_time=slice(np.timedelta64(lag, 'h'), None))
                    # Change init_time to current init time
                    # Change lead_time to 0
                    previous = previous.assign_coords({
                        'init_time': previous.init_time + np.timedelta64(lag, 'h')}).assign_coords({
                        'lead_time': previous.lead_time - np.timedelta64(lag, 'h')
                    })
                    
                    
                    
                    members.extend([current, previous])
                    names.extend([model, f'{model}-{lag}h'])

                href_ds = xr.concat(
                    members, 
                    dim=xr.DataArray(names, dims='member', name='member'), 
                    coords='minimal',
                    compat='override'
                )
                
                # Dynamically check for 2x values
                # Use nam_conusnest as reference
                # Only do this for NMMB
                diff = href_ds.diff('lead_time').mean(('lat', 'lon'))
                ratio = (diff / diff.sel(member='nam_conusnest')).mean('lead_time')
                threshold = 1.5
                is_not_x2 = ratio < threshold
                is_not_x2[:] = True
                is_not_nmmb = ['nmmb' not in m for m in ratio.member.values]
                is_not_x2[is_not_nmmb] = True
                if date in nmmb_x2_dates:
                    is_not_x2[2] = False
                if previous_date in nmmb_x2_dates:
                    is_not_x2[3] = False
                href_ds = href_ds.where(is_not_x2, href_ds / 2.)
#                 print(is_not_x2)
#                 pprint.pprint({m: not bool(b) for m, b in zip(is_not_x2.member.values, is_not_x2.values)})
                print('\t'.join([str(is_not_x2.time.values)] + [str(not b) for b in is_not_x2.values]))
                
                

                print('Saving', save_fn)
                href_ds.to_netcdf(save_fn)
                
                href_ds.close()
                current.close()
                previous.close()
            except FileNotFoundError:
#                 print('Not all files exist')
                pass
        else:
            print('Exists:', save_fn)
    

if __name__ == '__main__':
    Fire(main)
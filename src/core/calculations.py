""" 
Now we have countries, their imports, and their prevailing tariff rates (WIP). Now we need to 
Find the change in the tariff rates as a function, and then we can calculate the change in the price index. 
For now, let's also take the data for the expenditure shares from Baslandze and Fuchs (2025).
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import country_converter as coco

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))

ii_data = pd.read_csv('data/working/import_intensity.csv')
ii_data['tariff_rate'] = ii_data['tariff_rate'].astype(float)
ii_data['tariff_rate']= ii_data['tariff_rate']/100
ii_data['trade_openness_wt_expShare'] = ii_data['country_import_weight'] * ii_data['import_intensity_weighted']

exp_data = pd.read_stata('data/raw/numerator_panjiva_match_firm_dept_yr.dta')
exp_data = exp_data.rename(columns={'sector_CEX': 'sector'})

max_year = exp_data['year'].max()
exp_data= exp_data[exp_data['year'] == max_year]

# Generate sales weight denominator
exp_data['total_sales'] = exp_data.groupby(['year','department_description'])['item_total_st_wt'].transform('sum')
exp_data['ExpendShareYInNumerator'] = exp_data['item_total_st_wt'] / exp_data['total_sales']
# Collapse exp_data to the department_description year level
collapsed_exp_data = exp_data.groupby(['year', 'department_description']).agg(
    total_sales=('total_sales', 'mean'),
    sector=('sector', 'first')
).reset_index()

merged_data = pd.merge(collapsed_exp_data, ii_data, on='sector', how='left')

# Calculate the openness weighted with expenditure shares for each country: 

merged_data['tottotsales'] = merged_data.groupby(['year', 'country'])['total_sales'].transform('sum')
merged_data['dept_share'] = merged_data['total_sales'] / merged_data['tottotsales']

merged_data['trade_openness_wt_expShare_wt'] =  merged_data['trade_openness_wt_expShare'] * merged_data['dept_share']

# Collapse down by year country summing up the trade_openness. 
merged_data = merged_data.groupby(['year', 'country']).agg(
    trade_openness_wt_expShare=('trade_openness_wt_expShare_wt', 'sum'),
    weight_check = ('dept_share', 'sum'),
    tariff = ('tariff_rate', 'mean')
).reset_index()

# Clean Gaza and WEst bank 
merged_data['country'] = merged_data['country'].replace(
    {'west bank administered by israel': 'palestine', 'gaza strip administered by israel': 'palestine'}
)

merged_data['ISO_A3'] = coco.convert(names=merged_data['country'], to='ISO3')

def calculate_price_effects(data, new_tariffs, pass_through):
    """
    Calculate the estimated price effects from tariff changes using country‐specific
    old tariffs given in the "tariff_rate" column.
    
    Parameters
    ----------
    data : pd.DataFrame
        A DataFrame containing at least the following columns:
          - 'country': Name or code of the country.
          - 'tariff_rate': The current (old) tariff rate for the country.
          - 'trade_openness_wt_expShare_wt': A factor used in the price change calculation.
    new_tariffs : dict
        A dictionary mapping country names (or codes) to the new tariff rate.
        For example: {'USA': 0.08, 'Canada': 0.1}. THESE ARE CHANGES, NOT THE NEW TARIFF RATE.
    pass_through : float
        The pass-through rate applied in the calculation.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame with columns 'country' and 'price_effect' showing the estimated
        price change for each country with a new tariff.
    """
    # Make a copy to avoid modifying the original data
    df = data.copy()
    
    # Create a new column 'new_tariff' that uses the new tariff for countries in new_tariffs,
    # otherwise it remains the same as the old tariff.
    df['new_tariff'] = df.apply(
        lambda row: new_tariffs.get(row['ISO_A3'], row['tariff']),
        axis=1
    )
    
    # Compute the logged tariff values. The old tariff is taken from the existing column.
    df['ln_tariff_old'] = np.log(1 + df['tariff'])
    df['ln_tariff_new'] = np.log(1 + df['tariff'] + df['new_tariff'])
    
    # Calculate the change in the log tariff
    df['D_tariff'] = df['ln_tariff_new'] - df['ln_tariff_old']
    print(df['D_tariff']) 
    
    # Compute the price change. For rows where the tariff does not change, D_tariff==0, and D_price==0.
    df['D_price'] = (np.exp(pass_through * df['D_tariff'] * df['trade_openness_wt_expShare']) - 1)*100
    
    # If you want to return only the results for countries where a new tariff was applied:
    result_df = df[df['ISO_A3'].isin(new_tariffs.keys())].copy()
    
    # Rename the column to reflect that it is a price effect
    result_df.rename(columns={'D_price': 'price_effect'}, inplace=True)
    
    # Return only the relevant columns
    return result_df[['ISO_A3', 'price_effect', 'new_tariff', 'tariff']]
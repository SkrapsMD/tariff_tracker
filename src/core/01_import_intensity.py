# For all the backend calculations, we produce on the computer level
# annually, and this 

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import country_converter as coco

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR))
print(ROOT_DIR)
from src.utils.name_mappings import descriptions, bj2021_sectors 
from src.utils.tariff_rates import tariff_rates

# Load in Data 
all_import_data = pd.read_csv('data/raw/USTRADE_all_countries_imports_exports.csv', header= 2)


# Filter out most recent year: 
max_year = all_import_data['Time'].max()
import_data = all_import_data[all_import_data['Time'] == max_year]
# Clean up the data a bit
import_data.drop(columns=['Time','Unnamed: 5'], inplace=True)
import_data.columns = ['country','description','export_value','import_value']
import_data['description'] = import_data['description'].str.lower()
import_data['country'] = import_data['country'].str.lower().replace('all geographic regions (world total)', 'all_countries')
import_data['country'] = import_data['country'].str.lower().replace('world total', 'all_countries')
import_data['description'] = import_data['description'].replace('all commodities', '000000 all_commodities')
import_data['description'] = import_data['description'].replace('all commodities', '000000 all_commodities')
import_data[['industry_code', 'description_type']] = import_data['description'].str.split(' ', n=1, expand=True)
# Remove commas from import_value and export_value and convert to integer
import_data['import_value'] = import_data['import_value'].str.replace(',', '').astype(float)
import_data['export_value'] = import_data['export_value'].str.replace(',', '').astype(float)
import_data['industry_code'] = import_data['industry_code'].astype(int)
# reorder the columns for readability
import_data = import_data[['country', 'industry_code', 'description_type', 'import_value', 'export_value', 'description']]
# Combine rows for apparel and leather products and Textiles and textile mill output
import_data['industry_code'] = import_data['industry_code'].replace(316, 315) ##  For the apparel
import_data['industry_code'] = import_data['industry_code'].replace(314, 313) ## For the textile industry
import_data['industry_code'] = import_data['industry_code'].replace(312, 311) ## For the Food, Beverage, and Tobacco Products
# Group by country and industry_code, then sum the import_value and export_value
import_data = import_data.groupby(['country', 'industry_code'], as_index=False).agg({
    'import_value': 'sum',
    'export_value': 'sum',
    'description_type': 'first',
    'description': 'first'
})
# read in the harmonized 2023 GDP data from 04_openness_vs_ppi.py
gdp_data = pd.read_csv('data/raw/gdp_naics_harm.csv', usecols=lambda column: column != 'Unnamed: 0')
gdp_data['gdp'] = gdp_data['gdp']*1000000

# merge the import data with the harmonized GDP data by industry code
import_gdp_data = pd.merge(import_data, gdp_data, on='industry_code', how='left')
import_gdp_data = import_gdp_data.groupby(['country','industry_code'], as_index=False).agg({
    'import_value': 'first',
    'export_value': 'first',
    'gdp': 'sum',
    'Title': 'first'
})
# Map the cleaner descriptions to the descriptions in the data
import_gdp_data['description_clean'] = import_gdp_data['Title'].map(descriptions)

import_gdp_data = import_gdp_data[import_gdp_data['gdp']!= 0.0]

# Map the sectors to the descriptions
import_gdp_data['sector'] = import_gdp_data['description_clean'].map(bj2021_sectors)
# Drop rows where sector is None
import_gdp_data = import_gdp_data.dropna(subset=['sector'])
import_gdp_data = import_gdp_data[import_gdp_data['sector'] != 'None']

# Create the import intensities by description and sector output weights and sector import aggregates.
total_imports_all_countries = import_gdp_data[import_gdp_data['country'] == 'all_countries'][['industry_code','sector', 'import_value', 'export_value', 'gdp']]
total_imports_all_countries.rename(columns={'import_value': 'import_value_all_countries', 'export_value': 'export_value_all_countries'}, inplace=True)
sector_output = total_imports_all_countries.groupby(['sector'])['gdp'].sum()
sector_imports = total_imports_all_countries.groupby(['sector'])['import_value_all_countries'].sum()
total_imports_all_countries['sector_output'] = total_imports_all_countries['sector'].map(sector_output)
total_imports_all_countries['sector_imports'] = total_imports_all_countries['sector'].map(sector_imports)
# Sector Output Weights
total_imports_all_countries['sector_output_weight'] = total_imports_all_countries['gdp'] / total_imports_all_countries['sector_output']
# Import Intensity
total_imports_all_countries['import_intensity'] = import_gdp_data['import_value'] / (import_gdp_data['gdp'] + import_gdp_data['import_value'] - import_gdp_data['export_value'])
total_imports_all_countries['import_intensity_weighted'] = total_imports_all_countries['import_intensity'] * total_imports_all_countries['sector_output_weight']
total_imports_all_countries = total_imports_all_countries[['industry_code', 'import_intensity_weighted', 'import_intensity', 'sector_output', 'sector_imports']]
import_gdp_data = pd.merge(import_gdp_data, total_imports_all_countries, on='industry_code', how='left')
import_intensity_sectors = import_gdp_data.groupby(['country', 'sector'], as_index=False).agg({
    'import_intensity_weighted': 'sum',
    'import_value': 'sum'
})
import_intensity_sectors['sector_import_values'] = import_intensity_sectors['sector'].map(sector_imports) # For all country = "all countries". sector_import_values should equal sector_imports mechanically.
import_intensity_sectors['country_import_weight'] = import_intensity_sectors['import_value'] / import_intensity_sectors['sector_import_values']


# Save the data: Country X Sector X Import Intensity X Import Weights
import_intensity = import_intensity_sectors[['country', 'sector', 'import_intensity_weighted', 'country_import_weight']]

# Map tariff rates to countries: 
MFN_RATE = 3.4
import_intensity['tariff_rate'] = import_intensity['country'].map(tariff_rates).fillna(MFN_RATE)


print('main done')
ii_data = import_intensity
del import_intensity
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

merged_data.to_csv('data/working/import_intensity.csv', index=False)

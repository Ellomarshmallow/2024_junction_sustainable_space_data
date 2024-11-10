import pandas as pd

FIPS = ['06023']
YEARS = ['2015']

### DOWNLOAD DROOUGHT DATA ###
'''
Download from here  https://www.kaggle.com/datasets/cdminix/us-drought-meteorological-data
- test_timeseries.csv 
- train_timeseries.csv (2000-2016)
- validation_timeseries.csv
move into data/ folder
'''
dfs = []
for name, path in {'drought_2000_2016': 'data/train_timeseries.csv', 'drought_2019_2020': 'data/test_timeseries.csv', 'drought_2017_2018': 'data/validation_timeseries.csv'}.items():
    print(f"Reading {name}...")
    dfs.append(pd.read_csv(path,parse_dates=['date']))

drought_data = pd.concat([dfs[0], dfs[1], dfs[2]], ignore_index=True)
print(type(drought_data))
drought_data['date'] = pd.to_datetime(drought_data['date'])


drought_data['fips'] = drought_data['fips'].apply(lambda x: '0' + str(x) if len(str(x)) == 5 else str(x))
drought_data = drought_data[drought_data['fips'].isin(FIPS)]
drought_data = drought_data[drought_data['date'].dt.year.isin(YEARS)]
drought_data = drought_data.rename(columns={'fips': 'FIPS', 'date': 'DATE'})

print("drought data downloaded")

#### DOWNLOAD FIRE INCIDENT DATA ###
# download https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires to data/FPA_FOD_20170508.sqlite
# only available for 2015
import sqlite3
YEAR = 2015
fips_state_codes = {
    'AL': '01', 'AK': '02', 'AS': '60', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09', 
    'DE': '10', 'DC': '11', 'FL': '12', 'FM': '64', 'GA': '13', 'GU': '66', 'HI': '15', 'ID': '16', 
    'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MH': '68', 
    'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31', 
    'NV': '32', 'NH': '33', 'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'MP': '69', 
    'OH': '39', 'OK': '40', 'OR': '41', 'PW': '70', 'PA': '42', 'PR': '72', 'RI': '44', 'SC': '45', 
    'SD': '46', 'TN': '47', 'TX': '48', 'UM': '74', 'UT': '49', 'VT': '50', 'VA': '51', 'VI': '78', 
    'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56'
}
state_codes = []
county_codes = []
for s in FIPS:
    state_codes.append(s[:2])  # First two characters for state code
    county_codes.append(s[-3:])  # Last three characters for county code
state_names = [key for key, val in fips_state_codes.items() if val in state_codes]

db_path = 'data/FPA_FOD_20170508.sqlite'
county_associated = ["HUMBOLDT", "Humboldt County","023"]
columns = ['longitude', 'latitude', 'FIPS_CODE', 'STATE',  'fire_size', 'DISCOVERY_DOY']
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
query = f"""
SELECT {', '.join(columns)} 
FROM Fires 
WHERE STATE IN ({', '.join(f"'{code}'" for code in state_names)}) 
AND FIPS_CODE IN ({', '.join(f"'{code}'" for code in county_codes)}) 
AND FIRE_YEAR IN ({', '.join(str(year) for year in YEARS)});
"""

cursor.execute(query)
fires = cursor.fetchall()
conn.close()

fires = pd.DataFrame(fires, columns=columns)
from datetime import datetime, timedelta

def doy_to_date(year, doy):
    date = datetime(year, 1, 1) + timedelta(days=doy - 1)
    return date

fires["DATE"] = fires["DISCOVERY_DOY"].apply(lambda x: doy_to_date(YEAR, x))
fires = fires.drop(columns=['DISCOVERY_DOY'])
fires['FIPS'] = fires['STATE'].map(fips_state_codes) + fires['FIPS_CODE']
fires["FIRE"] = 1

dates = pd.date_range(start=f'{YEAR}-01-01', end=f'{YEAR}-12-31', freq='D')

# Create the DataFrame with all combinations of dates and FIPS codes
day_had_fire = pd.DataFrame(
    [(date, fips) for date in dates for fips in FIPS], 
    columns=['DATE', 'FIPS_CODE']
)

day_had_fire = day_had_fire.merge(fires[["DATE", 'FIPS', "FIRE"]], on=["DATE", 'FIPS'], how='left', validate="1:m")
day_had_fire['FIRE'] = day_had_fire['FIRE'].fillna(0).astype(int)
day_had_fire = day_had_fire.rename(columns={'FIPS': 'FIPS'})
day_had_fire = day_had_fire.drop_duplicates()

### DOWNLOAD NVDI DATA ###
import get_nvdi_data

get_nvdi_data.main(YEARS, FIPS)

print("nvdi data downloaded")

### MERGE DATA ###

# merge drought and fire data
FEATURES = ["WS10M_MIN", "WS10M_MAX", "WS50M_MIN", "WS50M_MAX", "T2M_MIN", "T2M_MAX", "PRECTOT"]
INDEX_COLUMNS = ["DATE", "FIPS"]
masterdata = drought_data[INDEX_COLUMNS + FEATURES].merge(day_had_fire, on=INDEX_COLUMNS, how='right', validate='one_to_one')

average_nvdi = pd.read_csv('data/average_nvdi_per_day.csv', dtype={'FIPS':str})
average_nvdi['DATE'] = pd.to_datetime(average_nvdi['DATE'])

masterdata = masterdata.merge(average_nvdi, on=['FIPS', 'DATE'], how='left', validate='one_to_one')

### FEATURE LAGGING ###

LAGGED_FEATURE_COLUMNS = []
FEATURES_TO_LAG = ["T2M_MIN", "T2M_MAX", "PRECTOT", 'NVDI_AVG']
DAYS_TO_LAG = 10

masterdata = masterdata.sort_values(by="DATE")
for lag in range(1, DAYS_TO_LAG+1):
    lagged_features = masterdata[FEATURES_TO_LAG].shift(lag)
    lagged_features.columns = [f'{col}_lag_{lag}' for col in FEATURES_TO_LAG]
    masterdata = pd.concat([masterdata, lagged_features], axis=1)
    LAGGED_FEATURE_COLUMNS.append(lagged_features.columns)

LAGGED_FEATURE_COLUMNS = [item for sublist in LAGGED_FEATURE_COLUMNS for item in sublist]
# Drop first DAYS_TO_LAG rows as we won't have the feature values for those
masterdata = masterdata.iloc[DAYS_TO_LAG:]

masterdata.to_csv('data/masterdata.csv', index=False)
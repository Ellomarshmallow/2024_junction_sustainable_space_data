from shapely.geometry import Point
import geopandas as gpd
import fiona
from netCDF4 import Dataset
from icecream import ic
import numpy as np
import pandas as pd
from netCDF4 import num2date
import os
from tqdm import tqdm
import cowsay
import requests
from bs4 import BeautifulSoup



def download_files(base_url, output_dir):
    response = requests.get(base_url)
    if response.status_code != 200:
        print("Failed to access the page")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")  
    
    # Find all links to files in the directory
    for link in soup.find_all("a"):
        file_name = link.get("href")

        # Filter to only .nc files (or add other conditions if needed)
        if file_name.endswith(".nc"):
            if os.path.exists("/Users/antonia/dev/data_nvdi/" +output_dir+"/"+file_name):
                print(f"Skipping {file_name} (already exists)")
                continue
            else:
                print(f"Downloading {file_name}")
                file_url = base_url + file_name

                # Download and save each file                
                file_response = requests.get(file_url, stream=True)
                if file_response.status_code == 200:
                    with open(os.path.join(output_dir, file_name), "wb") as file:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    print(f"Downloaded {file_name}")
                else:
                    print(f"Failed to download {file_name}")

def get_fips_polygon(path, FIPS_CODE):
    ##### read fips polygon file #####
    gdf = gpd.read_file(shapefile_path)
    index = gdf[gdf['GEOID'] == FIPS_CODE].index
    fips_polygon = gdf.loc[index, 'geometry']
    return fips_polygon

def get_nvdi_averages(directory, fips_polygon, dataframe, FIPS_CODE):
    indices_in_fips = []
    for k, filename in enumerate(tqdm(os.listdir(directory), desc="Processing files")):

        #load nvdi data
        nvdi_path = os.path.join(directory, filename)
        try:
            nc_file = Dataset(nvdi_path, mode='r')
        except OSError as e:
            print(f"Error opening {filename}: {e}")
            continue

        # Access a specific variable (replace 'variable_name' with the actual variable name)
        data_lon = nc_file.variables['longitude'][:]
        data_lat = nc_file.variables['latitude'][:]
        ndvi_data = nc_file.variables['NDVI'][:].data[0]
        ndvi_mask = nc_file.variables['NDVI'][:].mask[0]
        
        ## calculate which indices are within FIPS once
        if k == 0:
            for i in range(data_lon.shape[0]):
                for j in range(data_lat.shape[0]):
                    point = Point(data_lon[i], data_lat[j])
                    is_within = fips_polygon.contains(point)
                    if is_within.bool():
                        indices_in_fips.append([i,j])

        # access nvdi data for indices_in_fips    
        nvdi_values = []
        
        # Loop through indices
        for l in range(len(indices_in_fips)):
            y_index = indices_in_fips[l][1]
            x_index = indices_in_fips[l][0]
            
            if ndvi_mask[y_index, x_index]:
                continue
            else:
                nvdi_value = ndvi_data[y_index, x_index]
                nvdi_values.append(nvdi_value.item())

        NVDI_MEAN = np.array(nvdi_values).mean()
    
        ### PANDAS DATETIME ####
        # Access the time value and units from the NetCDF file
        time_value = nc_file.variables['time'][:][0]  # Get the numeric time value
        time_units = nc_file.variables['time'].units  # Units specifying the time reference
        calendar = nc_file.variables['time'].calendar if 'calendar' in nc_file.variables['time'].ncattrs() else 'standard'

        # Convert the numeric time to a cftime datetime object
        date_cftime = num2date(time_value, units=time_units, calendar=calendar)

        # Convert to string, then to Pandas datetime
        DATE_PD = pd.to_datetime(str(date_cftime))
        #print("Pandas datetime:", DATE_PD)

        ##### add to dataframe #####
        dataframe = dataframe._append({"DAY": DATE_PD, "FIPS": FIPS_CODE, "NVDI_AVG": NVDI_MEAN}, ignore_index=True)

    return dataframe

## main method

if __name__ == '__main__':
    cowsay.cow("Vamos!")

    years = ['2015']
    fips_codes = ['06023', '06059']
    dataframe = pd.DataFrame(columns=["DAY", "FIPS", "NVDI_AVG"])

    ### DOWNLOAD NDVI DATA BY YEAR ###
    for year in years:
        base_url = "https://www.ncei.noaa.gov/data/land-normalized-difference-vegetation-index/access/" + year + "/"
        output_dir = "nvdi_data"
        #os.makedirs(output_dir, exist_ok=True)
        download_files(base_url, output_dir)
    
     ### CALCULATE DAILY NVDI AVERAGES FOR EACH FIPS ###
    for FIPS_CODE in fips_codes:
        print("Processing FIPS code:", FIPS_CODE)
        
        # load fips polygon, downloaded from http://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_us_county_500k.zip
        shapefile_path = "/Users/antonia/Downloads/cb_2016_us_county_500k/cb_2016_us_county_500k.shp"
        fips_polygon = get_fips_polygon(shapefile_path, FIPS_CODE)

        # process nvdi data for fips
        directory = output_dir
        dataframe = get_nvdi_averages(directory, fips_polygon, dataframe, FIPS_CODE)
    
    ### SAVE DATAFRAME TO CSV ###
    dataframe.to_csv('output.csv', index=False)

# Program to search for and download Sentinel-2 datasets

# Requires the sentinelsat third-party library as well as a Copernicus
# Open Access Hub account

# ==============================================================================

import datetime

import Sentinel2

from sentinelsat import SentinelAPI

# ==============================================================================

# Set the Copernicus access credentials here
Copernicus_username = "<SET USERNAME>"
Copernicus_password = "<SET PASSWORD>"

# List of UTM/MGRS tiles to search for -- Sentinel2.py defines some useful
# groups
# tiles = Sentinel2.tiles["Cancun_Tulum"]
tiles = ["16QEJ"]

# The directory where the images are to be downloaded
data_dir = "./"

# The range of dates -- Python datetimes, or dates in "YYYY-MM-DD" or
# "YYYYMMDD" format
start_date = datetime.date(2019, 7, 6)
end_date = datetime.date(2019, 7, 6)

# Unzip downloaded files?
unzip = True

# ==============================================================================

Sentinel2.search_and_download_datasets(tiles, start_date, end_date, data_dir, Copernicus_username, Copernicus_password, unzip=unzip)

# ==============================================================================

# Utilities to search for and download Sentinel-2 datasets

# Requires the sentinelsat third-party library as well as a Copernicus
# SciHub account

# The Copernicus access credentials are stored in the base.py file

# ==============================================================================

import datetime
import os
import zipfile

import base

from sentinelsat import SentinelAPI

# ==============================================================================

def search_products(tile=None, date=None, search_string=None, product_type="L2A", satellite=None, query_args=None):
  """Searches Copernicus SciHub for Sentinel-2 datasets (products) for a given
  tile and date. Alternatively, if search_string is given pass that directly
  to the Copernicus API (ignoring all other arguments).

  Parameters:

    tile : string
      The UTM/MGRS tile, e.g. '16QEJ'

    date : string, date or datetime object
      The date for which to the tile. Can be a string in "YYYY-MM-DD" or
      "YYYYMMDD" format, or a Python date or datetime object

    -- OR --

    search_string : string
      If given, pass this directly to Copernicus and ignore tile and date

  Options:

    product_type : string (default: 'L2A')
      A Sentinel-2 product name: 'L1C', 'L2A' or 'L2Ap'

    satellite : string (default: None, i.e. both)
      If given, which Sentinel-2 satellite to search for: 'A' or 'B'

    query_args : dictionary (default: None)
      Additional query arguments to be passed directly to SentinelAPI.query().
      If None, orbitdirection will be set to 'Descending'

  Returns:

    A dictionary with the found products, with UUIDs as keys
  """

  # Parse dates if strings
  if date is not None and isinstance(date, str):
    _date = datetime.datetime.strptime(date.replace("-", ""), "%Y%m%d")

  # Login to Copernicus
  api = SentinelAPI(base.Copernicus_username, base.Copernicus_password)

  # Generate product search string if not giben
  if search_string is None:
    search_string = ""
    if satellite is not None:
      search_string += "S2{}".format(satellite)
    else:
      search_string += "S2*"
    search_string += "_MSI{}".format(product_type)
    search_string += "_{}*".format(_date.strftime("%Y%m%d"))
    search_string += "_N*_R*"
    search_string += "_T{}".format(tile)
    search_string += "_*"

  if query_args is not None:
    if "orbitdirection" not in query_args:
      query_args["orbitdirection"] = "Descending"

  # Search Copernicus for products
  if query_args is None:
    products = api.query(filename=search_string)
  else:
    products = api.query(filename=search_string, *query_args)

  if len(products) > 0:
    return products
  else:
    return {}

# ------------------------------------------------------------------------------

def download_products(products, datadir, unzip=False, max_retries=3, verbose=True):
  """Downloads a set of Sentinel-2 products.

  Parameters:

    products : dict
      A dict with Sentinel-2 products, as returned by SentinelAPI.query() or
      search_products(); keys must be Sentinel-2 UUIDs and values must be
      dicts with at least the "identifier" property.

    datadir : string
      The path to the directory where the products should be downloaded

  Options:

    unzip : boolean (default: False)
      Whether to unzip the downloaded products (to the same dir)

    max_retries : integer (default: 3)
      The maximum number of retires

    verbose : boolean (default: True)
      Whether to report progress to screen

  Returns:

    None
  """

  # Login to Copernicus
  api = SentinelAPI(base.Copernicus_username, base.Copernicus_password)

  for product_id, product_info in products.items():

    tile = product_info["identifier"].split("_")[5][1:]
    tile_dir_path = os.path.join(datadir, "T{}".format(tile))
    zip_fname = product_info["identifier"] + ".zip"
    zip_fpath = os.path.join(tile_dir_path, zip_fname)

    if os.path.isfile(zip_fpath):

      # Skip download if the zip already exists
      if verbose:
        print("Already downloaded: {}".format(product_info["identifier"]))

    else:

      # Create tile subdir if not found
      if not os.path.exists(tile_dir_path):
        os.makedirs(tile_dir_path)

      # Download (and check with MD5) product
      if verbose:
        print(product_info["identifier"])

      tries_left = max_retries
      while tries_left > 0:
        try:
          result = api.download(product_id, tile_dir_path)
          break
        except SentinelAPI.InvalidChecksumError:
          tries_left -= 1
          if verbose:
            if tries_left > 0:
              print("Bad MD5 checksum! Retrying.")
            else:
              print("Bad MD5 checksum! Max retries reached; skipping.")
          os.remove(zip_fpath)
        except:
          tries_left -= 1
          if verbose:
            if tries_left > 0:
              print("Unknown error! Retrying.")
            else:
              print("Unknown error! Skipping.")

    # Unzip if asked
    if unzip:
      unzipped_fname = product_info["identifier"] + ".SAFE"
      unzipped_path = os.path.join(tile_dir_path, unzipped_fname)
      if os.path.exists(unzipped_path):
        if verbose:
          print("Dataset already unzipped")
      else:
        if verbose:
          print("Unzipping dataset ...")
        with zipfile.ZipFile(zip_fpath, "r") as zip:
          zip.extractall(tile_dir_path)

# ------------------------------------------------------------------------------

def search_and_download_datasets(tiles, start_date, end_date, datadir, unzip=False, max_retries=3, verbose=True, query_args=None):
  """Search datasets (products) for the given list of tiles and the given date
  range, and download the found products (zip files) to datadir, optionally
  unzipping them afer download.

  The datasets will be downloaded to subdirs for each tile, which whill be
  created if it doesn't exist. If a dataset zip already exists, it will be
  skipped.

  Only products with orbitdirection='Descending' will be searched by default,
  as Sentinel-2 has 10:30 local solar time at descending node, so Descendin
  passes are during daylight while ascending passes are during the night. To
  override, set orbitdirection in query_args.

  See https://hls.gsfc.nasa.gov/products-description/tiling-system/ for info
  on the UTM/MGRS tiling system.

  Parameters:

    tiles : list of strings
      A list of UTM/MGRS tiles

    start_date, end_date : strings, date or datetime objects
      The range of dates for which to download tiles. Can be strings in
      "YYYY-MM-DD" or "YYYYMMDD" format, or Python date or datetime objects

    datadir : string
      The path to the directory where the products should be downloaded

  Options:

    unzip : boolean (default: False)
      Whether to unzip the downloaded products (to the same dir)

    max_retries : integer (default: 3)
      The maximum number of retires

    verbose : boolean (default: True)
      Whether to report progress to screen

    query_args : dictionary (default: None)
      Additional query arguments to be passed directly to SentinelAPI.query()
      If None, orbitdirection will be set to 'Descending'

  Returns:

    None
  """

  # Parse dates if strings
  if isinstance(start_date, str):
    _start_date = datetime.datetime.strptime(start_date.replace("-", ""), "%Y%M%D")
  else:
    _start_date = start_date
  if isinstance(end_date, str):
    _end_date = datetime.datetime.strptime(end_date.replace("-", ""), "%Y%m%d")
  else:
    _end_date = end_date

  _date = _start_date
  oneday = datetime.timedelta(days=1)
  while _date <= _end_date:

    if verbose:
      print("\n>>", _date)

    tot_tiles = len(tiles)
    for count,tile in enumerate(tiles):

      # Search for products
      products = search_products(tile, _date.strftime("%Y%m%d"), query_args=query_args)
      if verbose:
        s = "\n{}, {} ({}/{}): ".format(_date.strftime("%Y-%m-%d"), tile, count+1, tot_tiles)
        if len(products) > 0:
          s += "{} product{} found".format(len(products), "s" if len(products) > 1 else "")
        else:
          s += "no products found"
        print(s)

      if len(products) > 0:

        # Download products
        download_products(products, datadir, unzip=unzip, max_retries=max_retries, verbose=verbose)

    _date += oneday

# ==============================================================================

# Downlod the specified tiles in the given range of dates
if __name__ == "__main__":

  tiles = base.tiles["Cancun_Tulum"]

  datadir = "/home/meithan/Desktop/OH19/datasets/"

  start_date = datetime.date(2019, 7, 6)
  end_date = datetime.date(2019, 7, 6)
  step = datetime.timedelta(days=1)

  # -------------------------------------

  search_and_download_datasets(tiles, start_date, end_date, datadir, unzip=True)

# Utilities to search, download and handle Sentinel-2 datasets

# ==============================================================================

import datetime
import glob
import os
import sys
import zipfile

from sentinelsat import SentinelAPI
import rasterio

# ==============================================================================

# Some tiles of interest in UTM/MGRS format

# Sentinel-2A and Sentinel-2B occupy the same orbit, but separated by 180 degrees. The mean orbital altitude is 786 km. The orbit inclination is 98.62° and the Mean Local Solar Time (MLST) at the descending node is 10:30.

tiles = {}

# Contains Cancún
tiles["Cancun"] = ["16QEJ"]

# Coastal tiles of the Riviera Maya from Cancún to Tulum
tiles["Cancun_Tulum"] = ["16QEJ", "16QDH", "16QEH", "16QDG", "16QEG", "16QDF", "16QEF"]

# The complete "Mexican Caribbean", extending to about Cuba eastward and
# down to Honduras southward
tiles["Mexican_Caribbean"] = [
"16QEJ", "16QFJ", "16QGJ", "16QHJ",
"16QDH", "16QEH", "16QFH", "16QGH", "16QHH",
"16QDG", "16QEG", "16QFG", "16QGG", "16QHG",
"16QDF", "16QEF", "16QFF", "16QGF", "16QHF",
"16QCE", "16QDE", "16QEE", "16QFE", "16QGE", "16QHE",
"16QCD", "16QDD", "16QED", "16QFD", "16QGD", "16QHD",
"16PCC", "16PDC", "16PEC", "16PFC", "16PGC", "16PHC",
]

# The French Antilles: Guadeloupe and Martinique
tiles["French_Antilles"] = [
"20QND", "20QPD", "20QQD",
"20PNC", "20PPC", "20PQC",
"20PNB", "20PPB", "20PQB",
"20PNA", "20PPA", "20PQA"
]

# The French Guiana; 22NCL contains Cayenne
tiles["Guyane"] = [
"21NZG", "21NHZ", "22NBM", "22NBN", "22NCN", "22NCM", "22NCL", "22NDN",
"22NDM", "22NDL", "22NEM", "22NEL"
]

# ==============================================================================
# Sentinel-2 Quantification Value to convert DN values to reflectance

QUANT_VAL_ASI = float(2**16-1)    # Value required for older ASI models
QUANT_VAL_S2 = 10000              # Value to use for AFAI or new ASI models

# ==============================================================================

def search_and_download_datasets(tiles, start_date, end_date, data_dir, username, password, unzip=False, max_retries=3, verbose=True, query_args=None):
  """Search datasets (products) for the given list of tiles and the given date
  range, and download the found products (zip files) to data_dir, optionally
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

    data_dir : string
      The path to the directory where the products should be downloaded

    username, password : string
      Copernicus Open Access Hub username and password

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

  if username in ["", None] or password in ["", None]:
    print("Error: you must provide your Copernicus credentials; you can set them in download_datasets.py")
    sys.exit()

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
      products = search_products(tile=tile, date=_date.strftime("%Y%m%d"), query_args=query_args, username=username, password=password)

      if verbose:
        s = "\n{}, {} ({}/{}): ".format(_date.strftime("%Y-%m-%d"), tile, count+1, tot_tiles)
        if len(products) > 0:
          s += "{} product{} found".format(len(products), "s" if len(products) > 1 else "")
        else:
          s += "no products found"
        print(s)

      if len(products) > 0:

        # Download products
        download_products(products, data_dir, username, password, unzip=unzip, max_retries=max_retries, verbose=verbose)

    _date += oneday

# ==============================================================================

def download_products(products, data_dir, username, password, unzip=False, max_retries=3, verbose=True):
  """Downloads a set of Sentinel-2 products.

  Parameters:

    products : dict
      A dict with Sentinel-2 products, as returned by SentinelAPI.query() or
      search_products(); keys must be Sentinel-2 UUIDs and values must be
      dicts with at least the "identifier" property.

    data_dir : string
      The path to the directory where the products should be downloaded

    username, password : string
      Copernicus Open Access Hub username and password

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

  if username in ["", None] or password in ["", None]:
    print("Error: you must provide your Copernicus credentials; you can set them in download_datasets.py")
    sys.exit()

  # Login to Copernicus
  api = SentinelAPI(username, password)

  for product_id, product_info in products.items():

    tile = product_info["identifier"].split("_")[5][1:]
    tile_dir_path = os.path.join(data_dir, "T{}".format(tile))
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

      if verbose:
        print("Downloaded {}".format(zip_fname))

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
        if verbose:
          print("Unzipped {}".format(unzipped_fname))

# ==============================================================================

def search_products(tile=None, date=None, search_string=None, product_type="L2A", username=None, password=None, satellite=None, query_args=None):
  """Searches Copernicus SciHub for Sentinel-2 datasets (products) for a given
  tile and date. Alternatively, if search_string is given pass that directly
  to the Copernicus API (ignoring all other arguments).

  Parameters:

    --------

    tile : string
      The UTM/MGRS tile, e.g. '16QEJ'

    date : string, date or datetime object
      The date for which to the tile. Can be a string in "YYYY-MM-DD" or
      "YYYYMMDD" format, or a Python date or datetime object

    -- OR --

    search_string : string
      If given, pass this directly to Copernicus and ignore tile and date

    --------

    username, password : string
      Copernicus Open Access Hub username and password

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

  if username in ["", None] or password in ["", None]:
    print("Error: you must provide your Copernicus credentials; you can set them in download_datasets.py")
    sys.exit()

  # Parse dates if strings
  if date is not None and isinstance(date, str):
    _date = datetime.datetime.strptime(date.replace("-", ""), "%Y%m%d")

  # Login to Copernicus
  api = SentinelAPI(username, password)

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

# ==============================================================================

def load_channels(dataset_path, channels, resolution, img_data_path=None, s2_quant=QUANT_VAL_ASI, verbose=False):
  """ Load bottom-of-atmosphere reflectivity channels from a Sentinel-2 dataset

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

    channels : list of strings:
      A list with the channel names to load

    resolution : int or string
      Sentinel-2 spatial resolution to use

  Options:

    s2_quant : numeric value (default: QUANT_VAL_ASI)
      Sentinel-2 QUANTIFICATION_VALUE to convert from digital levels to
      reflectance; defaults to the value used by the older ASI models, but
      QUANT_VAL_S2 should be used for AFAI or new ASI models

    verbose : boolean (default: True)
      Whether to report progress to screen

  Returns:

    A dictionary with following structure:
    {
      "meta": <image metdata>,
      "channels": {
        "channel1_name": <numpy array with data>,
        "channel2_name": <numpy array with data>,
        ...
      }
    }

  """
  # ----------------------------------------------------------------------------

  img_data_path = locate_data_path(dataset_path, resolution)
  if img_data_path is None:
    return None

  dataset = {"meta": None, "channels": {}}
  for ch_name in channels:

    pattern = os.path.join(img_data_path, "*_{}_*.jp2".format(ch_name))
    paths = glob.glob(pattern)

    if len(paths) == 0:
      print("Couldn't find image for channel {}".format(ch_name))
      return None

    if len(paths) > 1:
      print("Warning: multiple channel {} images found; using first".format(ch_name))

    img_path = paths[0]

    # Stored Sentinel-2 L2A data is stored as uint16, we convert it to float32
    # to have 15 bits of precision in calculations
    dtype = "float32"
    img = rasterio.open(img_path, driver='JP2OpenJPEG')
    data = img.read(1).astype(dtype)

    if verbose:
      NX, NY = data.shape
      print("Loaded {}, {} x {}, {:.1f} MB".format(os.path.basename(img_path), NX, NY, data.nbytes/1024**2))

    if dataset["meta"] is None:
      dataset["meta"] = {}
      dataset["meta"]["dtype"] = dtype
      dataset["meta"]["nodata"] = img.meta["nodata"]
      dataset["meta"]["width"] = img.meta["width"]
      dataset["meta"]["height"] = img.meta["height"]
      dataset["meta"]["crs"] = img.meta["crs"]
      dataset["meta"]['transform'] = img.meta["transform"]

    # Convert the Sentinel-2 stored data to reflectivity values
    data /= float(s2_quant)

    dataset["channels"][ch_name] = data

  return dataset

# ==============================================================================

def load_SCL(dataset_path, resolution, return_path=False):
  """ Load Scene Classification Layer at given resolution from a Sentinel-2
  dataset

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

    resolution : int or string
      Sentinel-2 spatial resolution to use

  Options:

    return_path : boolean (default: False)
      Whether to return the path to the found SCL instead of the data

  Returns:

    A numpy array with the SCL, or the file path if return_path is true

  """
  # ----------------------------------------------------------------------------

  img_data_path = locate_data_path(dataset_path, resolution)
  if img_data_path is None:
    return None

  pattern = os.path.join(img_data_path, "*_SCL_*.jp2")
  paths = glob.glob(pattern)

  if len(paths) == 0:
    print("Couldn't find SCL image in {}!".format(pattern))
    return None

  if len(paths) > 1:
    print("Warning: multiple SCL masks found")
  SCL_path = paths[0]

  SCL_im = rasterio.open(SCL_path, driver='JP2OpenJPEG')
  SCL = SCL_im.read(1)

  if return_path:
    return SCL_path
  else:
    return SCL

# ==============================================================================

def locate_data_path(dataset_path, resolution):
  """ Locate JP2 images at requested resolution

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

    resolution : int, float or string
      Sentinel-2 spatial resolution to use

  Returns:

    A string with the path to the image data directory of this dataset,
    or None if not found

  """
  # ----------------------------------------------------------------------------

  pattern = os.path.join(dataset_path, "GRANULE/L2A*/IMG_DATA/R{}m".format(int(resolution)))
  paths = glob.glob(pattern)

  if len(paths) == 0:
    print("Couldn't find IMG_DATA directory at {}m resolution in {}".format(resolution, pattern))
    return None

  if len(paths) > 1:
    print("Warning: multiple IMG_data directories found; using first")

  return paths[0]

# ==============================================================================

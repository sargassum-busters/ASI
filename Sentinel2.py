# Utilities to handle Sentinel-2 datasets

# ==============================================================================

import glob
import os

import rasterio

# ==============================================================================
# Globals

QUANT_VAL_ASI = float(2**16-1)    # Value required for older ASI models
QUANT_VAL_S2 = 10000             # Value to use for AFAI or new ASI models

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

def load_SCL(dataset_path, resolution, verbose=True):
  """ Load Scene Classification Layer at given resolution from a Sentinel-2
  dataset

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

    resolution : int or string
      Sentinel-2 spatial resolution to use

  Options:

    verbose : boolean (default. True)
      Sentinel-2 QUANTIFICATION_VALUE to convert from digital levels to
      reflectance; defaults to the value used by the older ASI models

  Returns:

    A boolean numpy array with the SCL

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

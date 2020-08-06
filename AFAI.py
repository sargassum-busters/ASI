# A class to compute the AFAI index

from Sargassum_Index import Sargassum_Index

# ==============================================================================

class AFAI_Index(Sargassum_Index):
  """ Wang & HU's Alternative Floating Algae Index (AFAI)"""

  # ----------------------------------------------------------------------------

  name = "AFAI"

  # Sentinel-2 channels used to compute AFAI
  required_channels = ["B04", "B06", "B8A"]
  meta_channels = {
    "RED": {"ch": "B04", "lambda": 665.},   # ~ MODIS 667
    "NIR": {"ch": "B06", "lambda": 740.},   # ~ MODIS 748
    "SWIR": {"ch": "B8A", "lambda": 865.}   # ~ MODIS 869
  }

  # ----------------------------------------------------------------------------

  def __init__(self, verbose=True):
    self.verbose = verbose

  # ----------------------------------------------------------------------------

  def compute(self, channels_data):

    RED = channels_data[self.meta_channels["RED"]["ch"]]
    NIR = channels_data[self.meta_channels["NIR"]["ch"]]
    SWIR = channels_data[self.meta_channels["SWIR"]["ch"]]

    RED_lambda = self.meta_channels["RED"]["lambda"]
    NIR_lambda = self.meta_channels["NIR"]["lambda"]
    SWIR_lambda = self.meta_channels["SWIR"]["lambda"]

    R_NIR_prime = RED + (SWIR - RED) * (NIR_lambda - RED_lambda)/(SWIR_lambda - RED_lambda)

    AFAI = NIR - R_NIR_prime

    if self.verbose:
      print("Min: {}".format(AFAI.min()))
      print("Max: {}".format(AFAI.max()))

    return AFAI

# ==============================================================================

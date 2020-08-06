# The base class for Sargassum indices

# ==============================================================================

class Sargassum_Index:
  """Base class for sargassum indices used by detect_sargassum().

  Any derived class must override three things:

  1) The 'name' class variable

  2) The 'required_channels' class variable, which must be a list of strings
     with the names of the channels that this index requires

  3) The 'compute()' method, which must receive at least the 'channels_data'
     parameter, a dict containing a parsed Sentinel-2 dataset as returned by
     Sentinel2.load_channels(), and return a numpy array with the result."""

  # Class variables -- to be overriden by derived clases
  name = None
  required_channels = None

  # Mandatory method for derived classes
  def compute(self, channels_data):
    """Derived classes must override this method.

    The single required parameter is channels_data, which must be a dict
    with the structures specified by Sentinel2.load_channels().

    Must return a numpy array with the result of the sargassum prediction."""
    raise NotImplementedError

# ==============================================================================

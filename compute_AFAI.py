# Driver program to compute the AFAI of a given Sentinel-2 L2A product

# ==============================================================================

import sys

from AFAI import AFAI_Index
from detect_sargassum import detect_sargassum

# ==============================================================================
# Program configuration
# See detect_sargassum documentation for further details

# Path to the SAFE directory containing the Sentinel-2 image
dataset_path = sys.argv[1]

# Output directory
out_dir = "./"

# Mask out pixels using SCL?
apply_mask = True

# List of SCl labels to keep
mask_keep_categs = [6]

# If set to a numeric value, threshold the image using this
threshold = None

# Save the result as a raw numpy array?
save_npy = True

# Save the result as georeferenced GeoTIFF?
save_geotiff = True

# Save the result as georeferenced OpenJPEG2000?
save_jp2 = False

# Report actions to screen?
verbose = True

# ==============================================================================

# Initialize AFAI index
index = AFAI_Index(verbose=verbose)

# Compute index on image
result = detect_sargassum(dataset_path, index, out_dir=out_dir, apply_mask=apply_mask, mask_keep_categs=mask_keep_categs, threshold=threshold, save_npy=save_npy, save_geotiff=save_geotiff, save_jp2=save_jp2, verbose=verbose)

# ==============================================================================

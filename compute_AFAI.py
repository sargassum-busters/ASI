# A wrapper program to compute the AFAI of a given Sentinel-2 L2A product

# ==============================================================================

import sys

from AFAI import AFAI_Index
from detect_sargassum import detect_sargassum

# ==============================================================================
# Program configuration
# See detect_sargassum documentation for details

dataset_path = sys.argv[1]

outdir = "./"

apply_mask = False
mask_keep_categs = [6]
threshold = None
save_npy = False
save_geotiff = True
save_jp2 = False
resolution = "20"
verbose = True

# ==============================================================================

# Initialize AFAI index
index = AFAI_Index(verbose=verbose)

# Compute index on image
detect_sargassum(dataset_path, index, outdir=outdir, apply_mask=apply_mask, mask_keep_categs=mask_keep_categs, save_npy=save_npy, save_geotiff=save_geotiff, save_jp2=save_jp2, verbose=verbose)

# ==============================================================================

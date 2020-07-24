# Plots the Scene Classification Layer (SCL) of a Sentinel-2 SAFE dataset

import glob
import os
import sys

import numpy as np
import rasterio
from PIL import Image

# ==============================================================================
# OPTIONS

# The path to the SAFE archive directory to process
safe_dir = sys.argv[1]

# Output directory for all results
out_dir = "./"

# Sentinel-2 spatial resolution to use,
resolution = 20

# Show and/or save resulting image
save_image = True
show_image = False

# =============================================================================

# Convert hex value to RGB tuple
def hex_to_rgb(hx):
  hx = hx.lstrip("#")
  return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

# Colors taken from Sentinel user manual
# https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm
label_colors = {0: "#000000", 1: "#fb0c00", 2: "#3e3e3e", 3: "#843900", 4: "#29ff00", 5: "#feff00", 6: "#1500cd", 7: "#767271", 8: "#afacab", 9: "#d1cfcf", 10: "#2ccdff", 11: "#fd66ff"}

# Generate subdir with JP2 files
pattern = os.path.join(safe_dir, "GRANULE", "*", "IMG_DATA", "R{}m".format(resolution))
result = glob.glob(pattern)
if len(result) == 1:
  jp2_dir = result[0]
elif len(result) > 1:
  print("Warning: multiple JP2 dirs found in archive; using first")
  for x in result:
    print(x)
  jp2_dir = result[0]
else:
  jp2_dir = None
if not os.path.isdir(jp2_dir):
  print("Couldn't find JP2 directory!")
  if jp2_dir is not None:
    print("Not found:", jp2_dir)
  sys.exit()

# Generate output base name
tokens = safe_dir.split("_")
out_fname_base = "{}_{}_SCL".format(tokens[5], tokens[2])

# Load mask
SCL_fname = glob.glob(os.path.join(jp2_dir, "*_SCL_*.jp2"))[0]
SCL = rasterio.open(SCL_fname, driver='JP2OpenJPEG').read(1)
bname = os.path.basename(SCL_fname)
print("Loaded mask: {}".format(bname))
print("{} x {}, min: {}, max: {}".format(*SCL.shape, SCL.min(), SCL.max()))

h, w = SCL.shape

print("Creating image ...")
img_data = np.zeros((h, w, 3), dtype=np.uint8)
for c in range(11+1):
  img_data[SCL == c] = hex_to_rgb(label_colors[c])

img = Image.fromarray(img_data, 'RGB')

if save_image:
  out_fname = out_fname_base + ".png"
  out_path = os.path.join(out_dir, out_fname)
  img.save(out_path)
  print("wrote {}".format(out_path))

if show_image:
  img.show()

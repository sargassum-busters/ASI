# Plots the Scene Classification Layer (SCL) of a Sentinel-2 SAFE dataset

import glob
import os
import sys

import numpy as np
from PIL import Image
import rasterio

import Sentinel2

# Requires Pillow
# https://pypi.org/project/Pillow/

# ==============================================================================

def plot_SCL(dataset_path, resolution, show_image=True, save_png=False, save_geotiff=False, out_dir="./"):
  """ Plots the SCL layer from a Sentinel-2 dataset

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

    resolution : int or string
      Sentinel-2 spatial resolution to use

  Options:

    show_image : boolean (default: true)
      Whether to display the image

    save_png : boolean (default: false)
      Whether to save the image to disk in PNG format at full resolution

    save_geotiff : boolean (default: false)
      Whether to save the image to disk in GeoTIFF format

    out_dir : string (default: "./")
      The output path where the image  is saved if save_png or save_geotiff
      are true. Defaults to current working directory.

  Returns:

    None

  """
  # ----------------------------------------------------------------------------

  # The SCL classes
  # https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm
  SCL_classes = {
    0: {"name": "NO_DATA", "color": "#000000"},
    1: {"name": "SATURATED_OR_DEFECTIVE", "color": "#fb0c00"},
    2: {"name": "DARK_AREA_PIXELS", "color": "#3e3e3e"},
    3: {"name": "CLOUD_SHADOWS", "color": "#843900"},
    4: {"name": "VEGETATION", "color": "#29ff00"},
    5: {"name": "NOT_VEGETATED", "color": "#feff00"},
    6: {"name": "WATER", "color": "#1500cd"},
    7: {"name": "UNCLASSIFIED", "color": "#767271"},
    8: {"name": "CLOUD_MEDIUM_PROBABILITY", "color": "#afacab"},
    9: {"name": "CLOUD_HIGH_PROBABILITY", "color": "#d1cfcf"},
    10: {"name": "THIN_CIRRUS", "color": "#2ccdff"},
    11: {"name": "SNOW", "color": "#fd66ff"}
  }

  # Convert hex value to RGB tuple
  def hex_to_rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

  # ----------------------------------------------------------------------------

  for c in SCL_classes.keys():
    SCL_classes[c]["rgb_color"] = hex_to_rgb(SCL_classes[c]["color"])

  # Load mask
  SCL_path = Sentinel2.load_SCL(dataset_path, resolution, return_path=True)
  SCL_im = rasterio.open(SCL_path, driver='JP2OpenJPEG')
  SCL = SCL_im.read(1)

  base_name = os.path.splitext(os.path.basename(SCL_path))[0]
  print("Loaded {}".format(base_name))

  nx, ny = SCL.shape
  ntot = nx * ny
  print("Size {} x {}, counts:".format(nx, ny, SCL.min(), SCL.max()))
  unique, counts = np.unique(SCL, return_counts=True)
  mask_counts = dict(zip(unique, counts))
  for c, count in mask_counts.items():
    print("{:<2} {:<25} {:,} ({:.2f}%)".format(c, SCL_classes[c]["name"], count, 100*count/ntot))

  if save_png or show_image:

    print("Creating image ...")
    img_data = np.zeros((ny, nx, 3), dtype=np.uint8)
    for c in SCL_classes.keys():
      img_data[SCL == c] = SCL_classes[c]["rgb_color"]
    img = Image.fromarray(img_data, 'RGB')

    out_fname = base_name + ".png"
    out_path = os.path.join(out_dir, out_fname)
    img.save(out_path)
    print("wrote {}".format(out_path))

    if show_image:
      print("Displaying in external viewer ...")
      img.show()

  if save_geotiff:

    meta = {}
    meta["dtype"] = np.uint8
    meta["nodata"] = SCL_im.meta["nodata"]
    meta["width"] = SCL_im.meta["width"]
    meta["height"] = SCL_im.meta["height"]
    meta["crs"] = SCL_im.meta["crs"]
    meta["transform"] = SCL_im.meta["transform"]
    meta["driver"] = "GTiff"
    meta["count"] = 1

    out_fname = base_name + ".tif"
    out_path = os.path.join(out_dir, out_fname)

    with rasterio.open(out_path, "w", **meta) as fout:
      fout.write(SCL, 1)
    print("Wrote {}".format(out_path))

# ==============================================================================

if __name__ == "__main__":

  # The path to the SAFE archive directory to process
  dataset_path = sys.argv[1]

  # Output directory for all results
  out_dir = "./"

  # Sentinel-2 spatial resolution to use,
  resolution = 20

  # Show image?
  show_image = False

  # Save image?
  save_png = False
  save_geotiff = True

  plot_SCL(dataset_path=dataset_path, resolution=resolution, show_image=show_image, save_png=save_png, save_geotiff=save_geotiff, out_dir=out_dir)

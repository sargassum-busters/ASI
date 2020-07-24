# Plots the provided numpy array

# ==============================================================================

import os
import sys

import matplotlib as mpl
import numpy as np

# =============================================================================

def plot_npy(file_path, out_dir="./", cmap="viridis", resolution=20, show_colorbar=True, save_image=False, show_image=True):

  data = np.load(file_path)

  NX, NY = data.shape
  print("Loaded {}, {} x {}, {:.1f} MB".format(file_path, NX, NY, data.nbytes/1024**2))

  if not show_image:
    mpl.use("Agg")

  import matplotlib.pyplot as plt
  import matplotlib.colors as mcolors
  from mpl_toolkits.axes_grid1 import make_axes_locatable

  fig = plt.figure()

  # if isinstance(cmap, str):
  #   cmap = mpl.cm.get_cmap(cmap)
  map_colors = [(0, 0, 0.3), (0, 1, 0)]
  cmap = mcolors.LinearSegmentedColormap.from_list("custom", [mcolors.to_rgb(c) for c in map_colors])

  cmap.set_bad("0.05")

  im = plt.imshow(data, cmap=cmap)

  plt.gca().get_xaxis().set_visible(False)
  plt.gca().get_yaxis().set_visible(False)

  if show_colorbar:
    divider = make_axes_locatable(plt.gca())
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)

  dpi = fig.get_dpi()
  if not show_colorbar:
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.set_size_inches(NX/dpi*1.05, NY/dpi)
  else:
    plt.tight_layout()
    fig.set_size_inches(NX/dpi, NY/dpi)

  if save_image:
    print("Writing image ...")
    out_basename = os.path.splitext(os.path.basename(file_path))[0]
    fname = out_basename + ".png"
    out_path = os.path.join(out_dir, fname)
    plt.savefig(out_path, bbox_inches=0)
    print("Saved {}".format(out_path))

  if show_image:
    print("Plotting image ...")
    plt.show()


# ==============================================================================
# PROGRAM CONFIGURATION

if __name__ == "__main__":

  # The path to the GeoTIFF file to read -- currently passed as command line arg
  file_path = sys.argv[1]

  # Output directory for all results
  out_dir = "./tests/"

  # Sentinel-2 spatial resolution to use,
  resolution = 20

  # Show colorbar?
  show_colorbar = False

  # Show and/or save resulting image
  save_image = True
  show_image = False

  plot_npy(file_path, out_dir=out_dir, resolution=resolution, show_colorbar=show_colorbar, save_image=save_image, show_image=show_image)

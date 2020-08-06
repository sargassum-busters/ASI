# Create an ASI training set from a Sentinel-2 dataset

# ==============================================================================

import glob
import os
import random
import sys

import numpy as np

from AFAI import AFAI_Index
from detect_sargassum import detect_sargassum
import Sentinel2

# ==============================================================================

def generate_training_set(dataset_path, out_dir="./", full_array=True, AFAI_threshold=0.005, mask_keep_categs=[6], verbose=True):
  """Create an ASI training set from a Sentinel-2 dataset using AFAI

  This is done by computing the AFAI and applying a user-specified threshold
  to generate a discrete array where each pixel has one of the following values:

    1 = sargassum in water (or non-masked) pixel
    0 = not-sargassum in water (or non-masked) pixel
    2 = masked pixel/unknown (when full_array is True)

  The result is written to disk as a numpy array and its shape dependson a few
  options:

  1) If full_array is True, then all pixels in the image are included in the
  taining set and the array will have shape (N, M, 12), where N = M = 5490 at
  20m resolution. In this case the 12 columns are:

    1-2: the i,j image coordinates of the pixel
    3-11: the 9 Sentinel-2 bands used by ASI: "B02", "B03", "B04", "B05", "B06",
         "B07", "B8A", "B11", "B12"
    12: the calculated class of the pixel, as described above

  The Sentinel-2 SCL mask is applied to filter out pixels identified as
  not-water (clouds, cloud shadows, land, etc.) by setting them to class 2.
  Use 'keep_categs' to set which classes of the SCl to keep and which to mask.

  2) If full_array is False, a "small" training set is build by only saving sargassum pixels and the same number of randomly-selected non-sargassum (non-
  masked) pixels. The array will have shape (NT, 12), where NT is the total
  number of pixels written (half of which are sargassum and half non-sargassum). Each row is one pixel, and the 12 columsn are:

    1: the i coordinate of the pixel
    2: the j coordinate of the pixel
    3-11: the 9 Sentinel-2 bands used by ASI
    12: the calculated class of the pixel, as described above

  With this option no masked pixels are saved.

  Parameters:

    dataset_path : string
      The path to the SAFE directory with the Sentinel-2 dataset

  Options:

    out_dir : string (default: "./")
      The output path where the training set is saved; defaults to current dir

    full_array : boolean (default: True)
      Write all pixels to learning set, or only sargassum pix + equal amount of
      non-Sargassum pix? See details above.

    AFAI_threshold : float (default: 0.005)
      The AFAI threshold to use to create the class. The default value of 0.005
      applies to the old S2_QUANT of 2**16-1 only.

    mask_keep_categs : list of integers (default: [6])
      The classes of the SCL mask where the sargassum classification is done.
      6 is water.

  Returns:

    None; the result is saved to disk
  """

  # ============================================================================

  # The features to save to the training set
  ASI_features = ["B02", "B03", "B04", "B05", "B06", "B07", "B8A", "B11", "B12"]

  basename = os.path.basename(os.path.normpath(dataset_path))
  out_fname = "{}_{}_train.npy".format(basename[39:44], basename[11:26])

  # Initialize AFAI
  AFAI_index = AFAI_Index(verbose=verbose)

  # Create classification mask from AFAI
  AFAI_mask = detect_sargassum(dataset_path, AFAI_index, apply_mask=True, mask_keep_categs=mask_keep_categs, masked_value=2, threshold=AFAI_threshold, resolution="20", save_npy=False, save_geotiff=False, save_jp2=False, verbose=verbose)

  num_sarg = np.count_nonzero(AFAI_mask == 1)
  num_not_sarg = np.count_nonzero(AFAI_mask == 0)
  num_masked = np.count_nonzero(AFAI_mask == 2)
  NX, NY = AFAI_mask.shape
  NTOT = AFAI_mask.size
  NFEAT = len(ASI_features)

  if verbose:
    print("\nClassification results:")
    print("{:,} ({:.1f}%) sargassum pixels".format(num_sarg, 100*num_sarg/NTOT))
    print("{:,} ({:.1f}%) not-sargassum pixels".format(num_not_sarg, 100*num_not_sarg/NTOT))
    print("{:,} ({:.1f}%) masked pixels".format(num_masked, 100*num_masked/NTOT))

  # Load ASI channels
  if verbose:
    print("\nLoading ASI features ...")
  ASI_dataset = Sentinel2.load_channels(dataset_path, ASI_features, resolution=20, verbose=True)

  if full_array:

    # Just stack and reshape
    train_set = np.stack([ASI_dataset["channels"][ch] for ch in ASI_features] + [AFAI_mask.astype("float32")])
    train_set = np.transpose(train_set, axes=(1,2,0))

  else:

    if verbose:
      print("\nBuilding minimal training set ...")

    # Extract coordinates
    if verbose:
      print("Extracting coordinates ...")
    sargassum_coords = np.argwhere(AFAI_mask == 1)
    not_sargassum_coords = np.argwhere(AFAI_mask == 0)

    num_sarg = len(sargassum_coords)
    num_tot = 2*num_sarg
    ncols = 2 + NFEAT + 1

    # Randomly choose equal number of non-sargassum coords
    if verbose:
      print("Randomly selecting non-sargassum pixels ...")
    nonsarg_coords = random.sample(list(not_sargassum_coords), num_sarg)

    # Pack data
    if verbose:
      print("Packing data ...")
    train_set = np.empty((num_tot, ncols), dtype="float32")
    for k in range(num_tot):
      if k <= num_sarg-1:
        i, j = sargassum_coords[k]
      else:
        i, j = not_sargassum_coords[k]
      train_set[k, 0] = i
      train_set[k, 1] = j
      for l in range(NFEAT):
        train_set[k, 2+l] = ASI_dataset["channels"][ASI_features[l]][i,j]
      train_set[k, ncols-1] = AFAI_mask[i,j]

  # Write training set to disk
  out_fname = "T{}_{}_ML_{}.npy".format(basename[39:44], basename[11:26], "full" if full_array else "small")
  out_path = os.path.join(out_dir, out_fname)
  if verbose:
    print("\nWriting training set to disk ...")
  np.save(out_path, train_set)
  if verbose:
    print("Saved {}, {}, {:.1f} MB".format(out_path, " x ".join(str(x) for x in train_set.shape), train_set.nbytes/1024**2))

# ==============================================================================

if __name__ == "__main__":

  import sys

  if len(sys.argv) < 2:
    print("Pass path to Sentinel-2 L2A dataset as argument")
    sys.exit()

  generate_training_set(sys.argv[1], full_array=False)

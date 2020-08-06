# Computes a sargassum index (e.g. AFAI or ASI) from an L2A Sentinel-2 dataset

# =====================================================

import datetime
import glob
import os
import sys

import numpy as np
import rasterio

import Sentinel2
from AFAI import AFAI_Index
from ASI import ASI_Index

# ==============================================================================

def detect_sargassum(dataset_path, sarg_index, compute_kwargs={}, apply_mask=True, mask_keep_categs=[6], masked_value=np.nan, threshold=None, resolution="20", save_npy=False, save_geotiff=False, save_jp2=False, out_dir=None, verbose=True):
  """Computes a sargassum index from a Sentinel-2 dataset.

  Parameters:

    dataset_path : string
      The path to the .SAFE directory containing an L2A Sentinel-2 dataset.

    sarg_index : an instance of a class derived from Sargassum_Index
      The sargassum index to use for the detection.

  Options:

    compute_kwargs : dict (default: empty dict)
      A dictionary of additional parameters to be passed to sarg_index's
      compute().

    apply_mask : boolean (default: True)
      Whether to apply the Sentinel-2 SCL mask to the data, resulting in  masked pixels being marked as invalid values.

    mask_keep_categs : list or tuple (default: [6])
      The SCL categories to consider valid if apply_musk is True. Defaults to
      only WATER.

    masked_value : float or np.float (default: np.nan)
      The value to use to indicate masked pixels in the output image.

    threshold : numeric (default: None)
      If given, the image output by the Sargassum_Index will be thresholded
      using this value, with values below set to 0 and values above set to 1.
      Masked pixels will be set to 2 in this cases.

    resolution : numeric (default: 20)
      The Sentinel-2 spatial resolution to use. All channels required by the
      Sargassum_Index must be available at this resolution. Defaults to 20 m.

    save_npy : boolean (default: False)
      Whether to save the data in the output image as a numpy array.

    save_geotiff : boolean (default: False)
      Whether to save the output image in GeoTIFF format. Georeferecing data
      will be copied over from the Sentinel-2 metadata.

    save_jp2 : boolean (default: False)
      Whether to save the output image in OpenJPEG2000 format. Georeferecing
      data will be copied over from the Sentinel-2 metadata.

    out_dir : string (default: "./")
      The output directory where the results are to be saved. Defaults to the
      current directory.

    verbose : boolean (default: True)
      Whether to report actions to the screen.

  Returns:

    result : numpy array
      A numpy array of same shape as the channels with the result of the
      sargassum detection
  """
  # ----------------------------------------------------------------------------

  # Parse tile and date from dataset name

  basename = os.path.basename(os.path.normpath(dataset_path))
  if verbose:
    print("\nComputing sargassum index {} for Sentinel-2 dataset:\n{}".format(sarg_index.name, dataset_path))
  date = datetime.datetime.strptime(basename[11:26], "%Y%m%dT%H%M%S")
  tile = basename[39:44]
  satellite = basename[1:3]
  if verbose:
    print("UTM/MGRS Tile: {}".format(tile))
    print("Sensing Date: {} UTC".format(date.strftime("%Y-%m-%d %H:%M:%S")))
    print("Satellite: Sentinel-{}".format(satellite))

  # --------------------------------------------------
  # Load required channels at requested resolution

  img_data_path = Sentinel2.locate_data_path(dataset_path, resolution)

  if verbose:
    print("\nLoading channels {} ...".format(sarg_index.required_channels))

  dataset = Sentinel2.load_channels(dataset_path, sarg_index.required_channels, resolution, verbose=verbose)

  ch0 = dataset["channels"][sarg_index.required_channels[0]]
  NX, NY = ch0.shape
  NTOT = NX * NY
  img_meta = dataset["meta"]
  NCH = len(dataset)

  # --------------------------------------------------
  # Load SCL (if using mask)

  if verbose:
    print("\nLoading SCL mask ...")

  SCL = Sentinel2.load_SCL(dataset_path, resolution)
  SCL_mask = np.isin(SCL, mask_keep_categs)

  if verbose:

    mask_categs, counts = np.unique(SCL, return_counts=True)
    mask_counts = dict(zip(mask_categs, counts))
    print("Mask counts:", mask_counts)

    mask_keep_count = np.count_nonzero(SCL_mask)
    print("{:,} ({:.1f}%) pixels are unmasked".format(mask_keep_count, 100*mask_keep_count/SCL.size))

  # --------------------------------------------------
  # Compute index

  if verbose:
    print("\nComputing {} ...".format(sarg_index.name))

  result = sarg_index.compute(dataset["channels"], **compute_kwargs)

  # --------------------------------------------------
  # Apply threshold, if requested

  if threshold is not None:

    if verbose:
      print("\nApplying threshold of {} ...".format(threshold))

    result = np.where(result >= threshold, 1, 0).astype("uint8")

  # --------------------------------------------------
  # Apply mask, if requested

  if apply_mask:

    if verbose:
      print("\nApplying mask ...")

    if threshold is not None:
      result[~SCL_mask] = 2
    else:
      result[~SCL_mask] = masked_value

  # --------------------------------------------------
  # Save result to disk as a numpy array, if requested

  if save_npy:

    index_name = sarg_index.name.replace(" ", "_")
    fname = "{}_{}_{}.npy".format(tile, date.strftime("%Y%m%d"), index_name)

    if out_dir is None:
      out_dir = dataset_path
    out_path = os.path.join(out_dir, fname)

    np.save(out_path, result)

    if verbose:
      print("\nWrote {}".format(out_path))

  # --------------------------------------------------
  # Save result to disk as GeoTIFF, if requested

  if save_geotiff :

    # Copy image metadata from SCL mask
    img_meta['driver'] = "GTiff"
    img_meta['dtype'] = result.dtype
    img_meta['count'] = 1

    index_name = sarg_index.name.replace(" ", "_")
    fname = "{}_{}_{}.tif".format(tile, date.strftime("%Y%m%d"), index_name)

    if out_dir is None:
      out_dir = dataset_path
    out_path = os.path.join(out_dir, fname)

    with rasterio.open(out_path, "w", **img_meta) as fout:
      fout.write(result, 1)

    if verbose:
      print("\nWrote {}".format(out_path))

  # --------------------------------------------------
  # Save result to disk as JPEG2000, if requested

  if save_jp2 and result.dtype not in ["uint8"]:
    print("\nWarning: can't save float image as JPEG2000; skipping")
    save_jp2 = False

  if save_jp2:

    # Copy image metadata from SCL mask
    img_meta['driver'] = "JP2OpenJPEG"
    img_meta['dtype'] = result.dtype

    index_name = sarg_index.name.replace(" ", "_")
    fname = "{}_{}_{}.jp2".format(tile, date.strftime("%Y%m%d"), index_name)

    if out_dir is None:
      out_dir = dataset_path
    out_path = os.path.join(out_dir, fname)

    with rasterio.open(out_path, "w", **img_meta) as fout:
      fout.write(result, 1)

    if verbose:
      print("\nWrote {}".format(out_path))

  # --------------------------------------------------

  return result

# =====================================================

# Example: compute ASI on the dataset passed as command-line arg
if __name__ == "__main__":

  import sys

  dataset_path = sys.argv[1]

  # sarg_index = AFAI_Index()
  sarg_index = ASI_Index(model_path="ASImodelColabv2.h5")

  detect_sargassum(dataset_path, sarg_index, out_dir="./", apply_mask=False, mask_keep_categs=[6], save_npy=True, save_geotiff=True, save_jp2=False)

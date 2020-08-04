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

def detect_sargassum(dataset_path, index, apply_mask=True, mask_keep_categs=(6,10), masked_value=np.nan, threshold=None, resolution="20", save_npy=False, save_geotiff=False, save_jp2=False, outdir=None, verbose=True):
  """Computes a sargassum index from a Sentinel-2 dataset.



  Parameters:

    dataset_path : string
      The path to the .SAFE directory containing an L2A Sentinel-2 dataset

    index : an instance of the AFAIIndex or ASIIndex class

  """


  # --------------------------------------------------
  # Parse tile and date from dataset name

  basename = os.path.basename(os.path.normpath(dataset_path))
  if verbose:
    print("\nComputing sargassum index {} for Sentinel-2 dataset:\n{}".format(index.name, dataset_path))
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
    print("\nLoading channels {} ...".format(index.required_channels))

  dataset = Sentinel2.load_channels(dataset_path, index.required_channels, resolution, verbose=verbose)

  ch0 = dataset["channels"][index.required_channels[0]]
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
    print("\nComputing {} ...".format(index.name))

  result = index.compute(dataset["channels"])

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

    index_name = index.name.replace(" ", "_")
    fname = "{}_{}_{}.npy".format(tile, date.strftime("%Y%m%d"), index_name)

    if outdir is None:
      outdir = dataset_path
    out_path = os.path.join(outdir, fname)

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

    index_name = index.name.replace(" ", "_")
    fname = "{}_{}_{}.tif".format(tile, date.strftime("%Y%m%d"), index_name)

    if outdir is None:
      outdir = dataset_path
    out_path = os.path.join(outdir, fname)

    with rasterio.open(out_path, "w", **img_meta) as fout:
      fout.write(result, 1)

    if verbose:
      print("\nWrote {}".format(out_path))

  # --------------------------------------------------
  # Save result to disk as JPEG2000, if requested

  if save_jp2 and result.dtype not in ["utin8"]:
    print("\nWarning: can't save float image as JPEG2000; skipping")
    save_jp2 = False

  if save_jp2:

    # Copy image metadata from SCL mask
    img_meta['driver'] = "JP2OpenJPEG"
    img_meta['dtype'] = result.dtype

    index_name = index.name.replace(" ", "_")
    fname = "{}_{}_{}.jp2".format(tile, date.strftime("%Y%m%d"), index_name)

    if outdir is None:
      outdir = dataset_path
    out_path = os.path.join(outdir, fname)

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

  # index = AFAI_Index()
  index = ASI_Index(model_path="ASImodelColabv2.h5", batch_size=2048)

  detect_sargassum(sys.argv[1], index, outdir="./", apply_mask=False, mask_keep_categs=[6], save_npy=True, save_geotiff=True, save_jp2=False)

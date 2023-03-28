# SynthSeg
Containerized implementation of SynthSeg with additional preprocessing options

```
usage: synthseg brain segmentation --input INPUT --output OUTPUT [-h]
                                   [--mask MASK] [--mask-pad MASK_PAD]
                                   [--parc] [--robust] [--vol] [--qc] [--post]
                                   [--crop CROP [CROP ...]]

Wrapper for brain segmentation using synthseg. By default, synthseg input
images are resampled to 1mm and cropped to 192 mm^3 about the center of the
image. In this container, the input image is automatically resampled to 1mm
isotropic resolution with b-spline interpolation. The user can provide a brain
mask, the image is then cropped and resampled about this mask, which should
ensure that the synthseg region of interest contains the brain. The crop
region is large enough to fit adult brains without running out of memory on
the GPU. Output is also simplified, the user only needs to specify a prefix
with --output. Optional outputs are written to the same prefix with the
appropriate suffixes.

Required arguments:
  --input INPUT         Input structural image (default: None)
  --output OUTPUT       Output prefix (default: None)

Optional arguments:
  -h, --help            show this help message and exit
  --mask MASK           Brain mask about which to crop the input image
                        (default: None)
  --mask-pad MASK_PAD   Padding around brain mask, in voxels (default: 32)

SynthSeg arguments:
  --parc                Do cortical parcellation (default: False)
  --robust              Use robust fitting for low-resolution or other
                        challenging data (default: False)
  --vol                 Output a CSV file containing label volumes (default:
                        False)
  --qc                  Output a CSV file containing QC measures (default:
                        False)
  --post                Output a multi-component image containing label
                        posterior probabilities (default: False)
  --crop CROP [CROP ...]
                        Crop parameters, must be multiples of 32. (default:
                        [224, 256, 192])
```

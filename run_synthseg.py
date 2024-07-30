#!/usr/bin/env python

import argparse
import numpy as np
import os
import shutil
import SimpleITK as sitk
import subprocess

class RawDefaultsHelpFormatter(
    argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    pass

parser = argparse.ArgumentParser(formatter_class=RawDefaultsHelpFormatter,
                                 prog="synthseg brain segmentation", add_help = False, description='''
Wrapper for brain segmentation using synthseg.

By default, synthseg input images are resampled to 1mm and cropped to 192 mm^3 about the center of
the image.

In this container, the input image is automatically resampled to 1mm isotropic resolution with
b-spline interpolation.

It is recommended that the user provide a brain mask, in which case the image is cropped and
resampled about the mask bounding box. This should ensure that the synthseg region of interest
contains the brain. The default crop region is large enough to fit most adult brains without running
out of memory on the FTDC GPU (11 Gb capacity).

If the brain mask is larger than the specified crop parameters, the crop is enlarged and synthseg is
switched to CPU mode.

A brain mask can be computed quickly and robustly with SynthStrip.

For output, specify a prefix with --output. Optional outputs are written to the same prefix with the
appropriate suffixes, explained below.

Output suffixes:

  SynthSegInput.nii.gz - The resampled image used as input for SynthSeg. If a brain mask is used,
  this image will also be cropped to the bounding box of the mask plus a constant padding, before
  running SynthSeg. Otherwise, the original image is resampled to 1mm resolution.

  SynthSeg.nii.gz - The SynthSeg output label image. This is in the same space as the SynthSegInput
  image.

Optional output suffixes:

  PosteriorsOrig.nii.gz - Posterior probabilites for each label, resampled to the original space of
  the input structural image.

  Posteriors.nii.gz - Posterior probabilities for each label, in space of the 1mm isotropic
  SynthSegInput image.

  QC.csv - QC metrics produced by SynthSeg.

  SynthSegOrig.nii.gz - The SynthSeg output label image, resampled to the original space of
  the input structural image.

  Volumes.csv - Label volumes computed by SynthSeg in the SynthSegInput space.

''')

required = parser.add_argument_group('Required arguments')
required.add_argument('--input', help='Input structural image', type=str, required=True)
required.add_argument('--output', help='Output prefix', type=str, required=True)
optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h', '--help', action='help', help='show this help message and exit')
optional.add_argument('--mask', help='Brain mask about which to crop the input image', type=str)
optional.add_argument('--mask-pad', help='Padding around brain mask, in voxels', type=int, default = 32)
optional.add_argument('--resample-orig', action='store_true', help='Resample the output images to the original space. '
                      'This is a post-processing step, all QC / volume measures are computed in the 1mm space.')
synthseg = parser.add_argument_group('SynthSeg arguments')
synthseg.add_argument('--cpu', action='store_true', help='Use CPU instead of GPU, even if GPU is available')
synthseg.add_argument('--crop', help='Crop parameters, must be multiples of 32. If increasing beyond the default, '
                      'you may need to add --cpu to avoid running out of memory', nargs='+', type=int,
                      default = [192, 256, 192])
synthseg.add_argument('--post', action='store_true', help='Output a multi-component image containing label posterior '
                      'probabilities')
synthseg.add_argument('--parc', action='store_true', help='Do cortical parcellation')
optional.add_argument('--antsct', action='store_true', help='Output results in antsct format (implies --resample-orig '
                      'and --post)')
synthseg.add_argument('--qc', action='store_true', help='Output a CSV file containing QC measures')
synthseg.add_argument('--robust', action='store_true', help='Use robust fitting for low-resolution or other challenging data')
synthseg.add_argument('--vol', action='store_true', help='Output a CSV file containing label volumes')

args = parser.parse_args()

# These control multi-threading for basic operations, set to 1 because they don't take much time
# You can separately control tensorflow threads in the call to synthseg, but this might increase the
# already substantial memory requirements, so that's not currently an option
os.environ['OMP_NUM_THREADS'] = "1"
os.environ['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS'] = "1"

use_cpu = args.cpu

input_t1w = os.path.realpath(args.input)
output_prefix = os.path.realpath(args.output)

output_dir = os.path.dirname(output_prefix)

if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

output_file_prefix = os.path.basename(output_prefix)

# Crop input data if applicable
synthseg_input = output_prefix + "SynthSegInput.nii.gz"

crop_params = args.crop

if (args.mask is not None and os.path.isfile(args.mask)):
    print(f"Cropping input image around mask", flush=True)
    subprocess.run(['ExtractRegionFromImageByMask', '3', input_t1w, synthseg_input, args.mask, str(1), str(args.mask_pad)])

    # Check if mask fits inside crop area
    mask_image = sitk.ReadImage(args.mask)
    label_shape = sitk.LabelShapeStatisticsImageFilter()
    label_shape.Execute(sitk.Cast(mask_image, sitk.sitkUInt8))
    # bb = [ xMin, yMin, zMin, xSize, ySize, zSize ]
    bb_vox = label_shape.GetBoundingBox(1)

    bb_min_vox = bb_vox[0:3]
    bb_max_vox = tuple([int(b) for b in np.add(bb_vox[0:3], bb_vox[3:6])])

    bb_min_mm = mask_image.TransformIndexToPhysicalPoint(bb_min_vox)
    bb_max_mm = mask_image.TransformIndexToPhysicalPoint(bb_max_vox)

    # The length of the sides of the bounding box in physical coordinates
    # ITK uses LPS but lengths of the BB are the same as NIFTI RAS
    bb_extent_ras = np.round(np.abs(np.subtract(bb_max_mm, bb_min_mm)))

    for idx in range(0,3):
        if bb_extent_ras[idx] > args.crop[idx]:
            print("WARNING: brain mask extent is larger than cropped region for synthseg, " +
                "using CPU to avoid running out of memory", flush=True)
            # Crop must be a multiple of 32
            crop_params[idx] = crop_params[idx] + 32
            use_cpu = True

else:
    shutil.copyfile(input_t1w, synthseg_input)

# Resample to 1mm
subprocess.run(['ResampleImage', '3', synthseg_input, synthseg_input, '1x1x1', '0', '4'])

print(f"Input image: {input_t1w} resampled to {synthseg_input}")

output_seg = output_prefix + 'SynthSeg.nii.gz'

synthseg_args = ['--i', synthseg_input, '--o', output_seg, '--crop'] + [str(c) for c in crop_params]

# Set up synthseg options
if (args.post):
    post_output_file = output_prefix + 'Posteriors.nii.gz'
    synthseg_args = synthseg_args + ['--post', post_output_file]
if (args.qc):
    qc_output_file = output_prefix + 'QC.csv'
    synthseg_args = synthseg_args + ['--qc', qc_output_file]
if (args.vol):
    vol_output_file = output_prefix + 'Volumes.csv'
    synthseg_args = synthseg_args + ['--vol', vol_output_file]
if (args.parc):
    synthseg_args = synthseg_args + ['--parc']
if (args.robust):
    synthseg_args = synthseg_args + ['--robust']
if (use_cpu):
    synthseg_args = synthseg_args + ['--cpu']

# Now call synthseg
print(f"Running synthseg on {synthseg_input}", flush=True)
print(f"synthseg args: {synthseg_args}", flush=True)
subprocess.run(['python', '/opt/SynthSeg/scripts/commands/SynthSeg_predict.py'] + synthseg_args)

if args.resample_orig or args.antsct:
    print("Resampling output to input orig space")
    subprocess.run(['antsApplyTransforms', '-d', '3', '-i', output_seg, '-o',
                    output_prefix + 'SynthSegOrig.nii.gz', '-t', 'Identity', '-r', input_t1w, '-n',
                    'GenericLabel', '--verbose'])
    if args.post or args.antsct:
        subprocess.run(['antsApplyTransforms', '-d', '3', '-e', '3', '-i', post_output_file, '-o',
                        output_prefix + 'PosteriorsOrig.nii.gz', '-t', 'Identity', '-r', input_t1w, '--verbose'])
    if args.parc:
        subprocess.run(['antsApplyTransforms', '-d', '3', '-i', output_prefix + 'CorticalParcellation.nii.gz', '-o',
                        output_prefix + 'CorticalParcellationOrig.nii.gz', '-t', 'Identity', '-r', input_t1w, '-n',
                        'GenericLabel', '--verbose'])

    # If requested, output in antsct format
    if args.antsct:
        print("Outputting in antsct format")
        synthseg_labels = sitk.ReadImage(output_prefix + 'SynthSegOrig.nii.gz')

        # Convert to antsct labels
        label_to_ants = {
            0: 0,  # background
            2: 3,  # left_cerebral_white_matter
            3: 2,  # left_cerebral_cortex
            4: 1,  # left_lateral_ventricle
            5: 1,  # left_inferior_lateral_ventricle
            7: 6,  # left_cerebellum_white_matter
            8: 6,  # left_cerebellum_cortex
            10: 4,  # left_thalamus
            11: 4,  # left_caudate
            12: 4,  # left_putamen
            13: 4,  # left_pallidum
            14: 1,  # 3rd_ventricle
            15: 1,  # 4th_ventricle
            16: 5,  # brain-stem
            17: 4,  # left_hippocampus
            18: 4,  # left_amygdala
            24: 1,  # CSF
            26: 4,  # left_accumbens_area
            28: 4,  # left_ventral_DC
            41: 3,  # right_cerebral_white_matter
            42: 2,  # right_cerebral_cortex
            43: 1,  # right_lateral_ventricle
            44: 1,  # right_inferior_lateral_ventricle
            46: 6,  # right_cerebellum_white_matter
            47: 6,  # right_cerebellum_cortex
            49: 4,  # right_thalamus
            50: 4,  # right_caudate
            51: 4,  # right_putamen
            52: 4,  # right_pallidum
            53: 4,  # right_hippocampus
            54: 4,  # right_amygdala
            58: 4,  # right_accumbens_area
            60: 4   # right_ventral_DC
        }

        synthseg_array = sitk.GetArrayFromImage(synthseg_labels)

        output_array = np.zeros_like(synthseg_array)

        for label, ants_label in label_to_ants.items():
            output_array[synthseg_array == label] = ants_label

        output_image = sitk.GetImageFromArray(output_array)
        output_image.SetOrigin(synthseg_labels.GetOrigin())
        output_image.SetSpacing(synthseg_labels.GetSpacing())
        output_image.SetDirection(synthseg_labels.GetDirection())

        sitk.WriteImage(output_image, output_prefix + 'SynthSegToAntsCT.nii.gz')

        prob_image = sitk.ReadImage(output_prefix + 'PosteriorsOrig.nii.gz')

        # Get the numpy array from the probability image
        prob_array = sitk.GetArrayFromImage(prob_image)

        # Initialize a list of arrays for category probabilities, for ants posteriors
        ants_probs = [np.zeros(prob_array.shape[1:], dtype=prob_array.dtype) for _ in range(6)]

        # Sum of probabilities for all categories, use this to label
        sum_probs = np.zeros(prob_array.shape[1:], dtype=prob_array.dtype)

        # Iterate over the labels and add probabilities to the corresponding ants categories
        for idx, label in enumerate(label_to_ants.keys()):
            if (label == 0):
                continue
            category = label_to_ants[label]
            ants_probs[category - 1] += prob_array[idx]

        for i, category_prob in enumerate(ants_probs):
            ants_posterior = sitk.GetImageFromArray(category_prob)
            # Use 3D synthseg_labels for header info
            ants_posterior.SetOrigin(synthseg_labels.GetOrigin())
            ants_posterior.SetSpacing(synthseg_labels.GetSpacing())
            ants_posterior.SetDirection(synthseg_labels.GetDirection())
            sitk.WriteImage(ants_posterior, output_prefix + 'AntsctPosteriors' + str(i + 1) + '.nii.gz')




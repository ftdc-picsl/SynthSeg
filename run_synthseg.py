#!/usr/bin/env python

import argparse
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                 prog="synthseg brain segmentation", add_help = False, description='''
Wrapper for brain segmentation using synthseg.

By default, synthseg input images are resampled to 1mm and cropped to 192 mm^3 about the center of
the image.

In this container, the input image is automatically resampled to 1mm isotropic resolution with
b-spline interpolation. The user can provide a brain mask, the image is then cropped and resampled
about this mask, which should ensure that the synthseg region of interest contains the brain. The
crop region is large enough to fit adult brains without running out of memory on the GPU.

Output is also simplified, the user only needs to specify a prefix with --output. Optional outputs are
written to the same prefix with the appropriate suffixes.

''')

required = parser.add_argument_group('Required arguments')
required.add_argument("--input", help="Input structural image", type=str, required=True)
required.add_argument("--output", help="Output prefix", type=str, required=True)
optional = parser.add_argument_group('Optional arguments')
optional.add_argument("-h", "--help", action="help", help="show this help message and exit")
optional.add_argument("--mask", help="Brain mask about which to crop the input image", type=str)
optional.add_argument("--mask-pad", help="Padding around brain mask, in voxels", type=int, default = 32)

synthseg = parser.add_argument_group('SynthSeg arguments')
synthseg.add_argument("--parc", action='store_true', help="Do cortical parcellation")
synthseg.add_argument("--robust", action='store_true', help="Use robust fitting for low-resolution or other challenging data")
synthseg.add_argument("--vol", action='store_true', help="Output a CSV file containing label volumes")
synthseg.add_argument("--qc", action='store_true', help="Output a CSV file containing QC measures")
synthseg.add_argument("--post", action='store_true', help="Output a multi-component image containing label posterior probabilities")
synthseg.add_argument("--crop", help="Crop parameters, must be multiples of 32.", nargs='+', type=int, default = [224, 256, 192])

args = parser.parse_args()

input_t1w = os.path.realpath(args.input)
output_prefix = os.path.realpath(args.output)

output_dir = os.path.dirname(output_prefix)

if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

output_file_prefix = os.path.basename(output_prefix)

# Crop input data if applicable
synthseg_input = output_prefix + "SynthSegInput.nii.gz"

if (args.mask is not None and os.path.isfile(args.mask)):
    print(f"Cropping input image around mask", flush=True)
    subprocess.run(['ExtractRegionFromImageByMask', '3', input_t1w, synthseg_input, args.mask, str(1), str(args.mask_pad)])
else:
    shutil.copyfile(input_t1w, synthseg_input)

# Resample to 1mm
subprocess.run(['ResampleImage', '3', synthseg_input, synthseg_input, '1x1x1', '0', '4'])

print(f"Input image: {input_t1w} resampled to {synthseg_input}")

synthseg_args = ['--i', synthseg_input, '--o', output_prefix + 'SynthSeg.nii.gz', '--crop'] + [str(c) for c in args.crop]

# Set up synthseg options
if (args.post):
    post_output_file = output_prefix + 'posteriors.nii.gz'
    synthseg_args = synthseg_args + ['--post', post_output_file]
if (args.qc):
    qc_output_file = output_prefix + 'QC.csv'
    synthseg_args = synthseg_args + ['--qc', qc_output_file]
if (args.vol):
    vol_output_file = output_prefix + 'Volumes.csv'
    synthseg_args = synthseg_args + ['--vol', vol_output_file]
if (args.parc):
    synthseg_args = synthseg_args + '--parc'
if (args.robust):
    synthseg_args = synthseg_args + '--robust'


# Now call synthseg
print(f"Running synthseg on {synthseg_input}", flush=True)
print(f"synthseg args: {synthseg_args}", flush=True)
subprocess.run(['python', '/opt/SynthSeg/scripts/commands/SynthSeg_predict.py'] + synthseg_args)


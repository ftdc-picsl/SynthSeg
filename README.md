# SynthSeg
Containerized implementation of SynthSeg with additional preprocessing options

Containers are [available on DockerHub](https://hub.docker.com/repository/docker/cookpa/synthseg-mask/general)


## Base image

https://github.com/cookpa/SynthSegContainer - go here if you want to build SynthSeg that just runs the built-in prediction script.


## Licensing and citations

This container uses SynthSeg, please see its license and cite the appropriate papers.

[SynthSeg license](https://github.com/BBillot/SynthSeg/blob/master/LICENSE.txt).

The authors ask that if it is used in published research, to cite:

SynthSeg: Domain Randomisation for Segmentation of Brain MRI Scans of any
Contrast and Resolution
B. Billot, D.N. Greve, O. Puonti, A. Thielscher, K. Van Leemput, B. Fischl, A.V.
Dalca, J.E. Iglesias (https://pubmed.ncbi.nlm.nih.gov/36857946/)

For cortical parcellation, automated QC, or robust fitting, please also cite the following
paper:

Robust Segmentation of Brain MRI in the Wild with Hierarchical CNNs and no Retraining
B. Billot, M. Colin, S.E. Arnold, S. Das, J.E. Iglesias [MICCAI
2022](https://link.springer.com/chapter/10.1007/978-3-031-16443-9_52)



FROM cookpa/synthseg:conda-0.1

# Copy all of ANTs. Can reduce container later by building a static ANTs and only copying programs
# we need
COPY --from=antsx/ants:v2.4.3 /opt/ants /opt/ants

ARG DOCKER_IMAGE_TAG="unknown"
ARG DOCKER_IMAGE_VERSION="unknown"

ARG GIT_REMOTE="unknown"
ARG GIT_COMMIT="unknown"

# Base image includes sh, venv activation does not support that shell
# Can't use dash because recognition of that depends on ps, which isn't installed in base image
RUN rm /bin/sh && \
    cd /bin && \
    ln -s bash sh

RUN . ${VIRTUAL_ENV}/bin/activate && \
    pip install simpleitk==2.2.1

COPY run_synthseg.py /opt/run_synthseg.py

ENV LD_LIBRARY_PATH=/opt/ants/lib:$LD_LIBRARY_PATH
ENV ANTSPATH=/opt/ants/bin/
ENV PATH=/opt/ants/bin:$PATH

LABEL maintainer="Philip A Cook (https://github.com/cookpa)" \
      description="Container for SynthSeg, with custom resampling to center input image on mask. \
      Please see SynthSeg repository for citations." \
      synthseg_repo="https://github.com/BBillot/SynthSeg"

LABEL git.remote=$GIT_REMOTE
LABEL git.commit=$GIT_COMMIT

ENV GIT_REMOTE=$GIT_REMOTE
ENV GIT_COMMIT=$GIT_COMMIT
ENV DOCKER_IMAGE_TAG=$DOCKER_IMAGE_TAG
ENV DOCKER_IMAGE_VERSION=$DOCKER_IMAGE_VERSION


ENTRYPOINT ["python", "/opt/run_synthseg.py"]

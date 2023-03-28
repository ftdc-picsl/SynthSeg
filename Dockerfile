FROM cookpa/synthseg:conda-0.1

# Copy all of ANTs. Can reduce container later by building a static ANTs and only copying programs
# we need
COPY --from=antsx/ants:v2.4.3 /opt/ants /opt/ants

COPY run_synthseg.py /opt/run_synthseg.py

ENV LD_LIBRARY_PATH=/opt/ants/lib:$LD_LIBRARY_PATH
ENV ANTSPATH=/opt/ants/bin/
ENV PATH=/opt/ants/bin:$PATH

LABEL maintainer="Philip A Cook (https://github.com/cookpa)" \
      description="Container for SynthSeg, with custom resampling to center input image on mask. \
      Please see SynthSeg repository for citations." \
      synthseg_repo="https://github.com/BBillot/SynthSeg"

ENTRYPOINT ["python", "/opt/run_synthseg.py"]

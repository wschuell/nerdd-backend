FROM mambaorg/micromamba:2.0.5-alpine3.20

# necessary to display the image on Github
LABEL org.opencontainers.image.source="https://github.com/shirte/nerdd"

# Necessary, so Docker doesn't buffer the output and that we can see the output 
# of the application in real-time.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# create the conda environment
# --mount=type=cache,target=/home/mambauser/.mamba/pkgs: create a cache directory for conda, so that
#     it doesn't have to download the dependencies every time we build the image
# micromamba clean: remove the cache and the tarballs of the packages
COPY environment.yml .
RUN --mount=type=cache,target=/home/mambauser/.mamba/pkgs \
    micromamba env create -f environment.yml && \
    micromamba clean --all --yes

COPY . .

# --mount=type=cache,target=/root/.cache/pip: create a cache directory for pip, so that
# it doesn't have to download the dependencies every time we build the image
RUN --mount=type=cache,target=/root/.cache/pip \
    micromamba run -n nerdd_backend pip install .

ENTRYPOINT micromamba run -n nerdd_backend \
    python -m nerdd_backend.main --config-name production \
    ++db.host=$RETHINK_DB_HOST ++db.port=$RETHINK_DB_PORT ++channel.broker_url=$KAFKA_BROKER_URL

FROM mambaorg/micromamba:2.0.5

# necessary to display the image on Github
LABEL org.opencontainers.image.source="https://github.com/molinfo-vienna/nerdd-backend"

# Necessary, so Docker doesn't buffer the output and that we can see the output 
# of the application in real-time.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# create the conda environment
# --mount=type=cache,target=/home/mambauser/.mamba/pkgs: create a cache directory for conda, so that
#     it doesn't have to download the dependencies every time we build the image
# micromamba clean: remove the cache and the tarballs of the packages
COPY environment.yml requirements.txt ./
RUN --mount=type=cache,target=/home/mambauser/.mamba/pkgs \
    micromamba env create -f environment.yml && \
    micromamba clean --all --yes

# --mount=type=cache,target=/root/.cache/pip: create a cache directory for pip, so that
# it doesn't have to download the dependencies every time we build the image
RUN --mount=type=cache,target=/root/.cache/pip \
    micromamba run -n nerdd_backend pip install -r requirements.txt

COPY . .
RUN micromamba run -n nerdd_backend pip install --no-deps .

ENTRYPOINT micromamba run -n nerdd_backend \
    python -m nerdd_backend.main --config-name production \
    ++db.host=$RETHINK_DB_HOST ++db.port=$RETHINK_DB_PORT ++channel.broker_url=$KAFKA_BROKER_URL

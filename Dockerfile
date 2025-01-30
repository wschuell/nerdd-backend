FROM mambaorg/micromamba:2.0.5-alpine3.20

# necessary to display the image on Github
LABEL org.opencontainers.image.source="https://github.com/shirte/nerdd"

USER root

# rdkit requires libxrender, libxext-dev, libxau and g++
RUN apk update && apk add libxrender libxext-dev libxau g++

# Necessary, so Docker doesn't buffer the output and that we can see the output 
# of the application in real-time.
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# create the conda environment
COPY environment.yml .
RUN micromamba env create -f environment.yml

COPY . .

# --mount=type=cache,target=/root/.cache/pip: create a cache directory for pip, so that
# it doesn't have to download the dependencies every time we build the image
RUN --mount=type=cache,target=/root/.cache/pip \
    micromamba run -n nerdd_backend pip install .

# --no-capture-output: output of the application is not buffered and we can see it 
# Note: PYTHONUNBUFFERED is not enough, because it only affects the Python
# standard output, not the output of the application.
ENTRYPOINT micromamba run -n nerdd_backend \
    python -m nerdd_backend.main --config-name production \
    ++db.host=$RETHINK_DB_HOST ++db.port=$RETHINK_DB_PORT ++channel.broker_url=$KAFKA_BROKER_URL

# Nerdd Backend


## Architecture

* A FastAPI **lifespan** is a separate process that runs in parallel while serving HTTP
  requests. We use them to read and process messages from Kafka.

## Contribute

```sh
# create conda environment
conda env create -f environment.yml

# install package in development mode
pip install -e .[test]

# run with a toy communication channel, database backend and a basic computational module (quickstart)
python -m nerdd_backend.main --config-name development

# turn off fake data
python -m nerdd_backend.main --config-name development ++mock_infra=false

# set storage directory
python -m nerdd_backend.main --config-name development ++media_root=./data

# run on existing kafka cluster as communication channel and rethinkdb database backend
# (see all options in config files in settings folder)
python -m nerdd_backend.main --config-name production \
  ++db.host=localhost ++db.port=31562 \
  ++channel.broker=localhost:31624

# use localhost:8000 for api requests
# (see all endpoints on http://localhost:8000/docs)
curl localhost:8000/modules
```
# Nerdd Backend


## Architecture

* A FastAPI **lifespan** is a separate process that runs in parallel while serving HTTP
  requests. We use them to read and process messages from Kafka.
import os

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL") or "my-cluster-kafka-bootstrap.kafka:9092"

RETHINKDB_HOST = os.environ.get("RETHINKDB_HOST") or "rethinkdb-service.default"
RETHINKDB_PORT = os.environ.get("RETHINKDB_PORT") or 28015
RETHINKDB_DB = os.environ.get("RETHINKDB_DB") or "nerdd"

PAGE_SIZE = 5

__all__ = ["RecordNotFoundError", "RecordAlreadyExistsError"]


class RecordNotFoundError(Exception):
    """Exception raised when a database record is not found."""

    def __init__(self, ModelClass, record_id):
        super().__init__(f"{ModelClass.__name__} with id {record_id} not found")


class RecordAlreadyExistsError(Exception):
    """Exception raised when a database record already exists."""

    def __init__(self, ModelClass, record_id):
        super().__init__(f"{ModelClass.__name__} with id {record_id} already exists")

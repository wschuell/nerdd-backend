from typing import Any, Optional

from nerdd_module.config import Module as NerddModule
from pydantic import model_validator

__all__ = ["Module"]


class Module(NerddModule):
    id: Optional[str] = None

    @model_validator(mode="after")
    @classmethod
    def validate_model(cls, values: Any) -> Any:
        assert isinstance(values, Module)

        module = super().validate_model(values)

        # TODO: incorporate versioning
        # compute the primary key from name and version
        # if "version" in module.keys():
        #     version = module["version"]
        # else:
        #     version = "1.0.0"
        # name = module["name"]
        module.id = module.name

        return module

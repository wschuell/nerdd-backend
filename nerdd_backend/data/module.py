from typing import Any

from nerdd_module.config import Module as NerddModule
from pydantic import computed_field, model_validator

__all__ = ["Module"]


class Module(NerddModule):
    @computed_field
    @property
    def id(self) -> str:
        # TODO: incorporate versioning
        # compute the primary key from name and version
        # if "version" in module.keys():
        #     version = module["version"]
        # else:
        #     version = "1.0.0"
        # name = module["name"]
        return self.name

from typing import Optional

from nerdd_module.config import Module as NerddModule
from pydantic import BaseModel, computed_field

__all__ = ["Module", "ModulePublic", "ModuleShort"]


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


class ModulePublic(Module):
    module_url: str


class ModuleShort(BaseModel):
    id: str
    rank: Optional[int] = None
    name: Optional[str] = None
    version: Optional[str] = None
    visible_name: Optional[str] = None
    logo: Optional[str] = None
    logo_title: Optional[str] = None
    logo_caption: Optional[str] = None
    module_url: str

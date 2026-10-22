"""Mongo boundary models for new durable records; public IDs are UUID strings."""
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
    id: PyObjectId = Field(alias='_id')

    @classmethod
    def from_mongo(cls, doc):
        return cls.model_validate(doc)

    def to_mongo(self):
        return self.model_dump(by_alias=True, exclude_none=True)

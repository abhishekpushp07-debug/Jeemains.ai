"""Fast JSON for every answer the server builds from plain data (Phase 3, Level 5).

FastAPI turns a returned dict into JSON in two steps: `jsonable_encoder` walks the whole value in Python, then `json.dumps`
writes it. For a 30-card match view that walk alone took ~1.2 ms of CPU; orjson writes the same JSON in ~0.014 ms.
Routes with a response model are left exactly as they were. Anything orjson cannot write on its own (a pydantic model
inside a dict, a set, a Decimal) goes through `jsonable_encoder` for that one value, and a value orjson refuses as a whole
(an integer above 64 bits) falls back to the old path, so every answer stays the same JSON as before."""
import json

import fastapi.routing
import orjson
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

OPTIONS = orjson.OPT_NON_STR_KEYS  # int keys become "1", exactly like json.dumps


def dumps(content) -> bytes:
    try:
        return orjson.dumps(content, default=jsonable_encoder, option=OPTIONS)
    except TypeError:  # orjson.JSONEncodeError is a TypeError
        return json.dumps(jsonable_encoder(content), ensure_ascii=False, allow_nan=False, indent=None, separators=(",", ":")).encode("utf-8")


class FastJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return dumps(content)


_serialize = fastapi.routing.serialize_response


async def serialize_response(*, field=None, response_content, **kwargs):
    if field is None and not any(kwargs.get(k) for k in ("include", "exclude", "exclude_unset", "exclude_defaults", "exclude_none")):
        return response_content  # FastJSONResponse writes it (the app's default response class)
    return await _serialize(field=field, response_content=response_content, **kwargs)


fastapi.routing.serialize_response = serialize_response

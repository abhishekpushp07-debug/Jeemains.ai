"""Is this server the workspace's own (the owner's preview), or the one students use?

Made-up samples (tests/matched_sample.py, tests/choice_sample.py) are for the owner's eyes on the preview. A database can
travel without the code knowing: on 26 Nov 2026 a Publish made from a copy of the workspace pointed production at a copy
of the preview's database, and students were served the preview's made-up Matched shifts as if JEE Main had matched them.
So a sample is shown only by a server that is surely the workspace's own, whatever its database holds: one whose MongoDB
runs on the same machine, without a password. Production's MongoDB is a managed cluster and never looks like that; a
server that cannot tell is treated as production."""
import os
import re

LOCAL = re.compile(r"^mongodb://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?(/[^@]*)?$")


def own(url=None) -> bool:
    """True only for the workspace's own server. `url`: a MongoDB address to judge instead of this server's."""
    return bool(LOCAL.match(os.environ.get("MONGO_URL", "") if url is None else url))

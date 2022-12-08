"""JSON UUID encoder"""

import json
from typing import Any
from uuid import UUID


class UUIDEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, UUID):
            return o.hex
        return json.JSONEncoder.default(self, o)

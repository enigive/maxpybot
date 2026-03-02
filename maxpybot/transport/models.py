from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class RequestOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    path: str
    params: Optional[Dict[str, str]] = None
    authorized: bool = True

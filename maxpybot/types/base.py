from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class MaxBaseModel(BaseModel):
    """Base public model with forward-compatible extra fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    raw_payload: Optional[Dict[str, Any]] = None

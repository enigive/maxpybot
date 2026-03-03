from typing import Any, Dict, Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from ..api_client import MaxBot


class MaxBaseModel(BaseModel):
    """Base public model with forward-compatible extra fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    raw_payload: Optional[Dict[str, Any]] = None
    _bot: Optional["MaxBot"] = PrivateAttr(default=None)

    @property
    def bot(self) -> Optional["MaxBot"]:
        return self._bot

    @bot.setter
    def bot(self, value: Optional["MaxBot"]) -> None:
        self._bot = value

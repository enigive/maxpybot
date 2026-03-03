from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from ..fsm.storage import BaseStorage
from ..fsm import FSMContext

if TYPE_CHECKING:
    from .router import Router


@dataclass
class HandlerContext:
    update: Any
    router: "Router"
    storage: Optional[BaseStorage]
    fsm: Optional[FSMContext]
    state: Optional[str]

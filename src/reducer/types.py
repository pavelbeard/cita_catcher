from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ActionType:
    type: Dict[str, Any]
    payload: Any

class Store(dict):
    def state(self):
        return self["state"]()
    
    def dispatch(self, action: ActionType):
        return self["dispatch"](action)
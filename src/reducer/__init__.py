from typing import Any, Callable

from reducer.types import ActionType, Store


def create_store(reducer: Callable[[Any, dict], Any], init_arg: Any) -> Store:
    if not hasattr(reducer, "__call__"):
        raise TypeError("Reducer must be a function")

    current_reducer = [reducer]
    current_state = [init_arg]

    is_dispatching = [False]

    def dispatch(action: ActionType):
        if not isinstance(action, ActionType):
            raise TypeError("Action must be of type ActionType")

        try:
            is_dispatching[0] = True
            current_state[0] = current_reducer[0](current_state[0], action)
        finally:
            is_dispatching[0] = False

        return current_state[0]

    def get_state():
        return current_state[0]

    return Store(state=get_state, dispatch=dispatch)

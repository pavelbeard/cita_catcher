from citabot_actions.reducer_types import IntervalAction, ProvinceAction
from reducer import ActionType


def interval_reducer(state, action: ActionType):
    if action.type == IntervalAction.CHANGE_INTERVAL:
        return action.payload
    elif action.type == IntervalAction.SET_INTERVAL:
        return action.payload
    elif action.type == IntervalAction.ADD_TIME:
        return state + action.payload


def province_reducer(state: set, action: ActionType):
    if action.type == ProvinceAction.ADD_PROVINCE:
        return state | {action.payload}
    elif action.type == ProvinceAction.REMOVE_PROVINCE:
        try:
            return state - {action.payload}
        except KeyError:
            return state

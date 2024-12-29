from enum import Enum


class IntervalAction(str, Enum):
    CHANGE_INTERVAL = "CHANGE_INTERVAL"
    SET_INTERVAL = "SET_INTERVAL"
    ADD_TIME = "ADD_TIME"

class ProvinceAction(str, Enum):
    ADD_PROVINCE = "ADD_PROVINCE"
    REMOVE_PROVINCE = "REMOVE_PROVINCE"
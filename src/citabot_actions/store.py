from citabot_actions.reducer import interval_reducer, province_reducer
from citabot_utils.types import Intervals
from reducer import create_store


interval_store = create_store(interval_reducer, init_arg=Intervals.I_1M.value)
province_store = create_store(province_reducer, init_arg=set())
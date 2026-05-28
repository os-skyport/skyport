from schedulers.fcfs import FCFSScheduler
from schedulers.fixed_priority import FixedPriorityScheduler
from schedulers.multilevel import HybridMLQScheduler
from schedulers.np_sjf import NonPreemptiveSJFScheduler

SCHEDULERS = {
    "fcfs": FCFSScheduler,
    "priority": FixedPriorityScheduler,
    "sjf": NonPreemptiveSJFScheduler,
    "hybrid": HybridMLQScheduler,
}

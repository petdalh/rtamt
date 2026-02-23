import interval
from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation
from rtamt.semantics.stl.discrete_time.online.or_operation import OrOperation

class IOrOperation(OrOperation):
    def update(self, sample_left, sample_right):
        if isinstance(sample_left, interval.interval) and isinstance(sample_right, interval.interval):
            sample_return = sample_left.maximum(sample_right)
        else:
            sample_return = max(sample_left, sample_right)
        return sample_return

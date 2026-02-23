import collections
import interval
import numpy as np
from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation
from rtamt.semantics.stl.discrete_time.online.once_timed_operation import OnceTimedOperation

class IOnceTimedOperation(OnceTimedOperation):
    def reset(self):
        for i in range(self.end + 1):
            val = interval.interval(-float("inf"), -float("inf"))
            self.buffer.append(val)

    def update(self, sample):
        sample_return = interval.interval(-float("inf"), -float("inf"))
        self.buffer.append(sample)
        for i in range(self.end-self.begin+1):
            sample_return = sample_return.maximum(self.buffer[i])
        return sample_return

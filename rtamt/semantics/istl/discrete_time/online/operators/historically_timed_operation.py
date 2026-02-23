import collections
import interval
from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation
from rtamt.semantics.stl.discrete_time.online.historically_timed_operation import HistoricallyTimedOperation

class IHistoricallyTimedOperation(HistoricallyTimedOperation):
    def reset(self):
        for i in range(self.end + 1):
            val = interval.interval(float("inf"), float("inf"))
            self.buffer.append(val)

    def update(self, sample):
        self.buffer.append(sample)
        sample_return = interval.interval(float("inf"), float("inf"))
        for i in range(self.end-self.begin+1):
            #TODO: Could fix the mimumum typo in the npinterval repo if time: https://github.com/gtfactslab/npinterval
            sample_return = sample_return.mimumum(self.buffer[i])
        return sample_return

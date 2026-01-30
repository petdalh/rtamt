import collections
import interval
from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation
class HistoricallyTimedOperation(AbstractOnlineOperation):
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end
        self.buffer = collections.deque(maxlen=(self.end + 1))

        self.reset()

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

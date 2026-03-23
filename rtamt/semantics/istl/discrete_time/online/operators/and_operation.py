from rtamt.semantics.stl.discrete_time.online.and_operation import AndOperation
from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation


class IAndOperation(AndOperation):
    def __init__(self):
        pass

    def reset(self):
        pass

    def update(self, sample_left, sample_right):
        sample_return = sample_left.minimum(sample_right)
        return sample_return

from rtamt.semantics.abstract_online_operation import AbstractOnlineOperation
from rtamt.semantics.enumerations.comp_oper import StlComparisonOperator
from rtamt.exception.exception import RTAMTException

import numpy as np
import interval

class PredicateOperation(AbstractOnlineOperation):
    def __init__(self, comparison_op):
        self.comparison_op = comparison_op

    def reset(self):
        pass

    def update(self, sample_left, sample_right):
        if self.comparison_op.value == StlComparisonOperator.EQ.value:
            sample_return = - abs(sample_left - sample_right)
        elif self.comparison_op.value == StlComparisonOperator.NEQ.value:
            sample_return = abs(sample_left - sample_right)
        elif self.comparison_op.value == StlComparisonOperator.LEQ.value or self.comparison_op.value == StlComparisonOperator.LESS.value:
            sample_return = sample_right - sample_left
        elif self.comparison_op.value == StlComparisonOperator.GEQ.value or self.comparison_op.value == StlComparisonOperator.GREATER.value:
            sample_return = sample_left - sample_right
        else:
            raise RTAMTException('Unknown predicate operation')

        return sample_return

    def sat(self, sample_left, sample_right):
        if self.comparison_op.value == StlComparisonOperator.EQ.value:
            sample_return = sample_left == sample_right
        elif self.comparison_op.value == StlComparisonOperator.NEQ.value:
            sample_return = sample_left != sample_right
        elif self.comparison_op.value == StlComparisonOperator.GEQ.value:
            sample_return = sample_left >= sample_right
        elif self.comparison_op.value == StlComparisonOperator.GREATER.value:
            sample_return = sample_left > sample_right
        elif self.comparison_op.value == StlComparisonOperator.LEQ.value:
            sample_return = sample_left <= sample_right
        elif self.comparison_op.value == StlComparisonOperator.LESS.value:
            sample_return = sample_left < sample_right
        else:
            raise RTAMTException('Unknown predicate operation')

        return sample_return
class IPredicateOperation(PredicateOperation):
    def update(self, sample_left, sample_right):
        #TODO: Figure out the root cause of why I have to do this conversion here
        # since we define it as an interval in the spec, should not have to do it twice
        if not isinstance(sample_left, interval.interval):
            if isinstance(sample_left, list):
                sample_left = interval.interval(sample_left[0], sample_left[1])
            else: 
                sample_left = interval.interval(sample_left, sample_left)    
                
        if not isinstance(sample_right, interval.interval):
            if isinstance(sample_right, list):
                sample_right = interval.interval(sample_right[0], sample_right[1])
            else:
                sample_right = interval.interval(sample_right, sample_right)

        #TODO: Go over this later
        if self.comparison_op.value == StlComparisonOperator.EQ.value:
            sample_return = - abs(sample_left - sample_right)
        elif self.comparison_op.value == StlComparisonOperator.NEQ.value:
            sample_return = abs(sample_left - sample_right)
        elif self.comparison_op.value == StlComparisonOperator.LEQ.value or self.comparison_op.value == StlComparisonOperator.LESS.value:
            sample_return = sample_right - sample_left
        elif self.comparison_op.value == StlComparisonOperator.GEQ.value or self.comparison_op.value == StlComparisonOperator.GREATER.value:
            sample_return = sample_left - sample_right
        else:
            raise RTAMTException('Unknown predicate operation')

        return sample_return

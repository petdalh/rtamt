import math
import operator
import collections
import interval

from rtamt.semantics.stl.discrete_time.offline.ast_visitor import StlDiscreteTimeOfflineAstVisitor
from rtamt.syntax.ast.visitor.stl.ast_visitor import StlAstVisitor
from rtamt.semantics.enumerations.comp_oper import StlComparisonOperator
from rtamt.exception.exception import RTAMTException

# This is the interval version of the offline visitor. It overrides the relevant methods to handle interval values.
class IStlDiscreteTimeOfflineAstVisitor(StlDiscreteTimeOfflineAstVisitor):
    def visitPredicate(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        for i in range(len(sample_left)):
            # print(f"step {i}: {type(sample_left)}, {type(sample_right)} and sample right value is {sample_right[i]}")
            val_left = sample_left[i]
            val_right = sample_right[i]

            if not isinstance(val_left, interval.interval):
                if isinstance(val_left, list):
                    val_left = interval.interval(val_left[0], val_left[1])
                else:
                    val_left = interval.interval(val_left, val_left)
            if not isinstance(val_right, interval.interval):
                if isinstance(val_right, list):
                    val_right = interval.interval(val_right[0], val_right[1])
                else:
                    val_right = interval.interval(val_right, val_right)

            if node.operator.value == StlComparisonOperator.EQ.value:
                # print("EQ operation in predicate")
                val = -abs(val_left - val_right)
            elif node.operator.value == StlComparisonOperator.NEQ.value:
                # print("NEQ operation in predicate")
                val = abs(val_left - val_right)
            elif node.operator.value == StlComparisonOperator.LEQ.value or node.operator.value == StlComparisonOperator.LESS.value:
                # print("LEQ or LESS operation in predicate")
                val = val_right - val_left
            elif node.operator.value == StlComparisonOperator.GEQ.value or node.operator.value == StlComparisonOperator.GREATER.value:
                # print("GEQ or GREATER operation in predicate")
                val = val_left - val_right
            else:
                raise RTAMTException('Unknown predicate operation')
            # print(f"step {i}: val_left={val_left}, val_right={val_right}, val={val}")
            sample_return.append(val)

        #print(f"sample return is {sample_return}")
        return sample_return

    def visitAnd(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        for left, right in zip(sample_left, sample_right):
            sample_return.append(left.mimumum(right))
        return sample_return


    def visitOr(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)
    
        sample_return = []
        for left, right in zip(sample_left, sample_right):
            sample_return.append(left.maximum(right))

        return sample_return

    def visitTimedAlways(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        sample_len = len(sample)

        inf = interval.interval(float("inf"), float("inf"))

        if sample_len <= end:
            sample += [inf] * (end - sample_len + 1)

        diff = end - begin
        sample_return = []
        for i in range(begin, end + 1):
            minimum = inf
            for j in range(i, i + diff + 1):
                minimum = minimum.mimumum(sample[j])
            sample_return.append(minimum)

        for i in range(end + 1, len(sample)):
            minimum = inf
            for j in range(i, min(i + diff + 1, len(sample))):
                minimum = minimum.mimumum(sample[j])
            sample_return.append(minimum)

        sample_return += [inf] * (len(sample) - len(sample_return))
        return sample_return[0:sample_len]

    def visitTimedEventually(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        sample_len = len(sample)

        if isinstance(sample[0], interval.interval):
            neg_inf = interval.interval(-float("inf"), -float("inf"))
        else:
            neg_inf = -float("inf")

        if sample_len <= end:
            sample += [neg_inf] * (end - sample_len + 1)

        diff = end - begin

        if isinstance(sample[0], interval.interval):
            sample_return = []
            
            for i in range(begin, end+1):
                maximum = interval.interval(-float("inf"), -float("inf"))
                
                for j in range(i, i+diff+1):
                    maximum = maximum.maximum(sample[j])
                sample_return.append(maximum)

            tmp = []

            for i in range(end+1, len(sample)):
                window_limit = min(i + diff + 1, len(sample))
                
                maximum = interval.interval(-float("inf"), -float("inf"))
                
                for j in range(i, window_limit):
                    maximum = maximum.maximum(sample[j])
                tmp.append(maximum)

            sample_return += tmp

            tmp = [neg_inf for j in range(len(sample) - len(sample_return))]

        elif isinstance(sample[0], (int, float)):
            sample_return  = [max(sample[j:j+diff+1]) for j in range(begin, end+1)]
            tmp = [max(sample[j:j+diff+1]) for j in range(end+1,len(sample))]
            sample_return += tmp
            tmp = [-float("inf") for j in range(len(sample)-len(sample_return))]

        sample_return += tmp
        # print(f"return from eventually: {sample_return[0:sample_len]}")
        return sample_return[0:sample_len]

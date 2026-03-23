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
            sample_return.append(left.minimum(right))
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
                minimum = minimum.minimum(sample[j])
            sample_return.append(minimum)

        for i in range(end + 1, len(sample)):
            minimum = inf
            for j in range(i, min(i + diff + 1, len(sample))):
                minimum = minimum.minimum(sample[j])
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
            tmp = [interval.interval(-float("inf"), -float("inf")) for j in range(len(sample)-len(sample_return))]

        sample_return += tmp
        return sample_return[0:sample_len]

    def visitImplies(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = [(-l).maximum(r) for l,r in zip(sample_left, sample_right)]
        return sample_return

    def visitEventually(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        for i in reversed(sample):
            out_sample = i.maximum(prev_out)
            prev_out = out_sample
            sample_return.append(out_sample)
        sample_return.reverse()
        return sample_return

    def visitAlways(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        prev_out = interval.interval(float("inf"), float("inf"))
        for i in reversed(sample):
            out_sample = i.minimum(prev_out)
            prev_out = out_sample
            sample_return.append(out_sample)
        sample_return.reverse()
        return sample_return


    def visitUntil(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        next_out = interval.interval(-float("inf"), -float("inf"))
        for i in range(len(sample_left)-1, -1, -1):
            out_sample = sample_left[i].minimum(next_out)
            out_sample = out_sample.maximum(sample_right[i])
            next_out = out_sample
            sample_return.append(out_sample)
        sample_return.reverse()
        return sample_return


    def visitOnce(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        for i in sample:
            out_sample = i.maximum(prev_out)
            prev_out = out_sample
            sample_return.append(out_sample)
        return sample_return


    def visitHistorically(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        prev_out = interval.interval(float("inf"), float("inf"))
        for i in sample:
            out_sample = i.minimum(prev_out)
            prev_out = out_sample
            sample_return.append(out_sample)
        return sample_return


    def visitSince(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        for i in range(len(sample_left)):
            out_sample = sample_left[i].minimum(prev_out)
            out_sample = out_sample.maximum(sample_right[i])
            prev_out = out_sample
            sample_return.append(out_sample)
        return sample_return


    def visitRise(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        prev = sample[:-1]
        prev.insert(0,interval.interval(-float("inf"), -float("inf")))
        sample_return = [(-p).minimum(s) for p,s in zip(prev, sample)]
        return sample_return


    def visitFall(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)

        prev = sample[:-1]
        prev.insert(0,interval.interval(float("inf"), float("inf")))
        sample_return = [p.minimum(-s) for p,s in zip(prev, sample)]
        return sample_return

    def visitTimedOnce(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        neg_inf = interval.interval(-float("inf"), -float("inf"))
        sample = [neg_inf for j in range(end)] + sample

        sample_return = []
        for j in range(end, len(sample)):
            maximum = neg_inf
            for k in range(j - end, j - begin + 1):
                maximum = maximum.maximum(sample[k])
            sample_return.append(maximum)

        return sample_return


    def visitTimedHistorically(self, node, *args, **kwargs):
        sample = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        inf = interval.interval(float("inf"), float("inf"))
        sample = [inf for j in range(end)] + sample

        sample_return = []
        for j in range(end, len(sample)):
            minimum = inf
            for k in range(j - end, j - begin + 1):
                minimum = minimum.minimum(sample[k])
            sample_return.append(minimum)

        return sample_return

    def visitTimedSince(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        sample_return = []
        buffer_left = collections.deque(maxlen=(end + 1))
        buffer_right = collections.deque(maxlen=(end + 1))

        for i in range(end + 1):
            s_left = interval.interval(float("inf"), float("inf"))
            s_right = interval.interval(-float("inf"), -float("inf"))
            buffer_left.append(s_left)
            buffer_right.append(s_right)

        for i in range(len(sample_left)):
            buffer_left.append(sample_left[i])
            buffer_right.append(sample_right[i])
            out_sample = interval.interval(-float("inf"), -float("inf"))
            

            for j in range(end-begin+1):
                c_left = interval.interval(float("inf"), float("inf"))
                c_right = buffer_right[j]
                for k in range(j+1, end+1):
                    c_left = c_left.minimum(buffer_left[k])
                out_sample = out_sample.maximum(c_left.minimum(c_right))
            sample_return.append(out_sample)
        return sample_return


    def visitTimedUntil(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        sample_return = []
        buffer_left = collections.deque(maxlen=(end + 1))
        buffer_right = collections.deque(maxlen=(end + 1))

        for i in range(end + 1):
            s_left = interval.interval(float("inf"), float("inf"))
            s_right = interval.interval(-float("inf"), -float("inf"))
            buffer_left.append(s_left)
            buffer_right.append(s_right)
        for i in range(len(sample_left)-1, -1, -1):
            buffer_left.append(sample_left[i])
            buffer_right.append(sample_right[i])
            out_sample = interval.interval(-float("inf"), -float("inf"))

            for j in range(end-begin+1):
                c_left = interval.interval(float("inf"), float("inf"))
                c_right = buffer_right[j]
                for k in range(j+1, end+1):
                    c_left = c_left.minimum(buffer_left[k])
                out_sample = out_sample.maximum(c_left.minimum(c_right))
            sample_return.append(out_sample)
        sample_return.reverse()
        return sample_return

import math
import operator
import collections
import interval

from rtamt.semantics.stl.discrete_time.offline.ast_visitor import StlDiscreteTimeOfflineAstVisitor
from rtamt.syntax.ast.visitor.stl.ast_visitor import StlAstVisitor
from rtamt.semantics.enumerations.comp_oper import StlComparisonOperator
from rtamt.exception.exception import RTAMTException


class pacSTLDiscreteTimeOfflineAstVisitor(StlDiscreteTimeOfflineAstVisitor):
    def visitPredicate(self, node, *args, **kwargs):
        sample_left  = self.visit(node.children[0], *args, **kwargs)
        sample_right = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        t_lows  = []
        t_highs = []

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
            # +1 for 1-based indexing in t_lows and t_highs
            t_lows.append(i+1)
            t_highs.append(i+1)

        #print(f"sample return is {sample_return}")
        return sample_return, t_lows, t_highs

    def visitAnd(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs   = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        t_lows  = []
        t_highs = []

        for i, (left, right) in enumerate(zip(sample_left, sample_right)):
            t_lows.append(left_t_lows[i] if left.l < right.l else right_t_lows[i])
            t_highs.append(left_t_highs[i] if left.u < right.u else right_t_highs[i])
            sample_return.append(left.mimumum(right))

        return sample_return, t_lows, t_highs


    def visitOr(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs   = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)
    
        sample_return = []
        t_lows  = []
        t_highs = []

        for i, (left, right) in enumerate(zip(sample_left, sample_right)):
            t_lows.append(left_t_lows[i] if left.l > right.l else right_t_lows[i])
            t_highs.append(left_t_highs[i] if left.u > right.u else right_t_highs[i])
            sample_return.append(left.maximum(right))

        return sample_return, t_lows, t_highs

    def visitNot(self, node, *args, **kwargs):
        samples, t_lows, t_highs = self.visit(node.children[0], *args, **kwargs)
        return [-s for s in samples], t_highs, t_lows

    def visitTimedAlways(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        sample_len = len(sample)

        inf = interval.interval(float("inf"), float("inf"))

        if sample_len <= end:
            sample    += [inf] * (end - sample_len + 1)
            s_t_lows  += [-1]  * (end - sample_len + 1)
            s_t_highs += [-1]  * (end - sample_len + 1)

        diff = end - begin
        sample_return = []
        t_lows  = []
        t_highs = []

        for i in range(begin, end + 1):
            minimum    = inf
            min_t_low  = -1
            min_t_high = -1
            for j in range(i, i + diff + 1):
                curr = sample[j]
                if curr.l < minimum.l:
                    min_t_low = s_t_lows[j]
                if curr.u < minimum.u:
                    min_t_high = s_t_highs[j]
                minimum = minimum.mimumum(curr)
            sample_return.append(minimum)
            t_lows.append(min_t_low)
            t_highs.append(min_t_high)

        for i in range(end + 1, len(sample)):
            minimum    = inf
            min_t_low  = -1
            min_t_high = -1
            for j in range(i, min(i + diff + 1, len(sample))):
                curr = sample[j]
                if curr.l < minimum.l:
                    min_t_low = s_t_lows[j]
                if curr.u < minimum.u:
                    min_t_high = s_t_highs[j]
                minimum = minimum.mimumum(curr)
            sample_return.append(minimum)
            t_lows.append(min_t_low)
            t_highs.append(min_t_high)

        pad_len = len(sample) - len(sample_return)
        sample_return += [inf] * pad_len
        t_lows        += [-1]  * pad_len
        t_highs       += [-1]  * pad_len

        return sample_return[0:sample_len], t_lows[0:sample_len], t_highs[0:sample_len]

    def visitTimedEventually(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        sample_len = len(sample)

        if isinstance(sample[0], interval.interval):
            neg_inf = interval.interval(-float("inf"), -float("inf"))
        else:
            neg_inf = -float("inf")

        if sample_len <= end:
            sample    += [neg_inf] * (end - sample_len + 1)
            s_t_lows  += [-1]      * (end - sample_len + 1)
            s_t_highs += [-1]      * (end - sample_len + 1)

        diff = end - begin

        if isinstance(sample[0], interval.interval):
            sample_return = []
            t_lows  = []
            t_highs = []
            
            for i in range(begin, end+1):
                maximum = interval.interval(-float("inf"), -float("inf"))
                max_t_low  = -1
                max_t_high = -1
                
                for j in range(i, i+diff+1):
                    curr = sample[j]
                    if curr.l > maximum.l:
                        max_t_low = s_t_lows[j]
                    if curr.u > maximum.u:
                        max_t_high = s_t_highs[j]
                    maximum = maximum.maximum(curr)
                sample_return.append(maximum)
                t_lows.append(max_t_low)
                t_highs.append(max_t_high)

            tmp = []
            tmp_t_lows  = []
            tmp_t_highs = []

            for i in range(end+1, len(sample)):
                window_limit = min(i + diff + 1, len(sample))
                
                maximum = interval.interval(-float("inf"), -float("inf"))
                max_t_low  = -1
                max_t_high = -1
                
                for j in range(i, window_limit):
                    curr = sample[j]
                    if curr.l > maximum.l:
                        max_t_low = s_t_lows[j]
                    if curr.u > maximum.u:
                        max_t_high = s_t_highs[j]
                    maximum = maximum.maximum(curr)
                tmp.append(maximum)
                tmp_t_lows.append(max_t_low)
                tmp_t_highs.append(max_t_high)

            sample_return += tmp
            t_lows        += tmp_t_lows
            t_highs       += tmp_t_highs

            pad_len = len(sample) - len(sample_return)
            tmp         = [neg_inf for j in range(pad_len)]
            tmp_t_lows  = [-1 for j in range(pad_len)]
            tmp_t_highs = [-1 for j in range(pad_len)]

        elif isinstance(sample[0], (int, float)):
            sample_return = []
            t_lows  = []
            t_highs = []

            for i in range(begin, end+1):
                max_val    = -float("inf")
                max_t_low  = -1
                max_t_high = -1
                for j in range(i, i+diff+1):
                    if sample[j] > max_val:
                        max_val    = sample[j]
                        max_t_low  = s_t_lows[j]
                        max_t_high = s_t_highs[j]
                sample_return.append(max_val)
                t_lows.append(max_t_low)
                t_highs.append(max_t_high)

            tmp = []
            tmp_t_lows  = []
            tmp_t_highs = []

            for i in range(end+1, len(sample)):
                max_val    = -float("inf")
                max_t_low  = -1
                max_t_high = -1
                for j in range(i, min(i+diff+1, len(sample))):
                    if sample[j] > max_val:
                        max_val    = sample[j]
                        max_t_low  = s_t_lows[j]
                        max_t_high = s_t_highs[j]
                tmp.append(max_val)
                tmp_t_lows.append(max_t_low)
                tmp_t_highs.append(max_t_high)

            sample_return += tmp
            t_lows        += tmp_t_lows
            t_highs       += tmp_t_highs

            pad_len = len(sample) - len(sample_return)
            tmp         = [-float("inf") for j in range(pad_len)]
            tmp_t_lows  = [-1 for j in range(pad_len)]
            tmp_t_highs = [-1 for j in range(pad_len)]

        sample_return += tmp
        t_lows        += tmp_t_lows
        t_highs       += tmp_t_highs

        # print(f"return from eventually: {sample_return[0:sample_len]}")
        return sample_return[0:sample_len], t_lows[0:sample_len], t_highs[0:sample_len]
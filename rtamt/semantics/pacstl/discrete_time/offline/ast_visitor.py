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
            sample_return.append(left.minimum(right))

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
                minimum = minimum.minimum(curr)
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
                minimum = minimum.minimum(curr)
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
                
                for j in range(i, min(i + diff + 1, len(sample))):
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

        return sample_return[0:sample_len], t_lows[0:sample_len], t_highs[0:sample_len]
        
    def visitImplies(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        for i, (l, r) in enumerate(zip(sample_left, sample_right)):
            neg_l = -l
            val = neg_l.maximum(r)
            # max selects larger lower bound and larger upper bound
            t_lows.append(left_t_highs[i] if neg_l.l > r.l else right_t_lows[i])
            t_highs.append(left_t_lows[i] if neg_l.u > r.u else right_t_highs[i])
            sample_return.append(val)
        return sample_return, t_lows, t_highs


    def visitEventually(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        prev_t_low = -1
        prev_t_high = -1
        for i in range(len(sample) - 1, -1, -1):
            curr = sample[i]
            if curr.l > prev_out.l:
                new_t_low = s_t_lows[i]
            else:
                new_t_low = prev_t_low
            if curr.u > prev_out.u:
                new_t_high = s_t_highs[i]
            else:
                new_t_high = prev_t_high
            out_sample = curr.maximum(prev_out)
            prev_out = out_sample
            prev_t_low = new_t_low
            prev_t_high = new_t_high
            sample_return.append(out_sample)
            t_lows.append(new_t_low)
            t_highs.append(new_t_high)
        sample_return.reverse()
        t_lows.reverse()
        t_highs.reverse()
        return sample_return, t_lows, t_highs


    def visitAlways(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        prev_out = interval.interval(float("inf"), float("inf"))
        prev_t_low = -1
        prev_t_high = -1
        for i in range(len(sample) - 1, -1, -1):
            curr = sample[i]
            if curr.l < prev_out.l:
                new_t_low = s_t_lows[i]
            else:
                new_t_low = prev_t_low
            if curr.u < prev_out.u:
                new_t_high = s_t_highs[i]
            else:
                new_t_high = prev_t_high
            out_sample = curr.minimum(prev_out)
            prev_out = out_sample
            prev_t_low = new_t_low
            prev_t_high = new_t_high
            sample_return.append(out_sample)
            t_lows.append(new_t_low)
            t_highs.append(new_t_high)
        sample_return.reverse()
        t_lows.reverse()
        t_highs.reverse()
        return sample_return, t_lows, t_highs


    def visitUntil(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        next_out = interval.interval(-float("inf"), -float("inf"))
        next_t_low = -1
        next_t_high = -1
        for i in range(len(sample_left) - 1, -1, -1):
            # min(left[i], next_out)
            min_val = sample_left[i].minimum(next_out)
            if sample_left[i].l < next_out.l:
                min_t_low = left_t_lows[i]
            else:
                min_t_low = next_t_low
            if sample_left[i].u < next_out.u:
                min_t_high = left_t_highs[i]
            else:
                min_t_high = next_t_high

            # max(min_val, right[i])
            out_sample = min_val.maximum(sample_right[i])
            if min_val.l > sample_right[i].l:
                out_t_low = min_t_low
            else:
                out_t_low = right_t_lows[i]
            if min_val.u > sample_right[i].u:
                out_t_high = min_t_high
            else:
                out_t_high = right_t_highs[i]

            next_out = out_sample
            next_t_low = out_t_low
            next_t_high = out_t_high
            sample_return.append(out_sample)
            t_lows.append(out_t_low)
            t_highs.append(out_t_high)
        sample_return.reverse()
        t_lows.reverse()
        t_highs.reverse()
        return sample_return, t_lows, t_highs


    def visitOnce(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        prev_t_low = -1
        prev_t_high = -1
        for i in range(len(sample)):
            curr = sample[i]
            if curr.l > prev_out.l:
                new_t_low = s_t_lows[i]
            else:
                new_t_low = prev_t_low
            if curr.u > prev_out.u:
                new_t_high = s_t_highs[i]
            else:
                new_t_high = prev_t_high
            out_sample = curr.maximum(prev_out)
            prev_out = out_sample
            prev_t_low = new_t_low
            prev_t_high = new_t_high
            sample_return.append(out_sample)
            t_lows.append(new_t_low)
            t_highs.append(new_t_high)
        return sample_return, t_lows, t_highs


    def visitHistorically(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        prev_out = interval.interval(float("inf"), float("inf"))
        prev_t_low = -1
        prev_t_high = -1
        for i in range(len(sample)):
            curr = sample[i]
            if curr.l < prev_out.l:
                new_t_low = s_t_lows[i]
            else:
                new_t_low = prev_t_low
            if curr.u < prev_out.u:
                new_t_high = s_t_highs[i]
            else:
                new_t_high = prev_t_high
            out_sample = curr.minimum(prev_out)
            prev_out = out_sample
            prev_t_low = new_t_low
            prev_t_high = new_t_high
            sample_return.append(out_sample)
            t_lows.append(new_t_low)
            t_highs.append(new_t_high)
        return sample_return, t_lows, t_highs


    def visitSince(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)

        sample_return = []
        t_lows = []
        t_highs = []
        prev_out = interval.interval(-float("inf"), -float("inf"))
        prev_t_low = -1
        prev_t_high = -1
        for i in range(len(sample_left)):
            # min(left[i], prev_out)
            min_val = sample_left[i].minimum(prev_out)
            if sample_left[i].l < prev_out.l:
                min_t_low = left_t_lows[i]
            else:
                min_t_low = prev_t_low
            if sample_left[i].u < prev_out.u:
                min_t_high = left_t_highs[i]
            else:
                min_t_high = prev_t_high

            # max(min_val, right[i])
            out_sample = min_val.maximum(sample_right[i])
            if min_val.l > sample_right[i].l:
                out_t_low = min_t_low
            else:
                out_t_low = right_t_lows[i]
            if min_val.u > sample_right[i].u:
                out_t_high = min_t_high
            else:
                out_t_high = right_t_highs[i]

            prev_out = out_sample
            prev_t_low = out_t_low
            prev_t_high = out_t_high
            sample_return.append(out_sample)
            t_lows.append(out_t_low)
            t_highs.append(out_t_high)
        return sample_return, t_lows, t_highs


    def visitRise(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        neg_inf = interval.interval(-float("inf"), -float("inf"))
        prev = sample[:-1]
        prev.insert(0, neg_inf)
        prev_t_lows = s_t_lows[:-1]
        prev_t_lows.insert(0, -1)
        prev_t_highs = s_t_highs[:-1]
        prev_t_highs.insert(0, -1)

        sample_return = []
        t_lows = []
        t_highs = []
        for i, (p, s) in enumerate(zip(prev, sample)):
            neg_p = -p
            val = neg_p.minimum(s)
            # min selects smaller lower / smaller upper
            if neg_p.l < s.l:
                t_low = prev_t_highs[i]  # negation swaps
            else:
                t_low = s_t_lows[i]
            if neg_p.u < s.u:
                t_high = prev_t_lows[i]  # negation swaps
            else:
                t_high = s_t_highs[i]
            sample_return.append(val)
            t_lows.append(t_low)
            t_highs.append(t_high)
        return sample_return, t_lows, t_highs


    def visitFall(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)

        inf = interval.interval(float("inf"), float("inf"))
        prev = sample[:-1]
        prev.insert(0, inf)
        prev_t_lows = s_t_lows[:-1]
        prev_t_lows.insert(0, -1)
        prev_t_highs = s_t_highs[:-1]
        prev_t_highs.insert(0, -1)

        sample_return = []
        t_lows = []
        t_highs = []
        for i, (p, s) in enumerate(zip(prev, sample)):
            neg_s = -s
            val = p.minimum(neg_s)
            if p.l < neg_s.l:
                t_low = prev_t_lows[i]
            else:
                t_low = s_t_highs[i]  # negation swaps
            if p.u < neg_s.u:
                t_high = prev_t_highs[i]
            else:
                t_high = s_t_lows[i]  # negation swaps
            sample_return.append(val)
            t_lows.append(t_low)
            t_highs.append(t_high)
        return sample_return, t_lows, t_highs


    def visitTimedOnce(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        neg_inf = interval.interval(-float("inf"), -float("inf"))
        sample = [neg_inf for j in range(end)] + sample
        s_t_lows = [-1 for j in range(end)] + s_t_lows
        s_t_highs = [-1 for j in range(end)] + s_t_highs

        sample_return = []
        t_lows = []
        t_highs = []
        for j in range(end, len(sample)):
            maximum = neg_inf
            max_t_low = -1
            max_t_high = -1
            for k in range(j - end, j - begin + 1):
                curr = sample[k]
                if curr.l > maximum.l:
                    max_t_low = s_t_lows[k]
                if curr.u > maximum.u:
                    max_t_high = s_t_highs[k]
                maximum = maximum.maximum(curr)
            sample_return.append(maximum)
            t_lows.append(max_t_low)
            t_highs.append(max_t_high)
        return sample_return, t_lows, t_highs


    def visitTimedHistorically(self, node, *args, **kwargs):
        sample, s_t_lows, s_t_highs = self.visit(node.children[0], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        inf = interval.interval(float("inf"), float("inf"))
        sample = [inf for j in range(end)] + sample
        s_t_lows = [-1 for j in range(end)] + s_t_lows
        s_t_highs = [-1 for j in range(end)] + s_t_highs

        sample_return = []
        t_lows = []
        t_highs = []
        for j in range(end, len(sample)):
            minimum = inf
            min_t_low = -1
            min_t_high = -1
            for k in range(j - end, j - begin + 1):
                curr = sample[k]
                if curr.l < minimum.l:
                    min_t_low = s_t_lows[k]
                if curr.u < minimum.u:
                    min_t_high = s_t_highs[k]
                minimum = minimum.minimum(curr)
            sample_return.append(minimum)
            t_lows.append(min_t_low)
            t_highs.append(min_t_high)
        return sample_return, t_lows, t_highs


    def visitTimedSince(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        sample_return = []
        t_lows = []
        t_highs = []
        buffer_left = collections.deque(maxlen=(end + 1))
        buffer_right = collections.deque(maxlen=(end + 1))
        buf_left_t_lows = collections.deque(maxlen=(end + 1))
        buf_left_t_highs = collections.deque(maxlen=(end + 1))
        buf_right_t_lows = collections.deque(maxlen=(end + 1))
        buf_right_t_highs = collections.deque(maxlen=(end + 1))

        for i in range(end + 1):
            buffer_left.append(interval.interval(float("inf"), float("inf")))
            buffer_right.append(interval.interval(-float("inf"), -float("inf")))
            buf_left_t_lows.append(-1)
            buf_left_t_highs.append(-1)
            buf_right_t_lows.append(-1)
            buf_right_t_highs.append(-1)

        for i in range(len(sample_left)):
            buffer_left.append(sample_left[i])
            buffer_right.append(sample_right[i])
            buf_left_t_lows.append(left_t_lows[i])
            buf_left_t_highs.append(left_t_highs[i])
            buf_right_t_lows.append(right_t_lows[i])
            buf_right_t_highs.append(right_t_highs[i])

            out_sample = interval.interval(-float("inf"), -float("inf"))
            out_t_low = -1
            out_t_high = -1

            for j in range(end - begin + 1):
                c_left = interval.interval(float("inf"), float("inf"))
                c_left_t_low = -1
                c_left_t_high = -1
                c_right = buffer_right[j]
                c_right_t_low = buf_right_t_lows[j]
                c_right_t_high = buf_right_t_highs[j]

                for k in range(j + 1, end + 1):
                    if buffer_left[k].l < c_left.l:
                        c_left_t_low = buf_left_t_lows[k]
                    if buffer_left[k].u < c_left.u:
                        c_left_t_high = buf_left_t_highs[k]
                    c_left = c_left.minimum(buffer_left[k])

                # min(c_left, c_right)
                combo = c_left.minimum(c_right)
                if c_left.l < c_right.l:
                    combo_t_low = c_left_t_low
                else:
                    combo_t_low = c_right_t_low
                if c_left.u < c_right.u:
                    combo_t_high = c_left_t_high
                else:
                    combo_t_high = c_right_t_high

                # max(out_sample, combo)
                if combo.l > out_sample.l:
                    out_t_low = combo_t_low
                if combo.u > out_sample.u:
                    out_t_high = combo_t_high
                out_sample = out_sample.maximum(combo)

            sample_return.append(out_sample)
            t_lows.append(out_t_low)
            t_highs.append(out_t_high)
        return sample_return, t_lows, t_highs


    def visitTimedUntil(self, node, *args, **kwargs):
        sample_left, left_t_lows, left_t_highs = self.visit(node.children[0], *args, **kwargs)
        sample_right, right_t_lows, right_t_highs = self.visit(node.children[1], *args, **kwargs)
        begin, end = self.time_unit_transformer(node)

        sample_return = []
        t_lows = []
        t_highs = []
        buffer_left = collections.deque(maxlen=(end + 1))
        buffer_right = collections.deque(maxlen=(end + 1))
        buf_left_t_lows = collections.deque(maxlen=(end + 1))
        buf_left_t_highs = collections.deque(maxlen=(end + 1))
        buf_right_t_lows = collections.deque(maxlen=(end + 1))
        buf_right_t_highs = collections.deque(maxlen=(end + 1))

        for i in range(end + 1):
            buffer_left.append(interval.interval(float("inf"), float("inf")))
            buffer_right.append(interval.interval(-float("inf"), -float("inf")))
            buf_left_t_lows.append(-1)
            buf_left_t_highs.append(-1)
            buf_right_t_lows.append(-1)
            buf_right_t_highs.append(-1)

        for i in range(len(sample_left) - 1, -1, -1):
            buffer_left.append(sample_left[i])
            buffer_right.append(sample_right[i])
            buf_left_t_lows.append(left_t_lows[i])
            buf_left_t_highs.append(left_t_highs[i])
            buf_right_t_lows.append(right_t_lows[i])
            buf_right_t_highs.append(right_t_highs[i])

            out_sample = interval.interval(-float("inf"), -float("inf"))
            out_t_low = -1
            out_t_high = -1

            for j in range(end - begin + 1):
                c_left = interval.interval(float("inf"), float("inf"))
                c_left_t_low = -1
                c_left_t_high = -1
                c_right = buffer_right[j]
                c_right_t_low = buf_right_t_lows[j]
                c_right_t_high = buf_right_t_highs[j]

                for k in range(j + 1, end + 1):
                    if buffer_left[k].l < c_left.l:
                        c_left_t_low = buf_left_t_lows[k]
                    if buffer_left[k].u < c_left.u:
                        c_left_t_high = buf_left_t_highs[k]
                    c_left = c_left.minimum(buffer_left[k])

                combo = c_left.minimum(c_right)
                if c_left.l < c_right.l:
                    combo_t_low = c_left_t_low
                else:
                    combo_t_low = c_right_t_low
                if c_left.u < c_right.u:
                    combo_t_high = c_left_t_high
                else:
                    combo_t_high = c_right_t_high

                if combo.l > out_sample.l:
                    out_t_low = combo_t_low
                if combo.u > out_sample.u:
                    out_t_high = combo_t_high
                out_sample = out_sample.maximum(combo)

            sample_return.append(out_sample)
            t_lows.append(out_t_low)
            t_highs.append(out_t_high)
        sample_return.reverse()
        t_lows.reverse()
        t_highs.reverse()
        return sample_return, t_lows, t_highs
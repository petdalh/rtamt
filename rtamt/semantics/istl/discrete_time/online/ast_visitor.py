from rtamt.semantics.stl.discrete_time.online.ast_visitor import StlDiscreteTimeOnlineAstVisitor
from rtamt.semantics.stl.discrete_time.online.strong_previous_operation import StrongPreviousOperation
from rtamt.semantics.stl.discrete_time.online.variable_operation import VariableOperation
from rtamt.syntax.ast.visitor.stl.ast_visitor import StlAstVisitor

from rtamt.semantics.arithmetic.discrete_time.online.addition_operation import AdditionOperation
from rtamt.semantics.arithmetic.discrete_time.online.multiplication_operation import MultiplicationOperation
from rtamt.semantics.arithmetic.discrete_time.online.subtraction_operation import SubtractionOperation
from rtamt.semantics.arithmetic.discrete_time.online.division_operation import DivisionOperation
from rtamt.semantics.arithmetic.discrete_time.online.abs_operation import AbsOperation
from rtamt.semantics.arithmetic.discrete_time.online.sqrt_operation import SqrtOperation
from rtamt.semantics.arithmetic.discrete_time.online.exp_operation import ExpOperation
from rtamt.semantics.arithmetic.discrete_time.online.pow_operation import PowOperation
from rtamt.semantics.arithmetic.discrete_time.online.negate_operation import NegateOperation
from rtamt.semantics.arithmetic.discrete_time.online.log_operation import LogOperation
from rtamt.semantics.arithmetic.discrete_time.online.ln_operation import LnOperation

from rtamt.semantics.stl.discrete_time.online.predicate_operation import IPredicateOperation
from rtamt.semantics.stl.discrete_time.online.and_operation import IAndOperation
from rtamt.semantics.stl.discrete_time.online.or_operation import IOrOperation
from rtamt.semantics.stl.discrete_time.online.once_timed_operation import IOnceTimedOperation
from rtamt.semantics.stl.discrete_time.online.historically_timed_operation import IHistoricallyTimedOperation
from rtamt.semantics.stl.discrete_time.online.precedes_timed_operation import IPrecedesTimedOperation

from rtamt.exception.exception import RTAMTException

class IStlDiscreteTimeOnlineAstVisitor(StlDiscreteTimeOnlineAstVisitor):
    def visitTimedHistorically(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        self.online_operator_dict[node.name] = IHistoricallyTimedOperation(begin, end)    

    def visitTimedOnce(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        self.online_operator_dict[node.name] = IOnceTimedOperation(begin, end)

    def visitOr(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        self.online_operator_dict[node.name] = IOrOperation()

    def visitTimedPrecedes(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        begin, end = self.time_unit_transformer(node)
        self.online_operator_dict[node.name] = IPrecedesTimedOperation(begin, end)

    def visitPredicate(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        self.online_operator_dict[node.name] = IPredicateOperation(node.operator)
    
    def visitAnd(self, node, *args, **kwargs):
        self.visitChildren(node, *args, **kwargs)
        self.online_operator_dict[node.name] = IAndOperation()

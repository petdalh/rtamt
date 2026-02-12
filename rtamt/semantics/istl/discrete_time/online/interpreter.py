from rtamt.semantics.istl.discrete_time.online.ast_visitor import StlDiscreteTimeOnlineAstVisitor, IStlDiscreteTimeOnlineAstVisitor
from rtamt.semantics.abstract_discrete_time_online_interpreter import discrete_time_online_interpreter_factory

def IStlDiscreteTimeOnlineInterpreter():
    ast_visitor = IStlDiscreteTimeOnlineAstVisitor
    stlDiscreteTimeOnlineInterpreter = discrete_time_online_interpreter_factory(ast_visitor)()
    return stlDiscreteTimeOnlineInterpreter

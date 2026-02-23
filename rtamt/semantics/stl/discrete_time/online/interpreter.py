from rtamt.semantics.stl.discrete_time.online.ast_visitor import StlDiscreteTimeOnlineAstVisitor
from rtamt.semantics.abstract_discrete_time_online_interpreter import discrete_time_online_interpreter_factory

def StlDiscreteTimeOnlineInterpreter():
    ast_visitor = StlDiscreteTimeOnlineAstVisitor
    stlDiscreteTimeOnlineInterpreter = discrete_time_online_interpreter_factory(ast_visitor)()
    return stlDiscreteTimeOnlineInterpreter

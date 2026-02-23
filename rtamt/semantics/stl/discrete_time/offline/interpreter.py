from rtamt.semantics.stl.discrete_time.offline.ast_visitor import StlDiscreteTimeOfflineAstVisitor
from rtamt.semantics.abstract_discrete_time_offline_interpreter import discrete_time_offline_interpreter_factory

def StlDiscreteTimeOfflineInterpreter():
    ast_visitor = StlDiscreteTimeOfflineAstVisitor
    stlDiscreteTimeOfflineInterpreter = discrete_time_offline_interpreter_factory(ast_visitor)()
    return stlDiscreteTimeOfflineInterpreter

from rtamt.semantics.istl.discrete_time.offline.ast_visitor import IStlDiscreteTimeOfflineAstVisitor
from rtamt.semantics.abstract_discrete_time_offline_interpreter import discrete_time_offline_interpreter_factory

def IStlDiscreteTimeOfflineInterpreter():
    ast_visitor = IStlDiscreteTimeOfflineAstVisitor
    stlDiscreteTimeOfflineInterpreter = discrete_time_offline_interpreter_factory(ast_visitor)()
    return stlDiscreteTimeOfflineInterpreter

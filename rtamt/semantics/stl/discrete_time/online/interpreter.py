from rtamt.semantics.stl.discrete_time.online.ast_visitor import StlDiscreteTimeOnlineAstVisitor, IStlDiscreteTimeOnlineAstVisitor
from rtamt.semantics.abstract_discrete_time_online_interpreter import discrete_time_online_interpreter_factory

def StlDiscreteTimeOnlineInterpreter(mode='STL'):
    if mode == 'Interval-STL':
        ast_visitor = IStlDiscreteTimeOnlineAstVisitor
    else:
        ast_visitor = StlDiscreteTimeOnlineAstVisitor

    stlDiscreteTimeOnlineInterpreter = discrete_time_online_interpreter_factory(ast_visitor)()
    return stlDiscreteTimeOnlineInterpreter

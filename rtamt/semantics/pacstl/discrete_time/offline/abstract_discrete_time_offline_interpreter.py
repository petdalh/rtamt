# -*- coding: utf-8 -*-

from rtamt.syntax.ast.visitor.abstract_ast_visitor import AbstractAstVisitor
from rtamt.semantics.abstract_discrete_time_offline_interpreter import AbstractDiscreteTimeOfflineInterpreter

from rtamt.exception.exception import RTAMTException

class pacstlAbstractDiscreteTimeOfflineInterpreter(AbstractDiscreteTimeOfflineInterpreter):

    def __init__(self):
        super(pacstlAbstractDiscreteTimeOfflineInterpreter, self).__init__()
        return

    def evaluate(self, dataset):
        self.exist_ast()

        self.set_variable_to_ast_from_dataset(dataset)

        length = len(dataset['time'])
        self.ast.results['time'] = dataset['time']

        eval_results = self.visitAst(self.ast, length)
        root_result = eval_results[len(eval_results)-1]

        rob_raw, t_lows, t_highs = root_result

        ts = dataset['time']
        for i in range(len(ts) - 1):
            duration = (ts[i+1] - ts[i]) * self.normalize
            self.update_sampling_violation_counter(duration)

        out_t = [[a[0], a[1]] for a in zip(ts, rob_raw)]
        rob_formatted = out_t

        return rob_formatted, t_lows, t_highs

    def set_variable_to_ast_from_dataset(self, dataset):
        for key in dataset:
            if key != 'time':
                self.ast.var_object_dict[key] = dataset[key]


def pacstl_discrete_time_offline_interpreter_factory(AstVisitor):
    if not issubclass(AstVisitor, AbstractAstVisitor):  # type check
        raise RTAMTException('{} is not RTAMT AST visitor'.format(AstVisitor.__name__))

    class DiscreteTimeOfflineInterpreter(pacstlAbstractDiscreteTimeOfflineInterpreter, AstVisitor):
        def __init__(self, *args, **kwargs):
            super(DiscreteTimeOfflineInterpreter, self).__init__(*args, **kwargs)
            
    return DiscreteTimeOfflineInterpreter

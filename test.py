import sys
import rtamt

def monitor():
    spec = rtamt.StlDiscreteTimeSpecification()
    spec.declare_var('a', 'interval')
    spec.declare_var('b', 'interval')
    # Formula: Is 'a' at least 'b' at some point in the last 2 steps?
    spec.spec = 'eventually[0,1] (a >= b);'

    try:
        spec.parse()
        spec.pastify()
    except rtamt.RTAMTException as err:
        print('RTAMT Exception: {}'.format(err))
        sys.exit()

    rob0 = spec.update(0, [('a', [10.0, 12.0]), ('b', [2.0, 4.0])])
    print(f'T=0: rob={rob0} -> Guaranteed Satisfaction (Lower > 0)')

    rob1 = spec.update(1, [('a', [5.0, 7.0]), ('b', [6.0, 8.0])])
    print(f'T=1: rob={rob1} -> Still Satisfied (Eventually found the [6, 10] in the window)')

    rob2 = spec.update(2, [('a', [-20.0, -18.0]), ('b', [0.0, 2.0])])
    print(f'T=2: rob={rob2} -> Uncertain (0 is inside [-3, 1])')

    rob3 = spec.update(3, [('a', [-50.0, -45.0]), ('b', [0.0, 0.0])])
    print(f'T=3: rob={rob3} -> Guaranteed Violation (Upper < 0)')

    import sys

def monitor_always():
    spec = rtamt.StlDiscreteTimeSpecification()
    spec.declare_var('a', 'interval')
    spec.declare_var('b', 'interval')
    # Formula: Has 'a' always been at least 'b' for the last 2 steps?
    spec.spec = 'always[0,1] (a >= b);'

    try:
        spec.parse()
        spec.pastify()
    except rtamt.RTAMTException as err:
        print('RTAMT Exception: {}'.format(err))
        sys.exit()

    print("--- Testing ALWAYS (Box) Operator ---")

    rob0 = spec.update(0, [('a', [20.0, 25.0]), ('b', [5.0, 10.0])])
    print(f'T=0: rob={rob0} -> Guaranteed Satisfaction')

    rob1 = spec.update(1, [('a', [10.0, 15.0]), ('b', [12.0, 18.0])])
    print(f'T=1: rob={rob1} -> Uncertain (Worst case in window is now [-8, 3])')

    rob2 = spec.update(2, [('a', [100.0, 110.0]), ('b', [0.0, 0.0])])
    print(f'T=2: rob={rob2} -> Still Uncertain (The dip at T=1 is still in the window)')

    rob3 = spec.update(3, [('a', [0.0, 5.0]), ('b', [20.0, 25.0])])
    print(f'T=3: rob={rob3} -> Guaranteed Violation')

import sys
import rtamt

def monitor_until():
    spec = rtamt.StlDiscreteTimeSpecification()
    spec.declare_var('a', 'interval')
    spec.declare_var('b', 'interval')
    # a must be >= 5 UNTIL b hits 10 (within 2 steps)
    spec.spec = '(a >= 5.0) until[0,2] (b >= 10.0);'

    try:
        spec.parse()
        spec.pastify()
    except rtamt.RTAMTException as err:
        print('RTAMT Exception: {}'.format(err))
        sys.exit()

    print("--- Testing UNTIL Operator ---")

    print("step 1")
    rob0 = spec.update(0, [('a', [15.0, 20.0]), ('b', [0.0, 2.0])])
    print(f'T=0: rob={rob0}')

    print("step 2")
    rob1 = spec.update(1, [('a', [4.0, 6.0]), ('b', [2.0, 4.0])])
    print(f'T=1: rob={rob1}')

    print("step 3")
    rob2 = spec.update(2, [('a', [20.0, 25.0]), ('b', [12.0, 15.0])])
    print(f'T=2: rob={rob2}')

    print("successful termination of until")

if __name__ == '__main__':
    # print("-------------------------------")
    # print("-----------  Monitoring test  ----------")
    # print("-------------------------------")
    # monitor()


    # print("-------------------------------")
    # print("-----------  Monitoring always  ----------")
    # print("-------------------------------")
    # monitor_always()


    print("-------------------------------")
    print("-----------  Monitoring until  ----------")
    print("-------------------------------")
    monitor_until()

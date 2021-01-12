import numpy as np
import decimal
from collections import defaultdict


def knapsack(items, maxweight, method='recursive'):
    r"""
    Solve the knapsack problem by finding the most valuable subsequence of
    `items` subject that weighs no more than `maxweight`.

    Args:
        items (tuple): is a sequence of tuples `(value, weight, id_)`, where
            `value` is a number and `weight` is a non-negative integer, and
            `id_` is an item identifier.

        maxweight (scalar):  is a non-negative integer.

    Returns:
        tuple: (total_value, items_subset) - a pair whose first element is the
            sum of values in the most valuable subsequence, and whose second
            element is the subsequence. Subset may be different depending on
            implementation (ie top-odwn recusrive vs bottom-up iterative)

    References:
        http://codereview.stackexchange.com/questions/20569/dynamic-programming-solution-to-knapsack-problem
        http://stackoverflow.com/questions/141779/solving-the-np-complete-problem-in-xkcd
        http://www.es.ele.tue.nl/education/5MC10/Solutions/knapsack.pdf

    Example:
        >>> # ENABLE_DOCTEST
        >>> import ubelt as ub
        >>> items = [(4, 12, 0), (2, 1, 1), (6, 4, 2), (1, 1, 3), (2, 2, 4)]
        >>> maxweight = 15
        >>> total_value1, items_subset1 = knapsack(items, maxweight, method='iterative')
        >>> print('items_subset1 = {}'.format(ub.repr2(items_subset1, nl=1)))
        >>> print('total_value1 = {}'.format(ub.repr2(total_value1, nl=1)))

    Example:
        >>> # ENABLE_DOCTEST
        >>> # Solve https://xkcd.com/287/
        >>> weights = [2.15, 2.75, 3.35, 3.55, 4.2, 5.8] * 2
        >>> items = [(w, w, i) for i, w in enumerate(weights)]
        >>> maxweight = 15.05
        >>> total_value1, items_subset1 = knapsack(items, maxweight, method='iterative')
        >>> total_weight = sum([t[1] for t in items_subset1])
        >>> print('total_weight = %r' % (total_weight,))
        >>> print('items_subset1 = %r' % (items_subset1,))
        >>> #assert items_subset1 == items_subset, 'NOT EQ\n%r !=\n%r' % (items_subset1, items_subset)

    Timeit:
        >>> import ubelt as ub
        >>> setup = ub.codeblock(
        >>>     '''
                import ubelt as ut
                weights = [215, 275, 335, 355, 42, 58] * 40
                items = [(w, w, i) for i, w in enumerate(weights)]
                maxweight = 2505
                #import numba
                #knapsack_numba = numba.autojit(knapsack_iterative)
                #knapsack_numba = numba.autojit(knapsack_iterative_numpy)
                ''')
        >>> # Test load time
        >>> stmt_list1 = ub.codeblock(
        >>>     '''
                knapsack_iterative(items, maxweight)
                knapsack_ilp(items, maxweight)
                #knapsack_numba(items, maxweight)
                #knapsack_iterative_numpy(items, maxweight)
                ''').split('\n')
        >>> ut.util_dev.timeit_compare(stmt_list1, setup, int(5))
    """
    if method == 'iterative':
        return knapsack_iterative(items, maxweight)
    elif method == 'ilp':
        return knapsack_ilp(items, maxweight)
    else:
        raise NotImplementedError('[util_alg] knapsack method=%r' % (method,))
        #return knapsack_iterative_numpy(items, maxweight)


def knapsack_ilp(items, maxweight, verbose=False):
    """
    solves knapsack using an integer linear program

    Example:
        >>> # DISABLE_DOCTEST
        >>> import ubelt as ub
        >>> # Solve https://xkcd.com/287/
        >>> weights = [2.15, 2.75, 3.35, 3.55, 4.2, 5.8, 6.55]
        >>> values  = [2.15, 2.75, 3.35, 3.55, 4.2, 5.8, 6.55]
        >>> indices = ['mixed fruit', 'french fries', 'side salad',
        >>>            'hot wings', 'mozzarella sticks', 'sampler plate',
        >>>            'barbecue']
        >>> items = [(v, w, i) for v, w, i in zip(values, weights, indices)]
        >>> #items += [(3.95, 3.95, 'mystery plate')]
        >>> maxweight = 15.05
        >>> verbose = True
        >>> total_value, items_subset = knapsack_ilp(items, maxweight, verbose)
        >>> print('items_subset = %s' % (ub.repr2(items_subset, nl=1),))
    """
    import pulp
    # Given Input
    values  = [t[0] for t in items]
    weights = [t[1] for t in items]
    indices = [t[2] for t in items]
    # Formulate integer program
    prob = pulp.LpProblem("Knapsack", pulp.LpMaximize)
    # Solution variables
    x = pulp.LpVariable.dicts(name='x', indexs=indices,
                              lowBound=0, upBound=1, cat=pulp.LpInteger)
    # maximize objective function
    prob.objective = sum(v * x[i] for v, i in zip(values, indices))
    # subject to
    prob.add(sum(w * x[i] for w, i in zip(weights, indices)) <= maxweight)
    # Solve using with solver like CPLEX, GLPK, or SCIP.
    #pulp.CPLEX().solve(prob)
    pulp.PULP_CBC_CMD().solve(prob)
    # Read solution
    flags = [x[i].varValue for i in indices]
    total_value = sum([val for val, flag in zip(values, flags) if flag])
    items_subset = [item for item, flag in zip(items, flags) if flag]
    # Print summary
    if verbose:
        print(prob)
        print('OPT:')
        print('\n'.join(['    %s = %s' % (x[i].name, x[i].varValue) for i in indices]))
        print('total_value = %r' % (total_value,))
    return total_value, items_subset


def number_of_decimals(num):
    r"""
    Args:
        num (float):

    References:
        stackoverflow.com/questions/6189956/finding-decimal-places

    Example:
        >>> # ENABLE_DOCTEST
        >>> num = 15.05
        >>> result = number_of_decimals(num)
        >>> print(result)
        2
    """
    exp = decimal.Decimal(str(num)).as_tuple().exponent
    return max(0, -exp)


def knapsack_iterative(items, maxweight):
    # Knapsack requires integral weights
    weights = [t[1] for t in items]
    max_exp = max([number_of_decimals(w_) for w_ in weights])
    coeff = 10 ** max_exp
    # Adjust weights to be integral
    int_maxweight = int(maxweight * coeff)
    int_items = [(v, int(w * coeff), idx) for v, w, idx in items]
    """
    items = int_items
    maxweight = int_maxweight
    """
    return knapsack_iterative_int(int_items, int_maxweight)


def knapsack_iterative_int(items, maxweight):
    r"""
    Iterative knapsack method

    Math:
        maximize \sum_{i \in T} v_i
        subject to \sum_{i \in T} w_i \leq W

    Notes:
        dpmat is the dynamic programming memoization matrix.
        dpmat[i, w] is the total value of the items with weight at most W
        T is idx_subset, the set of indicies in the optimal solution

    Example:
        >>> # ENABLE_DOCTEST
        >>> weights = [1, 3, 3, 5, 2, 1] * 2
        >>> items = [(w, w, i) for i, w in enumerate(weights)]
        >>> maxweight = 10
        >>> items = [(.8, 700, 0)]
        >>> maxweight = 2000
        >>> print('maxweight = %r' % (maxweight,))
        >>> print('items = %r' % (items,))
        >>> total_value, items_subset = knapsack_iterative_int(items, maxweight)
        >>> total_weight = sum([t[1] for t in items_subset])
        >>> print('total_weight = %r' % (total_weight,))
        >>> print('items_subset = %r' % (items_subset,))
        >>> result =  'total_value = %.2f' % (total_value,)
        >>> print(result)
        total_value = 0.80

    Ignore:
        DPMAT = [[dpmat[r][c] for c in range(maxweight)] for r in range(len(items))]
        KMAT  = [[kmat[r][c] for c in range(maxweight)] for r in range(len(items))]
    """
    values  = [t[0] for t in items]
    weights = [t[1] for t in items]
    maxsize = maxweight + 1
    # Sparse representation seems better
    dpmat = defaultdict(lambda: defaultdict(lambda: np.inf))
    kmat = defaultdict(lambda: defaultdict(lambda: False))
    idx_subset = []  # NOQA
    for w in range(maxsize):
        dpmat[0][w] = 0
    # For each item consider to include it or not
    for idx in range(len(items)):
        item_val = values[idx]
        item_weight = weights[idx]
        # consider at each possible bag size
        for w in range(maxsize):
            valid_item = item_weight <= w
            if idx > 0:
                prev_val = dpmat[idx - 1][w]
                prev_noitem_val = dpmat[idx - 1][w - item_weight]
            else:
                prev_val = 0
                prev_noitem_val = 0
            withitem_val = item_val + prev_noitem_val
            more_valuable = withitem_val > prev_val
            if valid_item and more_valuable:
                dpmat[idx][w] = withitem_val
                kmat[idx][w] = True
            else:
                dpmat[idx][w] = prev_val
                kmat[idx][w] = False
    # Trace backwards to get the items used in the solution
    K = maxweight
    for idx in reversed(range(len(items))):
        if kmat[idx][K]:
            idx_subset.append(idx)
            K = K - weights[idx]
    idx_subset = sorted(idx_subset)
    items_subset = [items[i] for i in idx_subset]
    total_value = dpmat[len(items) - 1][maxweight]
    return total_value, items_subset


def knapsack_iterative_numpy(items, maxweight):
    r"""
    Iterative knapsack method

    maximize \sum_{i \in T} v_i
    subject to \sum_{i \in T} w_i \leq W

    Notes:
        dpmat is the dynamic programming memoization matrix.
        dpmat[i, w] is the total value of the items with weight at most W
        T is the set of indicies in the optimal solution
    """
    #import numpy as np
    items = np.array(items)
    weights = items.T[1]
    # Find maximum decimal place (this problem is in NP)
    max_exp = max([number_of_decimals(w_) for w_ in weights])
    coeff = 10 ** max_exp
    # Adjust weights to be integral
    weights = (weights * coeff).astype(np.int)
    values  = items.T[0]
    MAXWEIGHT = int(maxweight * coeff)
    W_SIZE = MAXWEIGHT + 1

    dpmat = np.full((len(items), W_SIZE), np.inf)
    kmat = np.full((len(items), W_SIZE), 0, dtype=np.bool)
    idx_subset = []

    for w in range(W_SIZE):
        dpmat[0][w] = 0
    for idx in range(1, len(items)):
        item_val = values[idx]
        item_weight = weights[idx]
        for w in range(W_SIZE):
            valid_item = item_weight <= w
            prev_val = dpmat[idx - 1][w]
            if valid_item:
                prev_noitem_val = dpmat[idx - 1][w - item_weight]
                withitem_val = item_val + prev_noitem_val
                more_valuable = withitem_val > prev_val
            else:
                more_valuable = False
            dpmat[idx][w] = withitem_val if more_valuable else prev_val
            kmat[idx][w] = more_valuable
    K = MAXWEIGHT
    for idx in reversed(range(1, len(items))):
        if kmat[idx, K]:
            idx_subset.append(idx)
            K = K - weights[idx]
    idx_subset = sorted(idx_subset)
    items_subset = [items[i] for i in idx_subset]
    total_value = dpmat[len(items) - 1][MAXWEIGHT]
    return total_value, items_subset


#def knapsack_all_solns(items, maxweight):
#    """
#    TODO: return all optimal solutions to the knapsack problem

#    References:
#        stackoverflow.com/questions/30554290/all-solutions-from-knapsack-dp-matrix

#    >>> items = [(1, 2, 0), (1, 3, 1), (1, 4, 2), (1, 3, 3), (1, 3, 4), (1, 5, 5), (1, 4, 6), (1, 1, 7), (1, 1, 8), (1, 3, 9)]
#    >>> weights = ut.get_list_column(items, 1)
#    >>> maxweight = 6
#    """


def knapsack_greedy(items, maxweight):
    r"""
    non-optimal greedy version of knapsack algorithm
    does not sort input. Sort the input by largest value
    first if desired.

    Args:
        `items` (tuple): is a sequence of tuples `(value, weight, id_)`, where `value`
            is a scalar and `weight` is a non-negative integer, and `id_` is an
            item identifier.

        `maxweight` (scalar):  is a non-negative integer.

    Example:
        >>> # ENABLE_DOCTEST
        >>> items = [(4, 12, 0), (2, 1, 1), (6, 4, 2), (1, 1, 3), (2, 2, 4)]
        >>> maxweight = 15
        >>> total_value, items_subset = knapsack_greedy(items, maxweight)
        >>> result =  'total_value = %r\n' % (total_value,)
        >>> result += 'items_subset = %r' % (items_subset,)
        >>> print(result)
        total_value = 7
        items_subset = [(4, 12, 0), (2, 1, 1), (1, 1, 3)]
    """
    items_subset = []
    total_weight = 0
    total_value = 0
    for item in items:
        value, weight = item[0:2]
        if total_weight + weight > maxweight:
            continue
        else:
            items_subset.append(item)
            total_weight += weight
            total_value += value
    return total_value, items_subset


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/xdev/algo.py all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

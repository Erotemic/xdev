from typing import Union
from typing import List
import numbers


def edit_distance(string1: Union[str, List[str]], string2: Union[str,
                                                                 List[str]]):
    ...


def knapsack(items: tuple,
             maxweight: numbers.Real,
             method: str = ...) -> tuple:
    ...


def knapsack_ilp(items, maxweight, verbose: bool = ...):
    ...


def number_of_decimals(num: float):
    ...


def knapsack_iterative(items, maxweight):
    ...


def knapsack_iterative_int(items, maxweight):
    ...


def knapsack_iterative_numpy(items, maxweight):
    ...


def knapsack_greedy(items, maxweight):
    ...

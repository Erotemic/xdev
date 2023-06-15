from typing import List
import numbers


def edit_distance(
        string1: str | List[str],
        string2: str | List[str]) -> float | List[float] | List[List[float]]:
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

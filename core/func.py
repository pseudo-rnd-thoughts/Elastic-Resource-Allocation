"""Additional functions"""

from __future__ import annotations
from typing import Iterable, TypeVar, Dict
from random import choice
import sys

T = TypeVar('T')


def rand_list_max(args: Iterable[T], key=None) -> T:
    """
    Finds the maximum value in a list of values, if multiple values are all equal then choice a random value
    :param args: A list of values
    :param key: The key value function
    :return: A random maximum value
    """
    solution = []
    value = None

    for arg in args:
        arg_value = arg if key is None else key(arg)

        if arg_value is None or arg_value > value:
            solution = [arg]
            value = arg_value
        elif arg_value == value:
            solution = [arg]

    return choice(solution)


def get_args() -> Dict[str, str]:
    """
    Gets all of the arguments and places in a dictionary
    :return: All of the arguments in a dictionary
    """
    return {
        'model': 'models/'+sys.argv[1],
        'jobs': sys.argv[2],
        'servers': sys.argv[3],
        'repeat': sys.argv[4]
    }


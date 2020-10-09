"""
Relaxed model with a single super server allow a upper bound to be found, solved through mixed integer programming
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

from optimal.flexible_optimal import flexible_optimal_solver
from src.core.super_server import SuperServer
from src.extra.result import Result

if TYPE_CHECKING:
    from typing import List

    from src.core.server import Server
    from src.core.task import Task


def server_relaxed_flexible_optimal(tasks: List[Task], servers: List[Server],
                                    time_limit: Optional[int] = 15) -> Optional[Result]:
    """
    Runs the relaxed task allocation solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit for the solver
    :return: Optional relaxed results
    """
    super_server = SuperServer(servers)
    model_solution = flexible_optimal_solver(tasks, [super_server], time_limit)
    if model_solution:
        return Result('Server Relaxed Flexible Optimal', tasks, [super_server],
                      round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Server Relaxed Flexible Optimal error', file=sys.stderr)
        return Result('Server Relaxed Flexible Optimal', tasks, servers, 0, limited=True)

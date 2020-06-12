"""Fixed optimal algorithm"""

from __future__ import annotations

from typing import List, Optional

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.core import print_model_solution, allocate
from src.core.fixed_task import FixedTask
from src.core.result import Result
from src.core.server import Server


def fixed_optimal_algorithm(tasks: List[FixedTask], servers: List[Server], time_limit: int) -> Optional[Result]:
    """
    Finds the optimal solution
    :param tasks: A list of tasks
    :param servers: A list of servers
    :param time_limit: The time limit to solve with
    :return: The results
    """
    assert time_limit > 0, "Time limit: {}".format(time_limit)

    model = CpoModel("vcg")

    # As no resource speeds then only assign binary variables for the allocation
    allocations = {(task, server): model.binary_var(name='{} task {} server'.format(task.name, server.name))
                   for task in tasks for server in servers}

    # Allocation constraint
    for task in tasks:
        model.add(sum(allocations[(task, server)] for server in servers) <= 1)

    # Server resource speeds constraints
    for server in servers:
        model.add(sum(task.required_storage * allocations[(task, server)]
                      for task in tasks) <= server.storage_capacity)
        model.add(sum(task.compute_speed * allocations[(task, server)]
                      for task in tasks) <= server.computation_capacity)
        model.add(sum((task.loading_speed + task.sending_speed) * allocations[(task, server)]
                      for task in tasks) <= server.bandwidth_capacity)

    # Optimisation problem
    model.maximize(sum(task.value * allocations[(task, server)] for task in tasks for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # Check that the model is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print("Fixed VCG model failure")
        print_model_solution(model_solution)
        return None

    # Allocate all of the tasks to the servers
    try:
        for task in tasks:
            for server in servers:
                if model_solution.get_value(allocations[(task, server)]):
                    allocate(task, task.loading_speed, task.compute_speed, task.sending_speed, server)
                    break
    except (KeyError, AssertionError) as e:
        print("Assertion error in fixed optimal algo: ", e)
        print_model_solution(model_solution)
        return None

    # Return the sum of the task value for all of teh running tasks
    return Result("Fixed Optimal", tasks, servers, round(model_solution.get_solve_time(), 2),
                  solve_status=model_solution.get_solve_status())

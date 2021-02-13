"""
Tests using cplex for optimal solutions with cp and mp models
"""

from __future__ import annotations

from typing import Dict, Tuple, Any

from docplex.cp.model import CpoModel, SOLVE_STATUS_OPTIMAL
from docplex.mp.model import Model

from branch_bound.branch_bound import branch_bound_algorithm
from core.core import reset_model
from core.server import Server
from core.task import Task
from extra.model import ModelDistribution
from optimal.flexible_optimal import flexible_optimal_solver, flexible_optimal


def test_cplex():
    model = CpoModel('test')
    x = model.integer_var(name='x')
    model.minimize(5 * x ** 2 - 10 * x + 1)

    solution = model.solve()
    assert solution.get_solve_status() == SOLVE_STATUS_OPTIMAL


def test_cp_optimality():
    model = ModelDistribution('models/synthetic.mdl', 20, 3)
    tasks, servers = model.generate()

    results = flexible_optimal_solver(tasks, servers, time_limit=10)
    print(results.store())


# noinspection DuplicatedCode
def test_mip_model():
    model = ModelDistribution('models/synthetic.mdl', 4, 2)
    tasks, servers = model.generate()

    model = Model('test')

    loading_speeds: Dict[Task, Any] = {}
    compute_speeds: Dict[Task, Any] = {}
    sending_speeds: Dict[Task, Any] = {}
    server_task_allocation: Dict[Tuple[Task, Server], Any] = {}

    # The maximum bandwidth and the computation that the speed can be
    max_bandwidth, max_computation = max(server.bandwidth_capacity for server in servers) - 1, \
        max(server.computation_capacity for server in servers)

    # Loop over each task to allocate the variables and add the deadline constraints
    for task in tasks:
        loading_speeds[task] = model.integer_var(lb=1, ub=max_bandwidth, name=f'{task.name} loading speed')
        compute_speeds[task] = model.integer_var(lb=1, ub=max_computation, name=f'{task.name} compute speed')
        sending_speeds[task] = model.integer_var(lb=1, ub=max_bandwidth, name=f'{task.name} sending speed')

        model.add(task.required_storage * compute_speeds[task] * sending_speeds[task] +
                  loading_speeds[task] * task.required_computation * sending_speeds[task] +
                  loading_speeds[task] * compute_speeds[task] * task.required_results_data <=
                  task.deadline * loading_speeds[task] * compute_speeds[task] * sending_speeds[task])

        # The task allocation variables and add the allocation constraint
        for server in servers:
            server_task_allocation[(task, server)] = model.binary_var(name=f'Job {task.name} Server {server.name}')
        model.add(sum(server_task_allocation[(task, server)] for server in servers) <= 1)

    # For each server, add the resource constraint
    for server in servers:
        model.add(sum(task.required_storage * server_task_allocation[(task, server)]
                      for task in tasks) <= server.storage_capacity)
        model.add(sum(compute_speeds[task] * server_task_allocation[(task, server)]
                      for task in tasks) <= server.computation_capacity)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) * server_task_allocation[(task, server)]
                      for task in tasks) <= server.bandwidth_capacity)

    # The optimisation statement
    model.maximize(sum(task.value * server_task_allocation[(task, server)] for task in tasks for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=20)
    print(f'Model solution type: {type(model_solution)}')
    print(f'Variance type: {type(loading_speeds[tasks[0]])}')


def test_branch_bound():
    model = ModelDistribution('models/synthetic.mdl', 4, 2)
    tasks, servers = model.generate()

    branch_bound_result = branch_bound_algorithm(tasks, servers, debug_update_lower_bound=True)
    branch_bound_result.pretty_print()

    reset_model(tasks, servers)

    optimal_result = flexible_optimal(tasks, servers, time_limit=200)
    optimal_result.pretty_print()

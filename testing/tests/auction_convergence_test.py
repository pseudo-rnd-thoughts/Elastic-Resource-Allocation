"""Auction Testing"""

from __future__ import annotations
from typing import List, Dict, Tuple

from core.job import Job
from core.server import Server
from core.model import reset_model

from auctions.iterative_auction import iterative_auction
from auctions.vcg import vcg_auction

import graphing.plot_model as graphing


def auction_convergence(jobs: List[Job], servers: List[Server], epsilons: List[int], debug_prices: bool = True):
    """
    Tests the auctions convergence with different epsilon values
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param epsilons: A list of epsilon values being tested
    :param debug_prices: Debugs the server prices for each epsilon
    """
    auctions_utility = {}
    auctions_price = {}

    server_prices: Dict[Tuple[Server, int], float] = {}
    job_prices: Dict[Tuple[Job, int], float] = {}

    for epsilon in epsilons:
        print("Running iterative vcg with e={}".format(epsilon))
        price, utility = iterative_auction(jobs, servers, epsilon=epsilon)

        auctions_utility[str(epsilon)] = utility
        auctions_price[str(epsilon)] = price

        for server in servers:
            server_prices[(server, epsilon)] = server.revenue
        for job in jobs:
            job_prices[(job, epsilon)] = job.price

        reset_model(jobs, servers)

    print("Running vcg")
    vcg_auction(jobs, servers, debug_running=True, debug_time=True)
    vcg_utility = sum(server.utility for server in servers)
    vcg_price = sum(server.revenue for server in servers)

    graphing.plot_auction_convergence(auctions_utility, auctions_price, vcg_utility, vcg_price)

    if debug_prices:
        print("{:<10}|{}".format("Auction", "|".join([server.name for server in servers] + [job.name for job in jobs])))
        print("{:<10}|{}".format("Actual", "|".join(["{:^{}}".format("", len(server.name))
                                                     for server in servers] +
                                                    ["{:^{}}".format(job.utility, len(job.name))
                                                     for job in jobs])))
        print("{:<10}|{}".format("VCG", "|".join(["{:^{}}".format(server.revenue, len(server.name))
                                                  for server in servers] +
                                                 ["{:^{}}".format(job.price, len(job.name))
                                                  for job in jobs])))
        for epsilon in epsilons:
            print("{:<10}|{}".format("Epsilon " + str(epsilon),
                                     "|".join(["{:^{}}".format(server_prices[(server, epsilon)], len(server.name))
                                               for server in servers] +
                                              ["{:^{}}".format(job_prices[(job, epsilon)], len(job.name))
                                               for job in jobs])))

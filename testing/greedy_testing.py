

def run_greedy(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                server_selection_policy: ServerSelectionPolicy, resource_allocation_policy: ResourceAllocationPolicy):
    """
    A basic test with a supplied value density, selection policy and bid policy functions
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The resource allocation function
    """
    result: Result = greedy_algorithm(jobs, servers, value_density, server_selection_policy, resource_allocation_policy,
                                      job_values_debug=True)
    result.print(servers)
    
def run_greedy_matrix(jobs: List[Job], servers: List[Server], value_policy: MatrixValue):
    """
    A basic test with a supplied value density, selection policy and bid policy functions
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The resource allocation function
    """
    pass  # TODO


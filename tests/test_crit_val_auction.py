

def test_critical_value():
    """
    To test the critical value action actually returns the critical values

    1. Run the critical value auction normally
    2. Record the critical values
    3. Repeat the critical value auction with each task's value set as critical value if allocated previously
    4. Assert that the price of the task is equal to the critical value from the auction
    """

    tasks, servers = load_model('tests/test.mdl')

    results = critical_value_auction(tasks, servers, )

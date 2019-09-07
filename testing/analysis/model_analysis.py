"""Model Analysis"""

from core.model import load_dist, ModelDist
from graphing import graph_model


if __name__ == "__main__":
    files = [
        '../../models/basic.model',
        '../../models/big_small.model'
    ]
    models = []

    for file in files:
        model_name, job_dist, server_dist = load_dist(file)
        model_dist = ModelDist(model_name, job_dist, 1, server_dist, 1)
        models.append(model_dist)

    # graph_model.plot_job_distribution(models)
    graph_model.plot_server_distribution(models)

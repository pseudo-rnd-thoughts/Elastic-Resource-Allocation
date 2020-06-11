
from __future__ import annotations

from enum import Enum, auto
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rc

from src.core.server import Server
from src.core.task import Task

rc('text', usetex=True)


class ImageFormat(Enum):
    """
    Image format
    """
    EPS = auto()
    PNG = auto()
    PDF = auto()
    BOTH = auto()
    NONE = auto()


def save_plot(name: str, test_folder: str, additional: str = "",
              image_format: ImageFormat = ImageFormat.NONE, lgd=None):
    """
    Saves the plot to a file of the particular image format

    :param name: The plot name
    :param test_folder: The test name
    :param additional: Additional information to add to the filename
    :param image_format: The image format
    :param lgd: The legend to be added to the plot when saved
    """
    if lgd:
        lgd = (lgd,)
    if image_format == ImageFormat.EPS:
        filename = f'{test_folder}/eps/{name}{additional}.eps'
        print("Save file location: " + filename)
        plt.savefig(filename, format='eps', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')
    elif image_format == ImageFormat.PNG:
        filename = f'{test_folder}/png/{name}{additional}.png'
        print("Save file location: " + filename)
        plt.savefig(filename, format='png', bbox_extra_artists=lgd, bbox_inches='tight')
    elif image_format == ImageFormat.BOTH:
        save_plot(name, test_folder, additional, ImageFormat.EPS, lgd)
        save_plot(name, test_folder, additional, ImageFormat.PNG, lgd)
    elif image_format == ImageFormat.PDF:
        filename = f'{test_folder}/eps/{name}{additional}.pdf'
        print("Save file location: " + filename)
        plt.savefig(filename, format='pdf')


def plot_allocation_results(tasks: List[Task], servers: List[Server], title: str,
                            save_format: ImageFormat = ImageFormat.NONE):
    """
    Plots the allocation results

    :param tasks: List of tasks
    :param servers: List of servers
    :param title: Title for the graph
    :param save_format: Save format
    """
    allocated_tasks = [task for task in tasks if task.running_server]
    loading_df = pd.DataFrame(
        [[task.required_storage / server.storage_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    compute_df = pd.DataFrame(
        [[task.compute_speed / server.computation_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    sending_df = pd.DataFrame(
        [[(task.loading_speed + task.sending_speed) / server.bandwidth_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    resources_df = [loading_df, compute_df, sending_df]

    n_col, n_ind = len(resources_df[0].columns), len(resources_df[0].index)
    hatching = '/'

    axe = plt.subplot(111)
    for resource_df in resources_df:  # for each data frame
        axe = resource_df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, 3 * n_col, n_col):
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:
                rect.set_x(rect.get_x() + 1 / float(3 + 1) * i / float(n_col) - 0.125)
                rect.set_hatch(hatching * int(i / n_col))
                rect.set_width(1 / float(3 + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(3 + 1)) / 2. - 0.125)
    axe.set_xticklabels(resources_df[0].index, rotation=0)
    axe.set_xlabel(r'\textbf{Servers}', fontsize=12)

    axe.set_ylabel(r'\textbf{Resource Usage}', fontsize=12)
    axe.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    axe.set_yticklabels([r'0\%', r'20\%', r'40\%', r'60\%', r'80\%', r'100\%'])

    axe.set_title(title, fontsize=18)

    pos = -0.1 if sum(task.running_server is not None for task in tasks) else 0.0
    server_resources_legend = [axe.bar(0, 0, color="gray", hatch=hatching * i) for i in range(3)]
    tasks_legend = axe.legend(h[:n_col], _l[:n_col], loc=[1.025, pos + 0.325], title=r'\textbf{Tasks}')
    plt.legend(server_resources_legend, ['Storage', 'Computation', 'Bandwidth'],
               loc=[1.025, pos], title=r'\textbf{Server resources}')
    axe.add_artist(tasks_legend)

    save_plot(title.lower().replace(" ", "_"), "./figures/allocation", image_format=save_format)
    plt.show()

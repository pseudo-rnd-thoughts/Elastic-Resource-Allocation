
from __future__ import annotations

from enum import Enum, auto
from typing import List

import matplotlib.pyplot as plt
from matplotlib import rc
import numpy as np
import pandas as pd

from src.core.core import analysis_filename
from src.core.task import Task
from src.core.server import Server

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


def plot_allocation_results(jobs: List[Task], servers: List[Server], title: str,
                            save_format: ImageFormat = ImageFormat.NONE):
    """
    Plots the allocation results

    :param jobs: List of jobs
    :param servers: List of servers
    :param title: Title for the graph
    :param save_format: Save format
    """
    allocated_jobs = [job for job in jobs if job.running_server]
    loading_df = pd.DataFrame(
        [[job.required_storage / server.storage_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
    compute_df = pd.DataFrame(
        [[job.compute_speed / server.computation_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
    sending_df = pd.DataFrame(
        [[(job.loading_speed + job.sending_speed) / server.bandwidth_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
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
    axe.set_yticklabels(['0\\%', '20\\%', '40\\%', '60\\%', '80\\%', '100\\%'])

    axe.set_title(title, fontsize=18)

    server_resources_legend = [axe.bar(0, 0, color="gray", hatch=hatching * i) for i in range(3)]
    tasks_legend = axe.legend(h[:n_col], _l[:n_col], loc=[1.025, 0.35], title=r'\textbf{Tasks}')
    plt.legend(server_resources_legend, ['Storage', 'Computation', 'Bandwidth'],
               loc=[1.025, 0.05], title=r'\textbf{Server resources}')
    axe.add_artist(tasks_legend)

    save_plot(analysis_filename("allocation", title.lower().replace(" ", "_")), "./figures/allocation",
              image_format=save_format)
    plt.show()

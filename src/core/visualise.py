
from __future__ import annotations

from enum import Enum, auto
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.core.core import analysis_filename
from src.core.job import Job
from src.core.server import Server


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


def plot_allocation_results(jobs: List[Job], servers: List[Server], title: str,
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
    resource_df = [loading_df, compute_df, sending_df]

    hatching = '/'

    n_col = len(resource_df[0].columns)
    n_ind = len(resource_df[0].index)
    axe = plt.subplot(111)

    for df in resource_df:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)  # make bar plots

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, 3 * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(3 + 1) * i / float(n_col))
                rect.set_hatch(hatching * int(i / n_col))  # edited part
                rect.set_width(1 / float(3 + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(3 + 1)) / 2.)
    axe.set_xticklabels(resource_df[0].index, rotation=0)
    axe.set_title(title)
    axe.set_xlabel("Servers")
    axe.set_ylabel("Resource usage (%)")

    # Add invisible data to add another legend
    n = []
    for i in range(3):
        n.append(axe.bar(0, 0, color="gray", hatch=hatching * i))

    l1 = axe.legend(h[:n_col], _l[:n_col], loc=[1.01, 0.25], title='Tasks')
    plt.legend(n, ['Storage', 'Computation', 'Bandwidth'], loc=[1.01, 0.05], title='Server resources')
    axe.add_artist(l1)

    save_plot(analysis_filename("allocation", title.lower().replace(" ", "_")), "./figures/allocation",
              image_format=save_format)
    plt.show()

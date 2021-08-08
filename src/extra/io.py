"""
Input/Output functions
"""

import argparse
import datetime as dt
from enum import auto, Enum
from typing import Iterable

import matplotlib.pyplot as plt

from src.extra.model import ModelDist


class ImageFormat(Enum):
    """
    Image format
    """
    EPS = auto()
    PNG = auto()
    PDF = auto()


def save_plot(name: str, folder: str = 'figs', additional: str = '', lgd=None, dpi=1000,
              image_formats: Iterable[ImageFormat] = (ImageFormat.EPS, ImageFormat.PNG, ImageFormat.PDF)):
    """
    Saves the plot to a file of the particular image format

    :param name: The plot name
    :param folder: The save folder name
    :param additional: Additional information to add to the filename
    :param image_formats: The image format list
    :param lgd: The legend to be added to the plot when saved
    :param dpi: The dpi of the images
    """
    if lgd:
        lgd = (lgd,)

    for image_format in image_formats:
        if image_format == ImageFormat.EPS:
            filename = f'{folder}/eps/{name}{additional}.eps'
            print(f"Save file location: {filename}")
            plt.savefig(filename, format='eps', dpi=dpi, bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PNG:
            filename = f'{folder}/png/{name}{additional}.png'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='png', dpi=dpi, bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PDF:
            filename = f'{folder}/pdf/{name}{additional}.pdf'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='pdf', dpi=dpi, bbox_extra_artists=lgd, bbox_inches='tight')


def results_filename(test_name: str, model_dist: ModelDist, save_date: bool = True) -> str:
    """
    Generates the save filename for testing results

    :param test_name: The test name
    :param model_dist: The model distribution
    :param save_date: If to save the date
    :return: The concatenation of the test name, model distribution name and the repeat
    """
    extra_info = (f'_t{model_dist.num_tasks}' if model_dist.num_tasks is not None else '') + \
                 (f'_s{model_dist.num_servers}' if model_dist.num_servers is not None else '') + \
                 (f'_dt{dt.datetime.now().strftime("%m-%d_%H-%M-%S")}' if save_date else '')
    return f'{test_name}_{model_dist.name}{extra_info}.json'


def parse_args() -> argparse.Namespace:
    """
    Gets all of the arguments and places in a dictionary

    :return: Return the parsed arguments
    """
    parser = argparse.ArgumentParser(description='Process model arguments')
    parser.add_argument('-m', '--model', help='Location of the model file', default='synthetic')
    parser.add_argument('-t', '--tasks', help='Number of tasks', default=None)
    parser.add_argument('-s', '--servers', help='Number of servers', default=None)
    parser.add_argument('-e', '--extra', help='Extra information to pass to the script', default='')

    args = parser.parse_args()

    args.tasks = None if args.tasks == ' ' or args.tasks == '' or args.tasks is None else int(args.tasks)
    args.servers = None if args.servers == ' ' or args.servers == '' or args.servers is None else int(args.servers)

    if args.extra == ' ':
        args.extra = ''

    return args

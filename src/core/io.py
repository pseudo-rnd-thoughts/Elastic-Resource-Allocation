"""
Input/Output functions
"""

import re
import sys
from enum import auto, Enum
from typing import Iterable, Tuple, Union, Dict

import matplotlib.pyplot as plt


class ImageFormat(Enum):
    """
    Image format
    """
    EPS = auto()
    PNG = auto()
    PDF = auto()


def save_plot(name: str, test_name: str, additional: str = '',
              image_formats: Iterable[ImageFormat] = (), lgd=None):
    """
    Saves the plot to a file of the particular image format

    :param name: The plot name
    :param test_name: The test name
    :param additional: Additional information to add to the filename
    :param image_formats: The image format list
    :param lgd: The legend to be added to the plot when saved
    """
    if lgd:
        lgd = (lgd,)

    for image_format in image_formats:
        if image_format == ImageFormat.EPS:
            filename = f'../figures/{test_name}/eps/{name}{additional}.eps'
            print(f"Save file location: {filename}")
            plt.savefig(filename, format='eps', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PNG:
            filename = f'../figures/{test_name}/png/{name}{additional}.png'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='png', bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PDF:
            filename = f'../figures/{test_name}/eps/{name}{additional}.pdf'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='pdf', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')


# noinspection LongLine
def decode_filename(folder: str, filename: str) -> Tuple[str, str, str]:
    """
    Decodes the filename to recover the file location, the model name and the greedy name

    :param folder: The data folder
    :param filename: The encoded filename
    :return: Tuple of the location of the file and the model type
    """
    return f'../results/{folder}/{filename}.json', \
           re.findall(r'j\d+_s\d+', filename)[0].replace('_', ' ').replace('s', 'Servers: ').replace('t', 'Tasks: '), \
           filename.replace(re.findall(r'_j\d+_s\d+_\d+', filename)[0], '')


def analysis_filename(test_name: str, axis: str) -> str:
    """
    Generates the save filename for Analysis plot results

    :param test_name: The test name
    :param axis: The axis name
    :return: The concatenation of the test name and the axis
    """
    if test_name == "":
        return axis.lower().replace(" ", "_")
    else:
        return f'{test_name}_{axis.lower().replace(" ", "_")}'


def load_args() -> Dict[str, Union[str, int]]:
    """
    Gets all of the arguments and places in a dictionary

    :return: All of the arguments in a dictionary
    """
    assert len(sys.argv) == 5, f"Args: {sys.argv}"
    assert sys.argv[2].isdigit(), f"Jobs: {sys.argv[2]}"
    assert sys.argv[3].isdigit(), f"Servers: {sys.argv[3]}"
    assert sys.argv[4].isdigit(), f"Repeat: {sys.argv[4]}"

    return {
        'model': f'models/{sys.argv[1]}.json',
        'tasks': int(sys.argv[2]),
        'servers': int(sys.argv[3]),
        'repeat': int(sys.argv[4])
    }

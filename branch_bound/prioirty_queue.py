"""Implementation of a priority queue using a binary heap"""

from __future__ import annotations

from typing import List, Generic, TypeVar

T = TypeVar('T')


class PriorityQueue(Generic[T]):
    """
    A custom binary heap for the nodes of the branch and bound algorithm
    """

    queue: List[T] = []
    size: int = 0

    def pop(self) -> T:
        """

        :return:
        """
        if self.size == 1:
            return self.queue.pop(0)

        root = self.queue[0]
        self.queue[0] = self.queue.pop(-1)

        pos = 0
        while True:
            left, right, largest = self.left(pos), self.right(pos), pos

            if left < self.size and self.queue[left] > self.queue[pos]:
                largest = left
            if right < self.size and self.queue[right] > self.queue[pos]:
                largest = right

            if largest == pos:
                break
            else:
                self.swap(pos, largest)
                pos = largest

        return root

    def push(self, data: T):
        """

        :param data:
        :return:
        """
        self.queue.append(data)
        self.size += 1

        pos = self.size - 1
        parent = self.parent(pos)
        while pos > 0 and self.queue[parent] > self.queue[pos]:  # Add custom comparison here
            self.swap(pos, parent)

            pos = parent
            parent = self.parent(pos)

    def push_all(self, data: List[T]):
        """

        :param data:
        :return:
        """
        for d in data:
            self.push(d)

    def parent(self, pos: int) -> int:
        """

        :param pos:
        :return:
        """
        return (pos - 1) // 2

    def left(self, pos: int) -> int:
        """

        :param pos:
        :return:
        """
        return 2*pos + 1

    def right(self, pos: int) -> int:
        """

        :param pos:
        :return:
        """
        return 2*pos + 2

    def swap(self, child: int, parent: int):
        """

        :param child:
        :param parent:
        :return:
        """
        temp = self.queue[child]
        self.queue[child] = self.queue[parent]
        self.queue[parent] = temp

    def __str__(self) -> str:
        """

        :return:
        """
        return ', '.join(self.queue)

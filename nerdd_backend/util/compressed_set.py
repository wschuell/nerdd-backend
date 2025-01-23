from typing import List, Optional, Tuple

__all__ = ["CompressedSet"]


def bisect(a, x, key=lambda x: x):
    """Return the index where to insert item x in list a, assuming a is sorted.

    Parameters
    ----------
    a : list
        List of items.
    x : object
        Item to insert.
    key : callable
        Function that returns the key to compare.
    """
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(a[mid]) <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


class CompressedSet:
    def __init__(self, intervals: Optional[List[Tuple[int, int]]] = None):
        if intervals is None or len(intervals) == 0:
            intervals = [(0, 0)]
        self.intervals = intervals

    def add(self, x: int) -> "CompressedSet":
        # search for tuple (left, right) with the greatest i <= x
        i = bisect(self.intervals, x, key=lambda t: t[0]) - 1
        if i < 0:
            i = 0

        left, right = self.intervals[i]

        if left <= x < right:
            # x is already part of the set
            return self
        elif x < left:
            self.intervals.insert(i, (x, x + 1))
        elif x >= right:
            self.intervals.insert(i + 1, (x, x + 1))
            i = i + 1

        # merge with previous tuple if possible
        if i > 0 and self.intervals[i - 1][1] == x:
            self.intervals[i - 1] = (self.intervals[i - 1][0], self.intervals[i][1])
            self.intervals.pop(i)
            i = i - 1

        # merge with next tuple if possible
        if i < len(self.intervals) - 1 and self.intervals[i][1] == self.intervals[i + 1][0]:
            self.intervals[i] = (self.intervals[i][0], self.intervals[i + 1][1])
            self.intervals.pop(i + 1)

        return self

    def contains(self, x: int) -> bool:
        # search for tuple (i, j) with the greatest i < x
        i = bisect(self.intervals, x, key=lambda t: t[0]) - 1
        if i < 0:
            i = 0

        left, right = self.intervals[i]

        return left <= x < right

    def count(self) -> int:
        return sum(j - i for i, j in self.intervals)

    def to_intervals(self) -> List[Tuple[int, int]]:
        return self.intervals

    def __repr__(self) -> str:
        return f"CompressedSet({self.intervals})"

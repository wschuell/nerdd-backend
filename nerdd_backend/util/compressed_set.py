from typing import List, Optional, Tuple

__all__ = ["CompressedSet"]


class CompressedSet:
    def __init__(self, intervals: Optional[List[Tuple[int, int]]] = None):
        if intervals is None or len(intervals) == 0:
            intervals = []
        # copy the list of intervals
        self.intervals = list(intervals)

    def add(self, x: int) -> "CompressedSet":
        i = 0
        while i < len(self.intervals) and self.intervals[i][0] <= x:
            i += 1
        i = max(0, i - 1)
        if i >= len(self.intervals):
            self.intervals.append((x, x + 1))
        else:
            left, right = self.intervals[i]
            if left <= x < right:
                return self
            elif x < left:
                self.intervals.insert(i, (x, x + 1))
            else:
                self.intervals.insert(i + 1, (x, x + 1))
                i += 1
        if i > 0 and self.intervals[i - 1][1] == self.intervals[i][0]:
            self.intervals[i - 1] = (self.intervals[i - 1][0], self.intervals[i][1])
            self.intervals.pop(i)
            i -= 1
        if i < len(self.intervals) - 1 and self.intervals[i][1] == self.intervals[i + 1][0]:
            self.intervals[i] = (self.intervals[i][0], self.intervals[i + 1][1])
            self.intervals.pop(i + 1)
        return self

    def count(self) -> int:
        return sum(j - i for i, j in self.intervals)

    def to_intervals(self) -> List[Tuple[int, int]]:
        return self.intervals

    def __repr__(self) -> str:
        return f"CompressedSet({self.intervals})"

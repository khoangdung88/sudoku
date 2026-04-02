from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple
import math


@dataclass(frozen=True)
class Pos:
    r: int
    c: int


class SudokuBoard:
    """Sudoku board supporting variable sizes: 4x4, 6x6, 9x9, 12x12, 16x16, 25x25, 36x36."""
    
    VALID_SIZES = {4, 6, 9, 12, 16, 25, 36}
    
    def __init__(self, grid: Optional[Sequence[Sequence[int]]] = None, *, size: int = 9) -> None:
        if size not in self.VALID_SIZES:
            raise ValueError(f"Size must be one of {self.VALID_SIZES}, got {size}")
        self._size = size
        self._box_rows, self._box_cols = self._get_box_dimensions()
        
        if grid is None:
            self._grid = [[0 for _ in range(size)] for _ in range(size)]
        else:
            if len(grid) != size or any(len(row) != size for row in grid):
                raise ValueError(f"Grid must be {size}x{size}")
            self._grid = [[int(v) for v in row] for row in grid]
            self._validate_values()

    def _get_box_dimensions(self) -> Tuple[int, int]:
        """Calculate subgrid (box) dimensions based on grid size."""
        if self._size == 4:
            return 2, 2  # 2x2 boxes
        elif self._size == 6:
            return 2, 3  # 2x3 boxes
        elif self._size == 9:
            return 3, 3  # 3x3 boxes
        elif self._size == 12:
            return 3, 4  # 3x4 boxes
        elif self._size == 16:
            return 4, 4  # 4x4 boxes
        elif self._size == 25:
            return 5, 5  # 5x5 boxes
        elif self._size == 36:
            return 6, 6  # 6x6 boxes
        return int(math.sqrt(self._size)), int(math.sqrt(self._size))

    @property
    def size(self) -> int:
        return self._size

    @property
    def box_rows(self) -> int:
        return self._box_rows

    @property
    def box_cols(self) -> int:
        return self._box_cols

    @staticmethod
    def from_string(s: str, *, size: int = 9) -> "SudokuBoard":
        s = s.strip()
        expected_len = size * size
        if len(s) != expected_len:
            raise ValueError(f"Puzzle string must be length {expected_len} for {size}x{size}")
        vals = []
        for ch in s:
            if ch in ".0":
                vals.append(0)
            elif ch.isdigit():
                v = int(ch)
                if 1 <= v <= size:
                    vals.append(v)
                else:
                    raise ValueError(f"Digit {v} out of range for {size}x{size} grid")
            else:
                raise ValueError("Invalid character in puzzle")
        grid = [vals[i * size : (i + 1) * size] for i in range(size)]
        return SudokuBoard(grid, size=size)

    def to_string(self) -> str:
        return "".join(str(self._grid[r][c]) for r in range(self._size) for c in range(self._size))

    def clone(self) -> "SudokuBoard":
        return SudokuBoard(self._grid, size=self._size)

    def get(self, r: int, c: int) -> int:
        return self._grid[r][c]

    def set(self, r: int, c: int, v: int) -> None:
        if not (0 <= v <= self._size):
            raise ValueError(f"Value must be 0..{self._size}")
        self._grid[r][c] = v

    def givens_count(self) -> int:
        return sum(1 for r in range(self._size) for c in range(self._size) if self._grid[r][c] != 0)

    def empties(self) -> List[Pos]:
        return [Pos(r, c) for r in range(self._size) for c in range(self._size) if self._grid[r][c] == 0]

    def row_values(self, r: int) -> List[int]:
        return [self._grid[r][c] for c in range(self._size) if self._grid[r][c] != 0]

    def col_values(self, c: int) -> List[int]:
        return [self._grid[r][c] for r in range(self._size) if self._grid[r][c] != 0]

    def box_values(self, r: int, c: int) -> List[int]:
        br = (r // self._box_rows) * self._box_rows
        bc = (c // self._box_cols) * self._box_cols
        out: List[int] = []
        for rr in range(br, br + self._box_rows):
            for cc in range(bc, bc + self._box_cols):
                v = self._grid[rr][cc]
                if v != 0:
                    out.append(v)
        return out

    def is_valid_placement(self, r: int, c: int, v: int) -> bool:
        if v == 0:
            return True
        if any(self._grid[r][cc] == v for cc in range(self._size) if cc != c):
            return False
        if any(self._grid[rr][c] == v for rr in range(self._size) if rr != r):
            return False
        br = (r // self._box_rows) * self._box_rows
        bc = (c // self._box_cols) * self._box_cols
        for rr in range(br, br + self._box_rows):
            for cc in range(bc, bc + self._box_cols):
                if (rr, cc) != (r, c) and self._grid[rr][cc] == v:
                    return False
        return True

    def candidates(self, r: int, c: int) -> List[int]:
        if self._grid[r][c] != 0:
            return []
        used = set(self.row_values(r)) | set(self.col_values(c)) | set(self.box_values(r, c))
        return [v for v in range(1, self._size + 1) if v not in used]

    def is_consistent(self) -> bool:
        for r in range(self._size):
            for c in range(self._size):
                v = self._grid[r][c]
                if v != 0 and not self.is_valid_placement(r, c, v):
                    return False
        for pos in self.empties():
            if len(self.candidates(pos.r, pos.c)) == 0:
                return False
        return True

    def _validate_values(self) -> None:
        for r in range(self._size):
            for c in range(self._size):
                v = self._grid[r][c]
                if not (0 <= v <= self._size):
                    raise ValueError(f"Grid values must be 0..{self._size}")
        if not self.is_consistent():
            raise ValueError("Grid is inconsistent")

    def iter_units(self) -> Iterable[List[Pos]]:
        for r in range(self._size):
            yield [Pos(r, c) for c in range(self._size)]
        for c in range(self._size):
            yield [Pos(r, c) for r in range(self._size)]
        for br in range(0, self._size, self._box_rows):
            for bc in range(0, self._size, self._box_cols):
                yield [Pos(r, c) for r in range(br, br + self._box_rows) 
                      for c in range(bc, bc + self._box_cols)]

    def values_at(self, unit: Sequence[Pos]) -> List[int]:
        return [self._grid[p.r][p.c] for p in unit]

    def __repr__(self) -> str:
        return f"SudokuBoard({self.to_string()}, size={self._size})"

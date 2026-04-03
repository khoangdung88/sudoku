from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class NBPos:
    r: int
    c: int


@dataclass
class NurikabeBoard:
    size: int
    clues: List[List[int]]

    def __post_init__(self) -> None:
        if self.size <= 0:
            raise ValueError("size must be > 0")
        if len(self.clues) != self.size or any(len(row) != self.size for row in self.clues):
            raise ValueError("clues must be size x size")

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def neighbors4(self, r: int, c: int) -> Iterable[NBPos]:
        if r > 0:
            yield NBPos(r - 1, c)
        if r + 1 < self.size:
            yield NBPos(r + 1, c)
        if c > 0:
            yield NBPos(r, c - 1)
        if c + 1 < self.size:
            yield NBPos(r, c + 1)

    def clue_positions(self) -> List[NBPos]:
        out: List[NBPos] = []
        for r in range(self.size):
            for c in range(self.size):
                if int(self.clues[r][c]) > 0:
                    out.append(NBPos(r, c))
        return out

    def to_clues_string(self) -> str:
        parts: List[str] = []
        for r in range(self.size):
            parts.append(",".join(str(int(x)) for x in self.clues[r]))
        return "\n".join(parts)

    @staticmethod
    def from_clues_string(s: str) -> "NurikabeBoard":
        rows = [ln.strip() for ln in s.splitlines() if ln.strip()]
        if not rows:
            raise ValueError("empty clues")
        grid: List[List[int]] = []
        for ln in rows:
            grid.append([int(x.strip()) for x in ln.split(",")])
        n = len(grid)
        if any(len(row) != n for row in grid):
            raise ValueError("clues must be square")
        return NurikabeBoard(size=n, clues=grid)


@dataclass
class NurikabeState:
    board: NurikabeBoard
    assign: List[List[int]]
    clue_id_at: Dict[Tuple[int, int], int]
    clue_target: List[int]

    @staticmethod
    def new(board: NurikabeBoard) -> "NurikabeState":
        clue_pos = board.clue_positions()
        clue_id_at: Dict[Tuple[int, int], int] = {}
        clue_target: List[int] = []
        for i, p in enumerate(clue_pos):
            clue_id_at[(p.r, p.c)] = i + 1
            clue_target.append(int(board.clues[p.r][p.c]))

        assign = [[0 for _ in range(board.size)] for _ in range(board.size)]
        for (r, c), cid in clue_id_at.items():
            assign[r][c] = cid

        return NurikabeState(board=board, assign=assign, clue_id_at=clue_id_at, clue_target=clue_target)

    def clone(self) -> "NurikabeState":
        return NurikabeState(
            board=self.board,
            assign=[row[:] for row in self.assign],
            clue_id_at=dict(self.clue_id_at),
            clue_target=self.clue_target[:],
        )

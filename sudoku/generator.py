from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .board import Pos, SudokuBoard
from .difficulty import Difficulty
from .solver import SudokuSolver


@dataclass(frozen=True)
class GenerateParams:
    target_difficulty: Difficulty
    seed: Optional[int] = None
    size: int = 9  # Grid size: 4, 6, 9, 12, 16


class SudokuGenerator:
    def __init__(self) -> None:
        self._solver = SudokuSolver()

    def generate_full_solution(self, *, size: int = 9, rng: random.Random) -> SudokuBoard:
        b = SudokuBoard(size=size)

        def fill() -> bool:
            empties = b.empties()
            if not empties:
                return True

            best = None
            best_cand: List[int] = []
            for p in empties:
                cand = b.candidates(p.r, p.c)
                rng.shuffle(cand)
                if best is None or len(cand) < len(best_cand):
                    best = p
                    best_cand = cand
            if best is None:
                return False

            for v in best_cand:
                if b.is_valid_placement(best.r, best.c, v):
                    b.set(best.r, best.c, v)
                    if fill():
                        return True
                    b.set(best.r, best.c, 0)
            return False

        ok = fill()
        if not ok:
            raise RuntimeError("Failed to generate full solution")
        return b

    def generate_puzzle(self, params: GenerateParams) -> Tuple[SudokuBoard, SudokuBoard]:
        size = params.size
        rng = random.Random(params.seed)
        solution = self.generate_full_solution(size=size, rng=rng)
        puzzle = solution.clone()

        # Adjust givens targets based on grid size
        if size == 4:
            if params.target_difficulty == Difficulty.EASY:
                target_min, target_max = 12, 14
            elif params.target_difficulty == Difficulty.MEDIUM:
                target_min, target_max = 9, 11
            else:
                target_min, target_max = 6, 8
        elif size == 6:
            if params.target_difficulty == Difficulty.EASY:
                target_min, target_max = 22, 26
            elif params.target_difficulty == Difficulty.MEDIUM:
                target_min, target_max = 17, 21
            else:
                target_min, target_max = 12, 16
        elif size == 9:
            if params.target_difficulty == Difficulty.EASY:
                target_min, target_max = 36, 45
            elif params.target_difficulty == Difficulty.MEDIUM:
                target_min, target_max = 30, 35
            else:
                target_min, target_max = 22, 29
        elif size == 12:
            if params.target_difficulty == Difficulty.EASY:
                target_min, target_max = 65, 75
            elif params.target_difficulty == Difficulty.MEDIUM:
                target_min, target_max = 55, 64
            else:
                target_min, target_max = 45, 54
        elif size == 16:
            if params.target_difficulty == Difficulty.EASY:
                target_min, target_max = 120, 140
            elif params.target_difficulty == Difficulty.MEDIUM:
                target_min, target_max = 100, 119
            else:
                target_min, target_max = 80, 99
        else:
            target_min, target_max = size * size // 3, size * size * 2 // 3

        positions = [Pos(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(positions)

        def current_givens() -> int:
            return puzzle.givens_count()

        removals = 0
        for p in positions:
            if current_givens() <= target_min:
                break
            old = puzzle.get(p.r, p.c)
            if old == 0:
                continue
            puzzle.set(p.r, p.c, 0)

            if not puzzle.is_consistent():
                puzzle.set(p.r, p.c, old)
                continue

            n = self._solver.count_solutions(puzzle, limit=2)
            if n != 1:
                puzzle.set(p.r, p.c, old)
                continue

            removals += 1

        if current_givens() > target_max:
            extra_positions = [p for p in positions if puzzle.get(p.r, p.c) != 0]
            rng.shuffle(extra_positions)
            for p in extra_positions:
                if current_givens() <= target_max:
                    break
                old = puzzle.get(p.r, p.c)
                puzzle.set(p.r, p.c, 0)
                if self._solver.count_solutions(puzzle, limit=2) != 1:
                    puzzle.set(p.r, p.c, old)

        return puzzle, solution

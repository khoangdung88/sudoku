from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .board import Pos, SudokuBoard


class Technique(str, Enum):
    NAKED_SINGLE = "naked_single"
    HIDDEN_SINGLE = "hidden_single"
    GUESS = "guess"


@dataclass(frozen=True)
class SolveStep:
    technique: Technique
    r: int
    c: int
    value: int


@dataclass
class SolveResult:
    solved: bool
    board: SudokuBoard
    steps: List[SolveStep]
    used_backtracking: bool


class SudokuSolver:
    def solve(self, board: SudokuBoard, *, record_steps: bool = True) -> SolveResult:
        b = board.clone()
        steps: List[SolveStep] = []

        if not b.is_consistent():
            return SolveResult(False, b, steps, False)

        used_bt = False

        def apply_logic() -> bool:
            changed = False
            while True:
                progress = False

                for pos in b.empties():
                    cand = b.candidates(pos.r, pos.c)
                    if len(cand) == 1:
                        v = cand[0]
                        b.set(pos.r, pos.c, v)
                        if record_steps:
                            steps.append(SolveStep(Technique.NAKED_SINGLE, pos.r, pos.c, v))
                        progress = True
                        changed = True
                        if not b.is_consistent():
                            return changed

                if progress:
                    continue

                cand_map: Dict[Tuple[int, int], List[int]] = {
                    (p.r, p.c): b.candidates(p.r, p.c) for p in b.empties()
                }

                hidden_progress = False
                size = b.size
                for unit in b.iter_units():
                    needed = {v: [] for v in range(1, size + 1)}
                    for p in unit:
                        if b.get(p.r, p.c) == 0:
                            for v in cand_map[(p.r, p.c)]:
                                needed[v].append(p)
                    for v, places in needed.items():
                        if len(places) == 1:
                            p = places[0]
                            b.set(p.r, p.c, v)
                            if record_steps:
                                steps.append(SolveStep(Technique.HIDDEN_SINGLE, p.r, p.c, v))
                            hidden_progress = True
                            changed = True
                            if not b.is_consistent():
                                return changed
                if hidden_progress:
                    continue

                break
            return changed

        apply_logic()

        size = b.size
        if all(b.get(r, c) != 0 for r in range(size) for c in range(size)):
            return SolveResult(True, b, steps, False)

        def backtrack() -> bool:
            nonlocal used_bt

            apply_logic()
            if not b.is_consistent():
                return False
            empties = b.empties()
            if not empties:
                return True

            best = None
            best_cand: List[int] = []
            for p in empties:
                cand = b.candidates(p.r, p.c)
                if best is None or len(cand) < len(best_cand):
                    best = p
                    best_cand = cand
                    if len(best_cand) == 1:
                        break

            if best is None or not best_cand:
                return False

            r, c = best.r, best.c
            snapshot = b.clone()
            for v in best_cand:
                used_bt = True
                b.set(r, c, v)
                if record_steps:
                    steps.append(SolveStep(Technique.GUESS, r, c, v))
                if backtrack():
                    return True
                b2 = snapshot.clone()
                b._grid = b2._grid
                if record_steps and steps:
                    if steps[-1].technique == Technique.GUESS and steps[-1].r == r and steps[-1].c == c:
                        steps.pop()
            return False

        solved = backtrack()
        return SolveResult(solved, b, steps, used_bt)

    def count_solutions(self, board: SudokuBoard, *, limit: int = 2) -> int:
        b = board.clone()
        if not b.is_consistent():
            return 0

        count = 0

        def apply_logic() -> None:
            while True:
                progress = False

                # Naked singles
                for pos in b.empties():
                    cand = b.candidates(pos.r, pos.c)
                    if len(cand) == 1:
                        b.set(pos.r, pos.c, cand[0])
                        progress = True
                        if not b.is_consistent():
                            return

                if progress:
                    continue

                # Hidden singles
                cand_map: Dict[Tuple[int, int], List[int]] = {
                    (p.r, p.c): b.candidates(p.r, p.c) for p in b.empties()
                }
                size = b.size
                for unit in b.iter_units():
                    needed = {v: [] for v in range(1, size + 1)}
                    for p in unit:
                        if b.get(p.r, p.c) == 0:
                            for v in cand_map[(p.r, p.c)]:
                                needed[v].append(p)
                    for v, places in needed.items():
                        if len(places) == 1:
                            p = places[0]
                            b.set(p.r, p.c, v)
                            progress = True
                            if not b.is_consistent():
                                return

                if not progress:
                    break

        def search() -> None:
            nonlocal count
            if count >= limit:
                return

            apply_logic()
            if not b.is_consistent():
                return

            empties = b.empties()
            if not empties:
                count += 1
                return

            best = None
            best_cand: List[int] = []
            for p in empties:
                cand = b.candidates(p.r, p.c)
                if best is None or len(cand) < len(best_cand):
                    best = p
                    best_cand = cand
                    if len(best_cand) == 1:
                        break

            if best is None or not best_cand:
                return

            r, c = best.r, best.c
            snapshot = b.clone()
            for v in best_cand:
                b.set(r, c, v)
                if b.is_consistent():
                    search()
                b2 = snapshot.clone()
                b._grid = b2._grid
                if count >= limit:
                    return

        search()
        return count

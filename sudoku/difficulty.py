from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from .board import SudokuBoard
from .solver import SolveResult, Technique


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class DifficultyInfo:
    difficulty: Difficulty
    givens: int
    used_backtracking: bool
    techniques: List[str]


class DifficultyRater:
    def rate(self, puzzle: SudokuBoard, solve_result: SolveResult) -> DifficultyInfo:
        givens = puzzle.givens_count()
        tech = [s.technique.value for s in solve_result.steps]
        used_bt = solve_result.used_backtracking

        if used_bt:
            return DifficultyInfo(Difficulty.HARD, givens, True, tech)

        has_hidden = any(t == Technique.HIDDEN_SINGLE.value for t in tech)

        if givens >= 36 and not has_hidden:
            return DifficultyInfo(Difficulty.EASY, givens, False, tech)
        if givens >= 30:
            return DifficultyInfo(Difficulty.MEDIUM, givens, False, tech)
        return DifficultyInfo(Difficulty.HARD, givens, False, tech)

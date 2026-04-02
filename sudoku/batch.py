from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .difficulty import Difficulty, DifficultyRater
from .generator import GenerateParams, SudokuGenerator
from .lessons import LessonCatalog, LessonMode
from .solver import SudokuSolver


@dataclass(frozen=True)
class BatchConfig:
    total: int
    easy_percent: int
    medium_percent: int
    hard_percent: int
    seed: Optional[int]
    lesson_mode: LessonMode
    grid_size: int = 9  # 4, 6, 9, 12, 16


@dataclass(frozen=True)
class PuzzleItem:
    puzzle: str
    solution: str
    difficulty: str
    givens: int
    techniques: List[str]
    lessons: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "puzzle": self.puzzle,
            "solution": self.solution,
            "difficulty": self.difficulty,
            "givens": self.givens,
            "techniques": self.techniques,
            "lessons": self.lessons,
        }


ProgressCb = Callable[[int, int, str], None]


class BatchManager:
    def __init__(self) -> None:
        self._gen = SudokuGenerator()
        self._solver = SudokuSolver()
        self._rater = DifficultyRater()
        self._lessons = LessonCatalog()

    def generate(
        self,
        config: BatchConfig,
        *,
        on_progress: Optional[ProgressCb] = None,
        stop_flag: Optional[Dict[str, bool]] = None,
    ) -> List[PuzzleItem]:
        if config.total <= 0:
            return []

        e = max(0, config.easy_percent)
        m = max(0, config.medium_percent)
        h = max(0, config.hard_percent)
        s = e + m + h
        if s == 0:
            e, m, h = 34, 33, 33
            s = 100
        e_n = int(round(config.total * e / s))
        m_n = int(round(config.total * m / s))
        h_n = max(0, config.total - e_n - m_n)

        plan: List[Difficulty] = [Difficulty.EASY] * e_n + [Difficulty.MEDIUM] * m_n + [Difficulty.HARD] * h_n

        out: List[PuzzleItem] = []
        base_seed = config.seed

        attempts = 0
        max_attempts = max(200, config.total * 50)

        plan_index = 0
        while len(out) < len(plan):
            if stop_flag and stop_flag.get("stop"):
                break

            if attempts >= max_attempts:
                raise RuntimeError(
                    f"Unable to generate enough puzzles: generated {len(out)}/{len(plan)} after {attempts} attempts"
                )

            diff = plan[plan_index]
            plan_index += 1

            seed = None
            if base_seed is not None:
                seed = base_seed + (attempts + 1) * 9973

            attempts += 1

            if on_progress:
                on_progress(
                    len(out),
                    len(plan),
                    f"Generating {diff.value} ({len(out) + 1}/{len(plan)}) | attempts {attempts}",
                )

            try:
                puzzle_b, sol_b = self._gen.generate_puzzle(GenerateParams(diff, seed=seed, size=config.grid_size))
                solve_res = self._solver.solve(puzzle_b, record_steps=True)
                if not solve_res.solved:
                    continue

                info = self._rater.rate(puzzle_b, solve_res)
                lessons = self._lessons.lesson_for(
                    mode=config.lesson_mode, difficulty=info.difficulty, techniques=info.techniques
                )

                out.append(
                    PuzzleItem(
                        puzzle=puzzle_b.to_string(),
                        solution=sol_b.to_string(),
                        difficulty=info.difficulty.value,
                        givens=info.givens,
                        techniques=info.techniques,
                        lessons=[{"lesson_id": l.lesson_id, "title": l.title, "body": l.body} for l in lessons],
                    )
                )
            finally:
                if plan_index >= len(plan):
                    plan_index = 0

            if on_progress:
                on_progress(len(out), len(plan), f"Done {len(out)}/{len(plan)}")

        return out

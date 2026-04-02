from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .difficulty import Difficulty


class LessonMode(str, Enum):
    A = "A"
    B = "B"
    A_PLUS_B = "A+B"


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    title: str
    body: str


class LessonCatalog:
    def __init__(self) -> None:
        self._by_diff: Dict[Difficulty, Lesson] = {
            Difficulty.EASY: Lesson(
                "level_easy",
                "Easy Sudoku",
                "Mục tiêu: luyện kỹ năng quét hàng/cột/khối và điền các ô chắc chắn. Ưu tiên tìm ô có đúng 1 ứng viên (Naked Single).",
            ),
            Difficulty.MEDIUM: Lesson(
                "level_medium",
                "Medium Sudoku",
                "Mục tiêu: kết hợp quét và suy luận. Ngoài Naked Single, hãy tìm Hidden Single trong từng hàng/cột/khối.",
            ),
            Difficulty.HARD: Lesson(
                "level_hard",
                "Hard Sudoku",
                "Mục tiêu: puzzle đòi hỏi suy luận sâu hơn. Nếu bị kẹt, hãy quay lại kiểm tra ứng viên và thử các chiến lược nâng cao.",
            ),
        }
        self._technique: Dict[str, Lesson] = {
            "naked_single": Lesson(
                "tech_naked_single",
                "Naked Single",
                "Một ô chỉ còn đúng 1 ứng viên hợp lệ. Điền ngay giá trị đó.",
            ),
            "hidden_single": Lesson(
                "tech_hidden_single",
                "Hidden Single",
                "Trong một hàng/cột/khối, có một số chỉ xuất hiện ở đúng 1 vị trí ứng viên. Điền số đó.",
            ),
            "guess": Lesson(
                "tech_guess",
                "Guess / Backtracking",
                "Khi logic cơ bản không đủ, bạn có thể thử một ứng viên và kiểm tra mâu thuẫn để quay lui.",
            ),
        }

    def lesson_for(self, *, mode: LessonMode, difficulty: Difficulty, techniques: List[str]) -> List[Lesson]:
        lessons: List[Lesson] = []

        if mode in (LessonMode.B, LessonMode.A_PLUS_B):
            lessons.append(self._by_diff[difficulty])

        if mode in (LessonMode.A, LessonMode.A_PLUS_B):
            seen = set()
            for t in techniques:
                if t in self._technique and t not in seen:
                    lessons.append(self._technique[t])
                    seen.add(t)

        return lessons

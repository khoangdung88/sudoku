from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime

from .batch import BatchConfig
from .generator import GenerateParams, SudokuGenerator
from .solver import SudokuSolver
from .difficulty import Difficulty, DifficultyRater
from .lessons import LessonCatalog, LessonMode
from .board import SudokuBoard


@dataclass
class PuzzlePoolItem:
    """Single puzzle in the pool with metadata."""
    id: str  # unique identifier
    puzzle: str  # puzzle string (e.g., "0034000...")
    solution: str  # solution string
    difficulty: str  # easy/medium/hard
    givens: int
    techniques: List[str]
    lessons: List[Dict[str, str]]
    size: int  # grid size: 4, 6, 9, 12, 16
    created_at: str
    used: bool = False
    used_in_book: Optional[str] = None  # book identifier if used
    used_at: Optional[str] = None  # timestamp when used

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "difficulty": self.difficulty,
            "givens": self.givens,
            "techniques": self.techniques,
            "lessons": self.lessons,
            "size": self.size,
            "created_at": self.created_at,
            "used": self.used,
            "used_in_book": self.used_in_book,
            "used_at": self.used_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, object]) -> "PuzzlePoolItem":
        return cls(
            id=str(d.get("id", "")),
            puzzle=str(d.get("puzzle", "")),
            solution=str(d.get("solution", "")),
            difficulty=str(d.get("difficulty", "")),
            givens=int(d.get("givens", 0)),
            techniques=list(d.get("techniques", [])),
            lessons=list(d.get("lessons", [])),
            size=int(d.get("size", 9)),
            created_at=str(d.get("created_at", "")),
            used=bool(d.get("used", False)),
            used_in_book=d.get("used_in_book"),
            used_at=d.get("used_at"),
        )


class PuzzlePool:
    """Manages a pool of pre-generated Sudoku puzzles."""

    POOL_FILENAME = "sudoku_pool.json"

    def __init__(self, base_dir: str = ".") -> None:
        self._base_dir = base_dir
        self._pool_path = os.path.join(base_dir, self.POOL_FILENAME)
        self._items: List[PuzzlePoolItem] = []
        self._load()

    def _load(self) -> None:
        """Load pool from JSON file."""
        if not os.path.exists(self._pool_path):
            self._items = []
            return
        try:
            with open(self._pool_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items_data = data.get("items", [])
            if isinstance(items_data, list):
                self._items = [PuzzlePoolItem.from_dict(d) for d in items_data]
            else:
                self._items = []
        except Exception:
            self._items = []

    def _save(self) -> None:
        """Save pool to JSON file."""
        data = {
            "version": 1,
            "last_updated": datetime.now().isoformat(),
            "items": [item.to_dict() for item in self._items],
        }
        with open(self._pool_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """Get available (unused) puzzle counts by size and difficulty.
        
        Returns: {size: {difficulty: count, "total": count}, ...}
        """
        result: Dict[str, Dict[str, int]] = {}
        for size in [4, 6, 9, 12, 16, 25, 36]:
            result[str(size)] = {"easy": 0, "medium": 0, "hard": 0, "total": 0}
        
        for item in self._items:
            if item.used:
                continue
            size_key = str(item.size)
            if size_key in result:
                result[size_key][item.difficulty] += 1
                result[size_key]["total"] += 1
        return result

    def get_available(
        self,
        size: int,
        difficulty: str,
        count: int,
        *,
        mark_used: bool = False,
        book_id: Optional[str] = None
    ) -> List[PuzzlePoolItem]:
        """Get available puzzles from pool.
        
        Args:
            size: Grid size
            difficulty: easy/medium/hard
            count: Number of puzzles needed
            mark_used: If True, mark returned puzzles as used
            book_id: Identifier for the book (required if mark_used=True)
        
        Returns:
            List of available puzzles (may be fewer than requested if pool insufficient)
        """
        available = [
            item for item in self._items
            if item.size == size 
            and item.difficulty == difficulty 
            and not item.used
        ]
        
        result = available[:count]
        
        if mark_used and result:
            now = datetime.now().isoformat()
            for item in result:
                item.used = True
                item.used_in_book = book_id
                item.used_at = now
            self._save()
        
        return result

    def add_puzzles(
        self,
        items: List[PuzzlePoolItem]
    ) -> int:
        """Add new puzzles to pool.
        
        Returns:
            Number of puzzles added
        """
        self._items.extend(items)
        self._save()
        return len(items)

    def generate_to_pool(
        self,
        size: int,
        difficulty: str,
        count: int,
        *,
        seed: Optional[int] = None,
        lesson_mode: LessonMode = LessonMode.A_PLUS_B,
        on_progress=None,
        stop_flag=None
    ) -> int:
        """Generate puzzles and add to pool.
        
        Args:
            size: Grid size
            difficulty: easy/medium/hard
            count: Number to generate
            seed: Random seed
            lesson_mode: Lesson mode for lessons
            on_progress: Progress callback (done, total, message)
            stop_flag: Stop flag dict
        
        Returns:
            Number of puzzles actually generated and added
        """
        from .difficulty import Difficulty as DiffEnum
        
        generator = SudokuGenerator()
        solver = SudokuSolver()
        rater = DifficultyRater()
        lessons = LessonCatalog()
        
        target_diff = DiffEnum(difficulty)
        added = 0
        attempts = 0
        max_attempts = max(count * 20, 100)
        
        base_seed = seed
        
        while added < count and attempts < max_attempts:
            if stop_flag and stop_flag.get("stop"):
                break
            
            attempts += 1
            
            if on_progress:
                on_progress(added, count, f"Generating {difficulty} {size}x{size} ({added+1}/{count}) | attempt {attempts}")
            
            try:
                puzzle_seed = None
                if base_seed is not None:
                    puzzle_seed = base_seed + attempts * 9973
                
                puzzle_b, sol_b = generator.generate_puzzle(
                    GenerateParams(target_diff, seed=puzzle_seed, size=size)
                )
                
                solve_res = solver.solve(puzzle_b, record_steps=True)
                if not solve_res.solved:
                    continue
                
                info = rater.rate(puzzle_b, solve_res)
                puzzle_lessons = lessons.lesson_for(
                    mode=lesson_mode, difficulty=target_diff, techniques=info.techniques
                )
                
                # Generate unique ID
                puzzle_id = f"{size}x{size}_{difficulty}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{added:05d}"
                
                item = PuzzlePoolItem(
                    id=puzzle_id,
                    puzzle=puzzle_b.to_string(),
                    solution=sol_b.to_string(),
                    difficulty=difficulty,
                    givens=info.givens,
                    techniques=info.techniques,
                    lessons=[{"lesson_id": l.lesson_id, "title": l.title, "body": l.body} for l in puzzle_lessons],
                    size=size,
                    created_at=datetime.now().isoformat(),
                    used=False,
                )
                
                self._items.append(item)
                added += 1
                
            except Exception:
                continue
        
        if added > 0:
            self._save()
        
        return added

    def reset_used(self, book_id: Optional[str] = None) -> int:
        """Reset used status of puzzles.
        
        Args:
            book_id: If specified, only reset puzzles used in that book
        
        Returns:
            Number of puzzles reset
        """
        reset_count = 0
        for item in self._items:
            if item.used:
                if book_id is None or item.used_in_book == book_id:
                    item.used = False
                    item.used_in_book = None
                    item.used_at = None
                    reset_count += 1
        
        if reset_count > 0:
            self._save()
        return reset_count

    def get_stats(self) -> Dict[str, object]:
        """Get comprehensive pool statistics."""
        total = len(self._items)
        used = sum(1 for item in self._items if item.used)
        unused = total - used
        
        by_size: Dict[str, int] = {}
        by_diff: Dict[str, int] = {}
        
        for item in self._items:
            size_key = f"{item.size}x{item.size}"
            by_size[size_key] = by_size.get(size_key, 0) + 1
            by_diff[item.difficulty] = by_diff.get(item.difficulty, 0) + 1
        
        return {
            "total": total,
            "used": used,
            "unused": unused,
            "by_size": by_size,
            "by_difficulty": by_diff,
            "file_path": self._pool_path,
        }

    def get_books(self) -> List[Dict[str, object]]:
        """Get list of all books created from pool.
        
        Returns list of dicts with book_id, created_at, puzzle count by size/difficulty.
        """
        books: Dict[str, Dict[str, object]] = {}
        
        for item in self._items:
            if item.used and item.used_in_book:
                book_id = item.used_in_book
                if book_id not in books:
                    books[book_id] = {
                        "book_id": book_id,
                        "created_at": item.used_at or "",
                        "total": 0,
                        "by_size": {},
                        "by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
                        "puzzle_ids": [],
                    }
                
                books[book_id]["total"] += 1
                books[book_id]["puzzle_ids"].append(item.id)
                
                size_key = f"{item.size}x{item.size}"
                books[book_id]["by_size"][size_key] = books[book_id]["by_size"].get(size_key, 0) + 1
                books[book_id]["by_difficulty"][item.difficulty] = books[book_id]["by_difficulty"].get(item.difficulty, 0) + 0
        
        # Sort by created_at (newest first)
        return sorted(books.values(), key=lambda x: x["created_at"], reverse=True)

    def get_puzzles_by_book(self, book_id: str) -> List[PuzzlePoolItem]:
        """Get all puzzles used in a specific book."""
        return [item for item in self._items if item.used_in_book == book_id]

    def recreate_book(self, book_id: str) -> List[PuzzlePoolItem]:
        """Prepare to recreate a book by resetting puzzles for that book.
        
        Returns the list of puzzles that were reset (to be reused).
        """
        # Capture puzzles for this book BEFORE reset_used clears used_in_book
        puzzles = self.get_puzzles_by_book(book_id)

        # Reset used status for puzzles in this book
        self.reset_used(book_id)

        # Return captured puzzles for regeneration
        return puzzles

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .board import NBPos, NurikabeBoard
from .solver import NurikabeSolver


@dataclass(frozen=True)
class NurikabePuzzle:
    size: int
    clues: List[List[int]]
    wall_mask: List[List[int]]  # 1=wall(black), 0=island(white)

    def clues_string(self) -> str:
        parts: List[str] = []
        for r in range(self.size):
            parts.append(",".join(str(int(x)) for x in self.clues[r]))
        return "\n".join(parts)

    def wall_mask_string(self) -> str:
        parts: List[str] = []
        for r in range(self.size):
            parts.append(",".join(str(int(x)) for x in self.wall_mask[r]))
        return "\n".join(parts)


class NurikabeGenerator:
    def __init__(self) -> None:
        self._solver = NurikabeSolver()

    def generate(self, *, size: int, difficulty: str, seed: Optional[int] = None, max_attempts: int = 300) -> NurikabePuzzle:
        rng = random.Random(seed)

        # Difficulty influences number of islands and clue placement aggressiveness.
        if size == 5:
            islands_range = (5, 8) if difficulty == "easy" else (6, 10) if difficulty == "medium" else (7, 12)
            island_size_range = (1, 4)
        else:
            islands_range = (8, 14) if difficulty == "easy" else (10, 17) if difficulty == "medium" else (12, 20)
            island_size_range = (1, 6)

        for _attempt in range(max_attempts):
            wall_mask = [[1 for _ in range(size)] for _ in range(size)]
            islands: List[Set[Tuple[int, int]]] = []

            num_islands = rng.randint(islands_range[0], islands_range[1])

            def neighbors4(rc: Tuple[int, int]) -> List[Tuple[int, int]]:
                r, c = rc
                out = []
                if r > 0:
                    out.append((r - 1, c))
                if r + 1 < size:
                    out.append((r + 1, c))
                if c > 0:
                    out.append((r, c - 1))
                if c + 1 < size:
                    out.append((r, c + 1))
                return out

            def touches_island_edge(rc: Tuple[int, int]) -> bool:
                r, c = rc
                for nr, nc in neighbors4((r, c)):
                    if wall_mask[nr][nc] == 0:
                        return True
                return False

            def touches_other_island_edge(rc: Tuple[int, int], island: Set[Tuple[int, int]]) -> bool:
                r, c = rc
                for nr, nc in neighbors4((r, c)):
                    if wall_mask[nr][nc] == 0 and (nr, nc) not in island:
                        return True
                return False

            def carve_island(seed_cell: Tuple[int, int], target: int) -> Optional[Set[Tuple[int, int]]]:
                if wall_mask[seed_cell[0]][seed_cell[1]] == 0:
                    return None
                if touches_island_edge(seed_cell):
                    return None

                island: Set[Tuple[int, int]] = set([seed_cell])
                wall_mask[seed_cell[0]][seed_cell[1]] = 0

                for _ in range(target - 1):
                    frontier = []
                    for cell in list(island):
                        for nb in neighbors4(cell):
                            if wall_mask[nb[0]][nb[1]] == 0:
                                continue
                            if nb in island:
                                continue
                            if touches_other_island_edge(nb, island):
                                continue
                            frontier.append(nb)
                    if not frontier:
                        return None
                    pick = rng.choice(frontier)
                    island.add(pick)
                    wall_mask[pick[0]][pick[1]] = 0
                return island

            # Carve islands
            for _i in range(num_islands):
                # Choose a seed wall cell that isn't adjacent to existing islands.
                candidates = [(r, c) for r in range(size) for c in range(size) if wall_mask[r][c] == 1 and not touches_island_edge((r, c))]
                if not candidates:
                    break
                seed_cell = rng.choice(candidates)
                target = rng.randint(island_size_range[0], island_size_range[1])
                isl = carve_island(seed_cell, target)
                if isl is None:
                    continue
                islands.append(isl)

            # Validate wall constraints: no 2x2 wall blocks and wall connected.
            if self._has_2x2_walls(wall_mask):
                continue
            if not self._wall_connected(wall_mask):
                continue

            # Build clues: one clue per island (value = island size)
            clues = [[0 for _ in range(size)] for _ in range(size)]
            for isl in islands:
                if not isl:
                    continue
                value = len(isl)
                clue_cell = self._choose_clue_cell(rng, isl, difficulty)
                clues[clue_cell[0]][clue_cell[1]] = value

            clue_n = sum(1 for r in range(size) for c in range(size) if clues[r][c] > 0)

            # Quick reject: too few clues leads to huge solver search.
            min_clues = 4 if size == 5 else 7
            if clue_n < min_clues:
                continue

            board = NurikabeBoard(size=size, clues=clues)
            # NOTE: Skipping uniqueness enforcement for performance. We still export the known
            # solution derived from the generated wall mask.

            return NurikabePuzzle(size=size, clues=clues, wall_mask=wall_mask)

        raise RuntimeError("Failed to generate Nurikabe puzzle")

    def _choose_clue_cell(self, rng: random.Random, isl: Set[Tuple[int, int]], difficulty: str) -> Tuple[int, int]:
        cells = list(isl)
        if len(cells) == 1:
            return cells[0]

        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        cr = sum(rs) / len(rs)
        cc = sum(cs) / len(cs)

        def score(cell: Tuple[int, int]) -> float:
            r, c = cell
            d_center = abs(r - cr) + abs(c - cc)
            # Easy: prefer near center; Hard: allow farther.
            if difficulty == "easy":
                return d_center
            if difficulty == "medium":
                return d_center + rng.random() * 0.5
            return d_center * 0.3 + rng.random() * 2.0

        cells.sort(key=score)
        if difficulty == "easy":
            return cells[0]
        if difficulty == "medium":
            return cells[min(1, len(cells) - 1)]
        return cells[min(2, len(cells) - 1)]

    def _has_2x2_walls(self, wall_mask: List[List[int]]) -> bool:
        n = len(wall_mask)
        for r in range(n - 1):
            for c in range(n - 1):
                if wall_mask[r][c] == 1 and wall_mask[r + 1][c] == 1 and wall_mask[r][c + 1] == 1 and wall_mask[r + 1][c + 1] == 1:
                    return True
        return False

    def _wall_connected(self, wall_mask: List[List[int]]) -> bool:
        n = len(wall_mask)
        walls = [(r, c) for r in range(n) for c in range(n) if wall_mask[r][c] == 1]
        if not walls:
            return False
        seen = set([walls[0]])
        stack = [walls[0]]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < n and 0 <= nc < n and wall_mask[nr][nc] == 1:
                    t = (nr, nc)
                    if t not in seen:
                        seen.add(t)
                        stack.append(t)
        return len(seen) == len(walls)

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .board import NBPos, NurikabeBoard, NurikabeState


@dataclass(frozen=True)
class SolveResult:
    solved: bool
    state: Optional[NurikabeState]


class NurikabeSolver:
    def count_solutions(self, board: NurikabeBoard, *, limit: int = 2) -> int:
        state = NurikabeState.new(board)
        if not self._initial_consistency(state):
            return 0
        count = 0

        def search(st: NurikabeState) -> None:
            nonlocal count
            if count >= limit:
                return
            if not self._propagate(st):
                return
            if self._is_complete(st):
                if self._is_valid_solution(st):
                    count += 1
                return

            reach = self._compute_reachability(st)
            r, c = self._select_unassigned_cell(st, reach)
            if r is None:
                return

            for val in self._domain_for_cell(st, r, c, reach):
                st2 = st.clone()
                st2.assign[r][c] = val
                search(st2)
                if count >= limit:
                    return

        search(state)
        return count

    def solve_one(self, board: NurikabeBoard) -> SolveResult:
        state = NurikabeState.new(board)
        if not self._initial_consistency(state):
            return SolveResult(False, None)

        solved_state: Optional[NurikabeState] = None

        def search(st: NurikabeState) -> bool:
            nonlocal solved_state
            if not self._propagate(st):
                return False
            if self._is_complete(st):
                if self._is_valid_solution(st):
                    solved_state = st
                    return True
                return False

            reach = self._compute_reachability(st)
            r, c = self._select_unassigned_cell(st, reach)
            if r is None:
                return False

            for val in self._domain_for_cell(st, r, c, reach):
                st2 = st.clone()
                st2.assign[r][c] = val
                if search(st2):
                    return True
            return False

        ok = search(state)
        return SolveResult(ok, solved_state)

    def _compute_reachability(self, st: NurikabeState) -> List[Set[Tuple[int, int]]]:
        reach: List[Set[Tuple[int, int]]] = [set()]
        for cid in range(1, len(st.clue_target) + 1):
            reach.append(self._reachable_cells_for_island(st, cid))
        return reach

    def _quick_checks_light(self, st: NurikabeState) -> bool:
        n = st.board.size

        for r in range(n):
            for c in range(n):
                v = st.assign[r][c]
                if v > 0:
                    for nb in st.board.neighbors4(r, c):
                        ov = st.assign[nb.r][nb.c]
                        if ov > 0 and ov != v:
                            return False

        for cid in range(1, len(st.clue_target) + 1):
            if self._island_size(st, cid) > st.clue_target[cid - 1]:
                return False

        if not self._wall_component_possible(st):
            return False

        for r in range(n - 1):
            for c in range(n - 1):
                if self._count_walls_in_block(st, r, c) == 4:
                    return False

        return True

    def _initial_consistency(self, st: NurikabeState) -> bool:
        n = st.board.size
        if len(st.clue_target) == 0:
            return False
        for (r, c), cid in st.clue_id_at.items():
            if not (1 <= cid <= len(st.clue_target)):
                return False
            if st.clue_target[cid - 1] <= 0:
                return False

        for (r, c), cid in st.clue_id_at.items():
            for nb in st.board.neighbors4(r, c):
                other = st.assign[nb.r][nb.c]
                if other > 0 and other != cid:
                    return False

        for r in range(n - 1):
            for c in range(n - 1):
                if self._count_walls_in_block(st, r, c) == 4:
                    return False

        return True

    def _propagate(self, st: NurikabeState) -> bool:
        changed = True
        while changed:
            changed = False
            reach = self._compute_reachability(st)
            if not self._quick_checks(st, reach):
                return False

            forced = self._find_forced_assignments(st)
            for (r, c), v in forced.items():
                if st.assign[r][c] != 0 and st.assign[r][c] != v:
                    return False
                if st.assign[r][c] == 0:
                    st.assign[r][c] = v
                    changed = True
        return True

    def _quick_checks(self, st: NurikabeState, reach: List[Set[Tuple[int, int]]]) -> bool:
        n = st.board.size

        for r in range(n):
            for c in range(n):
                v = st.assign[r][c]
                if v > 0:
                    for nb in st.board.neighbors4(r, c):
                        ov = st.assign[nb.r][nb.c]
                        if ov > 0 and ov != v:
                            return False

        for cid in range(1, len(st.clue_target) + 1):
            if self._island_size(st, cid) > st.clue_target[cid - 1]:
                return False

        if not self._wall_component_possible(st):
            return False

        for r in range(n - 1):
            for c in range(n - 1):
                if self._count_walls_in_block(st, r, c) == 4:
                    return False

        for cid in range(1, len(st.clue_target) + 1):
            need = st.clue_target[cid - 1] - self._island_size(st, cid)
            if need < 0:
                return False
            if need == 0:
                continue
            if len(reach[cid]) < st.clue_target[cid - 1]:
                return False

        return True

    def _find_forced_assignments(self, st: NurikabeState) -> Dict[Tuple[int, int], int]:
        n = st.board.size
        forced: Dict[Tuple[int, int], int] = {}

        for cid in range(1, len(st.clue_target) + 1):
            tgt = st.clue_target[cid - 1]
            current = self._island_size(st, cid)
            if current >= tgt:
                continue
            frontier = self._island_frontier(st, cid)
            remaining = tgt - current
            if len(frontier) == remaining:
                for (r, c) in frontier:
                    if st.assign[r][c] == 0:
                        forced[(r, c)] = cid

        return forced

    def _reachable_cells_for_island(self, st: NurikabeState, cid: int) -> Set[Tuple[int, int]]:
        n = st.board.size
        starts = [(r, c) for r in range(n) for c in range(n) if st.assign[r][c] == cid]
        if not starts:
            return set()
        seen: Set[Tuple[int, int]] = set(starts)
        q = deque(starts)
        while q:
            r, c = q.popleft()
            for nb in st.board.neighbors4(r, c):
                v = st.assign[nb.r][nb.c]
                if v == -1:
                    continue
                if v > 0 and v != cid:
                    continue
                t = (nb.r, nb.c)
                if t not in seen:
                    seen.add(t)
                    q.append(t)
        return seen

    def _island_frontier(self, st: NurikabeState, cid: int) -> Set[Tuple[int, int]]:
        n = st.board.size
        frontier: Set[Tuple[int, int]] = set()
        for r in range(n):
            for c in range(n):
                if st.assign[r][c] != cid:
                    continue
                for nb in st.board.neighbors4(r, c):
                    if st.assign[nb.r][nb.c] == 0:
                        frontier.add((nb.r, nb.c))
        return frontier

    def _wall_component_possible(self, st: NurikabeState) -> bool:
        n = st.board.size
        cells = [(r, c) for r in range(n) for c in range(n) if st.assign[r][c] <= 0]
        if not cells:
            return True
        start = cells[0]
        seen = set([start])
        q = deque([start])
        while q:
            r, c = q.popleft()
            for nb in st.board.neighbors4(r, c):
                if st.assign[nb.r][nb.c] <= 0:
                    t = (nb.r, nb.c)
                    if t not in seen:
                        seen.add(t)
                        q.append(t)
        return len(seen) == len(cells)

    def _count_walls_in_block(self, st: NurikabeState, r: int, c: int) -> int:
        cnt = 0
        for dr in (0, 1):
            for dc in (0, 1):
                if st.assign[r + dr][c + dc] == -1:
                    cnt += 1
        return cnt

    def _island_size(self, st: NurikabeState, cid: int) -> int:
        n = st.board.size
        s = 0
        for r in range(n):
            for c in range(n):
                if st.assign[r][c] == cid:
                    s += 1
        return s

    def _max_reachable_island_cells(self, st: NurikabeState, cid: int) -> int:
        n = st.board.size
        starts = [(r, c) for r in range(n) for c in range(n) if st.assign[r][c] == cid]
        if not starts:
            return 0
        seen = set(starts)
        q = deque(starts)
        while q:
            r, c = q.popleft()
            for nb in st.board.neighbors4(r, c):
                v = st.assign[nb.r][nb.c]
                if v == -1:
                    continue
                if v > 0 and v != cid:
                    continue
                t = (nb.r, nb.c)
                if t not in seen:
                    seen.add(t)
                    q.append(t)
        return len(seen)

    def _is_complete(self, st: NurikabeState) -> bool:
        n = st.board.size
        for r in range(n):
            for c in range(n):
                if st.assign[r][c] == 0:
                    return False
        return True

    def _is_valid_solution(self, st: NurikabeState) -> bool:
        reach = self._compute_reachability(st)
        if not self._quick_checks(st, reach):
            return False

        for cid in range(1, len(st.clue_target) + 1):
            if self._island_size(st, cid) != st.clue_target[cid - 1]:
                return False
            if not self._island_connected(st, cid):
                return False

        return self._wall_connected(st)

    def _island_connected(self, st: NurikabeState, cid: int) -> bool:
        n = st.board.size
        starts = [(r, c) for r in range(n) for c in range(n) if st.assign[r][c] == cid]
        if not starts:
            return False
        seen = set([starts[0]])
        q = deque([starts[0]])
        while q:
            r, c = q.popleft()
            for nb in st.board.neighbors4(r, c):
                if st.assign[nb.r][nb.c] == cid:
                    t = (nb.r, nb.c)
                    if t not in seen:
                        seen.add(t)
                        q.append(t)
        return len(seen) == len(starts)

    def _wall_connected(self, st: NurikabeState) -> bool:
        n = st.board.size
        walls = [(r, c) for r in range(n) for c in range(n) if st.assign[r][c] == -1]
        if not walls:
            return False
        seen = set([walls[0]])
        q = deque([walls[0]])
        while q:
            r, c = q.popleft()
            for nb in st.board.neighbors4(r, c):
                if st.assign[nb.r][nb.c] == -1:
                    t = (nb.r, nb.c)
                    if t not in seen:
                        seen.add(t)
                        q.append(t)
        return len(seen) == len(walls)

    def _select_unassigned_cell(self, st: NurikabeState, reach: List[Set[Tuple[int, int]]]) -> Tuple[Optional[int], Optional[int]]:
        n = st.board.size
        best = None
        best_dom = None
        for r in range(n):
            for c in range(n):
                if st.assign[r][c] != 0:
                    continue
                dom = self._domain_for_cell(st, r, c, reach)
                if not dom:
                    return (r, c)
                if best is None or len(dom) < int(best_dom or 10**9):
                    best = (r, c)
                    best_dom = len(dom)
                    if best_dom == 1:
                        return best
        if best is None:
            return (None, None)
        return best

    def _domain_for_cell(self, st: NurikabeState, r: int, c: int, reach: List[Set[Tuple[int, int]]]) -> List[int]:
        n = st.board.size
        if st.assign[r][c] != 0:
            return [st.assign[r][c]]

        dom: List[int] = []

        # Wall is always a candidate; constraints will prune if it creates 2x2 or breaks connectivity.
        dom.append(-1)

        # Island assignment: allow if reachable from that island through unknown cells without
        # crossing other islands/walls.
        for cid in range(1, len(st.clue_target) + 1):
            if self._island_size(st, cid) >= st.clue_target[cid - 1]:
                continue
            if (r, c) in reach[cid]:
                dom.append(cid)

        ordered: List[int] = []
        for v in dom:
            st.assign[r][c] = v
            ok = self._quick_checks_light(st)
            st.assign[r][c] = 0
            if ok:
                ordered.append(v)
        return ordered

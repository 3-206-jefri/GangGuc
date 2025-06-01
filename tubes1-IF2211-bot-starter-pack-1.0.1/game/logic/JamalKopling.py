from typing import Tuple, List, Optional, Dict
import math
from game.models import Board, GameObject, Position
from game.logic.base import BaseLogic

class GreedyJamalLogic(BaseLogic):
    def __init__(self):
        self.portals: List[GameObject] = []
        self.portal_map: Dict[int, GameObject] = {}

    def next_move(self, bot: GameObject, board: Board) -> Tuple[int, int]:
        pos = bot.position
        props = bot.properties

        # Muat portal sekali saja
        if not self.portals:
            self._load_portals(board)

        # 🔁 Jika bot bawa diamond & berada tepat di samping base => langsung masuk ke base
        if props.diamonds > 0 and self._adjacent(pos, props.base):
            return self._step_towards(pos, props.base)

        # Jika penuh, pulang
        if props.diamonds >= props.inventory_size:
            return self._move_to(pos, props.base, board)

        # Jika setengah penuh dan dekat base, pulang juga
        if props.diamonds >= props.inventory_size // 2:
            if self._euclidean(pos, props.base) <= 3:
                return self._move_to(pos, props.base, board)

        # Pilih diamond berdasarkan greedy
        diamond = self._choose_diamond(bot, board)
        if diamond:
            return self._move_to(pos, diamond.position, board)

        return (0, 0)

    def _load_portals(self, board: Board):
        self.portals = [obj for obj in board.game_objects if obj.type == "TeleportGameObject"]
        if len(self.portals) >= 2:
            self.portal_map = {
                self.portals[0].id: self.portals[1],
                self.portals[1].id: self.portals[0],
            }

    def _choose_diamond(self, bot: GameObject, board: Board) -> Optional[GameObject]:
        available = [d for d in board.diamonds if d.properties.pair_id is None]
        if not available:
            return None

        diamonds_by_value = sorted(available, key=lambda d: (-d.properties.points, self._euclidean(bot.position, d.position)))

        if bot.properties.diamonds < bot.properties.inventory_size // 2:
            for d in diamonds_by_value:
                if d.properties.points > 1:
                    return d

        for d in diamonds_by_value:
            if d.properties.points > 1:
                return d

        one_point_diamonds = [d for d in diamonds_by_value if d.properties.points == 1]
        return one_point_diamonds[0] if one_point_diamonds else None

    def _move_to(self, start: Position, goal: Position, board: Board) -> Tuple[int, int]:
        dx = goal.x - start.x
        dy = goal.y - start.y

        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0

        if abs(dx) >= abs(dy):
            if board.is_valid_move(start, step_x, 0):
                return (step_x, 0)
            elif step_y != 0 and board.is_valid_move(start, 0, step_y):
                return (0, step_y)
        else:
            if board.is_valid_move(start, 0, step_y):
                return (0, step_y)
            elif step_x != 0 and board.is_valid_move(start, step_x, 0):
                return (step_x, 0)

        for dx, dy in [(1,0), (0,1), (-1,0), (0,-1)]:
            if board.is_valid_move(start, dx, dy):
                return (dx, dy)

        return (0, 0)

    def _step_towards(self, src: Position, dest: Position) -> Tuple[int, int]:
        dx = dest.x - src.x
        dy = dest.y - src.y
        return (dx, dy) if self._adjacent(src, dest) else (0, 0)

    def _adjacent(self, a: Position, b: Position) -> bool:
        return abs(a.x - b.x) + abs(a.y - b.y) == 1

    def _euclidean(self, a: Position, b: Position) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

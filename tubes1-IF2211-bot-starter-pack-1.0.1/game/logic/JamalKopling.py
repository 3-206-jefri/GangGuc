from typing import Tuple, List, Optional
import math
from game.models import Board, GameObject, Position
from game.logic.base import BaseLogic

class GreedyJamalLogic(BaseLogic):
    def __init__(self): # Initialize bot properties
        self.portals: List[GameObject] = []
        self.portal_map = {}
        self.my_bot: Optional[GameObject] = None # Reference to the current bot
        self.board: Optional[Board] = None # Reference to the current game board

    def next_move(self, bot: GameObject, board: Board) -> Tuple[int, int]:
        self.my_bot = bot # Set the current bot
        self.board = board # Set the current board

        pos = bot.position
        props = bot.properties

        # Load portals if not already loaded
        if not self.portals:
            self._load_portals(board)

        # Priority 1: Immediately return home if inventory is full
        if props.diamonds >= props.inventory_size:
            print(f"Inventory full ({props.diamonds}/{props.inventory_size}). Returning home.")
            return self._go_home(pos, props.base, board)

        # Priority 2: Find and move towards a diamond
        diamond = self._select_diamond(bot, board)
        if diamond:
            print(f"Moving towards diamond at {diamond.position}")
            return self._head_to(pos, diamond.position, board)
        
        # Fallback: If no suitable diamond, stay put
        print("No suitable diamond found, staying put.")
        return (0, 0)

    def _load_portals(self, board: Board):
        """Maps portals based on objects on the board."""
        self.portals = list(filter(lambda obj: obj.type == "TeleportGameObject", board.game_objects))
        if len(self.portals) >= 2:
            first, second = self.portals[0], self.portals[1]
            self.portal_map = {first.id: second, second.id: first}

    def _go_home(self, start: Position, home: Position, board: Board) -> Tuple[int, int]:
        """Generates a move to return to base."""
        return self._path_with_portal(start, home, board)

    def _head_to(self, start: Position, destination: Position, board: Board) -> Tuple[int, int]:
        """Generates a move towards a specific destination."""
        return self._path_with_portal(start, destination, board)

    def _path_with_portal(self, start: Position, goal: Position, board: Board) -> Tuple[int, int]:
        """Calculates the best path to the goal, considering portal usage, as in MyBot."""
        for p in self.portals:
            linked = self.portal_map.get(p.id)
            if linked:
                # If using the portal leads to a shorter path overall AND
                # the bot is adjacent to the portal, then move to the portal.
                if self._manhattan(linked.position, goal) < self._manhattan(start, goal) and self._adjacent(start, p.position):
                    return self._step_towards(start, p.position)
        
        # Otherwise, proceed with a direct naive step towards the goal.
        return self._naive_step(start, goal, board)

    def _select_diamond(self, bot: GameObject, board: Board) -> Optional[GameObject]:
        """Selects a non-paired diamond, prioritizing low-point diamonds if inventory is high."""
        possible = [d for d in board.diamonds if d.properties.pair_id is None]
        
        # MyBot's specific diamond selection logic:
        # If bot has 4 or more diamonds, only consider diamonds with 1 point.
        if bot.properties.diamonds >= 4:
            possible = [d for d in possible if d.properties.points == 1]
        
        if not possible:
            return None
        
        # Always choose the closest among the 'possible' diamonds (Euclidean distance).
        return sorted(possible, key=lambda d: self._euclidean(bot.position, d.position))[0]

    def _naive_step(self, src: Position, dst: Position, board: Board) -> Tuple[int, int]:
        """Generates a one-tile step directly towards the destination, using board.is_valid_move."""
        dx = dst.x - src.x
        dy = dst.y - src.y

        # Prioritize movement along the axis with the larger absolute difference
        if abs(dx) >= abs(dy):
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            if step_x != 0 and board.is_valid_move(src, step_x, 0):
                return (step_x, 0)
            
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            if step_y != 0 and board.is_valid_move(src, 0, step_y):
                return (0, step_y)
        else:
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            if step_y != 0 and board.is_valid_move(src, 0, step_y):
                return (0, step_y)
            
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            if step_x != 0 and board.is_valid_move(src, step_x, 0):
                return (step_x, 0)

        # Fallback: Find the first legal direction using board.is_valid_move
        for move in [(1,0), (-1,0), (0,1), (0,-1)]:
            if board.is_valid_move(src, move[0], move[1]):
                return move

        return (0, 0) # Stay in place if no valid moves

    def _step_towards(self, src: Position, dest: Position) -> Tuple[int, int]:
        """Generates a one-tile step towards the destination if adjacent."""
        if not self._adjacent(src, dest):
            return (0, 0) # Do not move if not adjacent
        return (dest.x - src.x, dest.y - src.y)

    def _adjacent(self, a: Position, b: Position) -> bool:
        """Checks if two positions are adjacent (Manhattan distance 1)."""
        return abs(a.x - b.x) + abs(a.y - b.y) == 1

    def _manhattan(self, a: Position, b: Position) -> int:
        """Calculates the Manhattan distance between two positions."""
        return abs(a.x - b.x) + abs(a.y - b.y)

    def _euclidean(self, a: Position, b: Position) -> float:
        """Calculates the Euclidean distance between two positions."""
        return math.hypot(a.x - b.x, a.y - b.y)

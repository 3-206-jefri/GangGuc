from typing import Optional, List, Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position

class GreedySlametLogic(BaseLogic):
    def __init__(self):
        self.base_return_threshold = 3
        self.safe_enemy_distance = 4
        self.visited_positions = set()

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.board = board
        self.my_bot = board_bot

        time_left = self.my_bot.properties.milliseconds_left // 1000
        dist_to_base = self.distance_with_teleporter(self.my_bot.position, self.my_bot.properties.base)
        diamonds_in_inventory = self.my_bot.properties.diamonds
        inventory_size = self.my_bot.properties.inventory_size

        # Check for nearby enemies
        enemies_close = self.enemies_within_distance(self.safe_enemy_distance)

        # If enemies are too close, retreat to base
        if enemies_close and dist_to_base > 0:
            print("Enemy nearby! Retreating to base for safety.")
            return self.move_towards_base()

        # If inventory is nearly full or time is critical, return to base
        if diamonds_in_inventory >= inventory_size - self.base_return_threshold or time_left <= dist_to_base + 2:
            if diamonds_in_inventory > 0:
                print("Inventory nearly full or time short. Returning to base.")
                return self.move_towards_base()

        # Gather diamonds within an adaptive search radius
        search_radius = self.adaptive_search_radius(diamonds_in_inventory)
        nearby_diamonds = self.get_collectable_diamonds(search_radius, inventory_size - diamonds_in_inventory)

        if nearby_diamonds:
            best_diamond = self.choose_best_diamond(nearby_diamonds)
            print(f"Moving towards diamond at {best_diamond.position} worth {best_diamond.properties.points}.")
            return self.move_towards_with_teleporter(best_diamond.position)

        # No diamonds found, explore unvisited safe tiles
        print("No diamonds nearby, exploring unvisited safe area.")
        return self.explore_unvisited()

    def adaptive_search_radius(self, diamonds_in_inventory: int) -> int:
        # Increase search radius if inventory is low, decrease if full
        return 15 if diamonds_in_inventory < 3 else 10

    def enemies_within_distance(self, n: int) -> List[GameObject]:
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        close_enemies = [e for e in enemies if self.distance_with_teleporter(self.my_bot.position, e.position) <= n]
        return close_enemies

    def get_collectable_diamonds(self, radius: int, capacity_left: int) -> List[GameObject]:
        diamonds = []
        for d in self.board.diamonds:
            dist = self.distance_with_teleporter(self.my_bot.position, d.position)
            if dist <= radius and d.properties.points <= capacity_left:
                diamonds.append(d)
        return diamonds

    def choose_best_diamond(self, diamonds: List[GameObject]) -> GameObject:
        # Sort by diamond points descending, then by distance ascending
        diamonds_sorted = sorted(
            diamonds,
            key=lambda d: (-d.properties.points, self.distance_with_teleporter(self.my_bot.position, d.position))
        )
        return diamonds_sorted[0]

    def explore_unvisited(self) -> Tuple[int, int]:
        # Explore unvisited tiles that are safe
        candidate_tiles = self.get_adjacent_positions(self.my_bot.position)
        safe_tiles = []

        for tile in candidate_tiles:
            if (tile.x, tile.y) not in self.visited_positions and self.is_safe(tile):
                safe_tiles.append(tile)

        if not safe_tiles:
            return self.move_towards_base()

        # Move to the first unvisited safe tile
        best_tile = safe_tiles[0]
        self.visited_positions.add((best_tile.x, best_tile.y))
        print(f"Exploring unvisited safe area towards {best_tile}")
        return self.move_towards_with_teleporter(best_tile)

    def is_safe(self, tile: Position) -> bool:
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        return all(self.distance_with_teleporter(tile, e.position) > self.safe_enemy_distance for e in enemies)

    def get_adjacent_positions(self, pos: Position) -> List[Position]:
        candidates = [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1)
        ]
        valid_positions = [p for p in candidates if 0 <= p.x < self.board.height and 0 <= p.y < self.board.width]
        return valid_positions

    def distance(self, a: Position, b: Position) -> int:
        return abs(a.x - b.x) + abs(a.y - b.y)

    def distance_with_teleporter(self, a: Position, b: Position) -> int:
        tele1, tele2 = self.get_teleporters()
        if not tele1 or not tele2:
            return self.distance(a, b)

        direct_distance = self.distance(a, b)
        tele_distance_1 = self.distance(a, tele1.position) + self.distance(tele2.position, b)
        tele_distance_2 = self.distance(a, tele2.position) + self.distance(tele1.position, b)
        return min(direct_distance, tele_distance_1, tele_distance_2)

    def move_towards(self, target: Position) -> Tuple[int, int]:
        delta_x = target.x - self.my_bot.position.x
        delta_y = target.y - self.my_bot.position.y
        if abs(delta_x) > abs(delta_y):
            step = (1 if delta_x > 0 else -1, 0)
        else:
            step = (0, 1 if delta_y > 0 else -1)

        new_x = self.my_bot.position.x + step[0]
        new_y = self.my_bot.position.y + step[1]

        if 0 <= new_x < self.board.height and 0 <= new_y < self.board.width:
            return step
        else:
            # Reverse if out of bounds
            return (-step[0], -step[1])

    def move_towards_with_teleporter(self, dest: Position) -> Tuple[int, int]:
        dist_direct = self.distance(self.my_bot.position, dest)
        dist_tele = self.distance_with_teleporter(self.my_bot.position, dest)

        if dist_tele < dist_direct:
            tele = self.get_closer_teleporter()
            if tele:
                return self.move_towards(tele.position)
        return self.move_towards(dest)

    def move_towards_base(self) -> Tuple[int, int]:
        return self.move_towards_with_teleporter(self.my_bot.properties.base)

    def get_teleporters(self) -> Tuple[Optional[GameObject], Optional[GameObject]]:
        teleporters = [obj for obj in self.board.game_objects if obj.type == "TeleportGameObject"]
        if len(teleporters) == 2:
            return teleporters[0], teleporters[1]
        return None, None

    def get_closer_teleporter(self) -> Optional[GameObject]:
        tele1, tele2 = self.get_teleporters()
        if not tele1 or not tele2:
            return None
        dist1 = self.distance(self.my_bot.position, tele1.position)
        dist2 = self.distance(self.my_bot.position, tele2.position)
        return tele1 if dist1 < dist2 else tele2

from typing import Optional, List, Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position

class GreedyJamalLogic(BaseLogic):

    def __init__(self):
        self.search_radius = 15
        self.safe_return_margin = 3
        self.safe_enemy_distance = 4
        self.visited_positions = set()
        self.tackle_distance = 2
        self.min_diamonds_to_tackle = 3

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.board = board
        self.my_bot = board_bot

        time_left = self.my_bot.properties.milliseconds_left // 1000
        dist_to_base = self.distance_with_teleporter(self.my_bot.position, self.my_bot.properties.base)
        diamonds_in_inventory = self.my_bot.properties.diamonds
        inventory_size = self.my_bot.properties.inventory_size

        # Check for tackle opportunities first
        tackle_target = self.should_tackle()
        if tackle_target:
            print(f"Attempting to tackle enemy at {tackle_target.position}")
            return self.tackle(tackle_target)

        enemies_close = self.enemies_within_distance(self.safe_enemy_distance)

        # If enemies too close and we can't tackle, retreat to base
        if enemies_close and dist_to_base > 0:
            print("Enemy nearby! Retreating to base for safety.")
            return self.move_towards_base()

        # Return to base if almost full or time critical
        if diamonds_in_inventory >= inventory_size - 1 or time_left <= dist_to_base + self.safe_return_margin:
            if diamonds_in_inventory > 0:
                print("Inventory nearly full or time short. Returning to base.")
                return self.move_towards_base()

        # Gather diamonds with improved selection
        nearby_diamonds = self.get_collectable_diamonds(self.search_radius, inventory_size - diamonds_in_inventory)
        if nearby_diamonds:
            best_diamond = self.choose_best_diamond_improved(nearby_diamonds)
            print(f"Moving towards diamond at {best_diamond.position} worth {best_diamond.properties.points}.")
            return self.move_towards_with_teleporter(best_diamond.position)

        # No diamonds found, explore strategically
        print("No diamonds nearby, exploring strategically.")
        return self.explore_strategically()

    def should_tackle(self) -> Optional[GameObject]:
        """Determine if we should tackle an enemy based on strategic conditions"""
        if self.my_bot.properties.diamonds < self.min_diamonds_to_tackle:
            return None
            
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        
        for enemy in enemies:
            distance = self.distance_with_teleporter(self.my_bot.position, enemy.position)
            
            # Only tackle if enemy is close and has significant diamonds
            if (distance <= self.tackle_distance and 
                enemy.properties.diamonds >= self.min_diamonds_to_tackle):
                
                # Additional check: make sure we're not too far from base
                base_dist = self.distance_with_teleporter(self.my_bot.position, self.my_bot.properties.base)
                if base_dist <= 10:  # Only tackle if relatively close to base
                    return enemy
        
        return None

    def tackle(self, target: GameObject) -> Tuple[int, int]:
        """Move towards enemy to tackle them"""
        return self.move_towards_with_teleporter(target.position)

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

    def choose_best_diamond_improved(self, diamonds: List[GameObject]) -> GameObject:
        """Improved diamond selection considering safety and efficiency"""
        scored_diamonds = []
        
        for diamond in diamonds:
            distance = self.distance_with_teleporter(self.my_bot.position, diamond.position)
            points = diamond.properties.points
            
            # Calculate safety score (distance from enemies)
            enemies = [bot for bot in self.board.bots if bot != self.my_bot]
            min_enemy_dist = min([self.distance_with_teleporter(diamond.position, e.position) 
                                 for e in enemies], default=100)
            
            # Score formula: prioritize points, minimize distance, maximize safety
            efficiency_score = points / max(1, distance)  # Points per distance unit
            safety_score = min(min_enemy_dist, 10)  # Cap safety bonus
            
            total_score = efficiency_score + (safety_score * 0.2)
            scored_diamonds.append((diamond, total_score))
        
        # Return diamond with highest score
        return max(scored_diamonds, key=lambda x: x[1])[0]

    def explore_strategically(self) -> Tuple[int, int]:
        """Strategic exploration towards diamond-rich areas"""
        center = Position(self.board.height // 2, self.board.width // 2)
        candidate_tiles = self.get_extended_positions(self.my_bot.position, 2)
        
        safe_tiles = []
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        
        for tile in candidate_tiles:
            # Check safety
            min_enemy_dist = min([self.distance_with_teleporter(tile, e.position) 
                                 for e in enemies], default=100)
            
            if (min_enemy_dist > self.safe_enemy_distance and 
                (tile.x, tile.y) not in self.visited_positions):
                
                # Score based on distance to center and potential diamond areas
                center_dist = self.distance_with_teleporter(tile, center)
                exploration_score = min_enemy_dist - (center_dist * 0.1)
                
                safe_tiles.append((tile, exploration_score))

        if not safe_tiles:
            return self.move_towards_base()

        # Pick tile with best exploration score
        best_tile = max(safe_tiles, key=lambda t: t[1])[0]
        self.visited_positions.add((best_tile.x, best_tile.y))
        print(f"Exploring strategically towards {best_tile}")
        return self.move_towards_with_teleporter(best_tile)

    def get_extended_positions(self, pos: Position, radius: int) -> List[Position]:
        """Get positions within a certain radius"""
        positions = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                new_pos = Position(pos.x + dx, pos.y + dy)
                if (0 <= new_pos.x < self.board.height and 
                    0 <= new_pos.y < self.board.width):
                    positions.append(new_pos)
        return positions

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

from typing import Optional, List, Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position

class GreedySlametLogic(BaseLogic):
    def __init__(self):
        self.base_return_threshold = 2
        self.safe_enemy_distance = 5
        self.visited_positions = set()
        self.tackle_distance = 2
        self.min_diamonds_to_tackle = 2
        self.aggressive_mode_threshold = 5

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.board = board
        self.my_bot = board_bot

        time_left = self.my_bot.properties.milliseconds_left // 1000
        dist_to_base = self.distance_with_teleporter(self.my_bot.position, self.my_bot.properties.base)
        diamonds_in_inventory = self.my_bot.properties.diamonds
        inventory_size = self.my_bot.properties.inventory_size

        # Determine if we should be aggressive based on diamonds collected
        is_aggressive = diamonds_in_inventory >= self.aggressive_mode_threshold

        # Check for tackle opportunities
        tackle_target = self.should_tackle(is_aggressive)
        if tackle_target:
            print(f"Attempting to tackle enemy at {tackle_target.position}")
            return self.tackle(tackle_target)

        # Adjust safe distance based on mode
        current_safe_distance = self.safe_enemy_distance if not is_aggressive else 3
        enemies_close = self.enemies_within_distance(current_safe_distance)

        # If enemies are too close and we can't tackle, retreat to base
        if enemies_close and dist_to_base > 0 and not is_aggressive:
            print("Enemy nearby! Retreating to base for safety.")
            return self.move_towards_base()

        # If inventory is nearly full or time is critical, return to base
        if (diamonds_in_inventory >= inventory_size - self.base_return_threshold or 
            time_left <= dist_to_base + 3):
            if diamonds_in_inventory > 0:
                print("Inventory nearly full or time short. Returning to base.")
                return self.move_towards_base()

        # Gather diamonds with adaptive search
        search_radius = self.adaptive_search_radius(diamonds_in_inventory, is_aggressive)
        nearby_diamonds = self.get_collectable_diamonds(search_radius, inventory_size - diamonds_in_inventory)

        if nearby_diamonds:
            best_diamond = self.choose_best_diamond_advanced(nearby_diamonds, is_aggressive)
            print(f"Moving towards diamond at {best_diamond.position} worth {best_diamond.properties.points}.")
            return self.move_towards_with_teleporter(best_diamond.position)

        # No diamonds found, explore intelligently
        print("No diamonds nearby, exploring intelligently.")
        return self.explore_intelligently(is_aggressive)

    def should_tackle(self, is_aggressive: bool) -> Optional[GameObject]:
        """Determine if we should tackle an enemy"""
        if self.my_bot.properties.diamonds < self.min_diamonds_to_tackle:
            return None
            
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        best_target = None
        best_score = 0
        
        for enemy in enemies:
            distance = self.distance_with_teleporter(self.my_bot.position, enemy.position)
            
            # Calculate tackle score
            if distance <= self.tackle_distance:
                enemy_diamonds = enemy.properties.diamonds
                base_dist = self.distance_with_teleporter(enemy.position, self.my_bot.properties.base)
                
                # Score: more diamonds = better, closer to our base = better
                tackle_score = enemy_diamonds - (base_dist * 0.1)
                
                # In aggressive mode or if enemy has many diamonds
                if (is_aggressive and enemy_diamonds >= 2) or enemy_diamonds >= 4:
                    if tackle_score > best_score:
                        best_score = tackle_score
                        best_target = enemy
        
        return best_target

    def tackle(self, target: GameObject) -> Tuple[int, int]:
        """Move towards enemy to tackle them"""
        return self.move_towards_with_teleporter(target.position)

    def adaptive_search_radius(self, diamonds_in_inventory: int, is_aggressive: bool) -> int:
        """Dynamic search radius based on inventory and mode"""
        base_radius = 18 if diamonds_in_inventory < 2 else 12
        
        # Increase radius in aggressive mode for better opportunities
        if is_aggressive:
            base_radius += 3
            
        return base_radius

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

    def choose_best_diamond_advanced(self, diamonds: List[GameObject], is_aggressive: bool) -> GameObject:
        """Advanced diamond selection with risk assessment"""
        scored_diamonds = []
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        
        for diamond in diamonds:
            distance = self.distance_with_teleporter(self.my_bot.position, diamond.position)
            points = diamond.properties.points
            
            # Calculate risk (proximity to enemies)
            min_enemy_dist = min([self.distance_with_teleporter(diamond.position, e.position) 
                                 for e in enemies], default=100)
            
            # Base score: points per distance
            efficiency = points / max(1, distance)
            
            # Risk factor
            if is_aggressive:
                # In aggressive mode, take more risks for high value diamonds
                risk_penalty = 0 if min_enemy_dist >= 2 else (3 - min_enemy_dist) * 0.3
            else:
                # In safe mode, heavily penalize risky diamonds
                risk_penalty = 0 if min_enemy_dist >= 4 else (5 - min_enemy_dist) * 0.8
            
            # Bonus for high-value diamonds
            value_bonus = 0.5 if points >= 3 else 0
            
            total_score = efficiency + value_bonus - risk_penalty
            scored_diamonds.append((diamond, total_score))
        
        return max(scored_diamonds, key=lambda x: x[1])[0]

    def explore_intelligently(self, is_aggressive: bool) -> Tuple[int, int]:
        """Intelligent exploration considering board coverage and diamond likelihood"""
        candidate_tiles = self.get_smart_exploration_tiles()
        
        if not candidate_tiles:
            return self.move_towards_base()
        
        safe_tiles = []
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        
        for tile in candidate_tiles:
            min_enemy_dist = min([self.distance_with_teleporter(tile, e.position) 
                                 for e in enemies], default=100)
            
            safe_distance = 3 if is_aggressive else self.safe_enemy_distance
            
            if (min_enemy_dist > safe_distance and 
                (tile.x, tile.y) not in self.visited_positions):
                
                # Score exploration candidates
                center = Position(self.board.height // 2, self.board.width // 2)
                center_proximity = 10 - self.distance_with_teleporter(tile, center)
                
                # Prefer unexplored corners and edges for diamonds
                edge_bonus = 2 if (tile.x <= 2 or tile.x >= self.board.height-3 or 
                                  tile.y <= 2 or tile.y >= self.board.width-3) else 0
                
                exploration_score = min_enemy_dist + center_proximity + edge_bonus
                safe_tiles.append((tile, exploration_score))

        if not safe_tiles:
            return self.move_towards_base()

        best_tile = max(safe_tiles, key=lambda t: t[1])[0]
        self.visited_positions.add((best_tile.x, best_tile.y))
        print(f"Exploring intelligently towards {best_tile}")
        return self.move_towards_with_teleporter(best_tile)

    def get_smart_exploration_tiles(self) -> List[Position]:
        """Get strategic exploration positions"""
        positions = []
        current_pos = self.my_bot.position
        
        # Get positions in expanding circles
        for radius in range(1, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only perimeter
                        new_pos = Position(current_pos.x + dx, current_pos.y + dy)
                        if (0 <= new_pos.x < self.board.height and 
                            0 <= new_pos.y < self.board.width):
                            positions.append(new_pos)
        
        return positions

    def is_safe(self, tile: Position, safe_distance: int = None) -> bool:
        if safe_distance is None:
            safe_distance = self.safe_enemy_distance
            
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        return all(self.distance_with_teleporter(tile, e.position) > safe_distance for e in enemies)

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

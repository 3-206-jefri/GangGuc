from typing import Optional, List, Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position

class GreedySlametLogic(BaseLogic):
    def __init__(self):
        self.base_return_threshold = 3
        self.safe_enemy_distance = 4
        self.visited_positions = set()
        self.last_move = (0, 0)  # Track last move to prevent oscillation
        self.stuck_counter = 0   # Counter for when bot is stuck

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.board = board
        self.my_bot = board_bot

        time_left = self.my_bot.properties.milliseconds_left // 1000
        dist_to_base = self.distance_with_teleporter(self.my_bot.position, self.my_bot.properties.base)
        diamonds_in_inventory = self.my_bot.properties.diamonds
        inventory_size = self.my_bot.properties.inventory_size

        # Check for nearby enemies
        enemies_close = self.enemies_within_distance(self.safe_enemy_distance)

        # If enemies are too close, attempt to tackle or retreat
        if enemies_close and dist_to_base > 0:
            tackle_move = self.attempt_tackle(enemies_close)
            if tackle_move:
                print(f"Tackling enemy at {tackle_move}")
                self.reset_stuck_counter()
                return tackle_move
            
            print("Enemy nearby! Finding safe retreat path.")
            retreat_move = self.safe_retreat()
            if retreat_move != (0, 0):
                self.reset_stuck_counter()
                return retreat_move

        # If inventory is nearly full or time is critical, return to base
        if diamonds_in_inventory >= inventory_size - self.base_return_threshold or time_left <= dist_to_base + 2:
            if diamonds_in_inventory > 0:
                print("Inventory nearly full or time short. Returning to base.")
                move = self.move_towards_base()
                if move != (0, 0):
                    self.reset_stuck_counter()
                    return move

        # Gather diamonds within an adaptive search radius
        search_radius = self.adaptive_search_radius(diamonds_in_inventory)
        nearby_diamonds = self.get_collectable_diamonds(search_radius, inventory_size - diamonds_in_inventory)

        if nearby_diamonds:
            best_diamond = self.choose_best_diamond(nearby_diamonds)
            print(f"Moving towards diamond at {best_diamond.position} worth {best_diamond.properties.points}.")
            move = self.move_towards_with_teleporter(best_diamond.position)
            if move != (0, 0):
                self.reset_stuck_counter()
                return move

        # No diamonds found, explore unvisited safe tiles
        print("No diamonds nearby, exploring unvisited safe area.")
        move = self.explore_unvisited()
        if move != (0, 0):
            self.reset_stuck_counter()
            return move
        
        # If all else fails, try random safe move
        random_move = self.get_random_safe_move()
        if random_move != (0, 0):
            self.reset_stuck_counter()
            return random_move
            
        # Last resort - stay in place
        print("No safe moves available, staying in place.")
        return (0, 0)

    def reset_stuck_counter(self):
        self.stuck_counter = 0

    def safe_retreat(self) -> Tuple[int, int]:
        """Find a safe retreat path away from enemies"""
        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        safe_moves = []
        
        for move in possible_moves:
            new_x = self.my_bot.position.x + move[0]
            new_y = self.my_bot.position.y + move[1]
            new_position = Position(new_x, new_y)
            
            if self.is_position_safe_and_valid(new_position):
                # Calculate distance from enemies at new position
                min_enemy_dist = float('inf')
                enemies = [bot for bot in self.board.bots if bot != self.my_bot]
                
                for enemy in enemies:
                    dist = self.distance(new_position, enemy.position)
                    min_enemy_dist = min(min_enemy_dist, dist)
                
                safe_moves.append((move, min_enemy_dist))
        
        if safe_moves:
            # Choose move that maximizes distance from nearest enemy
            safe_moves.sort(key=lambda x: x[1], reverse=True)
            return safe_moves[0][0]
        
        return (0, 0)

    def get_random_safe_move(self) -> Tuple[int, int]:
        """Get a random safe move when other strategies fail"""
        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        safe_moves = []
        
        for move in possible_moves:
            new_x = self.my_bot.position.x + move[0]
            new_y = self.my_bot.position.y + move[1]
            new_position = Position(new_x, new_y)
            
            if self.is_position_safe_and_valid(new_position):
                # Avoid going back to last position if possible
                if move != (-self.last_move[0], -self.last_move[1]) or len(safe_moves) == 0:
                    safe_moves.append(move)
        
        if safe_moves:
            # If we have multiple safe moves, prefer ones that don't reverse last move
            filtered_moves = [move for move in safe_moves if move != (-self.last_move[0], -self.last_move[1])]
            if filtered_moves:
                return filtered_moves[0]
            return safe_moves[0]
        
        return (0, 0)

    def adaptive_search_radius(self, diamonds_in_inventory: int) -> int:
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
        diamonds_sorted = sorted(
            diamonds,
            key=lambda d: (-d.properties.points, self.distance_with_teleporter(self.my_bot.position, d.position))
        )
        return diamonds_sorted[0]

    def explore_unvisited(self) -> Tuple[int, int]:
        candidate_tiles = self.get_adjacent_positions(self.my_bot.position)
        safe_tiles = []

        for tile in candidate_tiles:
            if (tile.x, tile.y) not in self.visited_positions and self.is_safe_and_valid_position(tile):
                safe_tiles.append(tile)

        if not safe_tiles:
            # If no unvisited safe tiles, try any safe tile
            for tile in candidate_tiles:
                if self.is_safe_and_valid_position(tile):
                    safe_tiles.append(tile)

        if not safe_tiles:
            return self.move_towards_base()

        best_tile = safe_tiles[0]
        self.visited_positions.add((best_tile.x, best_tile.y))
        print(f"Exploring safe area towards {best_tile}")
        return self.calculate_move_to_position(best_tile)

    def is_safe(self, tile: Position) -> bool:
        enemies = [bot for bot in self.board.bots if bot != self.my_bot]
        return all(self.distance_with_teleporter(tile, e.position) > self.safe_enemy_distance for e in enemies)

    def is_safe_and_valid_position(self, position: Position) -> bool:
        """Check if position is both safe and valid"""
        return self.is_position_safe_and_valid(position) and self.is_safe(position)

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

    def attempt_tackle(self, enemies: List[GameObject]) -> Optional[Tuple[int, int]]:
        """Attempt to tackle an enemy if advantageous"""
        for enemy in enemies:
            if self.distance(self.my_bot.position, enemy.position) == 1:
                # Check if we have an advantage (more diamonds or points)
                if (self.my_bot.properties.diamonds > enemy.properties.diamonds or 
                    self.my_bot.properties.score > enemy.properties.score):
                    delta_x = enemy.position.x - self.my_bot.position.x
                    delta_y = enemy.position.y - self.my_bot.position.y
                    return (delta_x, delta_y)
        return None

    def calculate_move_to_position(self, target: Position) -> Tuple[int, int]:
        """Calculate the move needed to reach target position"""
        delta_x = target.x - self.my_bot.position.x
        delta_y = target.y - self.my_bot.position.y
        
        # Normalize to single step
        if delta_x != 0:
            delta_x = 1 if delta_x > 0 else -1
        if delta_y != 0:
            delta_y = 1 if delta_y > 0 else -1
            
        return (delta_x, delta_y)

    def move_towards(self, target: Position) -> Tuple[int, int]:
        """Improved move_towards with better conflict resolution"""
        delta_x = target.x - self.my_bot.position.x
        delta_y = target.y - self.my_bot.position.y
        
        # Choose primary direction
        if abs(delta_x) > abs(delta_y):
            primary_step = (1 if delta_x > 0 else -1, 0)
            secondary_step = (0, 1 if delta_y > 0 else -1) if delta_y != 0 else None
        else:
            primary_step = (0, 1 if delta_y > 0 else -1)
            secondary_step = (1 if delta_x > 0 else -1, 0) if delta_x != 0 else None

        # Try primary direction
        new_position = Position(
            self.my_bot.position.x + primary_step[0], 
            self.my_bot.position.y + primary_step[1]
        )

        if self.is_position_safe_and_valid(new_position):
            self.last_move = primary_step
            return primary_step

        # Try secondary direction if available
        if secondary_step:
            new_position = Position(
                self.my_bot.position.x + secondary_step[0], 
                self.my_bot.position.y + secondary_step[1]
            )
            if self.is_position_safe_and_valid(new_position):
                self.last_move = secondary_step
                return secondary_step

        # Try to tackle if enemy is blocking
        enemies_in_primary = [bot for bot in self.board.bots 
                             if bot != self.my_bot and bot.position.x == new_position.x and bot.position.y == new_position.y]
        
        if enemies_in_primary:
            tackle_move = self.attempt_tackle(enemies_in_primary)
            if tackle_move:
                self.last_move = tackle_move
                return tackle_move

        # Find any safe alternative move
        alternative_move = self.find_safe_alternative_move()
        if alternative_move:
            self.last_move = alternative_move
            return alternative_move

        return (0, 0)

    def find_safe_alternative_move(self) -> Optional[Tuple[int, int]]:
        """Find any safe alternative move"""
        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        for move in possible_moves:
            new_x = self.my_bot.position.x + move[0]
            new_y = self.my_bot.position.y + move[1]
            new_position = Position(new_x, new_y)
            
            if self.is_position_safe_and_valid(new_position):
                # Avoid reversing last move if possible
                if move != (-self.last_move[0], -self.last_move[1]):
                    return move
        
        # If all moves would reverse, allow it as last resort
        for move in possible_moves:
            new_x = self.my_bot.position.x + move[0]
            new_y = self.my_bot.position.y + move[1]
            new_position = Position(new_x, new_y)
            
            if self.is_position_safe_and_valid(new_position):
                return move
                
        return None

    def is_position_safe_and_valid(self, position: Position) -> bool:
        """Check if position is within bounds and not occupied by other bots"""
        if not (0 <= position.x < self.board.height and 0 <= position.y < self.board.width):
            return False
        
        # Check for other bots in the position
        for bot in self.board.bots:
            if bot != self.my_bot and bot.position.x == position.x and bot.position.y == position.y:
                return False
        return True

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

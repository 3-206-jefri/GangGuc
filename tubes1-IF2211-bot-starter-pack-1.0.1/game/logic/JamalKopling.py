from typing import Tuple, List, Optional
import math
from game.models import Board, GameObject, Position
from game.logic.base import BaseLogic

class GreedyJamalLogic(BaseLogic):
    def __init__(self): # Inisialisasi properti bot
        self.portals: List[GameObject] = []
        self.portal_map = {}
        self.last_position: Optional[Position] = None # Melacak posisi terakhir untuk mencegah maju-mundur
        self.visited_positions = {} # Melacak posisi yang dikunjungi untuk eksplorasi
        self.turn_counter = 0 # Penghitung giliran untuk meluruhkan posisi yang dikunjungi
        self.my_bot: Optional[GameObject] = None # Referensi bot saat ini
        self.board: Optional[Board] = None # Referensi papan permainan saat ini

    def next_move(self, bot: GameObject, board: Board) -> Tuple[int, int]:
        self.my_bot = bot # Menetapkan bot saat ini agar dapat diakses di fungsi lain
        self.board = board # Menetapkan papan saat ini agar dapat diakses di fungsi lain
        self.turn_counter += 1 # Memperbarui penghitung giliran

        pos = bot.position
        props = bot.properties

        # Memperbarui posisi terakhir sebelum bergerak
        current_position = bot.position
        self.visited_positions[(current_position.x, current_position.y)] = self.turn_counter

        if not self.portals:
            self._load_portals(board)

        # Prioritas 1: Segera pulang jika inventaris penuh
        # Atau jika sudah mengumpulkan sejumlah berlian dan markas sudah dekat
        min_diamonds_to_return = 3 # Jumlah minimum berlian untuk kembali ke markas
        if props.diamonds >= props.inventory_size or \
           (props.diamonds >= min_diamonds_to_return and self._manhattan(pos, props.base) <= 5):
            print(f"Inventaris penuh ({props.diamonds}/{props.inventory_size}) atau berlian cukup dan markas dekat. Kembali ke markas.")
            move = self._go_home(pos, props.base, board)
            self.last_position = current_position
            return move

        # Prioritas 2: Cari dan bergerak menuju berlian
        diamond = self._select_diamond(bot, board)
        if diamond:
            print(f"Bergerak menuju berlian di {diamond.position}")
            move = self._head_to(pos, diamond.position, board)
            self.last_position = current_position
            return move
        
        # Fallback: Jika tidak ada berlian yang cocok, coba jelajahi area dengan aman
        print("Tidak ada berlian yang cocok ditemukan, menjelajahi.")
        move = self._explore_safely(pos, board) # Menggunakan fungsi eksplorasi
        self.last_position = current_position
        return move

    def _load_portals(self, board: Board):
        """Memetakan portal berdasarkan objek di papan."""
        self.portals = list(filter(lambda obj: obj.type == "TeleportGameObject", board.game_objects))
        if len(self.portals) >= 2:
            first, second = self.portals[0], self.portals[1]
            self.portal_map = {first.id: second, second.id: first}

    def _go_home(self, start: Position, home: Position, board: Board) -> Tuple[int, int]:
        """Menghasilkan langkah untuk kembali ke markas."""
        return self._path_with_portal(start, home, board)

    def _head_to(self, start: Position, destination: Position, board: Board) -> Tuple[int, int]:
        """Menghasilkan langkah menuju tujuan tertentu."""
        return self._path_with_portal(start, destination, board)

    def _path_with_portal(self, start: Position, goal: Position, board: Board) -> Tuple[int, int]:
        """Menghitung jalur terbaik menuju tujuan, mempertimbangkan penggunaan portal."""
        best_move = self._naive_step(start, goal, board)
        best_distance = self._manhattan(start, goal)

        for p in self.portals:
            linked = self.portal_map.get(p.id)
            if linked:
                # Jarak melalui portal: (jarak ke portal pertama) + (jarak dari portal kedua ke tujuan)
                dist_via_portal = self._manhattan(start, p.position) + self._manhattan(linked.position, goal)
                
                if dist_via_portal < best_distance:
                    # Jika teleportasi lebih efisien, bergerak ke portal
                    best_distance = dist_via_portal
                    best_move = self._step_towards(start, p.position)
                    # Cek jika sudah di samping portal
                    if self._adjacent(start, p.position):
                        return best_move # Langsung ke portal jika sudah di sebelahnya
        return best_move

    def _select_diamond(self, bot: GameObject, board: Board) -> Optional[GameObject]:
        """Pilih berlian yang tidak memiliki pasangan dan prioritaskan poin tertinggi."""
        possible = [d for d in board.diamonds if d.properties.pair_id is None]
        
        # Jika bot sudah punya banyak berlian (misal setengah kapasitas), fokus ke berlian poin rendah
        if bot.properties.diamonds >= bot.properties.inventory_size / 2:
            # Coba cari berlian poin tinggi dulu, baru poin rendah jika ada.
            high_value_diamonds = [d for d in possible if d.properties.points > 1]
            if high_value_diamonds:
                return sorted(high_value_diamonds, key=lambda d: self._euclidean(bot.position, d.position))[0]
            
            # Jika tidak ada berlian bernilai tinggi, ambil yang poin 1
            low_value_diamonds = [d for d in possible if d.properties.points == 1]
            if low_value_diamonds:
                return sorted(low_value_diamonds, key=lambda d: self._euclidean(bot.position, d.position))[0]

        # Jika inventaris kosong atau belum banyak, prioritaskan poin tertinggi
        if possible:
            # Urutkan berdasarkan poin menurun, lalu jarak menaik
            return sorted(possible, key=lambda d: (-d.properties.points, self._euclidean(bot.position, d.position)))[0]

        return None

    def _naive_step(self, src: Position, dst: Position, board: Board) -> Tuple[int, int]:
        """Menghasilkan langkah satu petak menuju tujuan secara langsung."""
        dx = dst.x - src.x
        dy = dst.y - src.y

        # Coba bergerak di sumbu yang memiliki jarak absolut lebih besar terlebih dahulu
        if abs(dx) >= abs(dy):
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            if step_x != 0 and self._is_valid_and_safe_move(src, (step_x, 0)):
                return (step_x, 0)
            
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            if step_y != 0 and self._is_valid_and_safe_move(src, (0, step_y)):
                return (0, step_y)
        else:
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            if step_y != 0 and self._is_valid_and_safe_move(src, (0, step_y)):
                return (0, step_y)
            
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            if step_x != 0 and self._is_valid_and_safe_move(src, (step_x, 0)):
                return (step_x, 0)

        # Fallback: cari arah legal pertama yang aman dan tidak mundur
        move = self._find_safe_alternative_move(current_pos=self.my_bot.position, avoid_reverse=True)
        if move != (0,0):
            return move

        # Fallback terakhir: coba gerakan mundur jika tidak ada pilihan lain
        move = self._find_safe_alternative_move(current_pos=self.my_bot.position, avoid_reverse=False)
        if move != (0,0):
            return move

        return (0, 0) # Tetap di tempat jika tidak ada gerakan yang valid

    def _is_valid_and_safe_move(self, current_pos: Position, move: Tuple[int, int]) -> bool:
        """Memeriksa apakah gerakan menghasilkan posisi yang valid dan aman."""
        new_x = current_pos.x + move[0]
        new_y = current_pos.y + move[1]
        new_position = Position(new_x, new_y)

        # Cek batas papan
        if not (0 <= new_x < self.board.height and 0 <= new_y < self.board.width):
            return False
        
        # Cek apakah ada bot lain di posisi tujuan
        for other_bot in self.board.bots:
            # Pastikan bukan bot kita sendiri dan posisi sama
            if other_bot.id != self.my_bot.id and other_bot.position.x == new_x and other_bot.position.y == new_y:
                return False
        
        # Cek apakah ada teleporter di posisi tujuan (ini tidak menghalangi gerakan, hanya tujuan)
        # Logika lebih lanjut untuk portal ditangani di _path_with_portal
        
        return True

    def _step_towards(self, src: Position, dest: Position) -> Tuple[int, int]:
        """Menghasilkan langkah satu petak menuju tujuan jika berdekatan."""
        dx = dest.x - src.x
        dy = dest.y - src.y

        if abs(dx) + abs(dy) == 1: # Hanya jika berdekatan
            return (dx, dy)
        return (0, 0) # Jangan bergerak jika tidak berdekatan

    def _adjacent(self, a: Position, b: Position) -> bool:
        """Memeriksa apakah dua posisi berdekatan (Manhattan distance 1)."""
        return abs(a.x - b.x) + abs(a.y - b.y) == 1

    def _manhattan(self, a: Position, b: Position) -> int:
        """Menghitung jarak Manhattan antara dua posisi."""
        return abs(a.x - b.x) + abs(a.y - b.y)

    def _euclidean(self, a: Position, b: Position) -> float:
        """Menghitung jarak Euclidean antara dua posisi."""
        return math.hypot(a.x -b.x,a.y-b.y)
    
    def _explore_safely(self, current_pos: Position, board: Board) -> Tuple[int, int]:
        """Logika untuk menjelajahi area aman dan kurang dikunjungi."""
        candidate_moves = [(1,0), (-1,0), (0,1), (0,-1)]
        safe_moves = []

        for move in candidate_moves:
            if self._is_valid_and_safe_move(current_pos, move):
                safe_moves.append(move)
        
        if safe_moves:
            # Prioritaskan gerakan yang tidak mundur dari posisi terakhir
            non_reverse_moves = []
            if self.last_position:
                # Hitung delta dari last_position ke current_pos
                last_delta_x = current_pos.x - self.last_position.x
                last_delta_y = current_pos.y - self.last_position.y
                reverse_move = (-last_delta_x, -last_delta_y) # Gerakan yang akan kembali ke last_position

                for move in safe_moves:
                    if move != reverse_move:
                        non_reverse_moves.append(move)
            
            if non_reverse_moves:
                return non_reverse_moves[0] # Ambil gerakan non-mundur pertama
            else:
                return safe_moves[0] # Jika semua gerakan adalah mundur, ambil saja yang pertama

        return (0, 0) # Tetap di tempat jika tidak ada gerakan aman

    def _find_safe_alternative_move(self, current_pos: Position, avoid_reverse: bool = True) -> Tuple[int, int]:
        """Mencari gerakan alternatif aman, dengan current_pos sebagai referensi."""
        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        non_reverse_moves = []
        all_safe_moves = []

        for move in possible_moves:
            # Memeriksa keamanan dan validitas posisi baru
            is_valid_and_safe = self._is_valid_and_safe_move(current_pos, move)
            
            if is_valid_and_safe:
                all_safe_moves.append(move)
                # Periksa apakah gerakan ini akan membalikkan posisi terakhir
                if self.last_position:
                    last_delta_x = current_pos.x - self.last_position.x
                    last_delta_y = current_pos.y - self.last_position.y
                    reverse_move = (-last_delta_x, -last_delta_y)
                    
                    if move != reverse_move:
                        non_reverse_moves.append(move)
                else: # Jika belum ada last_position, semua non-reverse
                    non_reverse_moves.append(move)
        
        if avoid_reverse and non_reverse_moves:
            return non_reverse_moves[0]
        elif all_safe_moves:
            return all_safe_moves[0]
            
        return (0, 0)

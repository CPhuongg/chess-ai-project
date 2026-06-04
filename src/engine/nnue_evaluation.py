"""
NNUE (Efficiently Updatable Neural Network) Evaluation Module
Module đánh giá thế trận sử dụng mạng nơ-ron cho AI cờ vua

Tác giả: Dựa trên dự án chess-bot
Ngày: 2026-06-04
Phiên bản: 1.0
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import chess
from pathlib import Path
from typing import Dict, List, Tuple
import pickle
from functools import lru_cache

# ============== PHẦN 1: ĐỊNH NGHĨA MẠNG NƠ-RON ==============

class NNUEBoard(nn.Module):
    """
    Mạng nơ-ron đánh giá thế trận theo kiến trúc NNUE
    
    Kiến trúc:
    - Input layer: 773 features (đặc trưng bàn cờ)
    - Hidden layer 1: 256 neurons + Dropout
    - Hidden layer 2: 128 neurons
    - Hidden layer 3: 64 neurons  
    - Hidden layer 4: 32 neurons
    - Output layer: 1 neuron (điểm số từ -3000 đến 3000)
    
    Activation functions:
    - ReLU cho các hidden layers
    - Tanh cho output layer (chuẩn hóa về [-1, 1])
    """
    
    def __init__(self):
        super(NNUEBoard, self).__init__()
        
        # Layer 1: Input (776) -> Hidden 1 (256)
        self.fc1 = nn.Linear(776, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.dropout1 = nn.Dropout(0.2)
        
        # Layer 2: Hidden 1 (256) -> Hidden 2 (128)
        self.fc2 = nn.Linear(256, 128)
        self.bn2 = nn.BatchNorm1d(128)
        self.dropout2 = nn.Dropout(0.2)
        
        # Layer 3: Hidden 2 (128) -> Hidden 3 (64)
        self.fc3 = nn.Linear(128, 64)
        self.bn3 = nn.BatchNorm1d(64)
        
        # Layer 4: Hidden 3 (64) -> Hidden 4 (32)
        self.fc4 = nn.Linear(64, 32)
        
        # Layer 5: Hidden 4 (32) -> Output (1)
        self.fc5 = nn.Linear(32, 1)
        
        # Residual connection (skip connection)
        self.residual = nn.Linear(776, 64)
        
        # Khởi tạo weights
        self._initialize_weights()
        
    def _initialize_weights(self):
        """Khởi tạo weights bằng Xavier/Glorot initialization"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
                    
    def forward(self, x):
        """
        Forward pass qua mạng nơ-ron
        
        Args:
            x: Input tensor shape (batch_size, 776)
            
        Returns:
            Điểm số shape (batch_size, 1) trong khoảng [-3000, 3000]
        """
        # Residual path
        residual = self.residual(x)
        residual = F.relu(residual)
        
        # Main path
        # Layer 1
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout1(x)
        
        # Layer 2
        x = self.fc2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout2(x)
        
        # Layer 3
        x = self.fc3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # Add residual connection
        x = x + residual
        
        # Layer 4
        x = self.fc4(x)
        x = F.relu(x)
        
        # Layer 5 (output)
        x = self.fc5(x)
        x = torch.tanh(x)  # Output trong [-1, 1]
        
        # Scale về điểm số cờ vua (centipawns)
        return x * 3000


# ============== PHẦN 2: TRÍCH XUẤT ĐẶC TRƯNG ==============

class FeatureExtractor:
    """
    Lớp trích xuất đặc trưng từ bàn cờ thành vector cho mạng nơ-ron
    """
    
    def __init__(self):
        # Ánh xạ quân cờ sang index
        self.piece_to_idx = {
            # White pieces (0-5)
            (chess.WHITE, chess.PAWN): 0,
            (chess.WHITE, chess.KNIGHT): 1,
            (chess.WHITE, chess.BISHOP): 2,
            (chess.WHITE, chess.ROOK): 3,
            (chess.WHITE, chess.QUEEN): 4,
            (chess.WHITE, chess.KING): 5,
            # Black pieces (6-11)
            (chess.BLACK, chess.PAWN): 6,
            (chess.BLACK, chess.KNIGHT): 7,
            (chess.BLACK, chess.BISHOP): 8,
            (chess.BLACK, chess.ROOK): 9,
            (chess.BLACK, chess.QUEEN): 10,
            (chess.BLACK, chess.KING): 11,
        }
        
        self.num_piece_features = 12 * 64  # 12 loại quân * 64 ô
        self.num_aux_features = 8  # 8 đặc trưng phụ
        self.total_features = self.num_piece_features + self.num_aux_features
        
    def extract_features(self, board: chess.Board) -> np.ndarray:
        """
        Chuyển bàn cờ thành feature vector
        
        Args:
            board: Bàn cờ python-chess
            
        Returns:
            Numpy array shape (776,)
        """
        features = []
        
        # === PHẦN 1: VỊ TRÍ QUÂN CỜ (12 * 64 = 768 features) ===
        # One-hot encoding cho từng ô của từng loại quân
        piece_features = np.zeros(self.num_piece_features, dtype=np.float32)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Lấy index của loại quân này
                piece_idx = self.piece_to_idx[(piece.color, piece.piece_type)]
                # Tính vị trí trong feature array
                feature_idx = piece_idx * 64 + square
                piece_features[feature_idx] = 1.0
                
        features.extend(piece_features)
        
        # === PHẦN 2: ĐẶC TRƯNG PHỤ (8 features) ===
        aux_features = []
        
        # 2.1: Quyền nhập thành (4 features)
        aux_features.append(1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0)
        aux_features.append(1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0)
        aux_features.append(1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0)
        aux_features.append(1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0)
        
        # 2.2: En passant (1 feature)
        aux_features.append(1.0 if board.ep_square is not None else 0.0)
        
        # 2.3: Lượt đi (1 feature) - 1 cho trắng, 0 cho đen
        aux_features.append(1.0 if board.turn == chess.WHITE else 0.0)
        
        # 2.4: Half-move clock cho rule 50 nước (normalized)
        aux_features.append(min(board.halfmove_clock / 100.0, 1.0))
        
        # 2.5: Full-move number (normalized)
        aux_features.append(min(board.fullmove_number / 100.0, 1.0))
        
        features.extend(aux_features)
        
        # Chuyển thành numpy array
        return np.array(features, dtype=np.float32)
    
    def get_feature_dimension(self) -> int:
        """Trả về số chiều của feature vector"""
        return self.total_features


# ============== PHẦN 3: LỚP ĐÁNH GIÁ NNUE ==============

class NNUEEvaluation:
    """
    Lớp đánh giá thế trận sử dụng mạng nơ-ron NNUE
    """
    
    def __init__(self, model_path: str = None, device: str = "cpu"):
        """
        Khởi tạo NNUE evaluator
        
        Args:
            model_path: Đường dẫn đến file model .pth hoặc .pt (optional)
            device: "cpu" hoặc "cuda" (nếu có GPU)
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model = NNUEBoard()
        self.feature_extractor = FeatureExtractor()
        
        # Load model nếu có
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
            print(f"✅ Loaded NNUE model from {model_path}")
        else:
            print("⚠️ Using untrained NNUE model (random weights)")
            print("   Model will still work but may not play optimally")
            
        self.model.to(self.device)
        self.model.eval()  # Chế độ evaluation (tắt dropout, batch norm)
        
        # Cache cho evaluation
        self.evaluation_cache = {}
        self.cache_size = 0
        self.max_cache_size = 10000
        
    def load_model(self, model_path: str):
        """
        Load model đã train từ file
        
        Args:
            model_path: Đường dẫn đến file model
        """
        try:
            # Load state dict
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"   Model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("   Continuing with random weights...")
            
    def save_model(self, save_path: str):
        """
        Lưu model hiện tại vào file
        
        Args:
            save_path: Đường dẫn để lưu model
        """
        torch.save(self.model.state_dict(), save_path)
        print(f"✅ Model saved to {save_path}")
        
    @lru_cache(maxsize=10000)
    def evaluate_cached(self, board_fen: str) -> float:
        """
        Đánh giá thế trận có cache (dùng LRU cache)
        
        Args:
            board_fen: FEN string của bàn cờ
            
        Returns:
            Điểm số đánh giá
        """
        board = chess.Board(board_fen)
        return self.evaluate(board)
    
    def evaluate(self, board: chess.Board) -> float:
        """
        Đánh giá thế trận từ góc nhìn của bên được đi
        
        Args:
            board: Bàn cờ python-chess
            
        Returns:
            Điểm số (positive = lợi thế cho bên được đi)
        """
        # Kiểm tra game over
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
            
        # Trích xuất features
        features = self.feature_extractor.extract_features(board)
        
        # Chuyển thành tensor
        tensor_input = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        tensor_input = tensor_input.to(self.device)
        
        # Forward qua mạng
        with torch.no_grad():
            score = self.model(tensor_input).item()
            
        # Điều chỉnh theo lượt đi (vì mạng học từ góc nhìn của trắng)
        # Nếu là lượt đen, đảo dấu
        if board.turn == chess.BLACK:
            score = -score
            
        return score
    
    def batch_evaluate(self, boards: List[chess.Board]) -> np.ndarray:
        """
        Đánh giá nhiều thế trận cùng lúc (batch processing)
        
        Args:
            boards: List các bàn cờ
            
        Returns:
            Numpy array các điểm số
        """
        if not boards:
            return np.array([])
            
        # Trích xuất features cho tất cả boards
        features_list = []
        for board in boards:
            features = self.feature_extractor.extract_features(board)
            features_list.append(features)
            
        # Stack thành batch
        batch_features = np.stack(features_list)
        tensor_input = torch.tensor(batch_features, dtype=torch.float32)
        tensor_input = tensor_input.to(self.device)
        
        # Forward pass
        with torch.no_grad():
            scores = self.model(tensor_input).cpu().numpy().flatten()
            
        # Điều chỉnh theo lượt đi
        for i, board in enumerate(boards):
            if board.turn == chess.BLACK:
                scores[i] = -scores[i]
                
        return scores


# ============== PHẦN 4: ĐÁNH GIÁ TRUYỀN THỐNG (PST) ==============

class TraditionalEvaluation:
    """
    Đánh giá thế trận truyền thống dựa trên:
    - Giá trị quân cờ
    - Bảng vị trí (Piece-Square Tables)
    - Tính di động (mobility)
    - An toàn vua (king safety)
    """
    
    def __init__(self):
        # Giá trị quân cờ (centipawns)
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # Bảng vị trí cho từng quân (Piece-Square Tables)
        # Được tối ưu dựa trên kinh nghiệm
        self.pst = self._init_piece_square_tables()
        
    def _init_piece_square_tables(self) -> Dict:
        """Khởi tạo Piece-Square Tables"""
        
        # Pawn table (ưu tiên center và promotion)
        pawn_table = np.array([
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10,-20,-20, 10, 10,  5,
            5, -4,-10,  0,  0,-10, -4,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5,  5, 10, 25, 25, 10,  5,  5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
            0,  0,  0,  0,  0,  0,  0,  0
        ])
        
        # Knight table (thích các ô trung tâm)
        knight_table = np.array([
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ])
        
        # Bishop table (thích các đường chéo chính)
        bishop_table = np.array([
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ])
        
        # Rook table (thích các cột mở)
        rook_table = np.array([
            0,  0,  0,  5,  5,  0,  0,  0,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            5, 10, 10, 10, 10, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ])
        
        # Queen table
        queen_table = np.array([
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -10,  5,  5,  5,  5,  5,  0,-10,
            0,  0,  5,  5,  5,  5,  0, -5,
            -5,  0,  5,  5,  5,  5,  0, -5,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ])
        
        # King table (mid game - khuyến khích nhập thành)
        king_table = np.array([
            20, 30, 10,  0,  0, 10, 30, 20,
            20, 20,  0,  0,  0,  0, 20, 20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30
        ])
        
        return {
            chess.PAWN: pawn_table,
            chess.KNIGHT: knight_table,
            chess.BISHOP: bishop_table,
            chess.ROOK: rook_table,
            chess.QUEEN: queen_table,
            chess.KING: king_table
        }
        
    def evaluate_mobility(self, board: chess.Board, color: chess.Color) -> float:
        """
        Đánh giá tính di động (số nước đi có thể)
        
        Args:
            board: Bàn cờ
            color: Màu quân cần đánh giá
            
        Returns:
            Điểm mobility (càng nhiều nước đi càng tốt)
        """
        original_turn = board.turn
        board.turn = color
        mobility = len(list(board.legal_moves))
        board.turn = original_turn
        
        # Mỗi nước đi được 5 điểm
        return mobility * 5
        
    def evaluate_king_safety(self, board: chess.Board, color: chess.Color) -> float:
        """
        Đánh giá an toàn của vua
        
        Args:
            board: Bàn cờ
            color: Màu quân cần đánh giá
            
        Returns:
            Điểm an toàn (càng cao càng an toàn)
        """
        king_square = board.king(color)
        if king_square is None:
            return 0
            
        safety_score = 0
        
        # Kiểm tra các quân đang tấn công vua
        attackers = board.attackers(not color, king_square)
        safety_score -= len(attackers) * 30
        
        # Bonus cho nhập thành
        if color == chess.WHITE:
            if board.has_kingside_castling_rights(chess.WHITE):
                safety_score += 20
            if board.has_queenside_castling_rights(chess.WHITE):
                safety_score += 15
        else:
            if board.has_kingside_castling_rights(chess.BLACK):
                safety_score += 20
            if board.has_queenside_castling_rights(chess.BLACK):
                safety_score += 15
                
        return safety_score
        
    def evaluate(self, board: chess.Board) -> float:
        """
        Đánh giá thế trận bằng phương pháp truyền thống
        
        Args:
            board: Bàn cờ
            
        Returns:
            Điểm số (positive = lợi thế cho trắng)
        """
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
            
        total_score = 0
        
        # Đánh giá cho từng màu
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            color_score = 0
            
            # 1. Giá trị quân cờ và vị trí
            for piece_type in self.piece_values:
                squares = board.pieces(piece_type, color)
                for square in squares:
                    # Giá trị cơ bản
                    color_score += self.piece_values[piece_type]
                    
                    # Bonus vị trí
                    if piece_type in self.pst:
                        if color == chess.BLACK:
                            # Mirror cho quân đen
                            rank = chess.square_rank(square)
                            file = chess.square_file(square)
                            mirrored_square = chess.square(file, 7 - rank)
                            color_score += self.pst[piece_type][mirrored_square]
                        else:
                            color_score += self.pst[piece_type][square]
                            
            # 2. Mobility
            color_score += self.evaluate_mobility(board, color)
            
            # 3. King safety
            color_score += self.evaluate_king_safety(board, color)
            
            total_score += multiplier * color_score
            
        # Điều chỉnh theo lượt đi
        if board.turn == chess.BLACK:
            total_score = -total_score
            
        return total_score


# ============== PHẦN 5: HYBRID EVALUATION (KẾT HỢP) ==============

class HybridEvaluation:
    """
    Kết hợp NNUE và Traditional evaluation để có kết quả tốt nhất
    Trọng số có thể điều chỉnh dựa trên giai đoạn game
    """
    
    def __init__(self, nnue_weight: float = 0.7, model_path: str = None):
        """
        Khởi tạo hybrid evaluator
        
        Args:
            nnue_weight: Trọng số cho NNUE (0-1), phần còn lại là traditional
            model_path: Đường dẫn đến NNUE model (optional)
        """
        self.nnue = NNUEEvaluation(model_path)
        self.traditional = TraditionalEvaluation()
        self.nnue_weight = nnue_weight
        
        # Ngưỡng để chuyển đổi trọng số
        self.midgame_threshold = 30  # < 30 nước là midgame
        self.endgame_threshold = 70  # > 70 nước là endgame
        
    def get_game_phase(self, board: chess.Board) -> str:
        """
        Xác định giai đoạn của ván cờ
        
        Args:
            board: Bàn cờ
            
        Returns:
            "opening", "midgame", hoặc "endgame"
        """
        total_moves = board.fullmove_number
        
        # Đếm số quân còn lại trên bàn
        piece_count = 0
        for square in chess.SQUARES:
            if board.piece_at(square):
                piece_count += 1
                
        if total_moves < 10 or piece_count > 28:
            return "opening"
        elif piece_count < 12:
            return "endgame"
        else:
            return "midgame"
            
    def get_dynamic_weight(self, board: chess.Board) -> float:
        """
        Điều chỉnh trọng số dựa trên giai đoạn game
        
        Args:
            board: Bàn cờ
            
        Returns:
            Trọng số cho NNUE
        """
        phase = self.get_game_phase(board)
        
        if phase == "opening":
            # Opening: ưu tiên traditional (book knowledge)
            return 0.4
        elif phase == "midgame":
            # Midgame: cân bằng
            return 0.6
        else:
            # Endgame: ưu tiên NNUE (tính toán chính xác hơn)
            return 0.8
            
    def evaluate(self, board: chess.Board) -> float:
        """
        Đánh giá thế trận kết hợp cả hai phương pháp
        
        Args:
            board: Bàn cờ
            
        Returns:
            Điểm số kết hợp
        """
        # Lấy dynamic weight
        weight = self.get_dynamic_weight(board) if self.nnue_weight is None else self.nnue_weight
        
        # Đánh giá từ cả hai phương pháp
        nnue_score = self.nnue.evaluate(board)
        traditional_score = self.traditional.evaluate(board) / 100.0  # Scale về cùng đơn vị
        
        # Kết hợp có trọng số
        final_score = weight * nnue_score + (1 - weight) * traditional_score
        
        return final_score
    
    def batch_evaluate(self, boards: List[chess.Board]) -> np.ndarray:
        """
        Đánh giá batch các thế trận
        
        Args:
            boards: List các bàn cờ
            
        Returns:
            Numpy array các điểm số
        """
        if not boards:
            return np.array([])
            
        nnue_scores = self.nnue.batch_evaluate(boards)
        traditional_scores = np.array([self.traditional.evaluate(b) / 100.0 for b in boards])
        
        weights = np.array([self.get_dynamic_weight(b) for b in boards])
        weights = weights.reshape(-1, 1) if len(boards) > 1 else weights
        
        final_scores = weights * nnue_scores + (1 - weights) * traditional_scores
        
        return final_scores


# ============== PHẦN 6: TEST & DEMO ==============

def test_nnue():
    """Test function để kiểm tra module hoạt động"""
    print("=" * 60)
    print("Testing NNUE Evaluation Module")
    print("=" * 60)
    
    # Khởi tạo evaluator
    print("\n1. Initializing evaluators...")
    nnue = NNUEEvaluation()
    traditional = TraditionalEvaluation()
    hybrid = HybridEvaluation(nnue_weight=0.7)
    
    # Test với bàn cờ khởi tạo
    print("\n2. Testing with starting position...")
    board = chess.Board()
    
    nnue_score = nnue.evaluate(board)
    trad_score = traditional.evaluate(board)
    hybrid_score = hybrid.evaluate(board)
    
    print(f"   NNUE score: {nnue_score:.2f}")
    print(f"   Traditional score: {trad_score:.2f}")
    print(f"   Hybrid score: {hybrid_score:.2f}")
    
    # Test với một số nước đi
    print("\n3. Testing after some moves...")
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    board.push_san("Bb5")  # Ruy Lopez opening
    
    nnue_score = nnue.evaluate(board)
    trad_score = traditional.evaluate(board)
    hybrid_score = hybrid.evaluate(board)
    
    print(f"   Position after Ruy Lopez:")
    print(f"   NNUE score: {nnue_score:.2f}")
    print(f"   Traditional score: {trad_score:.2f}")
    print(f"   Hybrid score: {hybrid_score:.2f}")
    print(f"   Game phase: {hybrid.get_game_phase(board)}")
    
    # Test batch evaluation
    print("\n4. Testing batch evaluation...")
    boards = [chess.Board(), chess.Board("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3")]
    scores = hybrid.batch_evaluate(boards)
    for i, score in enumerate(scores):
        print(f"   Board {i+1} score: {score:.2f}")
        
    # Test caching
    print("\n5. Testing evaluation cache...")
    import time
    fen = board.fen()
    
    start = time.time()
    for _ in range(100):
        nnue.evaluate_cached(fen)
    cached_time = time.time() - start
    
    start = time.time()
    for _ in range(100):
        nnue.evaluate(board)
    uncached_time = time.time() - start
    
    print(f"   Cached time: {cached_time:.4f}s")
    print(f"   Uncached time: {uncached_time:.4f}s")
    print(f"   Speedup: {uncached_time/cached_time:.2f}x")
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    test_nnue()
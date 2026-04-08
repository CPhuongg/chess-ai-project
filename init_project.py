import os

def create_structure():
    # Danh sách các thư mục cần tạo
    folders = [
        "assets/images/pieces",
        "assets/images/interface",
        "assets/fonts",
        "assets/sounds",
        "src/engine",
        "src/ui/components",
        "src/board",
        "tests",
        "docs",
        "data"
    ]
    
    # Danh sách các file khởi tạo và nội dung mặc định
    files = {
        "src/engine/__init__.py": "",
        "src/engine/minimax.py": "# Thuat toan Minimax & Alpha-Beta\n",
        "src/engine/evaluation.py": "# Ham luong gia ban co\n",
        "src/engine/constants.py": "# Chua bang PST va gia tri quan co\n",
        "src/ui/__init__.py": "",
        "src/ui/renderer.py": "# Ve ban co va quan co\n",
        "src/ui/screens.py": "# Quan ly Menu va man hinh Game\n",
        "src/board/__init__.py": "",
        "src/board/board_manager.py": "# Wrapper cho thu vien python-chess\n",
        "src/main.py": "# File khoi chay chinh\n",
        "requirements.txt": "chess\npygame\n",
        ".gitignore": "__pycache__/\n*.pyc\nvenv/\n.vscode/\n",
        "README.md": "# Chess AI Project\n"
    }

    print("--- Bat dau khoi tao cau truc du an ---")

    # Tạo thư mục
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"[OK] Da tao thu muc: {folder}")
        except Exception as e:
            print(f"[ERROR] Khong the tao thu muc {folder}: {e}")

    # Tạo file mẫu
    for file_path, content in files.items():
        if not os.path.exists(file_path):
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[OK] Da tao file: {file_path}")
            except Exception as e:
                print(f"[ERROR] Khong the tao file {file_path}: {e}")
        else:
            print(f"[SKIP] File da ton tai: {file_path}")

    print("\n--- Hoan thanh! Chuc nhom lam bai tot ---")

if __name__ == "__main__":
    create_structure()
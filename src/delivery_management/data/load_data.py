from pathlib import Path
import json

class DataLoader:
    BASE_DIR = Path(__file__).resolve().parent

    @staticmethod
    def load_data(filename: str):
        file_path = DataLoader.BASE_DIR / filename
        with open(file_path, "r") as f:
            return json.load(f)
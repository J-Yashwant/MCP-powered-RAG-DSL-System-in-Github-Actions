import csv
import os
from typing import Dict, Any

class FileRouter:
    @staticmethod
    def analyze_csv(file_path: str) -> Dict[str, Any]:
        """
        Reads CSV and checks if cell max length < 150.
        Returns routing decision.
        """
        max_length = 0
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    for cell in row:
                        if len(cell) > max_length:
                            max_length = len(cell)
        except Exception as e:
            return {"type": "error", "message": str(e)}

        if max_length < 150:
            return {"type": "tabular_short", "engine": "BM25_DSL"}
        else:
            return {"type": "mixed_long", "engine": "Chroma_RAG"}

    @staticmethod
    def process_document(file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return FileRouter.analyze_csv(file_path)
        elif ext in [".pdf", ".txt", ".docx"]:
            # Standard docs route to RAG
            return {"type": "document", "engine": "Chroma_RAG"}
        else:
            return {"type": "unknown", "engine": "None"}

file_router = FileRouter()

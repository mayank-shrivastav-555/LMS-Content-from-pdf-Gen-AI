import os
from typing import List

class DocumentFetcher:
    def __init__(self, directory: str):
        self.directory = directory

    def fetch_documents(self, extensions=(".pdf", ".docx", ".txt")) -> List[str]:
        """
        Fetches all documents with specified extensions from the directory.
        Returns a list of file paths.
        """
        files = []
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.lower().endswith(extensions):
                    files.append(os.path.join(root, filename))
        print("Documents found:", files)
        return files

    def read_text_file(self, file_path: str) -> str:
        """
        Reads and returns the content of a text file.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

"""
This module is responsible for itterating through a folder 
(environment variable found in .env file) and reading the files.
It will return a list of file paths. e.g: ["/path/to/file1.txt", "/path/to/file2.pdf"]
"""

import os
from dotenv import load_dotenv

load_dotenv()


class FileReader:
    """
    This class is responsible for reading the files from the folder.
    getting the full paths of each of the files inside the raw data folder.
    """

    def __init__(self, folder_path: str = os.getenv("RAW_DATA_FOLDER")):
        self.folder_path = folder_path

    def read_files(self):
        """
        This function reads the files from the folder and returns a list of file paths.
        """
        pdf_file_paths = []
        text_file_paths = []
        markdown_file_paths = []
        image_file_paths = []
        for file in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, file)
            absolute_path = os.path.abspath(file_path)
            if file.endswith(".pdf"):
                pdf_file_paths.append(absolute_path)
            elif file.endswith(".txt"):
                text_file_paths.append(absolute_path)
            elif file.endswith(".md"):
                markdown_file_paths.append(absolute_path)
            elif (
                file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png")
            ):
                image_file_paths.append(absolute_path)
        return {
            "pdf": pdf_file_paths,
            "text": text_file_paths,
            "markdown": markdown_file_paths,
            "image": image_file_paths,
        }


if __name__ == "__main__":
    file_reader = FileReader()
    print(file_reader.read_files())

"""
This module is responsible for chunking and embedding the text data.
"""

from typing import Dict, List
import os
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HybridChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()


class ChunkerEmbedder:
    """
    This class is responsible for chunking and embedding the text data.
    """

    def __init__(
        self, all_files: Dict[str, List[str]], chunk_size: int, chunk_overlap: int
    ):
        self.pdf_files = all_files["pdf"]
        self.text_files = all_files["text"]
        self.markdown_files = all_files["markdown"]
        self.image_files = all_files["image"]

        self.converter = DocumentConverter()

        self.chunker = HybridChunker(
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            respect_sentence_boundary=True,
            respect_word_boundary=True,
        )

        self.text_chunker = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size),
            chunk_overlap=int(chunk_overlap),
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self) -> List[Dict[str, List[str]]]:
        """
        This function chunks the text data into smaller chunks.
        """
        text_chunks = []
        for text_file in self.text_files:
            with open(text_file, "r", encoding="utf-8") as file:
                text = file.read()
                chunks = self.text_chunker.split_text(text)
                file_name = text_file.split("/")[-1]
                text_chunks.append(
                    {
                        "file": file_name,
                        "chunks": chunks,
                    }
                )
        return text_chunks

    def chunk_markdown(self) -> List[Dict[str, List[str]]]:
        """
        This function chunks the text data into smaller chunks.
        """
        markdown_chunks = []
        for markdown_file in self.markdown_files:
            doc = self.converter.convert(source=markdown_file).document
            chunks = self.chunker.chunk(dl_doc=doc)
            file_name = markdown_file.split("/")[-1]
            markdown_chunks.append(
                {
                    "file": file_name,
                    "chunks": [chunk.text for chunk in chunks],
                }
            )
        return markdown_chunks

    def chunk_pdf(self) -> List[Dict[str, List[str]]]:
        """
        This function chunks the pdf data into smaller chunks.
        """
        pdf_chunks = []
        # Initialize the document converter

        # Convert PDF to document format
        for pdf_file in self.pdf_files:
            result = self.converter.convert(pdf_file)
            docling_document = result.document
            chunks = self.chunker.chunk(docling_document)
            file_name = pdf_file.split("/")[-1]
            pdf_chunks.append(
                {
                    "file": file_name,
                    "chunks": [chunk.text for chunk in chunks],
                }
            )
        return pdf_chunks


if __name__ == "__main__":
    pass
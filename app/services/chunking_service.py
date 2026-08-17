import re
from typing import List

import logging

logger = logging.getLogger(__name__)


class ChunkingService:

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[str]:

        logger.info(
            "Starting text chunking | original_length=%s | chunk_size=%s | overlap=%s",
            len(text),
            chunk_size,
            overlap,
        )

        try:
            text = ChunkingService.clean_text(text)

            chunks = []
            start = 0
            length = len(text)

            while start < length:
                end = start + chunk_size

                chunk = text[start:end].strip()

                if chunk:
                    chunks.append(chunk)

                start = end - overlap

                if start < 0:
                    start = 0

            logger.info(
                "Chunking completed | cleaned_length=%s | chunks_created=%s",
                length,
                len(chunks),
            )

            return chunks

        except Exception:
            logger.exception(
                "Failed to chunk text | chunk_size=%s | overlap=%s",
                chunk_size,
                overlap,
            )
            raise
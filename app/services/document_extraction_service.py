from app.helpers.document_intelligence_client import (
    document_client,
)


class DocumentExtractionService:

    @staticmethod
    async def extract_text(
        file_bytes: bytes,
    ) -> str:

        poller = (
            await document_client.begin_analyze_document(
                "prebuilt-read",
                body=file_bytes,
            )
        )

        result = await poller.result()

        pages = []

        for page in result.pages:

            page_text = []

            for line in page.lines:
                page_text.append(
                    line.content
                )

            pages.append(
                "\n".join(page_text)
            )

        return "\n\n".join(pages)
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ResponseFormatter:

    @staticmethod
    async def format(
        *,
        status: str,
        answer: str,
        data: dict | None = None,
    ) -> dict:

        data = data or {}

        parts = []

        # =====================================================
        # 1. MAIN MESSAGE
        # =====================================================

        if answer:
            parts.append({
                "type": "text",
                "content": answer,
            })

        # =====================================================
        # 2. STATUS-SPECIFIC UI
        # =====================================================

        if status == "needs_input":
            ResponseFormatter._add_input_ui(
                parts,
                data,
            )

        elif status == "completed":
            ResponseFormatter._add_completed_ui(
                parts,
                data,
            )

        elif status in {
            "error",
            "failed",
        }:
            ResponseFormatter._add_error_ui(
                parts,
                data,
            )

        elif status == "max_iterations":
            parts.append({
                "type": "alert",
                "severity": "warning",
                "content": (
                    "The request could not be completed "
                    "within the allowed processing steps."
                ),
            })

        # =====================================================
        # 3. FALLBACK
        # =====================================================

        if not parts:
            parts.append({
                "type": "text",
                "content": answer or "",
            })

        return {
            "status": status,
            "parts": parts,
        }

    # =========================================================
    # NEEDS INPUT
    # =========================================================

    @staticmethod
    def _add_input_ui(
        parts: list,
        data: dict,
    ):

        missing_fields = data.get(
            "missing_fields"
        )

        if not missing_fields:
            return

        fields = []

        for field in missing_fields:

            if isinstance(field, str):

                fields.append({
                    "name": field,
                    "label": ResponseFormatter._label(
                        field
                    ),
                    "type": "text",
                    "required": True,
                })

            elif isinstance(field, dict):

                fields.append(
                    ResponseFormatter._normalize_field(
                        field
                    )
                )

        if fields:

            parts.append({
                "type": "form",
                "fields": fields,
            })

    # =========================================================
    # COMPLETED
    # =========================================================

    @staticmethod
    def _add_completed_ui(
        parts: list,
        data: dict,
    ):

        # -----------------------------------------------------
        # Generated document
        # -----------------------------------------------------

        document_url = data.get(
            "document_url"
        )

        if document_url:

            parts.append({
                "type": "download",
                "title": ResponseFormatter._download_title(
                    data
                ),
                "url": document_url,
            })

        # -----------------------------------------------------
        # News articles
        # -----------------------------------------------------

        articles = data.get(
            "articles"
        )

        if articles:

            parts.append(
                ResponseFormatter._format_articles(
                    articles
                )
            )

        # -----------------------------------------------------
        # Generic records
        # -----------------------------------------------------

        # Don't automatically turn every dictionary into
        # a card/table. Only handle explicit known structures.
        #
        # Future tools can add their own formatter here.

    # =========================================================
    # ERROR
    # =========================================================

    @staticmethod
    def _add_error_ui(
        parts: list,
        data: dict,
    ):

        message = data.get(
            "message"
        )

        if message:

            parts.append({
                "type": "alert",
                "severity": "error",
                "content": message,
            })

    # =========================================================
    # NEWS
    # =========================================================

    @staticmethod
    def _format_articles(
        articles: list,
    ) -> dict:

        columns = [
            {
                "key": "title",
                "label": "Title",
            },
            {
                "key": "source",
                "label": "Source",
            },
            {
                "key": "published_at",
                "label": "Published",
            },
            {
                "key": "url",
                "label": "URL",
            },
        ]

        rows = []

        for article in articles:

            rows.append({
                "title": article.get(
                    "title"
                ),
                "source": article.get(
                    "source"
                ),
                "published_at": article.get(
                    "published_at"
                ),
                "url": article.get(
                    "url"
                ),
            })

        return {
            "type": "table",
            "columns": columns,
            "rows": rows,
        }

    # =========================================================
    # FIELD NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_field(
        field: dict,
    ) -> dict:

        name = field.get(
            "name"
        )

        return {
            "name": name,
            "label": field.get(
                "label",
                ResponseFormatter._label(name),
            ),
            "type": field.get(
                "type",
                "text",
            ),
            "required": field.get(
                "required",
                True,
            ),
            **{
                key: value
                for key, value in field.items()
                if key not in {
                    "name",
                    "label",
                    "type",
                    "required",
                }
            },
        }

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _label(
        value: str | None,
    ) -> str:

        if not value:
            return ""

        return value.replace(
            "_",
            " ",
        ).strip().title()

    @staticmethod
    def _download_title(
        data: dict,
    ) -> str:

        document_type = data.get(
            "document_type"
        )

        if document_type:
            return (
                f"Download "
                f"{document_type.replace('_', ' ').title()}"
            )

        return "Download Document"
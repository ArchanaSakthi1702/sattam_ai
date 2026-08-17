# app/services/document_service.py

import uuid
import logging
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
)
from app.helpers.openai_client import client
from app.config import get_settings
from app.services.file_service import FileService

settings = get_settings()
logger = logging.getLogger(__name__)

class DocumentService:

    DOCUMENT_REQUIREMENTS = {
        "rental_agreement": [
            "landlord_name",
            "tenant_name",
            "property_address",
            "rent_amount",
        ],
        "employment_agreement": [
            "employer_name",
            "employee_name",
            "job_title",
            "salary",
        ],
        "nda": [
            "party_one",
            "party_two",
        ],
    }


    @staticmethod
    async def _create_pdf(
        content: str,
    ) -> bytes:

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
        )

        styles = getSampleStyleSheet()

        elements = []

        for line in content.split("\n"):

            if line.strip():

                elements.append(
                    Paragraph(
                        line,
                        styles["Normal"],
                    )
                )

                elements.append(
                    Spacer(
                        1,
                        6,
                    )
                )

        doc.build(elements)

        pdf_bytes = buffer.getvalue()

        buffer.close()

        return pdf_bytes


    @staticmethod
    async def _generate_document_content(
        *,
        document_type: str,
        document_details: dict,
    ):

        prompt = f"""
    Generate a complete professional
    {document_type}.

    Details:

    {document_details}

    Return only the document text.
    """

        response = await client.responses.create(
            model=settings.DEPLOYMENT_NAME,
            input=prompt,
        )

        return response.output_text


    @staticmethod
    def _get_missing_fields(
        *,
        document_type: str,
        document_details: dict,
    ):

        required_fields = (
            DocumentService.DOCUMENT_REQUIREMENTS.get(
                document_type,
                [],
            )
        )

        missing_fields = []

        for field in required_fields:

            value = document_details.get(
                field
            )

            if value in (
                None,
                "",
            ):
                missing_fields.append(
                    field
                )

        return missing_fields


    @staticmethod
    async def generate_document(
        *,
        arguments,
        db,
        user,
        session,
    ):

        document_type = arguments.get(
            "document_type"
        )

        document_details = arguments.get(
            "document_details",
            {},
        )

        missing_fields = (
            DocumentService._get_missing_fields(
                document_type=document_type,
                document_details=document_details,
            )
        )

        if missing_fields:

            fields_text = "\n".join(
                f"- {field.replace('_', ' ').title()}"
                for field in missing_fields
            )


            return {
                "status": "needs_input",
                 "message": (
                    f"I can generate the "
                    f"{document_type.replace('_', ' ')} "
                    f"once I have the following information:\n\n"
                    f"{fields_text}"
                ),
                "data": {
                    "document_type": document_type,
                    "missing_fields": missing_fields,
                },
            }
        logger.info(
            "Generating document=%s session_id=%s",
            document_type,
            session.id,
        )

        document_content = await (
            DocumentService._generate_document_content(
                document_type=document_type,
                document_details=document_details,
            )
        )

        file_bytes = (
            await DocumentService._create_pdf(
                document_content
            )
        )

        blob_name = (
            f"{user.id}/documents/"
            f"{uuid.uuid4()}.pdf"
        )

        document_url = (
            await FileService.upload_to_blob(
                blob_name=blob_name,
                content=file_bytes,
            )
        )

        return {
            "status": "completed",
            "message": "Document generated successfully.",
            "data": {
                "document_type": document_type,
                "document_url": document_url,
            },
        }
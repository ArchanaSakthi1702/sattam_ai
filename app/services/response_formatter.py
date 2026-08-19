import json
import logging

from app.helpers.openai_client import client
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ResponseFormatter:

    SYSTEM_PROMPT = """
You are a UI response formatter.

Convert the provided payload into JSON.

Return ONLY valid JSON.

Supported components:

- text
- form
- download
- table
- card

Examples:

{
  "parts": [
    {
      "type": "text",
      "content": "Hello"
    }
  ]
}

{
  "parts": [
    {
      "type": "text",
      "content": "Please provide the missing details."
    },
    {
      "type": "form",
      "fields": [
        {
          "name": "property_address",
          "label": "Property Address",
          "required": true
        }
      ]
    }
  ]
}
"""

    @staticmethod
    async def format(
        *,
        status: str,
        answer: str,
        data: dict | None = None,
    ) -> dict:

        payload = {
            "status": status,
            "answer": answer,
            "data": data or {},
        }

        response = await client.responses.create(
            model=settings.DEPLOYMENT_NAME,
            input=f"""
{ResponseFormatter.SYSTEM_PROMPT}

Payload:

{json.dumps(payload, indent=2, default=str)}
"""
        )

        try:
            return json.loads(
                response.output_text
            )

        except Exception:

            logger.exception(
                "Failed to parse formatter response"
            )

            return {
                "parts": [
                    {
                        "type": "text",
                        "content": answer,
                    }
                ]
            }
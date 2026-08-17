# app/agents/tools.py

TOOLS = [

    {
    "type": "function",
    "name": "get_user_profile",
    "description": (
        "Returns the authenticated user's profile "
        "information. Use this tool when the user asks "
        "about their account, profile, name, email, "
        "subscription, usage, or stored user details."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    },
    {
    "type": "function",
    "name": "search_legal_news",
    "description": "Search latest legal news articles",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search keywords for legal news"
                ),
            },
        },
        "required": [
            "query",
        ],
    },
},
    {
        "type": "function",
        "name": "get_current_time",
        "description": (
            "Get the current date and time."
            "Use when the user asks for the current time,"
            "current date, today's date, day of week,"
            "or needs the current timestamp."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "generate_document",
        "description": (
            "Generate a legal document."
            "Call this tool whenever the user requests a document."
            "The tool determines whether more information is needed."
            "If the tool returns missing_fields, ask the user "
            "for those fields."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "description": (
                        "Document type such as "
                        "rental_agreement, employment_agreement, "
                        "nda, legal_notice, sale_deed."
                    ),
                },
                "document_details": {
                    "type": "object",
                    "description": (
                        "Known information for the document."
                    ),
                    "additionalProperties": True,
                },
            },
            "required": [
                "document_type"
            ],
            "additionalProperties": False,
        },
    }
]
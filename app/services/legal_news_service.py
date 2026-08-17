# app/services/legal_news_service.py

import logging
import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LegalNewsService:

    BASE_URL = "https://newsapi.org/v2/everything"

    @staticmethod
    async def search_news(
        *,
        arguments,
        db,
        user,
        session,
    ):

        query = arguments.get("query")

        logger.info(
            "Searching legal news query=%s session_id=%s",
            query,
            session.id,
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(
                LegalNewsService.BASE_URL,
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                    "apiKey": settings.NEWS_API_KEY,
                },
                timeout=30,
            )

        response.raise_for_status()

        payload = response.json()

        articles = []

        for article in payload.get(
            "articles",
            [],
        ):

            articles.append(
                {
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "source": article.get(
                        "source",
                        {},
                    ).get("name"),
                    "published_at": article.get(
                        "publishedAt"
                    ),
                }
            )

        logger.info(
            "Found %s articles for query=%s",
            len(articles),
            query,
        )

        return {
            "status": "completed",
            "message": (
                f"Found {len(articles)} news articles."
            ),
            "data": {
                "query": query,
                "articles": articles,
            },
        }
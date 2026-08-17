from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.helpers.blob_setup import (
    ensure_blob_container_exists,
)
from app.helpers.blob_client import (
    blob_service_client,
)
from app.helpers.document_intelligence_client import document_client
from app.services.qdrant_service import (
    qdrant_client,
)
from app.helpers.openai_client import client as project_client , project_client as main_client,credential
from app.helpers.logging_config import setup_logging

from app.routes.auth.register import router as register_router
from app.routes.auth.login import router as login_router
from app.routes.auth.refresh_token import router as refresh_router
from app.routes.auth.email_verification import router as email_verification_router


from app.routes.user import router as user_router
from app.routes.subscription_plan import router as user_subscription_plan_router
from app.routes.chat import router as chat_router
from app.routes.gamification import router as gamification_router

from app.routes.admin.subscription_plan import router as admin_subscription_plan_router
from app.routes.admin.gamification import router as admin_gamification_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    await ensure_blob_container_exists()
    setup_logging()

    yield

    await project_client.close()
    await main_client.close()
    await credential.close()
    await blob_service_client.close()
    await document_client.close()
    await qdrant_client.close()


app=FastAPI(
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register_router)
app.include_router(login_router)
app.include_router(refresh_router)
app.include_router(email_verification_router)

app.include_router(user_router)
app.include_router(user_subscription_plan_router)
app.include_router(chat_router)
app.include_router(gamification_router)

app.include_router(admin_subscription_plan_router)
app.include_router(admin_gamification_router)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes import auth, analyze, history, profile, billing
from backend.webhooks.stripe_webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Image Analysis API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(history.router, prefix="/api", tags=["history"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(billing.router, prefix="/api", tags=["billing"])
app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])


@app.get("/health")
async def health():
    return {"status": "ok"}

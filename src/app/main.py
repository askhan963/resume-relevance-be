from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .core.config import settings
from .core.setup import create_application, lifespan_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    default_lifespan = lifespan_factory(settings)
    async with default_lifespan(app):
        yield


app = create_application(router=router, settings=settings, lifespan=lifespan)

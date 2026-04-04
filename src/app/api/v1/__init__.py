from fastapi import APIRouter

from .analysis import router as analysis_router
from .ats import router as ats_router
from .auth import router as auth_router
from .files import router as files_router
from .health import router as health_router
from .job_description import router as job_description_router
from .resume import router as resume_router
from .rewrite import router as rewrite_router
from .users import router as users_router

router = APIRouter(prefix="/v1")

# Core infrastructure
router.include_router(health_router)

# Authentication
router.include_router(auth_router)

# User profile
router.include_router(users_router)

# Domain features
router.include_router(resume_router)
router.include_router(job_description_router)
router.include_router(analysis_router)
router.include_router(ats_router)
router.include_router(rewrite_router)
router.include_router(files_router)

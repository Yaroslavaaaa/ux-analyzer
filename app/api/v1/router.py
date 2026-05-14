from fastapi import APIRouter
from app.api.v1.endpoints import elements, users, projects, metrics, analyses, pages, violations, recommendations, scores, overlays

router = APIRouter()

router.include_router(users.router)
router.include_router(projects.router)
router.include_router(metrics.router)
router.include_router(analyses.router)
router.include_router(pages.router)
router.include_router(elements.router)
router.include_router(violations.router)
router.include_router(recommendations.router)
router.include_router(scores.router)
router.include_router(overlays.router)
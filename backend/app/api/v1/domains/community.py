import logging
logger = logging.getLogger(__name__)

"""Community domain — groups community, forums, social, peer support endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/community-domain", tags=["Community Domain"])

try:
    from app.api.v1.endpoints import community
    router.include_router(community.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import community_v2_api
    router.include_router(community_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import forums_api
    router.include_router(forums_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import social
    router.include_router(social.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import peer_support_api
    router.include_router(peer_support_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import family_api
    router.include_router(family_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import family_network_api
    router.include_router(family_network_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

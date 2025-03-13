from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from loguru import logger


async def http_exception_handler(request: Request, exc: HTTPException):
    if exc and exc.status_code == 401:
        return RedirectResponse("/login")
    else:
        route = request.scope.get("path")
        method = request.scope.get("method")
        logger.error(
            f"Error in route {method} {route}: {exc.detail} : {exc.status_code}"
        )
        return Response(content="Error managed via HTTP module", status_code=400)

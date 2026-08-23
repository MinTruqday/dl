from fastapi import Request, Response

from src.services.session import SessionService


def set_refresh_cookie(response: Response, request: Request, token_data: dict):
    refresh_token = token_data.pop("_refresh_token")
    response.set_cookie(
        key="doclib_refresh_token",
        value=refresh_token,
        max_age=SessionService.refresh_cookie_seconds(),
        httponly=True,
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        samesite="lax",
        path="/",
    )
    return token_data

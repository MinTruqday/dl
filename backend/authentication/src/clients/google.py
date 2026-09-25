import httpx

from src.core.infrastructure.configuration import settings


class GoogleAuthorizationRejected(RuntimeError):
    pass


class GoogleProviderUnavailable(RuntimeError):
    pass


class GoogleClient:
    @staticmethod
    async def load_user(code: str) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
            ) as client:
                token_response = await client.post(
                    settings.GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                )
                token_response.raise_for_status()
                access_token = token_response.json().get("access_token")
                if not access_token:
                    raise GoogleAuthorizationRejected()
                user_response = await client.get(
                    settings.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                user_response.raise_for_status()
                return user_response.json()
        except GoogleAuthorizationRejected:
            raise
        except (httpx.HTTPError, ValueError) as error:
            raise GoogleProviderUnavailable() from error


google_client = GoogleClient()

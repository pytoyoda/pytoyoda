"""Toyota Connected Services Controller."""

from __future__ import annotations

import asyncio
import ssl
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, ClassVar
from urllib import parse
from uuid import uuid4

import httpx
import jwt
from hishel.httpx import AsyncCacheClient
from loguru import logger

from pytoyoda.const import (
    ACCESS_TOKEN_URL,
    API_BASE_URL,
    AUTHENTICATE_URL,
    AUTHORIZE_URL,
    CLIENT_VERSION,
    SUBARU_ACCESS_TOKEN_URL,
    SUBARU_AUTHENTICATE_URL,
    SUBARU_AUTHORIZE_URL,
    SUBARU_BASIC_AUTH,
    SUBARU_CLIENT_ID,
    SUBARU_JWT_AUDIENCE,
    SUBARU_REDIRECT_URI,
    TOYOTA_BASIC_AUTH,
    TOYOTA_CLIENT_ID,
    TOYOTA_JWT_AUDIENCE,
    TOYOTA_REDIRECT_URI,
)
from pytoyoda.exceptions import (
    ToyotaApiError,
    ToyotaInternalError,
    ToyotaInvalidUsernameError,
    ToyotaLoginError,
)
from pytoyoda.utils.helpers import generate_hmac_sha256
from pytoyoda.utils.log_utils import format_httpx_response

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@dataclass
class TokenInfo:
    """Class to store token information."""

    access_token: str
    refresh_token: str
    uuid: str
    expiration: datetime


class Controller:
    """Controller class for Toyota Connected Services."""

    # Class variable for token cache
    _TOKEN_CACHE: ClassVar[dict[str, TokenInfo]] = {}

    def __init__(
        self, username: str, password: str, brand: str = "T", timeout: int = 60
    ) -> None:
        """Initialize Controller class.

        Args:
            username: Toyota account username
            password: Toyota account password
            brand: Brand of the car (T for Toyota, L for Lexus, S for Subaru)
            timeout: HTTP request timeout in seconds

        """
        self._username: str = username
        self._password: str = password
        self._brand: str = brand
        self._timeout = timeout

        # Brand-specific auth config - Subaru uses a different realm and credentials
        self._api_base_url = httpx.URL(API_BASE_URL)
        if brand == "S":
            self._access_token_url = httpx.URL(SUBARU_ACCESS_TOKEN_URL)
            self._authenticate_url = httpx.URL(SUBARU_AUTHENTICATE_URL)
            self._authorize_url = httpx.URL(SUBARU_AUTHORIZE_URL)
            self._oauth_basic_auth = SUBARU_BASIC_AUTH
            self._oauth_client_id = SUBARU_CLIENT_ID
            self._oauth_redirect_uri = SUBARU_REDIRECT_URI
            self._jwt_audience = SUBARU_JWT_AUDIENCE
        else:
            self._access_token_url = httpx.URL(ACCESS_TOKEN_URL)
            self._authenticate_url = httpx.URL(AUTHENTICATE_URL)
            self._authorize_url = httpx.URL(AUTHORIZE_URL)
            self._oauth_basic_auth = TOYOTA_BASIC_AUTH
            self._oauth_client_id = TOYOTA_CLIENT_ID
            self._oauth_redirect_uri = TOYOTA_REDIRECT_URI
            self._jwt_audience = TOYOTA_JWT_AUDIENCE

        # Authentication state
        self._token_info: TokenInfo | None = None

        # Reused httpx.AsyncClient for data requests. Lazily constructed inside
        # an async context and kept for the lifetime of the Controller, so that
        # SSL context + TCP connection pool survive across request_raw calls.
        self._client: httpx.AsyncClient | None = None

        # Cached SSL context shared by every AsyncClient this Controller builds.
        # ssl.create_default_context() reads the CA bundle from disk
        # synchronously, which trips Home Assistant's blocking-call watchdog
        # when called from the event loop (one warning per AsyncClient
        # construction). We build it once in an executor and reuse.
        self._ssl_ctx: ssl.SSLContext | None = None

        # Load from cache if available
        if self._username in self._TOKEN_CACHE:
            self._token_info = self._TOKEN_CACHE[self._username]

    @property
    def _token(self) -> str | None:
        """Get the current access token."""
        return self._token_info.access_token if self._token_info else None

    @property
    def _refresh_token(self) -> str | None:
        """Get the current refresh token."""
        return self._token_info.refresh_token if self._token_info else None

    @property
    def _uuid(self) -> str | None:
        """Get the current UUID."""
        return self._token_info.uuid if self._token_info else None

    @property
    def _token_expiration(self) -> datetime | None:
        """Get the token expiration datetime."""
        return self._token_info.expiration if self._token_info else None

    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired."""
        if not self._token_info:
            return False
        return self._token_info.expiration > datetime.now(timezone.utc)

    async def login(self) -> None:
        """Perform initial login if necessary."""
        if not self._is_token_valid():
            await self._update_token()

    async def _update_token(self) -> None:
        """Update the authentication token.

        First tries to refresh the token if available, falls back to
        full authentication.

        """
        if not self._is_token_valid():
            if self._refresh_token:
                try:
                    await self._refresh_tokens()
                except ToyotaLoginError:
                    logger.debug(
                        "Token refresh failed, falling back to full authentication"
                    )
                else:
                    return

            await self._authenticate()

    async def _get_ssl_context(self) -> ssl.SSLContext:
        """Return a cached SSL context, building it off the event loop on first use.

        httpx.create_ssl_context() reads the CA bundle synchronously, which
        blocks the event loop for ~1-10ms and trips Home Assistant's
        blocking-call watchdog. By caching the context on the Controller and
        sharing it across AsyncClient constructions, we pay that cost once
        per Controller lifetime instead of per HTTP client.
        """
        if self._ssl_ctx is None:
            loop = asyncio.get_running_loop()
            self._ssl_ctx = await loop.run_in_executor(None, httpx.create_ssl_context)
        return self._ssl_ctx

    @asynccontextmanager
    async def _get_http_client(self) -> AsyncGenerator:
        """Context manager for HTTP client with consistent timeout."""
        ssl_ctx = await self._get_ssl_context()
        async with AsyncCacheClient(timeout=self._timeout, verify=ssl_ctx) as client:
            yield client

    async def _authenticate(self) -> None:
        """Authenticate with username and password."""
        logger.debug("Authenticating with username and password")

        async with self._get_http_client() as client:
            # Authentication flow
            auth_data = await self._perform_authentication(client)

            # Authorization flow
            auth_code = await self._perform_authorization(client, auth_data["tokenId"])

            # Token retrieval
            token_data = await self._retrieve_tokens(client, auth_code)

            # Update tokens
            self._update_tokens(token_data)

    async def _perform_authentication(self, client: AsyncCacheClient) -> dict[str, Any]:
        """Perform the authentication part of the login flow."""
        data: dict[str, Any] = {}

        for _ in range(10):  # Try up to 10 times
            if "callbacks" in data:
                for cb in data["callbacks"]:
                    if (
                        cb["type"] == "NameCallback"
                        and cb["output"][0]["value"] == "User Name"
                    ):
                        cb["input"][0]["value"] = self._username
                    elif cb["type"] == "PasswordCallback":
                        cb["input"][0]["value"] = self._password
                    elif (
                        cb["type"] == "TextOutputCallback"
                        and cb["output"][0]["value"] == "User Not Found"
                    ):
                        msg = "Authentication Failed. User Not Found."
                        raise ToyotaInvalidUsernameError(msg)

            resp = await client.post(self._authenticate_url, json=data)
            logger.debug(format_httpx_response(resp))

            if resp.status_code != HTTPStatus.OK:
                msg = f"Authentication Failed. {resp.status_code}, {resp.text}."
                raise ToyotaLoginError(msg)

            data = resp.json()

            # Wait for tokenId to be returned in response
            if "tokenId" in data:
                return data

        msg = "Authentication Failed. Token ID not received after multiple attempts."
        raise ToyotaLoginError(msg)

    async def _perform_authorization(
        self, client: AsyncCacheClient, token_id: str
    ) -> list[str]:
        """Perform the authorization part of the login flow.

        Args:
            client: HTTP client
            token_id: Token ID from authentication

        Returns:
            Authentication code

        """
        resp = await client.get(
            self._authorize_url,
            headers={"cookie": f"iPlanetDirectoryPro={token_id}"},
        )
        logger.debug(format_httpx_response(resp))

        if resp.status_code != HTTPStatus.FOUND:
            msg = f"Authorization failed. {resp.status_code}, {resp.text}."
            raise ToyotaLoginError(msg)

        return parse.parse_qs(httpx.URL(resp.headers.get("location")).query.decode())[
            "code"
        ]

    async def _retrieve_tokens(
        self, client: AsyncCacheClient, auth_code: list[str]
    ) -> dict[str, Any]:
        """Retrieve access and refresh tokens.

        Args:
            client: HTTP client
            auth_code: Authorization code

        Returns:
            Token response data

        """
        resp = await client.post(
            self._access_token_url,
            headers={"authorization": self._oauth_basic_auth},
            data={
                "client_id": self._oauth_client_id,
                "code": auth_code,
                "redirect_uri": self._oauth_redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": "plain",
            },
        )
        logger.debug(format_httpx_response(resp))

        if resp.status_code != HTTPStatus.OK:
            msg = f"Token retrieval failed. {resp.status_code}, {resp.text}."
            raise ToyotaLoginError(msg)

        return resp.json()

    async def _refresh_tokens(self) -> None:
        """Refresh the access token using the refresh token."""
        logger.debug("Refreshing tokens")

        async with self._get_http_client() as client:
            resp = await client.post(
                self._access_token_url,
                headers={"authorization": self._oauth_basic_auth},
                data={
                    "client_id": self._oauth_client_id,
                    "redirect_uri": self._oauth_redirect_uri,
                    "grant_type": "refresh_token",
                    "code_verifier": "plain",
                    "refresh_token": self._refresh_token,
                },
            )
            logger.debug(format_httpx_response(resp))

            if resp.status_code != HTTPStatus.OK:
                msg = f"Token refresh failed. {resp.status_code}, {resp.text}."
                raise ToyotaLoginError(msg)

            self._update_tokens(resp.json())

    def _update_tokens(self, response_data: dict[str, Any]) -> None:
        """Update token information from response data.

        Args:
            response_data: Token response data from API

        Raises:
            ToyotaLoginError: If required tokens are missing

        """
        # Verify all required tokens are present
        required_fields = ["access_token", "id_token", "refresh_token", "expires_in"]
        if missing_fields := [
            field for field in required_fields if field not in response_data
        ]:
            msg = f"Token retrieval failed. Missing fields: {', '.join(missing_fields)}"
            raise ToyotaLoginError(msg)

        # Decode the JWT to get the UUID
        uuid = jwt.decode(
            response_data["id_token"],
            algorithms=["RS256"],
            options={"verify_signature": False},
            audience=self._jwt_audience,
        )["uuid"]

        # Calculate expiration time
        expiration = datetime.now(timezone.utc) + timedelta(
            seconds=response_data["expires_in"]
        )

        # Update token info
        self._token_info = TokenInfo(
            access_token=response_data["access_token"],
            refresh_token=response_data["refresh_token"],
            uuid=uuid,
            expiration=expiration,
        )

        # Update cache
        self._TOKEN_CACHE[self._username] = self._token_info

    async def request_raw(  # noqa: PLR0913
        self,
        method: str,
        endpoint: str,
        vin: str | None = None,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send a raw HTTP request to the Toyota API.

        Args:
            method: The HTTP method to use ("GET", "POST", "PUT", "DELETE")
            endpoint: The API endpoint to request
            vin: Vehicle Identification Number (optional)
            body: Request body as dictionary (optional)
            params: URL query parameters (optional)
            headers: Additional HTTP headers (optional)

        Returns:
            The raw HTTP response

        Raises:
            ToyotaInternalError: If an invalid HTTP method is provided
            ToyotaApiError: If the API returns an error response

        """
        valid_methods = ("GET", "POST", "PUT", "DELETE")
        if method not in valid_methods:
            msg = f"Invalid request method: {method}. Must be one of {valid_methods}"
            raise ToyotaInternalError(msg)

        # Ensure we have a valid token
        if not self._is_token_valid():
            await self._update_token()

        # Prepare headers
        request_headers = self._prepare_headers(vin, headers)

        # Make the request using the reused client (TCP/TLS state is pooled
        # across calls instead of a fresh SSL handshake per request). Retry on
        # 429 (rate-limited) and 5xx with exponential backoff; 4xx client
        # errors fail fast. Total worst-case wait when Toyota is unhealthy:
        # 2 + 4 + 8 = 14s.
        if self._client is None:
            ssl_ctx = await self._get_ssl_context()
            self._client = httpx.AsyncClient(timeout=self._timeout, verify=ssl_ctx)

        backoffs_s = (2, 4, 8)
        response: httpx.Response | None = None

        for attempt in range(len(backoffs_s) + 1):
            response = await self._client.request(
                method,
                f"{self._api_base_url}{endpoint}",
                headers=request_headers,
                json=body,
                params=params,
                follow_redirects=True,
            )
            logger.debug(format_httpx_response(response))

            if response.status_code in [HTTPStatus.OK, HTTPStatus.ACCEPTED]:
                return response

            is_transient = (
                response.status_code == HTTPStatus.TOO_MANY_REQUESTS
                or response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
            )
            if not is_transient or attempt >= len(backoffs_s):
                break

            wait = backoffs_s[attempt]
            logger.warning(
                "Toyota API {} on {}; retrying in {}s (attempt {} of {})",
                response.status_code,
                endpoint,
                wait,
                attempt + 2,
                len(backoffs_s) + 1,
            )
            await asyncio.sleep(wait)

        msg = f"Request Failed. {response.status_code}, {response.text}."
        raise ToyotaApiError(msg)

    async def aclose(self) -> None:
        """Release the pooled httpx client. Safe to call multiple times."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _prepare_headers(
        self,
        vin: str | None = None,
        additional_headers: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Prepare headers for API requests.

        Args:
            vin: Vehicle Identification Number (optional)
            additional_headers: Additional headers to include (optional)

        Returns:
            Complete headers dictionary

        """
        brand = self._brand
        headers = {
            "x-api-key": "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF",
            "API_KEY": "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF",
            "x-guid": self._uuid,
            "guid": self._uuid,
            "x-client-ref": generate_hmac_sha256(CLIENT_VERSION, self._uuid),
            "x-correlationid": str(uuid4()),
            "x-appversion": CLIENT_VERSION,
            "x-channel": "ONEAPP",
            "x-brand": brand,
            "x-region": "EU",
            "authorization": f"Bearer {self._token}",
            "user-agent": "okhttp/4.10.0",
        }

        if brand in ("L", "S"):
            headers["x-appbrand"] = brand
            headers["brand"] = brand

        # Add VIN if provided
        if vin is not None:
            headers["vin"] = vin

        # Add additional headers
        if additional_headers:
            headers |= additional_headers

        return headers

    async def request_json(  # noqa: PLR0913
        self,
        method: str,
        endpoint: str,
        vin: str | None = None,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a request to the Toyota API and return JSON response.

        Args:
            method: The HTTP method to use ("GET", "POST", "PUT", "DELETE")
            endpoint: The API endpoint to request
            vin: Vehicle Identification Number (optional)
            body: Request body as dictionary (optional)
            params: URL query parameters (optional)
            headers: Additional HTTP headers (optional)

        Returns:
            The JSON response as a dictionary

        Examples:
            response = await controller.request_json("GET", "/cars", vin="1234567890")

        """
        response = await self.request_raw(method, endpoint, vin, body, params, headers)
        return response.json() if response.content else {}

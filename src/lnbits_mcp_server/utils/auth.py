"""Authentication utilities for LNbits API."""

from enum import Enum
from typing import Dict, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


class AuthMethod(str, Enum):
    """Supported authentication methods."""

    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    HTTP_BEARER = "http_bearer"
    OAUTH2 = "oauth2"


class AuthConfig:
    """Configuration for LNbits authentication."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        oauth2_token: Optional[str] = None,
        auth_method: AuthMethod = AuthMethod.API_KEY_HEADER,
    ):
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.oauth2_token = oauth2_token
        self.auth_method = auth_method

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {}

        if self.auth_method == AuthMethod.API_KEY_HEADER and self.api_key:
            headers["X-API-KEY"] = self.api_key
        elif self.auth_method == AuthMethod.HTTP_BEARER and self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.auth_method == AuthMethod.OAUTH2 and self.oauth2_token:
            headers["Authorization"] = f"Bearer {self.oauth2_token}"

        return headers

    def get_query_params(self) -> Dict[str, str]:
        """Get authentication query parameters."""
        params = {}

        if self.auth_method == AuthMethod.API_KEY_QUERY and self.api_key:
            params["api_key"] = self.api_key

        return params

    def is_configured(self) -> bool:
        """Check if authentication is properly configured."""
        if self.auth_method == AuthMethod.API_KEY_HEADER:
            return bool(self.api_key)
        elif self.auth_method == AuthMethod.API_KEY_QUERY:
            return bool(self.api_key)
        elif self.auth_method == AuthMethod.HTTP_BEARER:
            return bool(self.bearer_token)
        elif self.auth_method == AuthMethod.OAUTH2:
            return bool(self.oauth2_token)
        return False

    def __repr__(self) -> str:
        return (
            f"AuthConfig(method={self.auth_method}, configured={self.is_configured()})"
        )

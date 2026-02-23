"""
LinkedIn OAuth Handler

Handles OAuth 2.0 flow for LinkedIn API access.
"""

import os
import secrets
import urllib.parse
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LinkedInTokens:
    """LinkedIn OAuth tokens."""
    access_token: str
    expires_at: datetime
    refresh_token: Optional[str] = None


class LinkedInOAuth:
    """Handles LinkedIn OAuth 2.0 authentication."""

    # LinkedIn OAuth endpoints
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    PROFILE_URL = "https://api.linkedin.com/v2/userinfo"

    # Required scopes for posting
    SCOPES = ["openid", "profile", "w_member_social"]

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None
    ):
        """
        Initialize LinkedIn OAuth handler.

        Args:
            client_id: LinkedIn app client ID
            client_secret: LinkedIn app client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv(
            "LINKEDIN_REDIRECT_URI",
            "http://localhost:8080/callback"
        )

        # Store state tokens for CSRF protection
        self._pending_states: dict[str, int] = {}  # state -> chat_id

    def is_configured(self) -> bool:
        """Check if LinkedIn OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)

    def generate_auth_url(self, chat_id: int) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            chat_id: Telegram chat ID to associate with this auth flow

        Returns:
            Authorization URL to redirect user to
        """
        if not self.is_configured():
            raise ValueError("LinkedIn OAuth not configured. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET.")

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        self._pending_states[state] = chat_id

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(self.SCOPES),
        }

        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def validate_state(self, state: str) -> Optional[int]:
        """
        Validate OAuth state and return associated chat_id.

        Args:
            state: State token from callback

        Returns:
            Chat ID if valid, None otherwise
        """
        return self._pending_states.pop(state, None)

    def exchange_code(self, code: str) -> LinkedInTokens:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            LinkedInTokens with access token and expiry
        """
        if not self.is_configured():
            raise ValueError("LinkedIn OAuth not configured.")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(
            self.TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")

        token_data = response.json()

        # Calculate expiry time
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        return LinkedInTokens(
            access_token=token_data["access_token"],
            expires_at=expires_at,
            refresh_token=token_data.get("refresh_token")
        )

    def get_user_profile(self, access_token: str) -> dict:
        """
        Get LinkedIn user profile.

        Args:
            access_token: Valid LinkedIn access token

        Returns:
            User profile data
        """
        response = requests.get(
            self.PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get profile: {response.text}")

        return response.json()

    def is_token_valid(self, access_token: str) -> bool:
        """
        Check if access token is still valid.

        Args:
            access_token: LinkedIn access token to validate

        Returns:
            True if token is valid
        """
        try:
            self.get_user_profile(access_token)
            return True
        except:
            return False


# Singleton instance
linkedin_oauth = LinkedInOAuth()

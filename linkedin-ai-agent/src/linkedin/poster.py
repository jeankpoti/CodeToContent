"""
LinkedIn Post Publisher

Publishes posts to LinkedIn using the API.
"""

import os
import requests
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class PostResult:
    """Result of a LinkedIn post operation."""
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


class LinkedInPoster:
    """Publishes posts to LinkedIn."""

    # LinkedIn API endpoints
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    POSTS_URL = "https://api.linkedin.com/v2/posts"

    def __init__(self):
        """Initialize LinkedIn poster."""
        pass

    def get_user_urn(self, access_token: str) -> str:
        """
        Get the user's LinkedIn URN (unique identifier).

        Args:
            access_token: Valid LinkedIn access token

        Returns:
            User URN string (e.g., "urn:li:person:ABC123")
        """
        response = requests.get(
            self.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get user info: {response.text}")

        data = response.json()
        user_id = data.get("sub")

        if not user_id:
            raise ValueError("Could not get user ID from LinkedIn")

        return f"urn:li:person:{user_id}"

    def create_post(
        self,
        access_token: str,
        text: str,
        visibility: str = "PUBLIC"
    ) -> PostResult:
        """
        Create a LinkedIn post.

        Args:
            access_token: Valid LinkedIn access token
            text: Post content text
            visibility: Post visibility (PUBLIC, CONNECTIONS)

        Returns:
            PostResult with success status and post details
        """
        try:
            # Get user URN
            author_urn = self.get_user_urn(access_token)

            # Prepare post payload
            payload = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            # Try the newer Posts API first
            response = requests.post(
                self.POSTS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "LinkedIn-Version": "202401"
                },
                json={
                    "author": author_urn,
                    "commentary": text,
                    "visibility": visibility,
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                        "targetEntities": [],
                        "thirdPartyDistributionChannels": []
                    },
                    "lifecycleState": "PUBLISHED",
                    "isReshareDisabledByAuthor": False
                }
            )

            if response.status_code in [200, 201]:
                # Success
                result_data = response.json() if response.text else {}
                post_id = result_data.get("id", "")

                # Construct post URL
                post_url = None
                if post_id:
                    # Extract numeric ID from URN if present
                    numeric_id = post_id.split(":")[-1] if ":" in post_id else post_id
                    post_url = f"https://www.linkedin.com/feed/update/{post_id}"

                return PostResult(
                    success=True,
                    post_id=post_id,
                    post_url=post_url
                )

            else:
                return PostResult(
                    success=False,
                    error=f"API error {response.status_code}: {response.text}"
                )

        except Exception as e:
            return PostResult(
                success=False,
                error=str(e)
            )

    def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete a LinkedIn post.

        Args:
            access_token: Valid LinkedIn access token
            post_id: ID of the post to delete

        Returns:
            True if deleted successfully
        """
        try:
            response = requests.delete(
                f"{self.POSTS_URL}/{post_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "LinkedIn-Version": "202401"
                }
            )
            return response.status_code in [200, 204]
        except:
            return False


# Singleton instance
linkedin_poster = LinkedInPoster()

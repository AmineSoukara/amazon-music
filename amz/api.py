"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import re
from asyncio.exceptions import TimeoutError
from json.decoder import JSONDecodeError

import requests
from dotmap import DotMap
from requests.exceptions import ConnectionError
from urllib3.exceptions import MaxRetryError, NewConnectionError

from .errors import (
    ApiConnectionError,
    InvalidAccessToken,
    RateLimitExceeded,
    UserBanned,
)


class API:
    """A client for interacting with a music API service.

    This class provides methods to communicate with the API, handle authentication,
    and process responses. It includes error handling for common API issues and
    convenience methods for specific endpoints.

    Attributes:
        api_url (str): The base URL of the API service.
        timeout (int): Request timeout in seconds (default: 60).
        access_token (str): Bearer token for API authentication.
    """

    def __init__(self, api_url: str, access_token: str = "", timeout: int = 60):
        """Initialize the API client.

        Args:
            api_url: The base URL of the API service (with or without protocol).
            access_token: Optional bearer token for authenticated requests.
            timeout: Request timeout in seconds (default: 60).
        """
        self.api_url = self.format_api_url(api_url.strip(" /"))
        self.timeout = timeout
        self.access_token = access_token

    def format_api_url(self, url: str) -> str:
        """Ensure the API URL has a proper HTTP protocol prefix.

        Args:
            url: The base URL to format.

        Returns:
            The URL with http:// prefix if no protocol was specified.

        Example:
            >>> format_api_url("api.example.com")
            "http://api.example.com"
            >>> format_api_url("https://api.example.com")
            "https://api.example.com"
        """
        if not re.match(r"(?:http|ftp|https)://", url):
            return f"http://{url}"
        return url

    def fetch(
        self, route: str, method: str = "GET", params: dict = None, json: dict = None
    ) -> DotMap:
        """Make a request to the API and handle the response.

        Args:
            route: API endpoint path (e.g., "search", "account")
            method: HTTP method (GET or POST)
            params: Query parameters for the request
            json: JSON payload for POST requests

        Returns:
            DotMap: API response data with dot notation access

        Raises:
            InvalidAccessToken: When authentication fails (401/422)
            RateLimitExceeded: When rate limits are hit (429)
            UserBanned: When account is banned (403)
            ApiConnectionError: For network/connection issues
        """
        # Validate HTTP method
        method = method.upper()
        if method not in ("GET", "POST"):
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Prepare request components
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        url = f"{self.api_url}/{route.lstrip('/')}"
        request_args = {
            "method": method,
            "url": url,
            "headers": headers,
            "timeout": self.timeout,
        }

        # Add method-specific parameters
        if method == "GET" and params:
            request_args["params"] = params
        elif method == "POST" and json:
            request_args["json"] = json

        try:
            # Execute the request
            response = requests.request(**request_args)

            # Handle HTTP errors
            if response.status_code == 401 or response.status_code == 422:
                raise InvalidAccessToken("Invalid or expired access token")
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Try after: {retry_after} seconds"
                )
            elif response.status_code == 403:
                raise UserBanned(
                    "Forbidden, please check your token status or add new one"
                )
            elif not response.ok:
                raise ApiConnectionError(
                    f"API request failed with status {response.status_code}"
                )

            # Parse successful response
            try:
                return DotMap(response.json()) if response.content else DotMap()
            except ValueError:
                return DotMap({"content": response.text})

        except (TimeoutError, ConnectionError, MaxRetryError, NewConnectionError) as e:
            raise ApiConnectionError(f"Network error while connecting to {url}") from e
        except JSONDecodeError as e:
            raise ApiConnectionError(f"Failed to parse response from {url}") from e
        except Exception as e:
            raise ApiConnectionError(
                f"Unexpected error during API request: {str(e)}"
            ) from e

    # ----------- API ENDPOINT METHODS -----------

    def get_account_info(self) -> DotMap:
        """Get information about the authenticated user's account.

        Returns:
            Account information including user details, preferences, etc.
        """
        return self.fetch("account")

    def search(self, query: str, type: str = "track", max_results: int = 25) -> DotMap:
        """Search the API for content.

        Args:
            query: The search query string.
            type: The type of content to search for (default: "track").
                  Possible values: "track", "album", "artist", "playlist", etc.
            max_results: Maximum number of results to return (default: 25).

        Returns:
            Search results matching the query.
        """
        return self.fetch(
            "search", params={"query": query, "type": type, "max_results": max_results}
        )

    def get_track(self, track_id: str) -> DotMap:
        """Get detailed information about a specific track.

        Args:
            track_id: The unique identifier for the track.

        Returns:
            Track metadata including title, artist, duration, etc.
        """
        return self.fetch("track", params={"id": track_id})

    def get_album(self, album_id: str) -> DotMap:
        """Get detailed information about a specific album.

        Args:
            album_id: The unique identifier for the album.

        Returns:
            Album metadata including title, artist, track list, etc.
        """
        return self.fetch("album", params={"id": album_id})

    def get_artist(self, artist_id: str) -> DotMap:
        """Get detailed information about a specific artist.

        Args:
            artist_id: The unique identifier for the artist.

        Returns:
            Artist metadata including name, bio, discography, etc.
        """
        return self.fetch("artist", params={"id": artist_id})

    def get_playlist(self, playlist_id: str) -> DotMap:
        """Get detailed information about a specific playlist.

        Args:
            playlist_id: The unique identifier for the playlist.

        Returns:
            Playlist metadata including title, creator, track list, etc.
        """
        return self.fetch("playlist", params={"id": playlist_id})

    def get_playlist_community(self, playlist_id: str) -> DotMap:
        """Get community-generated content for a playlist.

        Args:
            playlist_id: The unique identifier for the playlist.

        Returns:
            Community content related to the playlist (comments, ratings, etc.).
        """
        return self.fetch("community_playlist", params={"id": playlist_id})

    def get_podcast_show(self, podcast_id: str) -> DotMap:
        """Get detailed information about a specific podcast show.

        Args:
            podcast_id: The unique identifier for the podcast.

        Returns:
            Podcast metadata including title, host, episode list, etc.
        """
        return self.fetch("podcast", params={"id": podcast_id})

    def get_track_lyrics(self, track_id: str) -> DotMap:
        """Get lyrics for a specific track.

        Args:
            track_id: The unique identifier for the track.

        Returns:
            Lyrics data including synchronized timestamps if available.
        """
        return self.fetch("lyrics", params={"id": track_id})

    def get_stream_urls(self, track_id: str) -> DotMap:
        """Get streaming URLs for a specific track.

        Args:
            track_id: The unique identifier for the track.

        Returns:
            URLs for streaming the track in various qualities/formats.
        """
        return self.fetch("stream_urls", params={"id": track_id})

    def get_widevine_key(self, pssh: str) -> DotMap:
        """Get Widevine DRM key for protected content.

        Args:
            pssh: The Protection System Specific Header for DRM content.

        Returns:
            Decryption key and related DRM information.
        """
        return self.fetch("widevine_key", method="POST", json={"pssh": pssh})

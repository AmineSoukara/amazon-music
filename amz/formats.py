"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

from enum import StrEnum
from typing import Any, Dict

from pathvalidate import sanitize_filename, sanitize_filepath


class FileFormat(StrEnum):
    """
    Enum representing different file naming formats for tracks.
    Formats can include title, artist, and quality information.
    """

    TITLE_ARTIST = "{track_explicit}{title} - {artist}"
    TITLE_ARTIST_QUALITY = "{track_explicit}{title} - {artist} ({quality})"
    ARTIST_TITLE = "{track_explicit}{artist} - {title}"
    ARTIST_TITLE_QUALITY = "{track_explicit}{artist} - {title} ({quality})"


FILE_FORMATS = {
    1: FileFormat.TITLE_ARTIST,
    2: FileFormat.TITLE_ARTIST_QUALITY,
    3: FileFormat.ARTIST_TITLE,
    4: FileFormat.ARTIST_TITLE_QUALITY,
}


class FolderFormat(StrEnum):
    """
    Enum representing different folder naming formats for albums.
    Formats can include album name, artist, and quality information.
    """

    ALBUM_ARTIST = "{album_explicit}{album} - {album_artist}"
    ALBUM_ARTIST_QUALITY = "{album_explicit}{album} - {album_artist} ({quality})"
    ARTIST_ALBUM = "{album_explicit}{album_artist} - {album}"
    ARTIST_ALBUM_QUALITY = "{album_explicit}{album_artist} - {album} ({quality})"


FOLDER_FORMATS = {
    1: FolderFormat.ALBUM_ARTIST,
    2: FolderFormat.ALBUM_ARTIST_QUALITY,
    3: FolderFormat.ARTIST_ALBUM,
    4: FolderFormat.ARTIST_ALBUM_QUALITY,
}


def get_file_name(
    track_data: Dict[str, Any],
    album_data: Dict[str, Any],
    file_format_number: int = 4,
    quality: str = "",
) -> str:
    """
    Generate a sanitized filename for a track based on the specified format.

    Args:
        track_data: Dictionary containing track information
        album_data: Dictionary containing album information
        file_format_number: Index of the format to use (default: 4)
        quality: Quality string to include in filename if format supports it

    Returns:
        Sanitized filename string

    Raises:
        KeyError: If required data is missing from track_data or album_data
    """
    try:
        file_format = FILE_FORMATS[file_format_number]
        name = file_format.format(
            track_explicit="🅴 " if track_data.get("explicit") else "",
            title=track_data["title"],
            artist=track_data["artist"]["name"],
            album=track_data["album"]["title"],
            album_explicit="🅴 " if album_data.get("explicit") else "",
            quality=quality,
        )
        return sanitize_filename(name)
    except KeyError as e:
        raise KeyError(f"Missing required track data: {e}")


def get_folder_name(
    album_data: Dict[str, Any],
    folder_format_number: int = 4,
    quality: str = "",
) -> str:
    """
    Generate a sanitized folder name for an album based on the specified format.

    Args:
        album_data: Dictionary containing album information
        folder_format_number: Index of the format to use (default: 4)
        quality: Quality string to include in folder name if format supports it

    Returns:
        Sanitized folder path string

    Raises:
        KeyError: If required data is missing from album_data
    """
    try:
        folder_format = FOLDER_FORMATS[folder_format_number]
        folder = folder_format.format(
            album_explicit="🅴 " if album_data.get("explicit") else "",
            album=album_data["title"],
            album_artist=album_data["artist"]["name"],
            quality=quality,
        )
        return sanitize_filepath(folder)
    except KeyError as e:
        raise KeyError(f"Missing required album data: {e}")

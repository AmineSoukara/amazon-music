"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import random
from collections import Counter
from pathlib import Path
from typing import List, Optional, Union
from zipfile import ZIP_DEFLATED, ZipFile

from .printer import error


def zip_music_folder(file_path: Union[str, Path], ignore_disc: bool = True) -> str:
    """
    Generate a zip file path for a music folder, optionally ignoring 'Disc' folders.

    Args:
        file_path: Path to an MP3 file within the folder to be zipped
        ignore_disc: If True and the file is in a 'Disc X' folder,
                     the zip will be created for the parent folder

    Returns:
        Path for the zip file to be created
    """
    folder_path = Path(file_path).parent

    # If ignoring 'Disc' folders, move up one level if inside a 'Disc X' folder
    if ignore_disc and folder_path.name.lower().startswith("disc "):
        folder_path = folder_path.parent

    return str(folder_path.with_suffix(".zip"))


def create_zip(tracks: List, zip_path: Union[str, Path]) -> Optional[str]:
    """
    Create a zip archive containing music tracks, preserving disc folder structure.

    Args:
        tracks: List of Track objects with file paths
        zip_path: Destination path for the zip file

    Returns:
        Path of the created zip file, or None if no valid tracks were processed
    """
    if not tracks:
        return None

    valid_tracks = [
        t for t in tracks if getattr(t, "file", None) and Path(t.file).is_file()
    ]
    if not valid_tracks:
        return None

    try:
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as z:
            for track in valid_tracks:
                track_path = Path(track.file)
                parts = track_path.parts

                # Find the first "Disc X" directory in the path
                disc_dir = next(
                    (p for p in parts if p.lower().startswith("disc ")), None
                )

                if disc_dir:
                    # Get all parts starting from the disc directory
                    disc_index = parts.index(disc_dir)
                    relative_path = Path(*parts[disc_index:])
                else:
                    # No disc folder - just use the filename
                    relative_path = track_path.name

                z.write(str(track_path), str(relative_path))

        return str(zip_path)

    except (IOError, OSError) as e:
        error(f"Error creating zip file: {e}")
        return None


def get_repeated_or_random_quality(
    qualities: List[Optional[str]], default: Optional[str] = None
) -> Optional[str]:
    """
    Get the first repeated quality or a random quality from a list.

    Args:
        qualities: List of quality strings (may contain None)
        default: Default value to return if no valid qualities found

    Returns:
        First repeated quality if exists, otherwise random non-None quality,
        or default if no valid qualities exist
    """
    # Filter out None values and empty strings
    valid_qualities = [q for q in qualities if q and str(q).strip()]

    if not valid_qualities:
        return default

    # Count occurrences of each quality
    quality_counts = Counter(valid_qualities)

    # Check for the first repeated quality
    for quality in valid_qualities:
        if quality_counts[quality] > 1:
            return quality

    # If no repeated quality, return a random quality or default
    return random.choice(valid_qualities) if default is None else default

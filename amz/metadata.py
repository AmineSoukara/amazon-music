"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import base64
import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import requests
from mutagen.flac import FLAC as MutagenFLAC
from mutagen.flac import Picture
from mutagen.mp4 import MP4 as MutagenMP4
from mutagen.mp4 import MP4Cover, MP4FreeForm
from mutagen.oggopus import OggOpus

from .printer import error, warning

ENCODER = "Amazon"
COMMENT = "Amazon Music"


class MetadataHandler:
    """Handles metadata operations for audio files."""

    @staticmethod
    def ms_to_lrc_timestamp(ms: int) -> str:
        """Convert milliseconds to LRC timestamp format."""
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        centiseconds = (ms % 1000) // 10
        return f"[{minutes:02}:{seconds:02}.{centiseconds:02}]"

    @staticmethod
    def synced_to_lrc(synced: list) -> str:
        """Convert synced lyrics to LRC format."""
        newline_char = "\n"
        return "\n".join(
            f"{MetadataHandler.ms_to_lrc_timestamp(item['start'])}"
            f"{item['text'].replace(newline_char, ' ').strip()}"
            for item in synced
        )

    @staticmethod
    def ms_timestamp_to_date_str(
        ms_timestamp: int, fmt: str = "%Y-%m-%d"
    ) -> Optional[str]:
        """Convert millisecond timestamp to formatted date string."""
        try:
            dt = datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)
            return dt.strftime(fmt)
        except Exception:
            warning(f"Invalid timestamp: {ms_timestamp}")
            return None

    @staticmethod
    def process_lyrics(lyrics: Dict) -> str:
        """Extract and format lyrics from dictionary."""
        if not lyrics:
            return ""

        if lyrics.get("synced"):
            return MetadataHandler.synced_to_lrc(lyrics["synced"])
        return lyrics.get("text", "")

    @staticmethod
    def add_flac_metadata(
        track_path: str,
        track: Dict,
        cover_data: Optional[bytes],
        date_str: str,
        year_str: str,
        lyric_text: str,
    ) -> bool:
        """Add metadata to FLAC files."""
        try:
            metadata = MutagenFLAC(track_path)

            if cover_data:
                picture = Picture()
                picture.data = cover_data
                picture.mime = "image/jpeg"
                metadata.add_picture(picture)

            metadata.update(
                {
                    "TITLE": track.get("title", ""),
                    "WORK": track.get("title", ""),
                    "TRACKNUMBER": str(track.get("track_num", "")),
                    "DISCNUMBER": str(track.get("disc_num", "")),
                    "ALBUM": track.get("album", {}).get("title", ""),
                    "ARTIST": track.get("artist", {}).get("name", ""),
                    "ALBUMARTIST": track.get("artist", {}).get("name", ""),
                    "encodedby": ENCODER,
                    "comment": COMMENT,
                    **(
                        {"GENRE": track["genre"], "ORIGINALGENRE": track["genre"]}
                        if track.get("genre")
                        else {}
                    ),
                    **(
                        {"DATE": date_str, "ORIGINALDATE": date_str} if date_str else {}
                    ),
                    **(
                        {"YEAR": year_str, "ORIGINALYEAR": year_str} if year_str else {}
                    ),
                    **(
                        {"COPYRIGHT": track["copyright"]}
                        if track.get("copyright")
                        else {}
                    ),
                    **({"ISRC": track["isrc"]} if track.get("isrc") else {}),
                    **({"BPM": str(track["bpm"])} if track.get("bpm") else {}),
                    **({"LYRICS": lyric_text} if lyric_text else {}),
                }
            )

            metadata.save(track_path)
            return True
        except Exception as e:
            error(f"FLAC metadata error: {e}")
            return False

    @staticmethod
    def add_m4a_metadata(
        track_path: str,
        track: Dict,
        cover_data: Optional[bytes],
        date_str: str,
        year_str: str,
        lyric_text: str,
    ) -> bool:
        """Add metadata to M4A files."""
        try:
            metadata = MutagenMP4(track_path)

            if cover_data:
                metadata["covr"] = [
                    MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)
                ]

            if lyric_text:
                metadata["\xa9lyr"] = [lyric_text]

            tag_dict = {
                "\xa9nam": track.get("title", ""),
                "trkn": [[track.get("track_num", 0), 0]],
                "disk": [[track.get("disc_num", 0), 0]],
                "aART": track.get("artist", {}).get("name", ""),
                "\xa9ART": track.get("artist", {}).get("name", ""),
                "\xa9alb": track.get("album", {}).get("title", ""),
                "\xa9too": ENCODER,
                "\xa9cmt": COMMENT,
                **({"\xa9gen": track["genre"]} if track.get("genre") else {}),
                **({"\xa9day": date_str} if date_str else {}),
                **(
                    {"\xa9wrt": ", ".join(track["song_writers"])}
                    if track.get("song_writers")
                    else {}
                ),
            }

            if track.get("isrc"):
                tag_dict["----:com.apple.iTunes:ISRC"] = [
                    MP4FreeForm(track["isrc"].encode("utf-8"))
                ]

            metadata.update(tag_dict)
            metadata.save(track_path)
            return True
        except Exception as e:
            error(f"M4A metadata error: {e}")
            return False

    @staticmethod
    def add_opus_metadata(
        track_path: str,
        track: Dict,
        cover_data: Optional[bytes],
        date_str: str,
        year_str: str,
        lyric_text: str,
    ) -> bool:
        """Add metadata to Opus files."""
        try:
            metadata = OggOpus(track_path)

            metadata.update(
                {
                    "TITLE": track.get("title", ""),
                    "TRACKNUMBER": str(track.get("track_num", "")),
                    "DISCNUMBER": str(track.get("disc_num", "")),
                    "ALBUM": track.get("album", {}).get("title", ""),
                    "ARTIST": track.get("artist", {}).get("name", ""),
                    "ALBUMARTIST": track.get("artist", {}).get("name", ""),
                    "ENCODED-BY": ENCODER,
                    "COMMENT": COMMENT,
                    **(
                        {"GENRE": track["genre"], "ORIGINALGENRE": track["genre"]}
                        if track.get("genre")
                        else {}
                    ),
                    **(
                        {"DATE": date_str, "ORIGINALDATE": date_str} if date_str else {}
                    ),
                    **(
                        {"YEAR": year_str, "ORIGINALYEAR": year_str} if year_str else {}
                    ),
                    **(
                        {"COPYRIGHT": track["copyright"]}
                        if track.get("copyright")
                        else {}
                    ),
                    **({"ISRC": track["isrc"]} if track.get("isrc") else {}),
                    **({"BPM": str(track["bpm"])} if track.get("bpm") else {}),
                    **({"LYRICS": lyric_text} if lyric_text else {}),
                }
            )

            if cover_data:
                pic = Picture()
                pic.data = cover_data
                pic.type = 3
                pic.mime = "image/jpeg"
                encoded_pic = base64.b64encode(pic.write()).decode("ascii")
                metadata["METADATA_BLOCK_PICTURE"] = [encoded_pic]

            metadata.save(track_path)
            return True
        except Exception as e:
            error(f"Opus metadata error: {e}")
            return False

    @staticmethod
    def add_metadata(
        track_path: str, track: Dict, album: Optional[Dict] = None, lyrics: Dict = {}
    ) -> bool:
        """Main method to add metadata to audio files."""
        if not track_path or not os.path.exists(track_path):
            error(f"Track path does not exist: {track_path}")
            return False

        extension = Path(track_path).suffix.lower()[1:]
        handlers = {
            "flac": MetadataHandler.add_flac_metadata,
            "m4a": MetadataHandler.add_m4a_metadata,
            "opus": MetadataHandler.add_opus_metadata,
            "ogg": MetadataHandler.add_opus_metadata,
        }

        if extension not in handlers:
            error(f"Unsupported file format: {extension}")
            return False

        try:
            # Prepare common data
            cover_data = Cover(track["image"]).content if track.get("image") else None
            release_date_ms = track.get("release_date")
            date_str = MetadataHandler.ms_timestamp_to_date_str(release_date_ms)
            year_str = date_str[:4] if date_str else ""
            lyric_text = MetadataHandler.process_lyrics(lyrics)

            return handlers[extension](
                track_path, track, cover_data, date_str, year_str, lyric_text
            )
        except Exception as e:
            error(f"Metadata processing failed: {e}")
            traceback.print_exc()
            return False


class Cover:
    """Handles cover art downloading and saving."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.content = self._download()

    def _download(self) -> Optional[bytes]:
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            error(f"Cover download failed: {e}")
            return None

    def save(self, filename: Optional[str] = None) -> Optional[str]:
        """Save cover art to file."""
        if not self.content:
            error("No cover content to save")
            return None

        directory = "Songs"
        os.makedirs(directory, exist_ok=True)
        filename = filename or f"{uuid.uuid4()}_image.jpg"
        file_path = os.path.join(directory, filename)

        try:
            with open(file_path, "wb") as f:
                f.write(self.content)
            return file_path
        except Exception as e:
            error(f"Cover save failed: {e}")
            return None

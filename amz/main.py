"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import os
import signal
import sys
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotmap import DotMap
from pathvalidate import sanitize_filename

from .api import API
from .converter import AudioConverter, AudioExtension
from .formats import get_file_name, get_folder_name
from .metadata import MetadataHandler
from .printer import (
    error,
    info,
    new_task,
    print_trace,
    progress,
    section,
    start_progress,
    stop_progress,
    success,
    update_task,
    warning,
)
from .utils import create_zip, get_repeated_or_random_quality, zip_music_folder

# Global dictionary to track task progress
TASKS_PROGRESS: Dict[str, Dict] = {}


@dataclass
class DownloadResult:
    """Simple result container for download operations."""

    success: bool = False
    quality: Optional[str] = None
    img: Dict[str, Optional[str]] = None
    file: Optional[str] = None
    data: Dict[str, Any] = None
    lyrics: Dict[str, Any] = None
    tracks: List[Dict[str, Any]] = None
    failed: List[str] = None
    total_tracks: int = 0
    zip: Optional[str] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.img is None:
            self.img = {}
        if self.data is None:
            self.data = {}
        if self.lyrics is None:
            self.lyrics = {}
        if self.tracks is None:
            self.tracks = []
        if self.failed is None:
            self.failed = []


class StreamQuality:
    """Handles quality selection logic for streams."""

    QUALITY_MAP = {
        "Max": ["UHD_192"],
        "Master": ["UHD_96"],
        "High": ["UHD_48", "UHD_44", "HD_44"],
        "Atmos_AC-4": [
            "SPATIAL_ATMOS_HIGH_AC-4",
            "SPATIAL_ATMOS_MEDIUM_AC-4",
            "SPATIAL_ATMOS_LOW_AC-4",
        ],
        "Atmos_EC-3": [
            "SPATIAL_ATMOS_HIGH_EC-3",
            "SPATIAL_ATMOS_MEDIUM_EC-3",
            "SPATIAL_ATMOS_LOW_EC-3",
        ],
        "Normal": ["SD_HIGH"],
        "Medium": ["SD_MEDIUM"],
        "Low": ["SD_LOW"],
        "Free": ["LD_MEDIUM", "LD_LOW"],
    }

    FALLBACK_ORDER = ["Max", "Master", "High", "Normal", "Medium", "Low", "Free"]
    ATMOS_ORDER = ["Atmos_AC-4", "Atmos_EC-3"]
    # Prioritize EC-3 for Sonos compatibility
    SONOS_ATMOS_ORDER = ["Atmos_EC-3", "Atmos_AC-4"]

    @classmethod
    def get_best_stream(
        cls,
        parsed_manifest: List[Dict],
        quality_preference: str,
        fallback: bool = False,
        sonos_compatible: bool = False,
    ) -> Optional[Dict]:
        """Select the best available stream based on quality preference."""
        quality_to_human = {}
        for human, codes in cls.QUALITY_MAP.items():
            for code in codes:
                quality_to_human.setdefault(code, human)

        for stream in parsed_manifest:
            stream["quality_human"] = quality_to_human.get(stream.get("quality"))

        pref = quality_preference.strip()

        # Determine search order based on preference and Sonos compatibility
        if pref in cls.ATMOS_ORDER:
            search_order = (
                cls.SONOS_ATMOS_ORDER if sonos_compatible else cls.ATMOS_ORDER
            )
        else:
            search_order = cls._get_fallback_order(pref.title())

        for group in search_order:
            qualities = cls.QUALITY_MAP.get(group, [])
            candidates = [s for s in parsed_manifest if s.get("quality") in qualities]
            if candidates:
                return max(candidates, key=lambda s: s.get("bandwidth", 0))

        return (
            max(parsed_manifest, key=lambda s: s.get("bandwidth", 0))
            if fallback and parsed_manifest
            else None
        )

    @classmethod
    def _get_fallback_order(cls, pref: str) -> List[str]:
        """Get quality fallback order starting from preferred quality."""
        if pref in cls.FALLBACK_ORDER:
            idx = cls.FALLBACK_ORDER.index(pref)
            return cls.FALLBACK_ORDER[idx:]
        return cls.FALLBACK_ORDER


class AmDownloader:
    """Main downloader class for Amazon Music content."""

    def __init__(
        self,
        path: str = None,  # Defaults to Windows Music folder
        path_temp: str = None,  # Defaults to "temp" inside Music folder
        api_url: str = "https://amazon-music-api.vercel.app",
        access_token: str = "",
        target_extension: AudioExtension = AudioExtension.OPUS,
    ):
        # Set default paths
        self.path = path or str(Path.home() / "Music/Amazon Music")
        self.path_temp = path_temp or str(
            Path(self.path) / "temp"
        )  # Inside Music folder

        self.api = API(api_url, access_token)
        self.target_extension = target_extension
        self._should_stop = False
        self._active_futures = []

        # Create directories if they don't exist
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(self.path_temp, exist_ok=True)

        # Setup signal handlers
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals (Ctrl+C)."""
        self._should_stop = True
        info("\n🚨 Received interrupt signal - Cancelling downloads...")

        # Cancel all active futures
        for future in self._active_futures:
            if not future.done():
                future.cancel()

        # Wait a moment for cancellations to process
        time.sleep(1)
        sys.exit(1)

    def _update_task_progress(
        self, task_id: str, success: bool = False, error: bool = False
    ) -> None:
        """Update the global task progress tracker."""
        if task_id in TASKS_PROGRESS:
            TASKS_PROGRESS[task_id]["current"] += 1
            if success:
                TASKS_PROGRESS[task_id]["success"] += 1
            if error:
                TASKS_PROGRESS[task_id]["errors"] += 1

    def download_stream(
        self,
        stream_info: Dict,
        headers: Optional[Dict] = None,
        out_path: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[str]:
        """Download stream segments and combine them into one file."""
        if self._should_stop:
            return None

        if not (base_url := stream_info.get("base_url")):
            error("No base_url found in stream_info")
            return None

        segments = stream_info.get("segments", [])
        if not segments:
            error("No segments found in stream_info")
            return None

        out_path = out_path or os.path.join(
            self.path_temp,
            f"{uuid.uuid4()}_{stream_info.get('quality', 'audio')}.mp4",
        )

        total_bytes = self._calculate_total_bytes(segments)
        desc = f"🎧 {os.path.basename(name) if name else 'Stream'}"

        with open(out_path, "wb") as out_file:
            if not progress.live.is_started:
                start_progress()

            task_id = progress.add_task(desc, total=total_bytes)

            try:
                for seg in segments:
                    if self._should_stop:
                        break

                    if not (
                        seg_range := seg.get("initialization_range")
                        or seg.get("media_range")
                    ):
                        continue
                    self._download_segment(
                        base_url,
                        seg_range,
                        headers or {},
                        out_file,
                        lambda size: progress.update(task_id, advance=size),
                    )

                if self._should_stop:
                    if os.path.exists(out_path):
                        os.remove(out_path)
                    return None

                return out_path

            except Exception as e:
                error(f"Download failed: {e}")
                if os.path.exists(out_path):
                    os.remove(out_path)
                return None
            finally:
                progress.remove_task(task_id)

    def _calculate_total_bytes(self, segments: List[Dict]) -> int:
        """Calculate total bytes to download from segments."""
        return sum(
            int(seg_range.split("-")[1]) - int(seg_range.split("-")[0]) + 1
            for seg in segments
            if (seg_range := seg.get("initialization_range") or seg.get("media_range"))
        )

    def _download_segment(
        self, base_url: str, seg_range: str, headers: Dict, out_file, progress_callback
    ) -> None:
        """Download a single segment and update progress."""
        if self._should_stop:
            return

        headers = headers.copy()
        headers["Range"] = f"bytes={seg_range}"
        resp = requests.get(base_url, headers=headers, stream=True)
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=8192):
            if self._should_stop:
                break
            out_file.write(chunk)
            progress_callback(len(chunk))

    def download_track(
        self,
        track_id: str,
        quality: str = "Normal",
        folder_format: int = 4,
        track_format: int = 4,
        album_data: Optional[Dict] = None,
        overwrite: bool = False,
        from_batch: bool = False,
    ) -> DownloadResult:
        """Download a single track with metadata."""
        if self._should_stop:
            return DownloadResult()

        result = DownloadResult(quality=quality)

        try:
            # Fetch track data
            if not (track_res := self.api.get_track(track_id)).success:
                error(f"[Track] Not found: {track_id}")
                return result

            track_data = track_res.data
            result.data = track_data

            if not from_batch:
                section(
                    f"🎵 Downloading track: {
                        track_data['title']} by {
                        track_data['artist']['name']}"
                )

            # Fetch album data if not provided
            if (
                not album_data
                and (album_res := self.api.get_album(track_data["album"]["id"])).success
            ):
                album_data = album_res.data

            if not album_data:
                error(f"[Album] Not found for track: {track_id}")
                return result

            # Get stream info
            if not (stream_res := self.api.get_stream_urls(track_id)).success:
                error(f"[Stream] No URLs for track: {track_id}")
                return result

            # Process stream and download
            sonos_mode = quality == "Atmos_EC-3"
            best_stream = StreamQuality.get_best_stream(
                stream_res.data, quality, sonos_compatible=sonos_mode
            )
            if not best_stream:
                error(f"[Stream] No suitable stream for track: {track_id}")
                return result

            stream_quality = best_stream.get("quality_human", quality)
            if stream_quality != quality:
                warning(f"Using {stream_quality} instead of {quality}")
                result.quality = stream_quality

            # Prepare paths
            filename = get_file_name(
                track_data, album_data, track_format, stream_quality
            )
            foldername = get_folder_name(album_data, folder_format, stream_quality)
            final_path = os.path.join(self.path, foldername, filename)

            if (
                os.path.exists(
                    final_path
                    + (
                        ".flac"
                        if quality in ["Max", "Master", "High"]
                        else self.target_extension.value
                    )
                )
                and not overwrite
            ):  # todo handle flac
                info(f"[Skip] File exists: {final_path}")
                result.success = True
                result.file = final_path
                result.img = DotMap(url=track_data.get("image"))
                if lyrics := track_data.get("lyrics", {}).get("lyrics"):
                    result.lyrics = DotMap(lyrics)
                return result

            os.makedirs(os.path.dirname(final_path), exist_ok=True)

            # Download and convert
            if not (raw_path := self.download_stream(best_stream, name=filename)):
                return result

            if not (
                key_res := self.api.get_widevine_key(best_stream.get("pssh", ""))
            ).success:
                error(f"[DRM] No key for track: {track_id}")
                return result

            converter = AudioConverter(target_extension=self.target_extension)
            if not (
                converted_path := converter.convert(
                    raw_path,
                    best_stream.get("codecs"),
                    final_path,
                    decryption_key=key_res.data,
                )
            ):
                return result

            # Clean up and add metadata
            os.remove(raw_path)
            if not MetadataHandler.add_metadata(
                converted_path,
                track_data,
                album_data,
                lyrics=track_data.get("lyrics", {}).get("lyrics"),
            ):
                error(f"[Metadata] Failed for track: {track_id}")
                return result

            result.success = True
            result.file = converted_path
            result.img = DotMap(url=track_data.get("image"))
            if lyrics := track_data.get("lyrics", {}).get("lyrics"):
                result.lyrics = DotMap(lyrics)

        except Exception as e:
            error(f"[Error] Track {track_id}: {e}")
            traceback.print_exc()

        if not from_batch:
            success("Downloaded Successfully")

        return result

    def _batch_download(
        self,
        items: List[Dict],
        quality: str,
        folder_format: int,
        track_format: int,
        max_workers: int,
        task_id: str,
        overwrite: bool,
        album_data: Optional[Dict] = None,
    ) -> DownloadResult:
        if self._should_stop:
            return DownloadResult()

        result = DownloadResult(quality=quality)
        result.total_tracks = len(items)

        section(f"🎶 Downloading {len(items)} track(s)")
        TASKS_PROGRESS[task_id] = {
            "total": len(items),
            "start_time": time.time(),
            "type": "Album" if album_data else "Playlist",
            "success": 0,
            "errors": 0,
            "current": 0,
            "limit": len(items),
        }

        start_progress()
        task_bar_id = new_task("Downloading Tracks", total=len(items))

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self.download_track,
                        item["id"],
                        quality,
                        folder_format,
                        track_format,
                        album_data,
                        overwrite,
                        from_batch=True,
                    ): item["id"]
                    for item in items
                }

                # Store futures for potential cancellation
                self._active_futures = list(futures.keys())

                for future in as_completed(futures):
                    if self._should_stop:
                        break

                    track_id = futures[future]
                    try:
                        track_result = future.result()
                        update_task(task_bar_id)

                        if track_result.success:
                            result.tracks.append(track_result)
                            self._update_task_progress(task_id, success=True)
                            success(f"Downloaded: {track_result.file}")
                        else:
                            result.failed.append(track_id)
                            self._update_task_progress(task_id, error=True)
                            warning(f"Failed: {track_id}")
                    except Exception as e:
                        if not isinstance(e, KeyboardInterrupt):
                            result.failed.append(track_id)
                            self._update_task_progress(task_id, error=True)
                            error(f"Error downloading track {track_id}")
                            print_trace(e)

        except KeyboardInterrupt:
            self._should_stop = True
            info("\n🚨 Download cancelled by user")
        finally:
            self._active_futures.clear()
            stop_progress()

        result.success = bool(result.tracks)
        result.quality = get_repeated_or_random_quality(
            [t.quality for t in result.tracks], quality
        )
        return result

    def download_album(
        self,
        album_id: str,
        quality: str = "Normal",
        folder_format: int = 4,
        track_format: int = 4,
        max_workers: int = 2,
        as_zip: bool = False,
        task_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> DownloadResult:
        """Download all tracks in an album."""
        if self._should_stop:
            return DownloadResult()

        task_id = task_id or str(uuid.uuid4())

        if not (meta_res := self.api.get_album(album_id)).success:
            error(f"[Album] Not found: {album_id}")
            return DownloadResult()

        meta = meta_res.data
        items = meta.get("tracks", [])

        TASKS_PROGRESS[task_id] = {
            "total": len(items),
            "start_time": time.time(),
            "type": "Album ZIP" if as_zip else "Album",
            "success": 0,
            "errors": 0,
            "current": 0,
            "limit": len(items),
        }

        result = self._batch_download(
            items,
            quality,
            folder_format,
            track_format,
            max_workers,
            task_id,
            overwrite,
            meta,
        )
        result.data = meta
        result.img = DotMap(url=meta.get("image"))

        if as_zip and result.tracks and not self._should_stop:
            result.zip = create_zip(
                result.tracks, zip_music_folder(result.tracks[0].file)
            )

        return result

    def download_playlist(
        self,
        playlist_id: str,
        quality: str = "Normal",
        folder_format: int = 4,
        track_format: int = 4,
        max_workers: int = 2,
        as_zip: bool = False,
        limit: int = 10,
        task_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> DownloadResult:
        """Download tracks from a playlist."""
        if self._should_stop:
            return DownloadResult()

        task_id = task_id or str(uuid.uuid4())
        is_community = playlist_id.endswith("sune")

        meta_res = (
            self.api.get_playlist_community(playlist_id)
            if is_community
            else self.api.get_playlist(playlist_id)
        )

        if not meta_res.success:
            error(f"[Playlist] Not found: {playlist_id}")
            return DownloadResult()

        meta = meta_res.data
        playlist = meta.get("playlist", {})
        items = meta.get("tracks", [])[:limit]

        TASKS_PROGRESS[task_id] = {
            "total": len(items),
            "start_time": time.time(),
            "type": "Playlist ZIP" if as_zip else "Playlist",
            "success": 0,
            "errors": 0,
            "current": 0,
            "limit": limit,
        }

        result = self._batch_download(
            items, quality, folder_format, track_format, max_workers, task_id, overwrite
        )
        result.data = meta
        result.img = DotMap(url=(playlist.get("images") or [None])[0])

        if as_zip and result.tracks and not self._should_stop:
            zip_name = sanitize_filename(
                f"{playlist.get('curated_by', 'Unknown')} - {playlist.get('title', 'Playlist')}.zip"
            )
            result.zip = os.path.join(self.path, zip_name)
            create_zip(result.tracks, result.zip)

        return result

"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""

import json
import os
import subprocess
from enum import Enum
from typing import Optional

from .printer import error, warning


class AudioExtension(Enum):
    FLAC = ".flac"
    M4A = ".m4a"
    OPUS = ".opus"
    OGG = ".ogg"
    MP3 = ".mp3"


class AudioConverter:
    def __init__(self, target_extension: AudioExtension = AudioExtension.OPUS):
        self.target_extension = target_extension

    @staticmethod
    def _get_audio_bitrate(input_path: str) -> Optional[str]:
        """Attempt to get the audio bitrate from a file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=bit_rate",
                "-of",
                "json",
                input_path,
            ]
            result = subprocess.run(cmd, capture_output=True, check=True)
            info = json.loads(result.stdout)
            if streams := info.get("streams"):
                bit_rate = streams[0].get("bit_rate")
                if bit_rate:
                    return f"{int(bit_rate) // 1000}k"
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            warning(f"[bitrate detection] failed: {e}")
        return None

    def convert(
        self,
        input_path: str,
        codec: str,
        output_name: str,
        decryption_key: Optional[str] = None,
    ) -> Optional[str]:
        """Convert an audio file to the specified format."""
        if not os.path.isfile(input_path):
            error(f"Input file does not exist: {input_path}")
            return None

        codec = codec.lower()
        ext = self.target_extension.value

        # Define codec map
        codec_map = {
            "flac": (".flac", "copy", []),
            "ec-3": (".m4a", "ac3", ["-metadata:s:a:0", "atmos=true"]),
            "ac-4.02.02.00": (".m4a", "ac4", ["-metadata:s:a:0", "atmos=true"]),
        }

        # Opus special handling
        if codec == "opus":
            if ext == ".m4a":
                codec_map["opus"] = (".m4a", "aac", [])
            elif ext in [".ogg", ".opus"]:
                codec_map["opus"] = (ext, "copy", [])

        if codec not in codec_map:
            error(f"Unsupported codec: {codec}")
            return None

        out_ext, audio_codec, extra_args = codec_map[codec]
        output_path = f"{output_name}{out_ext}"

        # Start building ffmpeg command
        ffmpeg_cmd = ["ffmpeg", "-y"]

        if decryption_key:
            ffmpeg_cmd += ["-decryption_key", decryption_key]

        ffmpeg_cmd += ["-i", input_path, "-c:a", audio_codec]

        # Bitrate logic (only for AAC)
        if audio_codec == "aac":
            bitrate = self._get_audio_bitrate(input_path) or "128k"
            ffmpeg_cmd += ["-b:a", bitrate]
            warning(f"Using AAC bitrate: {bitrate}")

        ffmpeg_cmd += extra_args

        # Enable faststart for M4A
        if out_ext == ".m4a":
            ffmpeg_cmd += ["-movflags", "+faststart"]

        ffmpeg_cmd += [output_path]

        result = subprocess.run(
            ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            error(f"[ffmpeg error] {result.stderr.decode(errors='ignore')}")
            return None

        # print(f"[ffmpeg] Conversion successful: {output_path}")
        return output_path

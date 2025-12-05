 <div align="center">
  <img src="https://i.imgur.com/Xj1dUCA.jpeg" alt="Amazon Music API" width="700">

# 🎵 Amazon Music API – Unofficial

A **FastAPI REST API** for Amazon Music offering metadata, playback, search, and lookups for tracks, albums, artists, playlists, and podcasts. Includes streaming URL extraction and Widevine DRM key retrieval.
<p>
  <a href="https://github.com/AmineSoukara/amazon-music/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/AmineSoukara/amazon-music" alt="Contributors">
  </a>
  <a href="https://github.com/AmineSoukara/amazon-music/commits/main">
    <img src="https://img.shields.io/github/last-commit/AmineSoukara/amazon-music" alt="Last commit">
  </a>
  <a href="https://github.com/AmineSoukara/amazon-music/network/members">
    <img src="https://img.shields.io/github/forks/AmineSoukara/amazon-music" alt="Forks">
  </a>
  <a href="https://github.com/AmineSoukara/amazon-music/stargazers">
    <img src="https://img.shields.io/github/stars/AmineSoukara/amazon-music?color=yellow" alt="Stars">
  </a>
  <a href="https://github.com/AmineSoukara/amazon-music/issues">
    <img src="https://img.shields.io/github/issues/AmineSoukara/amazon-music?color=purple" alt="Open Issues">
  </a>
  <a href="https://github.com/AmineSoukara/amazon-music/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/AmineSoukara/amazon-music.svg" alt="License">
  </a>
</p>

<h4>
  <a href="https://amz.dezalty.com">API Docs</a>
  <span> · </span>
  <a href="https://github.com/AmineSoukara/amazon-music/issues">Report Bug</a>
  <span> · </span>
  <a href="https://github.com/AmineSoukara/amazon-music/issues">Request Feature</a>
</h4>


---
> ⚠️ The API is still in development. For issues or suggestions: [contact support](https://bio.link/aminesoukara). Also This API requires a premium Amazon Music account. If you find it useful and have a premium account you'd like to donate, it would be greatly appreciated. Donations help keep the API running and support multi-region access.

---

## 📦 Installation
```bash
pip install amazon-music
```

## 🖥️ CLI Usage
The command-line interface provides easy access to Amazon Music content:

### Basic Commands
```bash
amz [URL_OR_ID] [OPTIONS]
```

<div align="left">
  
### Examples
```bash
# Download an track
amz https://music.amazon.com/albums/B077FLX9ZQ?trackAsin=B077F6QG2S

# Download an album
amz https://music.amazon.com/albums/B077FLX9ZQ

# Download a playlist with high quality
amz https://music.amazon.com/playlists/B0FBL3CC8M -q High

# Download a track by ID
amz B077F6QG2S -t track
```

### CLI Options
```
positional arguments:
  url_or_id             Amazon Music URL or ID

options:
  -h, --help      show this help message and exit
  --config        Interactive configuration setup
  -q, --quality {Max,Master,High,Normal,Medium,Low,Free}
          Audio quality preference (default: Normal)
  -t, --type {auto,track,album,playlist}
          Content type (default: auto-detect)
  -o OUTPUT, --output OUTPUT
          Output directory (default: ./Music)
  --temp-dir TEMP_DIR 
          Temporary directory (default: ./Music/temp)
  --format-folder {1,2,3,4}
          Folder naming format (1-4, default: 4)
  --format-track {1,2,3,4}
          Track naming format (1-4, default: 4)
  --workers WORKERS     Number of parallel download workers (default: 2)
  --zip                 Create ZIP archive for albums/playlists
  --overwrite           Overwrite existing files
  --token TOKEN         Amazon Music API access token
  --clear-token         Remove stored access token
  --show-token          Show the stored access token
  ```
</div>

## 🔐 Auth Token
Star the repository on GitHub, then click "Get Auth Tokens" to access your authentication credentials. [Click Here](https://amz.dezalty.com/login)

## 🎵 Quality

| Quality   | Specification                          | Bitrate          | Format |
|-----------|----------------------------------------|------------------|--------|
| Low       | 48kbps                                 | 48 kbps          | OPUS   |
| Medium    | 192kbps                                | 192 kbps         | OPUS   |
| Normal    | 320kbps                                | 320 kbps         | OPUS   |
| High      | ≤16-bit / ≤48 kHz                      | ≤1411 kbps       | FLAC   |
| Master    | 24-bit / ≤96 kHz                       | ≥2300 kbps       | FLAC   |
| Max       | 24-bit / ≤192 kHz                      | ≥4600 kbps       | FLAC   |

### 📁 File & Folder Naming Formats

#### Track File Formats

| ID | Format Name            | Example Output                          |
|----|------------------------|-----------------------------------------|
| 1  | TITLE_ARTIST          | {track_explicit}{title} - {artist}      |
| 2  | TITLE_ARTIST_QUALITY  | {title} - {artist} ({quality})          |
| 3  | ARTIST_TITLE          | {artist} - {title}                      |
| 4  | ARTIST_TITLE_QUALITY  | {artist} - {title} ({quality})          |

#### Album Folder Formats

| ID | Format Name              | Example Output                          |
|----|--------------------------|-----------------------------------------|
| 1  | ALBUM_ARTIST            | {album_explicit}{album} - {album_artist}|
| 2  | ALBUM_ARTIST_QUALITY    | {album} - {album_artist} ({quality})    |
| 3  | ARTIST_ALBUM            | {album_artist} - {album}                |
| 4  | ARTIST_ALBUM_QUALITY    | {album_artist} - {album} ({quality})    |

## 🔗 Quick Links
- **Base URL**: [Click Here](https://amz.dezalty.com)

---

## 📚 Endpoints Overview

| Method | Endpoint                            | Description                              |
| ------ | ----------------------------------- | ---------------------------------------- |
| `GET`  | `/login`                          | Get Access Tokens        |
| `GET`  | `/account`                          | Get authenticated account info           |
| `GET`  | `/search?query={query}&type={type}`                           | Search Amazon Music                      |
| `GET`  | `/track?id={track_id}`                 | Get metadata for a track                 |
| `GET`  | `/album?id={album_id}`                 | Get album details including tracks       |
| `GET`  | `/artist?id={artist_id}`               | Get artist info and discography          |
| `GET`  | `/playlist?id={playlist_id}`           | Get official playlist info               |
| `GET`  | `/community_playlist?id={playlist_id}` | Get community playlist info              |
| `GET`  | `/episode?id={episode_id}`             | Get a podcast episode                    |
| `GET`  | `/podcast?id={podcast_id}`             | Get a podcast show and episodes          |
| `GET`  | `/lyrics?id={track_id}`                | Get lyrics            |
| `GET`  | `/stream_urls?id={track_id}`           | Get streaming URLs in multiple qualities |
| `POST` | `/widevine_key`                     | Decrypt Widevine DRM using PSSH          |

---

## ⚠️ Legal Disclaimer

This project is intended for **educational and research purposes only**. It interacts with **Amazon’s internal APIs**, which may **violate their [Terms of Service](https://www.amazon.com/gp/help/customer/display.html?nodeId=508088)**.
The authors are **not affiliated with Amazon**. This software is provided **“as is” without any warranties**, express or implied. Use of this tool is **at your own risk**, and you are solely responsible for ensuring **compliance with applicable laws and terms** in your country or region.
This project is **non-commercial** and does **not host or distribute any Amazon-owned content**.

---

## 👨‍💻 Dev & Support

<a href="https://bio.link/aminesoukara"><img src="https://img.shields.io/badge/@AmineSoukara-000000?style=flat&logo=messenger&logoColor=white&logoWidth=100"></a>
<a href="https://t.me/DezAltySupport"><img src="https://img.shields.io/badge/Group-FF0000?style=flat&logo=telegram&logoColor=white&logoWidth=100"></a>
<a href="https://t.me/DezAlty"><img src="https://img.shields.io/badge/Channel-FF0000?style=flat&logo=telegram&logoColor=white&logoWidth=100"></a>

---

![⭐️](https://telegra.ph/file/b132a131aabe2106bd335.gif)

> ⭐️ If you find this project useful, please consider starring the repo! It helps support the project and keeps it visible to others.


---
</div>

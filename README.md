<div align="center">
  <h1>anydl</h1>
  <p>A unified, clean, and modern desktop application for downloading audio and video.</p>

  <img src="screenshots/home.png" alt="App Homepage" width="600">
</div>

**English** · [中文](README.zh-CN.md)

## Overview

**anydl** is an open-source Python desktop application built with [Flet](https://flet.dev). It doesn't implement any download logic itself — it provides a friendly graphical interface that orchestrates several industry-standard command-line download engines.

> This repository is a fork of [sytrusz/anydl](https://github.com/sytrusz/anydl). See [Changes from Upstream](#changes-from-upstream) below.

---

## Changes from Upstream

> Full details in [`Changes from upstream.md`](Changes%20from%20upstream.md).

A lot of work went into making the app simpler and the everyday actions quicker. The home screen went from 9 cards down to 2, so there's nothing to guess; and the two things you do every single time — pasting a link and typing a trim range — are now parsed automatically, saving you a manual step and a class of errors:

1. Went from a web page to a desktop app.
2. **Simpler layout:** the home screen went from 9 cards down to 2.
3. **More sites:** added Bilibili and Douyin.
4. **Paste anything:** links copied from Bilibili or Douyin come with the title and other junk attached, not just the URL. The URL is now extracted automatically, so you can paste the whole copied block as-is.
5. **Video trimming:** download only the segment you need — much handier for pulling material out of long videos.
6. **No format to memorise:** for a trim range you can type just seconds, or minutes plus seconds. Both are parsed on submit.
7. **Cleaner logs:** filtered the log output down to something actually readable.
8. Fixed the bug where a failed download still popped up a "Success" dialog.

**Note:** to download Douyin videos, install [Firefox](https://www.mozilla.org/firefox/new/) and open douyin.com in it once (no login needed). ANYDL needs the cookie from there to complete the download.

---

## 📌 Quick Start (Installation & Running)

### 1. Prerequisites

**🪟 Windows users:**
Nothing to install. If Python and FFmpeg are missing from your system, `start_windows.bat` downloads portable versions for you (Python 3.11 + FFmpeg). This happens only once.

**🍎 macOS / 🐧 Linux users:**
Two things must already be installed:

- **Python 3.8 or newer**: pre-installed on most Linux distros. Mac users can [download it here](https://www.python.org/downloads/).
- **FFmpeg**: required for all audio/video conversion and trimming.
  - **macOS**: `brew install ffmpeg`
  - **Linux**: use your package manager, e.g. `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`

**🔥 Downloading from Douyin?** Also install [Firefox](https://www.mozilla.org/firefox/new/) and open douyin.com in it once (no login needed). Reason: see the note at the end of the changes above.

### 2. Download and Run

1. **Download the repository:**
   Click the green **"Code"** button at the top, choose **"Download ZIP"**, and extract it. *(Or clone it: `git clone https://github.com/hh12356/anydl.git`)*

2. **Launch the application:**
   Open the extracted folder and run the startup script for your operating system:
   - 🪟 **Windows:** double-click `start_windows.bat`
   - 🍎 **macOS / 🐧 Linux:** run `./start_linux.sh` in a terminal

*The script sets up the environment and then opens the app window.*

---

## How to Use

1. **Pick an entry point:** the home screen has just two cards — **Video Downloader** and **Music Downloader**.
2. **Paste a link:** the video window handles YouTube, Bilibili, Douyin, TikTok, Facebook, Instagram and X; the music window handles Spotify and SoundCloud. **You don't need to say which site it is** — it's detected automatically.
3. **(Optional) Tune the options:** in the video window you can pick MP4 or MP3 output, enter a trim range, and tick "separate folder per playlist".
4. **Click Download.**

Files are saved to `~/Downloads/ANYDL` (`C:\Users\<your-name>\Downloads\ANYDL` on Windows). The folder is created automatically if it doesn't exist.

---

## Features

- 🎥 **Video downloads**: YouTube, Bilibili, Douyin, TikTok, Facebook, Instagram, X — merged to MP4 automatically
- 🎵 **Music downloads**: high-quality MP3 from Spotify and SoundCloud, with full metadata
- ✂️ **Trimming**: download only the part you need; type the time range however you like (see changes 5 and 6)
- 🚀 **Spotify rate-limit bypass**: put your own Spotify Developer API key in Settings to avoid throttling on the public API
- 📁 **Automatic playlist folders**: grouped as `anydl@sytrus - [Playlist Name]`
- 📊 **Progress & stats**: a live progress bar, plus a success/failure summary when it finishes
- 🎨 **Modern UI**: a clean card-based home screen with dark/light theme switching

---

## Powered By

All download capability comes from these open-source projects:

- [**yt-dlp**](https://github.com/yt-dlp/yt-dlp): the engine for YouTube, TikTok, Facebook, X (Twitter), Instagram, Bilibili, Douyin and more
- [**spotDL**](https://github.com/spotDL/spotify-downloader): the engine for Spotify tracks and playlists
- [**scdl**](https://github.com/flyingrub/scdl): the engine for SoundCloud audio

---

## Credits

Thanks to the open-source community:

- [**Flet**](https://flet.dev/): the UI framework
- [**yt-dlp**](https://github.com/yt-dlp/yt-dlp): the video engine
- [**spotDL**](https://github.com/spotDL/spotify-downloader): the Spotify engine
- [**scdl**](https://github.com/flyingrub/scdl): the SoundCloud engine

## License

This project is open-source. Feel free to fork, modify, and distribute it.

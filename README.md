# Photo & Video Sharing API

Upload photos and videos, browse them in a gallery, and delete files you no longer need. Built with **FastAPI, Jinja2, and Supabase**.

Supabase Storage holds the files, and PostgreSQL stores their titles, URLs, and media types.

## Features

- Upload photos and videos with a title.
- Browse a responsive gallery with lazy-loaded images and video controls.
- Check file extensions and sizes, and reject empty uploads.
- Generate UUID filenames to avoid filename collisions.
- Delete media files and their database records.
- Attempt to clean up stored files if an upload or metadata save fails.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, Uvicorn |
| Frontend | Jinja2 templates, HTML, CSS |
| Database | Supabase PostgreSQL |
| File storage | Supabase Storage |

## Supported Media

| Type | Extensions | Application limit |
| --- | --- | --- |
| Images | `png`, `jpg`, `jpeg`, `gif`, `webp`, `bmp`, `avif` | 10 MiB |
| Videos | `mp4`, `webm`, `mov`, `m4v` | 100 MiB |

Supabase storage limits also apply. Video playback depends on browser and codec support.

## Getting Started

### 1. Clone and install

You will need **Python 3.10+**, Git, and a Supabase project.

```bash
git clone https://github.com/madhavreddy1619-svg/photo-video-sharing-api.git
cd photo-video-sharing-api
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux / WSL
source .venv/bin/activate
```

Use `python3` if your system does not recognize `python`. With the virtual environment active, install the dependencies:

```bash
python -m pip install fastapi uvicorn supabase jinja2 python-multipart
```

### 2. Set up Supabase

Create a **public storage bucket** named `photos` and a database table named `photos` with these columns:

| Column | Type / configuration |
| --- | --- |
| `id` | Integer or bigint primary key, generated automatically |
| `title` | Text |
| `image_url` | Text; stores the public URL for either a photo or a video |
| `media_type` | Text; `image` or `video` |

In the bucket settings, allow the image and video MIME types and file sizes you want to upload. Your server key needs access to read, insert, and delete table records, and upload and remove storage files.

### 3. Configure the application

Copy `config.example.py` to `config.py`. Both `BUCKET_NAME` and `TABLE_NAME` default to `photos`; update them if you chose different names.

Set your Supabase credentials in the same terminal you will use to run the app:

**Windows PowerShell**

```powershell
$env:SUPABASE_URL = "https://your-project-ref.supabase.co"
$env:SUPABASE_KEY = "your-server-side-key"
```

**macOS / Linux / WSL**

```bash
export SUPABASE_URL='https://your-project-ref.supabase.co'
export SUPABASE_KEY='your-server-side-key'
```

`config.py` reads these environment variables directly; the app does not load `.env` files. Keep your key private. Both `config.py` and `.env` are listed in `.gitignore`.

### 4. Start the server

Run from the repository root:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Gallery:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Upload form:** [http://127.0.0.1:8000/upload](http://127.0.0.1:8000/upload)
- **API docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Endpoints

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Show the gallery, with higher record IDs first |
| `GET` | `/upload` | Display the upload form |
| `POST` | `/upload` | Upload media using multipart fields `title` and `file` |
| `POST` | `/delete/{media_id}` | Delete a media file and its database record |

Successful uploads and deletions return a `303` redirect to the gallery.

Upload the included sample image:

```bash
curl -i http://127.0.0.1:8000/upload -F "title=Sample photo" -F "file=@test_image.png;type=image/png"
```

Use `curl.exe` in Windows PowerShell.

## Project Files

| Path | Responsibility |
| --- | --- |
| `main.py` | Routes, upload validation, and database/storage operations |
| `config.example.py` | Configuration template |
| `templates/index.html` | Media gallery |
| `templates/upload.html` | Upload form |
| `static/style.css` | Shared interface styles |
| `diagnose.py` | Supabase configuration and storage checks |
| `test_image.png` | Sample file for manual uploads |

## Check the Setup

```bash
python diagnose.py
```

This script checks your configuration, table access, and storage bucket. It also uploads a temporary image and tries to remove it afterward. Review the output, then upload and delete a sample in the gallery.

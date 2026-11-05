# Photo & Video Sharing API

A media-sharing web application built with **FastAPI, Jinja2, and Supabase**. Upload photos and videos, browse them in a responsive gallery, and manage stored media through a simple browser interface.

Media files live in Supabase Storage, while titles, public URLs, and media types are saved in PostgreSQL through Supabase.

## Features

- **Photo and video uploads** — add a title and upload media from the browser.
- **Responsive gallery** — browse media with lazy-loaded images and built-in video playback controls.
- **Upload validation** — check file extensions, reject empty files, and enforce separate image and video size limits.
- **Unique filenames** — generate UUID-based storage names to avoid filename collisions.
- **Media management** — delete a stored file and its database record; attempt storage cleanup if an upload or metadata insert fails.
- **Interactive API documentation** — explore request fields and routes through FastAPI's Swagger UI.

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

Use `python3` instead of `python` if required by your system. With the environment active, install the packages used by the application:

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

Allow the image/video MIME types and upload sizes you intend to use in the bucket settings. Your server credential must have permission to read, insert, and delete table records, and upload and remove storage objects.

### 3. Configure the application

Copy `config.example.py` to `config.py`. Both `BUCKET_NAME` and `TABLE_NAME` default to `photos`; update them if you chose different names.

Set the following environment variables in the terminal where you will start the server:

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

`config.py` reads these variables from the environment; `.env` files are not loaded automatically. Keep credentials private. Both `config.py` and `.env` are excluded by `.gitignore`.

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
| `GET` | `/` | Render the gallery, ordered by descending record ID |
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

## Verify Your Setup

```bash
python diagnose.py
```

The diagnostic checks configuration, reads the media table, lists storage buckets, uploads a temporary image, and attempts to remove it. Review the printed results, then upload and delete a sample through the gallery to check the complete flow.

> **Current scope:** Media URLs are public, and the application has no user authentication or ownership checks. Add access controls before exposing upload and delete routes publicly.

---

Built by **Gundaram Madhav Reddy** · [GitHub](https://github.com/madhavreddy1619-svg)

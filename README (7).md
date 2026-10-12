# Photo & Video Sharing API

A media-sharing application built with **FastAPI, Jinja2, and Supabase**. Upload photos and videos, view them in a browser gallery, and delete media when needed.

Files are stored in Supabase Storage, while titles, URLs, and media types are saved in a Supabase database table.

## Features

- Upload images and videos with a title.
- Browse a responsive gallery with lazy-loaded images and video playback controls.
- Validate file extensions, reject empty uploads, and enforce file-size limits.
- Generate unique storage filenames using UUIDs.
- Delete media files and their database records.
- Attempt cleanup when an upload or metadata insert fails.

| Media | Supported extensions | Maximum size |
| --- | --- | --- |
| Images | `png`, `jpg`, `jpeg`, `gif`, `webp`, `bmp`, `avif` | 10 MiB |
| Videos | `mp4`, `webm`, `mov`, `m4v` | 100 MiB |

Supabase may enforce lower upload limits. Video playback depends on browser and codec support.

## Technology Stack

**Python · FastAPI · Jinja2 · Supabase Database (PostgreSQL) · Supabase Storage · HTML · CSS**

## Main Files

| File | Purpose |
| --- | --- |
| `main.py` | Application routes, validation, and Supabase operations |
| `config.example.py` | Configuration template |
| `diagnose.py` | Supabase configuration and storage checks |
| `templates/index.html` | Media gallery |
| `templates/upload.html` | Upload form |
| `static/style.css` | Application styles |
| `test_image.png` | Sample image for manual uploads |

## Getting Started

### Prerequisites

- Git and Python 3.10+ with `pip` and virtual environment support.
- A Supabase project with a database table, public storage bucket, and suitable server-side credentials.

### 1. Clone the Repository

```bash
git clone https://github.com/madhavreddy1619-svg/photo-video-sharing-api.git
cd photo-video-sharing-api
```

### 2. Install Dependencies

**macOS, Linux, or WSL:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install fastapi uvicorn supabase jinja2 python-multipart
cp config.example.py config.py
```

**Windows PowerShell:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi uvicorn supabase jinja2 python-multipart
Copy-Item config.example.py config.py
```

Dependencies are identified from the code; no manifest, pinned versions, or tested Python version is provided.

### 3. Configure Supabase Credentials

Set these variables in the terminal where you will run the application. Replace the placeholders with your project values.

**macOS, Linux, or WSL:**

```bash
export SUPABASE_URL='https://your-project-ref.supabase.co'
export SUPABASE_KEY='your-server-side-key'
```

**Windows PowerShell:**

```powershell
$env:SUPABASE_URL = "https://your-project-ref.supabase.co"
$env:SUPABASE_KEY = "your-server-side-key"
```

`config.py` reads these two environment variables. It also defines `BUCKET_NAME` and `TABLE_NAME`, both defaulting to `photos`. Edit those constants if your resources have different names.

**The application does not automatically load `.env` files.** Keep credentials out of source control; `config.py` and `.env` are excluded by `.gitignore`.

### 4. Configure the Database and Storage

The metadata table must support these fields used by the code:

| Field | Purpose |
| --- | --- |
| `id` | Integer-compatible identifier supplied by the database; used for ordering and deletion |
| `title` | Media title |
| `image_url` | Public URL for an image or video |
| `media_type` | `image` or `video` |

**Setup requires confirmation:** No schema migrations or policies are included. Confirm the column types, ID generation, and permissions in Supabase. The application does not create the table.

For storage:

- Create or verify a **public** bucket named `photos`, or match `BUCKET_NAME` in `config.py`.
- Allow the intended image/video MIME types and file sizes.
- Ensure the configured credential can read, insert, and delete metadata, and upload and remove storage objects.

Public access enables media retrieval; it does not automatically grant upload or delete permissions.

### 5. Run the Application

With the virtual environment active, run from the repository root:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Gallery:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Upload:** [http://127.0.0.1:8000/upload](http://127.0.0.1:8000/upload)
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

FastAPI also provides `/redoc` and `/openapi.json` by default.

## API Usage

| Method | Endpoint | Request | Success response |
| --- | --- | --- | --- |
| `GET` | `/` | None | `200` HTML gallery |
| `GET` | `/upload` | None | `200` HTML upload form |
| `POST` | `/upload` | Multipart fields: `title` and `file` | `303` redirect to `/` |
| `POST` | `/delete/{media_id}` | Integer ID in the path; no body | `303` redirect to `/` |

The gallery displays records by descending `id`. Files load from public Supabase URLs; uploads and deletions return redirects, not JSON.

### Example Requests

Upload the included image with the required `title` and `file` fields:

```bash
curl -i http://127.0.0.1:8000/upload -F "title=Sample photo" -F "file=@test_image.png;type=image/png"
```

Upload a video, replacing `sample.mp4` with your own file:

```bash
curl -i http://127.0.0.1:8000/upload -F "title=Sample video" -F "file=@sample.mp4;type=video/mp4"
```

Delete media, replacing `123` with an existing record ID:

```bash
curl -i -X POST http://127.0.0.1:8000/delete/123
```

Use `curl.exe` instead of `curl` in Windows PowerShell. Successful uploads and deletions return:

```http
HTTP/1.1 303 See Other
location: /
```

### Error Responses

| Status | Meaning |
| --- | --- |
| `400` | Unsupported extension or empty upload |
| `404` | Media record not found |
| `413` | File exceeds the application size limit |
| `422` | Missing required field or invalid integer ID |
| `500` | Database or storage operation failed |

Example `400` response:

```json
{"detail":"Unsupported file format."}
```

## Diagnostics and Testing

Check Supabase configuration and storage access:

```bash
python diagnose.py
```

This reads the table, lists buckets, uploads a temporary PNG, and attempts cleanup. Use a development project and check the printed results; failures do not reliably produce a nonzero exit code.

No automated tests are included. Manually verify upload, gallery display, deletion, and invalid inputs.

## Security and Limitations

- No login or ownership checks are implemented. Restrict application access before allowing uploads or deletions.
- Media URLs are public. Keep credentials private and avoid confidential uploads.
- File validation checks extension and size, not file contents. Accepted files are buffered in memory.
- Storage and database operations are separate; cleanup is best-effort. Server errors expose exception details.
- User accounts, likes, comments, search, and pagination are not implemented.

## Deployment

No deployment configuration or verified hosting procedure is provided. A starting command for a configured Python host is:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Provide `config.py`, environment variables, templates, static files, and Supabase access. Add HTTPS, request limits, and access control before public deployment.

## Future Improvements

Suggested additions, not current features:

- Dependency lockfile and database migrations.
- User authentication and ownership-based permissions.
- Automated tests and stronger media validation.
- Pagination, thumbnails, and private media access.

## Contributing

Fork the repository, create a branch, and submit a pull request explaining your changes and verification. Never commit credentials or private media.

## License

No `LICENSE` file is included. Confirm license terms with the repository owner.

## Author

**Gundaram Madhav Reddy**

[GitHub](https://github.com/madhavreddy1619-svg) · [Repository](https://github.com/madhavreddy1619-svg/photo-video-sharing-api)

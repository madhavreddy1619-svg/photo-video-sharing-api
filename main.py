import mimetypes
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client

from config import (
    BUCKET_NAME,
    SUPABASE_KEY,
    SUPABASE_URL,
    TABLE_NAME,
)
print("URL IN USE:", SUPABASE_URL)
print("KEY STARTS:", SUPABASE_KEY[:12])
print("KEY LENGTH:", len(SUPABASE_KEY))

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Photo & Video Sharing API")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

supabase = create_client(
    SUPABASE_URL.rstrip("/"),
    SUPABASE_KEY,
)

IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "bmp",
    "avif",
}

VIDEO_EXTENSIONS = {
    "mp4",
    "webm",
    "mov",
    "m4v",
}

ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# Videos are far larger than images, so they get a separate, higher cap.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024

# Size of each chunk streamed from the client. Streaming keeps a large
# video from being loaded into memory all at once.
CHUNK_SIZE = 1024 * 1024


def media_type_for(extension: str) -> str:
    if extension in VIDEO_EXTENSIONS:
        return "video"
    return "image"


def get_storage_path(media_url: str | None) -> str:
    if not media_url:
        return ""

    path = urlparse(media_url).path
    marker = f"/object/public/{BUCKET_NAME}/"

    if marker in path:
        return unquote(path.split(marker, 1)[1])

    return unquote(path.rsplit("/", 1)[-1])


@app.get("/", response_class=HTMLResponse)
def gallery(request: Request):

    try:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("*")
            .order("id", desc=True)
            .execute()
        )

        media = response.data or []

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read media: {exc}",
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"media": media},
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={},
    )


async def read_upload_limited(
    file: UploadFile,
    max_bytes: int,
) -> bytes:
    """Read an upload in chunks, failing fast once it exceeds max_bytes.

    Reading in chunks means an oversized upload is rejected as soon as it
    crosses the limit, instead of being fully buffered in memory first.
    """
    buffer = bytearray()

    while True:
        chunk = await file.read(CHUNK_SIZE)

        if not chunk:
            break

        buffer.extend(chunk)

        if len(buffer) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    "File exceeds the maximum allowed size "
                    f"({max_bytes // (1024 * 1024)} MB)."
                ),
            )

    return bytes(buffer)


@app.post("/upload")
async def upload_media(
    title: str = Form(...),
    file: UploadFile = File(...),
):

    original_name = file.filename or ""

    extension = (
        Path(original_name)
        .suffix
        .lstrip(".")
        .lower()
    )

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format.",
        )

    media_type = media_type_for(extension)

    max_bytes = (
        MAX_VIDEO_BYTES
        if media_type == "video"
        else MAX_IMAGE_BYTES
    )

    contents = await read_upload_limited(file, max_bytes)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    stored_name = f"{uuid.uuid4()}.{extension}"

    content_type = (
        file.content_type
        or mimetypes.guess_type(stored_name)[0]
        or "application/octet-stream"
    )

    try:
        # NOTE: the Supabase storage bucket must permit video MIME types
        # and a matching file-size limit, or large uploads are rejected
        # at the storage layer regardless of the checks above.
        supabase.storage.from_(BUCKET_NAME).upload(
            stored_name,
            contents,
            {
                "content-type": content_type,
                "upsert": "false",
            },
        )

        public_url = (
            supabase.storage
            .from_(BUCKET_NAME)
            .get_public_url(stored_name)
            .rstrip("?")
        )

        supabase.table(TABLE_NAME).insert(
            {
                "title": title,
                "image_url": public_url,
                "media_type": media_type,
            }
        ).execute()

    except Exception as exc:

        # If the metadata insert fails after the file is stored, remove
        # the orphaned file so storage and database stay consistent.
        try:
            supabase.storage.from_(BUCKET_NAME).remove(
                [stored_name]
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {exc}",
        )

    return RedirectResponse(
        url="/",
        status_code=303,
    )


@app.post("/delete/{media_id}")
def delete_media(media_id: int):

    try:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("*")
            .eq("id", media_id)
            .execute()
        )

        rows = response.data or []

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Media not found.",
            )

        item = rows[0]

        storage_path = get_storage_path(
            item.get("image_url")
        )

        if storage_path:
            supabase.storage.from_(
                BUCKET_NAME
            ).remove([storage_path])

        (
            supabase
            .table(TABLE_NAME)
            .delete()
            .eq("id", media_id)
            .execute()
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {exc}",
        )

    return RedirectResponse(
        url="/",
        status_code=303,
    )
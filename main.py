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

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "bmp",
    "avif",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def get_storage_path(image_url: str | None) -> str:
    if not image_url:
        return ""

    path = urlparse(image_url).path
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

        photos = response.data or []

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read photos: {exc}",
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"photos": photos},
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={},
    )


@app.post("/upload")
async def upload_photo(
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
            detail="Unsupported image format.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 10 MB.",
        )

    stored_name = f"{uuid.uuid4()}.{extension}"

    content_type = (
        file.content_type
        or mimetypes.guess_type(stored_name)[0]
        or "application/octet-stream"
    )

    try:
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
            }
        ).execute()

    except Exception as exc:

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


@app.post("/delete/{photo_id}")
def delete_photo(photo_id: int):

    try:
        response = (
            supabase
            .table(TABLE_NAME)
            .select("*")
            .eq("id", photo_id)
            .execute()
        )

        rows = response.data or []

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Photo not found.",
            )

        photo = rows[0]

        storage_path = get_storage_path(
            photo.get("image_url")
        )

        if storage_path:
            supabase.storage.from_(
                BUCKET_NAME
            ).remove([storage_path])

        (
            supabase
            .table(TABLE_NAME)
            .delete()
            .eq("id", photo_id)
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
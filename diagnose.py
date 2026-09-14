import base64
import uuid

from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    BUCKET_NAME,
    TABLE_NAME,
)
from supabase import create_client


def check_config():
    print("\n1. Checking configuration...")

    values = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "BUCKET_NAME": BUCKET_NAME,
        "TABLE_NAME": TABLE_NAME,
    }

    for name, value in values.items():
        if not value:
            raise ValueError(f"{name} is missing or None")

    print("[PASS] Configuration values exist")
    print(f"       URL: {SUPABASE_URL}")
    print(f"       Table: {TABLE_NAME}")
    print(f"       Bucket: {BUCKET_NAME}")


def create_supabase_client():
    print("\n2. Connecting to Supabase...")

    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[PASS] Supabase client created")
        return client

    except Exception as error:
        print(f"[FAIL] Connection failed: {error}")
        raise


def check_table(client):
    print(f"\n3. Checking table '{TABLE_NAME}'...")

    try:
        response = (
            client.table(TABLE_NAME)
            .select("*")
            .limit(5)
            .execute()
        )

        rows = response.data or []

        print(f"[PASS] Table works")
        print(f"       Rows returned: {len(rows)}")

    except Exception as error:
        print(f"[FAIL] Could not read table: {error}")
        raise


def check_bucket(client):
    print(f"\n4. Checking storage bucket '{BUCKET_NAME}'...")

    try:
        buckets = client.storage.list_buckets()

        bucket_names = [
            bucket.name if hasattr(bucket, "name") else bucket.get("name")
            for bucket in buckets
        ]

        if BUCKET_NAME not in bucket_names:
            raise ValueError(
                f"Bucket '{BUCKET_NAME}' does not exist"
            )

        print("[PASS] Storage bucket exists")

    except Exception as error:
        print(f"[FAIL] Bucket check failed: {error}")
        raise


def test_upload(client):
    print("\n5. Testing storage upload...")

    # Tiny 1x1 PNG image
    image_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    filename = f"diagnostic_{uuid.uuid4().hex[:8]}.png"

    try:
        client.storage.from_(BUCKET_NAME).upload(
            filename,
            image_data,
            {
                "content-type": "image/png",
                "upsert": "false",
            },
        )

        print("[PASS] Upload successful")

        url = (
            client.storage
            .from_(BUCKET_NAME)
            .get_public_url(filename)
        )

        print(f"[PASS] Public URL generated")
        print(f"       {url}")

    except Exception as error:
        print(f"[FAIL] Upload failed: {error}")
        raise

    finally:
        try:
            client.storage.from_(BUCKET_NAME).remove([filename])
            print("[PASS] Test image removed")
        except Exception:
            print("[WARN] Could not remove test image")


def main():
    print("=" * 60)
    print("PHOTO & VIDEO API - SUPABASE DIAGNOSTIC")
    print("=" * 60)

    try:
        check_config()

        client = create_supabase_client()

        check_table(client)

        check_bucket(client)

        test_upload(client)

        print("\n" + "=" * 60)
        print("ALL CORE CHECKS PASSED")
        print("=" * 60)

    except Exception as error:
        print("\n" + "=" * 60)
        print("DIAGNOSTIC FAILED")
        print(f"Reason: {type(error).__name__}: {error}")
        print("=" * 60)


if __name__ == "__main__":
    main()
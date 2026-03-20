# ============================================================
#  config/storage_backends.py
#
#  Two storage backends for Cloudflare R2.
#  Both use the same bucket but different prefixes:
#    StaticRootS3Boto3Storage  → bucket/static/
#    MediaRootS3Boto3Storage   → bucket/media/
#
#  R2 is S3-compatible so django-storages + boto3 works
#  with no extra packages needed.
# ============================================================

from storages.backends.s3boto3 import S3Boto3Storage


class StaticRootS3Boto3Storage(S3Boto3Storage):
    """
    Stores collectstatic output under /static/ in R2.
    Files are public and overwritable (versioned by Django's manifest).
    """

    location = "static"
    default_acl = "public-read"
    file_overwrite = True  # safe — collectstatic uses content hashes
    querystring_auth = False  # public URLs, no signed queries


class MediaRootS3Boto3Storage(S3Boto3Storage):
    """
    Stores user-uploaded files under /media/ in R2.
    Files are public but never overwritten (UUID filenames).
    """

    location = "media"
    default_acl = "public-read"
    file_overwrite = False  # never overwrite user uploads
    querystring_auth = False

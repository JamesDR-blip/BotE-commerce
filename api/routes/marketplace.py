"""Marketplace API routes."""

from __future__ import annotations

import base64
import binascii
import tempfile
from pathlib import Path

from fastapi import (
    Query,
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from api.dependencies import get_current_user, get_marketplace_service
from application.marketplace.marketplace_service import MarketplaceService
from domain.identity import CurrentUser
from schemas.marketplace import (
    MarketplaceInstallResponse,
    MarketplacePackageResponse,
)


router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get(
    "/packages",
    response_model=list[MarketplacePackageResponse],
)
def list_marketplace_packages(
    query: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
) -> list[MarketplacePackageResponse]:
    del current_user

    try:
        packages = service.list_packages(query=query)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return [
        MarketplacePackageResponse(
            package_id=package.package_id,
            version=package.version,
            package_type=package.package_type.value,
            publisher=package.publisher,
            interface_version=package.interface_version,
            content_hash=package.content_hash,
        )
        for package in packages
    ]


@router.post(
    "/install",
    response_model=MarketplaceInstallResponse,
)
async def install_marketplace_package(
    request: Request,
    archive: UploadFile = File(...),
    public_key: str = Form(...),
    signature: str = Form(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplaceInstallResponse:
    del current_user

    try:
        decoded_public_key = base64.b64decode(
            public_key,
            validate=True,
        )
        decoded_signature = base64.b64decode(
            signature,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid Base64 public key or signature",
        ) from exc

    if not decoded_public_key or not decoded_signature:
        raise HTTPException(
            status_code=422,
            detail="Public key and signature are required",
        )

    filename = Path(archive.filename or "marketplace-package.zip").name
    suffix = Path(filename).suffix.lower()

    if suffix not in {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz"}:
        raise HTTPException(
            status_code=422,
            detail="Unsupported marketplace archive format",
        )

    settings = request.app.state.container.settings
    staging_root = settings.marketplace_staging_path
    staging_root.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    total_bytes = 0

    try:
        with tempfile.NamedTemporaryFile(
            prefix="marketplace-upload-",
            suffix=suffix,
            dir=staging_root,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            while True:
                chunk = await archive.read(1024 * 1024)
                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=422,
                        detail="Marketplace archive exceeds maximum upload size",
                    )

                temporary_file.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=422,
                detail="Marketplace archive is empty",
            )

        installed = service.install(
            archive_path=temporary_path,
            public_key=decoded_public_key,
            signature=decoded_signature,
        )

        package = installed.package

        return MarketplaceInstallResponse(
            package_id=package.package_id,
            version=package.version,
            package_type=package.package_type.value,
            publisher=package.publisher,
            interface_version=package.interface_version,
            content_hash=package.content_hash,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

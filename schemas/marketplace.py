"""HTTP contracts for the marketplace API."""

from pydantic import BaseModel


class MarketplaceInstallResponse(BaseModel):
    package_id: str
    version: str
    package_type: str
    publisher: str
    interface_version: str
    content_hash: str


class MarketplacePackageResponse(BaseModel):
    package_id: str
    version: str
    package_type: str
    publisher: str
    interface_version: str
    content_hash: str

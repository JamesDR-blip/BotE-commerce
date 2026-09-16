from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.channels.credential_cipher import CredentialCipher
from database.models import Base, ChannelRecord
from domain.channel_sync import Channel, ChannelType
from infrastructure.security.credential_cipher import FernetCredentialCipher
from repositories.channels import ChannelRepository
from repositories.workspaces import WorkspaceRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def make_channel(
    *,
    channel_id: str = "ch-1",
    workspace_id: str = "ws-1",
    name: str = "Shopify Store",
) -> Channel:
    return Channel(
        id=channel_id,
        workspace_id=workspace_id,
        channel=ChannelType.SHOPIFY,
        name=name,
    )


def create_workspace(
    sessions,
    *,
    workspace_id: str,
    owner_id: str,
) -> None:
    WorkspaceRepository(sessions).create(
        workspace_id=workspace_id,
        owner_id=owner_id,
        name=f"Workspace {workspace_id}",
    )


def test_channel_repository_encrypts_credentials_at_rest() -> None:
    sessions = create_session()
    cipher = FernetCredentialCipher(FernetCredentialCipher.__module__ and __import__(
        "cryptography.fernet",
        fromlist=["Fernet"],
    ).Fernet.generate_key().decode())

    repository = ChannelRepository(sessions, cipher)
    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )

    stored = repository.create(
        channel=make_channel(),
        credentials='{"access_token":"secret-token"}',
    )

    assert stored.id == "ch-1"
    assert stored.channel is ChannelType.SHOPIFY

    with sessions() as session:
        record = session.get(ChannelRecord, "ch-1")

        assert record is not None
        assert record.credentials_encrypted != (
            '{"access_token":"secret-token"}'
        )
        assert "secret-token" not in record.credentials_encrypted


def test_channel_repository_round_trips_credentials_only_through_credential_port() -> None:
    sessions = create_session()

    from cryptography.fernet import Fernet

    cipher = FernetCredentialCipher(
        Fernet.generate_key().decode(),
    )
    repository = ChannelRepository(sessions, cipher)

    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )

    repository.create(
        channel=make_channel(),
        credentials='{"access_token":"secret-token"}',
    )

    loaded = repository.get_for_owner(
        channel_id="ch-1",
        owner_id="user-1",
    )

    assert loaded is not None
    assert not hasattr(loaded, "credentials")

    credentials = repository.get_credentials_for_owner(
        channel_id="ch-1",
        owner_id="user-1",
    )

    assert credentials == '{"access_token":"secret-token"}'


def test_channel_repository_scopes_by_workspace_owner() -> None:
    sessions = create_session()

    from cryptography.fernet import Fernet

    repository = ChannelRepository(
        sessions,
        FernetCredentialCipher(Fernet.generate_key().decode()),
    )

    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )
    create_workspace(
        sessions,
        workspace_id="ws-2",
        owner_id="user-2",
    )

    repository.create(
        channel=make_channel(workspace_id="ws-1"),
        credentials="credential-1",
    )
    repository.create(
        channel=make_channel(
            channel_id="ch-2",
            workspace_id="ws-2",
            name="Other Store",
        ),
        credentials="credential-2",
    )

    assert repository.get_for_owner(
        channel_id="ch-1",
        owner_id="user-1",
    ) is not None

    assert repository.get_for_owner(
        channel_id="ch-1",
        owner_id="user-2",
    ) is None

    assert repository.list_for_owner(
        workspace_id="ws-1",
        owner_id="user-1",
    )[0].id == "ch-1"

    assert repository.list_for_owner(
        workspace_id="ws-2",
        owner_id="user-1",
    ) == []


def test_channel_repository_enforces_workspace_channel_name_uniqueness() -> None:
    from cryptography.fernet import Fernet
    import pytest

    sessions = create_session()
    repository = ChannelRepository(
        sessions,
        FernetCredentialCipher(Fernet.generate_key().decode()),
    )

    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )

    repository.create(
        channel=make_channel(),
        credentials="credential-1",
    )

    with pytest.raises(Exception):
        repository.create(
            channel=Channel(
                id="ch-2",
                workspace_id="ws-1",
                channel=ChannelType.SHOPIFY,
                name="Shopify Store",
            ),
            credentials="credential-2",
        )


def test_channel_repository_allows_same_name_for_different_channel_types() -> None:
    from cryptography.fernet import Fernet

    sessions = create_session()
    repository = ChannelRepository(
        sessions,
        FernetCredentialCipher(Fernet.generate_key().decode()),
    )

    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )

    repository.create(
        channel=make_channel(),
        credentials="credential-1",
    )

    second = repository.create(
        channel=Channel(
            id="ch-2",
            workspace_id="ws-1",
            channel=ChannelType.AMAZON_SP_API,
            name="Shopify Store",
        ),
        credentials="credential-2",
    )

    assert second.id == "ch-2"


def test_channel_repository_missing_owner_cannot_read_credentials() -> None:
    from cryptography.fernet import Fernet

    sessions = create_session()
    repository = ChannelRepository(
        sessions,
        FernetCredentialCipher(Fernet.generate_key().decode()),
    )

    create_workspace(
        sessions,
        workspace_id="ws-1",
        owner_id="user-1",
    )

    repository.create(
        channel=make_channel(),
        credentials="credential-1",
    )

    assert repository.get_credentials_for_owner(
        channel_id="ch-1",
        owner_id="user-2",
    ) is None

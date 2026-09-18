from configs.settings import Settings
from services.container import Container
from application.datasets.dataset_ingestion import DatasetIngestionService


def test_container_exposes_workflow_authoring_service():

    settings = Settings(
        database_url="sqlite://"
    )

    container = Container(settings)

    assert container.workflow_authoring is not None
    assert isinstance(
        container.dataset_ingestion,
        DatasetIngestionService,
    )
def test_container_disables_copilot_agent_when_llm_is_disabled():
    settings = Settings(
        database_url="sqlite://",
        enable_llm=False,
        google_api_key=None,
    )

    container = Container(settings)

    assert container.copilot_agent is None
def test_container_disables_copilot_agent_when_api_key_is_missing():
    settings = Settings(
        database_url="sqlite://",
        enable_llm=True,
        google_api_key=None,
    )

    container = Container(settings)

    assert container.copilot_agent is None
def test_container_builds_copilot_agent_when_llm_is_enabled(monkeypatch):
    from application.copilot.agent import CopilotAgent

    class FakeModels:
        pass

    fake_models = FakeModels()

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.models = fake_models

    monkeypatch.setattr("google.genai.Client", FakeClient)

    settings = Settings(
        database_url="sqlite://",
        enable_llm=True,
        google_api_key="test-key",
        llm_model="test-model",
    )

    container = Container(settings)

    assert isinstance(container.copilot_agent, CopilotAgent)
    assert container.copilot_agent._model is fake_models
    assert container.copilot_agent._model_name == "test-model"
    assert container.copilot_agent._tool_registry is container.copilot_tools

def test_container_wires_copilot_agent_into_service(monkeypatch):
    from application.copilot.agent import CopilotAgent

    class FakeModels:
        pass

    fake_models = FakeModels()

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-key"
            self.models = fake_models

    monkeypatch.setattr("google.genai.Client", FakeClient)

    settings = Settings(
        database_url="sqlite://",
        enable_llm=True,
        google_api_key="test-key",
        llm_model="test-model",
    )

    container = Container(settings)

    assert isinstance(container.copilot_agent, CopilotAgent)
    assert container.copilot._agent is container.copilot_agent

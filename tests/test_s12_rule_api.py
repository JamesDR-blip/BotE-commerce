from fastapi.testclient import TestClient

from api.dependencies import get_rule_intelligence_service
from api.main import create_app
from configs.settings import Settings
from domain.rule_retriever import RetrievedRuleMatch, RuleQuery, SemanticRulePack


class FakeRuleIntelligenceService:
    def search(self, *, query: RuleQuery) -> SemanticRulePack:
        return SemanticRulePack(
            query=query,
            matches=(
                RetrievedRuleMatch(
                    rule_id="fashion.descriptive.1",
                    content="Remove unnecessary whitespace from Color.",
                    score=0.91,
                    category="Fashion",
                    metadata={
                        "source_kind": "descriptive",
                        "executable": False,
                    },
                ),
            ),
        )

    def recommend(
        self,
        *,
        query: RuleQuery,
        min_score: float = 0.0,
    ) -> SemanticRulePack:
        result = self.search(query=query)

        return SemanticRulePack(
            query=result.query,
            matches=tuple(
                match
                for match in result.matches
                if match.score >= min_score
            ),
        )


def _client(tmp_path):
    app = create_app(
        Settings(
            database_url="sqlite://",
            reports_path=tmp_path / "reports",
            rule_index_path=tmp_path / "chroma",
        )
    )
    app.dependency_overrides[get_rule_intelligence_service] = (
        lambda: FakeRuleIntelligenceService()
    )
    return TestClient(app)


def test_rule_search_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/rules/search",
        json={
            "query": "remove whitespace from color",
            "category": "Fashion",
            "fields": ["Color"],
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == {
        "query": "remove whitespace from color",
        "category": "Fashion",
        "fields": ["Color"],
        "top_k": 3,
    }

    assert len(body["matches"]) == 1
    assert body["matches"][0]["rule_id"] == "fashion.descriptive.1"
    assert body["matches"][0]["score"] == 0.91
    assert body["matches"][0]["metadata"]["executable"] is False


def test_rule_recommend_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/rules/recommend",
        json={
            "query": "remove whitespace from color",
            "category": "Fashion",
            "fields": ["Color"],
            "top_k": 5,
            "min_score": 0.9,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["matches"]) == 1
    assert body["matches"][0]["score"] >= 0.9


def test_rule_search_rejects_invalid_top_k(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/rules/search",
        json={
            "query": "price",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_rule_recommend_rejects_invalid_min_score(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/rules/recommend",
        json={
            "query": "price",
            "min_score": 1.5,
        },
    )

    assert response.status_code == 422

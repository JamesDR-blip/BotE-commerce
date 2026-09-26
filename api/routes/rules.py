"""Semantic rule intelligence API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_rule_intelligence_service
from application.rules.rule_intelligence_service import RuleIntelligenceService
from domain.rule_retriever import RuleQuery
from schemas.requests import RuleRecommendRequest, RuleSearchRequest
from schemas.responses import (
    RetrievedRuleMatchResponse,
    RuleSearchRequestEcho,
    RuleSearchResponse,
)


router = APIRouter(tags=["Rules"])


def _query_from_payload(
    payload: RuleSearchRequest | RuleRecommendRequest,
) -> RuleQuery:
    return RuleQuery(
        query=payload.query,
        category=payload.category,
        fields=tuple(payload.fields),
        top_k=payload.top_k,
    )


def _response(result) -> RuleSearchResponse:
    return RuleSearchResponse(
        query=RuleSearchRequestEcho(
            query=result.query.query,
            category=result.query.category,
            fields=list(result.query.fields),
            top_k=result.query.top_k,
        ),
        matches=[
            RetrievedRuleMatchResponse(
                rule_id=match.rule_id,
                content=match.content,
                score=match.score,
                category=match.category,
                metadata=dict(match.metadata),
            )
            for match in result.matches
        ],
    )


@router.post(
    "/rules/search",
    response_model=RuleSearchResponse,
     summary='Search rules',
     description='Search the rule knowledge available to the rule intelligence service.'
 )
def search_rules(
    payload: RuleSearchRequest,
    rule_intelligence: RuleIntelligenceService = Depends(
        get_rule_intelligence_service
    ),
) -> RuleSearchResponse:
    result = rule_intelligence.search(
        query=_query_from_payload(payload),
    )
    return _response(result)


@router.post(
    "/rules/recommend",
    response_model=RuleSearchResponse,
     summary='Recommend rules',
     description='Recommend rules for the supplied query subject to the requested minimum score.'
 )
def recommend_rules(
    payload: RuleRecommendRequest,
    rule_intelligence: RuleIntelligenceService = Depends(
        get_rule_intelligence_service
    ),
) -> RuleSearchResponse:
    result = rule_intelligence.recommend(
        query=_query_from_payload(payload),
        min_score=payload.min_score,
    )
    return _response(result)

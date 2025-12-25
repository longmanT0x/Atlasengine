from __future__ import annotations
"""
Decision Module

Makes evidence-based decisions about market viability.

Design Decisions:
- Decisions are based on models with uncertainty ranges
- All decision criteria are explicit and traceable
- Decisions include confidence levels and risk factors
- Never outputs single binary decisions - always includes uncertainty
- Competitor analysis infers positioning from language
- Risk analysis is specific and data-driven, not generic
- Decision engine considers: market size, competition, regulatory risk, data confidence
- CONDITIONAL verdicts include specific conditions to reach GO
- Mandatory "What would make this analysis wrong?" section
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel
from app.modeling import MarketModel
from app.decision.schemas import CompetitorInfo, RiskAnalysis, DecisionResult
from app.decision.data_retrieval import (
    get_competitor_facts,
    get_regulatory_facts,
    get_market_size_facts,
    get_growth_rate_facts,
    get_pricing_facts
)
from app.decision.competitor_analysis import analyze_competitors as analyze_competitors_from_facts
from app.decision.risk_analysis import (
    analyze_market_risks,
    analyze_competition_risks,
    analyze_regulatory_risks,
    analyze_distribution_risks
)
from app.decision.decision_engine import (
    score_market_size,
    score_competitive_intensity,
    score_regulatory_risk,
    score_data_confidence,
    calculate_viability_score,
    determine_verdict,
    generate_disconfirming_evidence
)


def analyze_competitors_from_data() -> List[CompetitorInfo]:
    """
    Analyze competitors from extracted data.
    
    Aggregates competitor mentions and infers positioning/differentiation
    from the language used in context sentences.
    
    Returns:
        List of CompetitorInfo objects with analyzed competitor data
    """
    competitor_facts = get_competitor_facts()
    competitors = analyze_competitors_from_facts(competitor_facts)
    
    return [
        CompetitorInfo(
            name=c['name'],
            positioning=c['positioning'],
            pricing=c['pricing'],
            geography=c['geography'],
            differentiator=c['differentiator'],
            source_url=c['source_url']
        )
        for c in competitors
    ]


def analyze_risks_from_data() -> RiskAnalysis:
    """
    Analyze risks from extracted data grouped by category.
    
    Returns specific, data-driven risk statements (not generic).
    
    Returns:
        RiskAnalysis with risks grouped by category
    """
    # Get all relevant facts
    market_size_facts = get_market_size_facts()
    growth_rate_facts = get_growth_rate_facts()
    competitor_facts = get_competitor_facts()
    regulatory_facts = get_regulatory_facts()
    pricing_facts = get_pricing_facts()
    
    # Analyze competitors for competition risks
    competitor_analysis = analyze_competitors_from_facts(competitor_facts)
    
    # Analyze each risk category
    market_risks = analyze_market_risks(market_size_facts, growth_rate_facts)
    competition_risks = analyze_competition_risks(competitor_facts, competitor_analysis)
    regulatory_risks = analyze_regulatory_risks(regulatory_facts)
    distribution_risks = analyze_distribution_risks(pricing_facts, market_size_facts)
    
    return RiskAnalysis(
        market=market_risks,
        competition=competition_risks,
        regulatory=regulatory_risks,
        distribution=distribution_risks
    )


def make_decision(
    market_model: MarketModel,
    competitors: List[CompetitorInfo],
    risks: RiskAnalysis
) -> DecisionResult:
    """
    Make GO/NO-GO/CONDITIONAL decision based on market model, competitors, and risks.
    
    Decision logic considers:
    - Market size range (from market_model)
    - Competitive intensity (from competitors and competition risks)
    - Regulatory risk (from regulatory risks)
    - Data confidence score (from market_model.overall_confidence)
    
    Args:
        market_model: MarketModel with TAM/SAM/SOM estimates
        competitors: List of analyzed competitors
        risks: RiskAnalysis with categorized risks
        
    Returns:
        DecisionResult with verdict, scores, conditions, and disconfirming evidence
    """
    # Score each factor
    market_score, market_reasoning = score_market_size(market_model)
    competition_score, competition_reasoning = score_competitive_intensity(
        competitors, risks.competition
    )
    regulatory_score, regulatory_reasoning = score_regulatory_risk(risks.regulatory)
    data_confidence_score, data_reasoning = score_data_confidence(
        market_model.overall_confidence
    )
    
    # Calculate overall viability score
    overall_score, factor_weights = calculate_viability_score(
        market_score,
        competition_score,
        regulatory_score,
        data_confidence_score
    )
    
    # Determine verdict
    verdict, conditions_to_go = determine_verdict(
        overall_score,
        market_score,
        competition_score,
        regulatory_score,
        data_confidence_score
    )
    
    # Generate disconfirming evidence
    disconfirming = generate_disconfirming_evidence(
        market_model,
        competitors,
        risks,
        overall_score
    )
    
    # Compile reasoning
    reasoning = {
        'market_size': market_reasoning,
        'competition': competition_reasoning,
        'regulatory': regulatory_reasoning,
        'data_confidence': data_reasoning
    }
    
    # Factor scores
    factor_scores = {
        'market_size': round(market_score, 1),
        'competition': round(competition_score, 1),
        'regulatory': round(regulatory_score, 1),
        'data_confidence': round(data_confidence_score, 1)
    }
    
    return DecisionResult(
        verdict=verdict,
        confidence_score=round(data_confidence_score),
        overall_score=round(overall_score, 1),
        factor_scores=factor_scores,
        conditions_to_go=conditions_to_go,
        disconfirming_evidence=disconfirming,
        reasoning=reasoning
    )


class ViabilityDecision(BaseModel):
    """Represents a market viability decision with uncertainty."""
    viability_score_range: tuple  # (min, max) 0.0 to 1.0
    recommendation: str  # Text recommendation
    confidence: float  # Overall confidence in decision
    key_factors: List[str]  # Key factors influencing decision
    risks: List[str]  # Identified risks
    assumptions: List[str]  # All assumptions made
    evidence_summary: Dict[str, Any]  # Summary of supporting evidence


def evaluate_viability(
    market_model: MarketModel,
    startup_parameters: Dict[str, Any]
) -> ViabilityDecision:
    """
    Evaluate market viability based on market model and startup parameters.
    
    Args:
        market_model: MarketModel with uncertainty ranges
        startup_parameters: Startup-specific parameters (product, team, etc.)
        
    Returns:
        ViabilityDecision with uncertainty ranges and full traceability
    """
    # Get competitors and risks
    competitors = analyze_competitors_from_data()
    risks = analyze_risks_from_data()
    
    # Make decision
    decision = make_decision(market_model, competitors, risks)
    
    # Convert to ViabilityDecision format (for backward compatibility)
    # Map overall_score to viability_score_range
    score_min = max(0.0, decision.overall_score - 15.0) / 100.0
    score_max = min(1.0, decision.overall_score + 15.0) / 100.0
    
    recommendation = f"{decision.verdict}"
    if decision.verdict == "CONDITIONAL":
        recommendation += f": {len(decision.conditions_to_go)} condition(s) must be met"
    
    return ViabilityDecision(
        viability_score_range=(score_min, score_max),
        recommendation=recommendation,
        confidence=decision.confidence_score / 100.0,
        key_factors=[
            f"Market size score: {decision.factor_scores['market_size']}/100",
            f"Competition score: {decision.factor_scores['competition']}/100",
            f"Regulatory score: {decision.factor_scores['regulatory']}/100",
            f"Data confidence: {decision.factor_scores['data_confidence']}/100"
        ],
        risks=risks.market + risks.competition + risks.regulatory + risks.distribution,
        assumptions=market_model.tam.assumptions + market_model.sam.assumptions + market_model.som.assumptions,
        evidence_summary={
            'overall_score': decision.overall_score,
            'verdict': decision.verdict,
            'conditions_to_go': decision.conditions_to_go,
            'disconfirming_evidence': decision.disconfirming_evidence
        }
    )

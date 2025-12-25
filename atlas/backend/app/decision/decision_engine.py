"""
Decision Engine Module

Implements decision logic for GO/NO-GO/CONDITIONAL verdicts.

Design Decisions:
- Considers multiple factors: market size, competition, regulatory risk, data confidence
- Always outputs specific conditions for CONDITIONAL verdicts
- Includes mandatory "What would make this analysis wrong?" section
- Decision logic is explicit and traceable
"""

from typing import Dict, Any, List, Literal, Tuple
from app.modeling import MarketModel
from app.decision.schemas import CompetitorInfo, RiskAnalysis


def score_market_size(market_model: MarketModel) -> Tuple[float, List[str]]:
    """
    Score market size factor (0-100).
    
    Higher scores for larger, more certain market sizes.
    
    Args:
        market_model: MarketModel with TAM/SAM/SOM estimates
        
    Returns:
        Tuple of (score 0-100, reasoning notes)
    """
    som = market_model.som
    som_base = som.base
    
    notes = []
    score = 0.0
    
    # Score based on SOM base case (most relevant for startup)
    if som_base >= 1.0:  # $1B+ SOM
        score = 90.0
        notes.append(f"Large addressable market (SOM: ${som_base:.2f}B base case)")
    elif som_base >= 0.5:  # $500M+ SOM
        score = 75.0
        notes.append(f"Moderate addressable market (SOM: ${som_base:.2f}B base case)")
    elif som_base >= 0.1:  # $100M+ SOM
        score = 60.0
        notes.append(f"Small but viable market (SOM: ${som_base:.2f}B base case)")
    elif som_base >= 0.05:  # $50M+ SOM
        score = 45.0
        notes.append(f"Very small market (SOM: ${som_base:.2f}B base case)")
    else:
        score = 20.0
        notes.append(f"Minimal market size (SOM: ${som_base:.2f}B base case)")
    
    # Adjust for range uncertainty (wider range = lower confidence)
    range_ratio = (som.max - som.min) / som_base if som_base > 0 else 1.0
    if range_ratio > 2.0:  # Range is more than 2x base
        score *= 0.7  # Reduce score by 30%
        notes.append(f"High uncertainty in market size (range ratio: {range_ratio:.1f}x)")
    elif range_ratio > 1.5:
        score *= 0.85
        notes.append(f"Moderate uncertainty in market size (range ratio: {range_ratio:.1f}x)")
    
    return min(100.0, max(0.0, score)), notes


def score_competitive_intensity(
    competitors: List[CompetitorInfo],
    competition_risks: List[str]
) -> Tuple[float, List[str]]:
    """
    Score competitive intensity factor (0-100).
    
    Lower scores for higher competition intensity.
    
    Args:
        competitors: List of analyzed competitors
        competition_risks: List of competition risk statements
        
    Returns:
        Tuple of (score 0-100, reasoning notes)
    """
    notes = []
    score = 100.0  # Start high, reduce for competition
    
    num_competitors = len(competitors)
    
    # Score based on number of competitors
    if num_competitors == 0:
        score = 80.0
        notes.append("No competitors identified - may indicate new market or incomplete research")
    elif num_competitors >= 10:
        score = 30.0
        notes.append(f"High number of competitors ({num_competitors}) - crowded market")
    elif num_competitors >= 5:
        score = 50.0
        notes.append(f"Moderate competition ({num_competitors} competitors identified)")
    elif num_competitors >= 2:
        score = 70.0
        notes.append(f"Limited competition ({num_competitors} competitors identified)")
    else:
        score = 85.0
        notes.append(f"Minimal competition ({num_competitors} competitor identified)")
    
    # Adjust based on competition risks
    high_risk_keywords = ['crowded', 'established', 'leaders', 'high competition', 'multiple']
    medium_risk_keywords = ['moderate', 'some', 'several']
    
    high_risk_count = sum(1 for risk in competition_risks 
                          if any(kw in risk.lower() for kw in high_risk_keywords))
    medium_risk_count = sum(1 for risk in competition_risks 
                           if any(kw in risk.lower() for kw in medium_risk_keywords))
    
    if high_risk_count > 0:
        score *= 0.7  # Reduce by 30%
        notes.append(f"{high_risk_count} high-severity competition risk(s) identified")
    elif medium_risk_count > 0:
        score *= 0.85  # Reduce by 15%
        notes.append(f"{medium_risk_count} moderate competition risk(s) identified")
    
    return min(100.0, max(0.0, score)), notes


def score_regulatory_risk(regulatory_risks: List[str]) -> Tuple[float, List[str]]:
    """
    Score regulatory risk factor (0-100).
    
    Lower scores for higher regulatory risk.
    
    Args:
        regulatory_risks: List of regulatory risk statements
        
    Returns:
        Tuple of (score 0-100, reasoning notes)
    """
    notes = []
    score = 100.0  # Start high, reduce for regulatory risk
    
    if not regulatory_risks:
        score = 90.0
        notes.append("No regulatory risks identified - low regulatory burden")
    else:
        # Count severity of regulatory risks
        high_severity_keywords = ['FDA', 'SEC', 'approval', 'compliance', 'require', 'restrict', 'prohibit']
        medium_severity_keywords = ['regulation', 'oversight', 'compliance']
        
        high_severity_count = sum(1 for risk in regulatory_risks 
                                 if any(kw in risk.lower() for kw in high_severity_keywords))
        medium_severity_count = sum(1 for risk in regulatory_risks 
                                   if any(kw in risk.lower() for kw in medium_severity_keywords))
        
        if high_severity_count > 0:
            score = 40.0
            notes.append(f"{high_severity_count} high-severity regulatory risk(s) - significant compliance requirements")
        elif medium_severity_count > 0:
            score = 65.0
            notes.append(f"{medium_severity_count} regulatory consideration(s) identified")
        else:
            score = 80.0
            notes.append(f"{len(regulatory_risks)} regulatory mention(s) - low to moderate risk")
    
    return min(100.0, max(0.0, score)), notes


def score_data_confidence(overall_confidence: str) -> Tuple[float, List[str]]:
    """
    Score data confidence factor (0-100).
    
    Higher scores for higher data confidence.
    
    Args:
        overall_confidence: 'high', 'medium', or 'low'
        
    Returns:
        Tuple of (score 0-100, reasoning notes)
    """
    notes = []
    
    if overall_confidence == 'high':
        score = 90.0
        notes.append("High data confidence - multiple high-quality sources")
    elif overall_confidence == 'medium':
        score = 65.0
        notes.append("Medium data confidence - some data quality concerns")
    else:  # low
        score = 40.0
        notes.append("Low data confidence - limited or low-quality data sources")
    
    return score, notes


def calculate_viability_score(
    market_score: float,
    competition_score: float,
    regulatory_score: float,
    data_confidence_score: float
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate overall viability score from factor scores.
    
    Uses weighted average with market size and data confidence weighted higher.
    
    Args:
        market_score: Market size score (0-100)
        competition_score: Competition score (0-100)
        regulatory_score: Regulatory risk score (0-100)
        data_confidence_score: Data confidence score (0-100)
        
    Returns:
        Tuple of (overall score 0-100, factor weights)
    """
    # Weight factors: market size and data confidence are most important
    weights = {
        'market': 0.35,
        'competition': 0.25,
        'regulatory': 0.20,
        'data_confidence': 0.20
    }
    
    overall_score = (
        market_score * weights['market'] +
        competition_score * weights['competition'] +
        regulatory_score * weights['regulatory'] +
        data_confidence_score * weights['data_confidence']
    )
    
    return overall_score, weights


def determine_verdict(
    overall_score: float,
    market_score: float,
    competition_score: float,
    regulatory_score: float,
    data_confidence_score: float
) -> Tuple[Literal["GO", "NO-GO", "CONDITIONAL"], List[str]]:
    """
    Determine GO/NO-GO/CONDITIONAL verdict based on scores.
    
    Args:
        overall_score: Overall viability score (0-100)
        market_score: Market size score (0-100)
        competition_score: Competition score (0-100)
        regulatory_score: Regulatory risk score (0-100)
        data_confidence_score: Data confidence score (0-100)
        
    Returns:
        Tuple of (verdict, conditions for CONDITIONAL)
    """
    conditions = []
    
    # GO threshold: high overall score AND no critical failures
    if overall_score >= 70 and all(score >= 50 for score in [market_score, competition_score, regulatory_score, data_confidence_score]):
        return "GO", []
    
    # NO-GO threshold: very low overall score OR critical failure in key factors
    if overall_score < 40:
        return "NO-GO", []
    
    if market_score < 30:
        return "NO-GO", []
    
    if data_confidence_score < 30:
        return "NO-GO", []
    
    # CONDITIONAL: everything else
    # Build conditions based on what needs improvement
    if market_score < 60:
        conditions.append(f"Market size must be validated - current SOM base case may be insufficient (score: {market_score:.0f}/100)")
    
    if competition_score < 60:
        conditions.append(f"Competitive differentiation must be proven - competition intensity is high (score: {competition_score:.0f}/100)")
    
    if regulatory_score < 60:
        conditions.append(f"Regulatory compliance path must be clarified - regulatory risks identified (score: {regulatory_score:.0f}/100)")
    
    if data_confidence_score < 60:
        conditions.append(f"Additional market research required - data confidence is low (score: {data_confidence_score:.0f}/100)")
    
    if overall_score < 60:
        conditions.append(f"Overall viability score must improve from {overall_score:.0f}/100 to at least 70/100")
    
    return "CONDITIONAL", conditions


def generate_disconfirming_evidence(
    market_model: MarketModel,
    competitors: List[Any],  # List[CompetitorInfo]
    risks: Any,  # RiskAnalysis
    overall_score: float
) -> List[str]:
    """
    Generate "What would make this analysis wrong?" section.
    
    Identifies key assumptions and scenarios that could invalidate the analysis.
    
    Args:
        market_model: MarketModel with estimates
        competitors: List of competitors
        risks: RiskAnalysis object
        overall_score: Overall viability score
        
    Returns:
        List of disconfirming evidence scenarios
    """
    disconfirming = []
    
    # Market size disconfirming scenarios
    if market_model.som.base < 0.5:
        disconfirming.append(
            f"Market size is overestimated - if actual SOM is below ${market_model.som.min:.2f}B, "
            f"the market may be too small to support viable business"
        )
    
    if market_model.tam.data_quality == 'low':
        disconfirming.append(
            "Market size data is unreliable - if reported TAM figures are inaccurate or outdated, "
            "all market size estimates (TAM/SAM/SOM) would be invalid"
        )
    
    # Competition disconfirming scenarios
    num_competitors = len(competitors) if competitors else 0
    if num_competitors == 0:
        disconfirming.append(
            "Competitive landscape is unknown - if significant competitors exist but were not identified, "
            "competition intensity is underestimated"
        )
    elif num_competitors >= 5:
        disconfirming.append(
            f"Competition may be more intense than assessed - if {num_competitors}+ competitors are actively "
            "competing, market share capture may be more difficult than estimated"
        )
    
    # Regulatory disconfirming scenarios
    regulatory_risks = getattr(risks, 'regulatory', []) if hasattr(risks, 'regulatory') else []
    if len(regulatory_risks) > 0:
        disconfirming.append(
            "Regulatory requirements may be more stringent than identified - if additional compliance "
            "requirements emerge, time-to-market and costs could be significantly higher"
        )
    else:
        disconfirming.append(
            "Regulatory risks may be underestimated - if regulatory oversight is required but not yet "
            "identified, compliance costs could materially impact viability"
        )
    
    # Data quality disconfirming scenarios
    if market_model.overall_confidence == 'low':
        disconfirming.append(
            "Low data confidence - if key assumptions based on limited data are incorrect, "
            "the entire analysis may be invalid"
        )
    
    # Market dynamics disconfirming scenarios
    if len(risks.market) > 0:
        disconfirming.append(
            "Market risks identified - if market growth is slower than estimated or market is declining, "
            "viability would be significantly reduced"
        )
    
    # General disconfirming scenarios
    if overall_score < 60:
        disconfirming.append(
            f"Overall viability score is {overall_score:.0f}/100 - multiple factors need validation. "
            "If any key assumption proves incorrect, verdict could change to NO-GO"
        )
    
    # Always include fundamental disconfirming scenarios
    disconfirming.append(
        "Customer willingness to pay may be lower than assumed - if pricing assumptions are incorrect, "
        "revenue projections would be invalid"
    )
    
    disconfirming.append(
        "Market timing may be wrong - if market is not ready for this solution or timing is premature, "
        "adoption could be slower than expected"
    )
    
    return disconfirming


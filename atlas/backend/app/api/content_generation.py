"""
Content Generation Module

Generates high-quality, concrete content for ATLAS output.

Design Decisions:
- Executive summaries must contain concrete details (numbers, names, channels)
- Bans vague phrases like "growing market", "strong demand", "many competitors"
- Every numeric claim must be source-attributed
- Key Unknowns identify critical information gaps
- Next 7 Days Tests provide actionable validation steps
"""

from typing import List, Dict, Any, Optional
from app.modeling import MarketModel
from app.decision import DecisionResult, CompetitorInfo, RiskAnalysis
from app.storage.database import get_db_connection


def generate_executive_summary(
    request: Any,
    market_model: Optional[MarketModel],
    decision: Optional[DecisionResult],
    competitors: List[CompetitorInfo],
    risks: Optional[RiskAnalysis],
    confidence_score: int
) -> List[str]:
    """
    Generate executive summary with 8-12 bullets containing concrete details.
    
    Bans vague phrases. Each bullet must contain:
    - A number, OR
    - A named competitor, OR
    - A specific channel, OR
    - A specific constraint
    
    Args:
        request: AnalyzeRequest
        market_model: MarketModel with estimates
        decision: DecisionResult
        competitors: List of competitors
        risks: RiskAnalysis
        confidence_score: Confidence score 0-100
        
    Returns:
        List of 8-12 concrete bullet points
    """
    bullets = []
    
    # 1. Verdict with score
    if decision:
        bullets.append(
            f"Verdict: {decision.verdict} (viability score: {decision.overall_score:.0f}/100, "
            f"confidence: {confidence_score}/100)"
        )
    else:
        bullets.append(f"Verdict: CONDITIONAL (confidence: {confidence_score}/100)")
    
    # 2. Market size with specific numbers
    if market_model:
        tam_base = market_model.tam.base
        sam_base = market_model.sam.base
        som_base = market_model.som.base
        
        if tam_base >= 1.0:
            bullets.append(
                f"TAM: ${tam_base:.2f}B (range: ${market_model.tam.min:.2f}B - ${market_model.tam.max:.2f}B) "
                f"via {market_model.tam.method} method"
            )
        else:
            bullets.append(
                f"TAM: ${tam_base*1000:.0f}M (range: ${market_model.tam.min*1000:.0f}M - ${market_model.tam.max*1000:.0f}M) "
                f"via {market_model.tam.method} method"
            )
        
        bullets.append(
            f"SAM: ${sam_base:.2f}B, SOM: ${som_base:.2f}B (5-year target) for {request.customer_type} in {request.geography}"
        )
    else:
        bullets.append("Market size: Unable to estimate (insufficient data)")
    
    # 3. Competitors with names
    if competitors:
        if len(competitors) == 1:
            bullets.append(f"Primary competitor: {competitors[0].name} ({competitors[0].positioning})")
        elif len(competitors) <= 3:
            names = ", ".join([c.name for c in competitors[:3]])
            bullets.append(f"Identified competitors: {names}")
        else:
            top_3 = ", ".join([c.name for c in competitors[:3]])
            bullets.append(f"Top competitors: {top_3} (plus {len(competitors)-3} others)")
    else:
        bullets.append("Competitive landscape: No competitors identified in research")
    
    # 4. Specific risk with numbers/details
    if risks:
        if risks.competition:
            comp_risk = risks.competition[0]
            bullets.append(f"Competition risk: {comp_risk}")
        elif risks.regulatory:
            reg_risk = risks.regulatory[0]
            bullets.append(f"Regulatory risk: {reg_risk}")
        elif risks.market:
            market_risk = risks.market[0]
            bullets.append(f"Market risk: {market_risk}")
    
    # 5. Data quality with numbers
    if market_model:
        data_quality = market_model.overall_confidence
        num_sources = len(market_model.evidence_sources)
        bullets.append(
            f"Data quality: {data_quality} confidence from {num_sources} source(s)"
        )
    
    # 6. Business model specifics
    bullets.append(f"Business model: {request.business_model} targeting {request.customer_type}")
    
    # 7. Pricing if provided
    if request.price_assumption:
        bullets.append(f"Price assumption: ${request.price_assumption:.2f} per unit")
    
    # 8. Conditions if CONDITIONAL
    if decision and decision.verdict == "CONDITIONAL" and decision.conditions_to_go:
        num_conditions = len(decision.conditions_to_go)
        bullets.append(f"CONDITIONAL: {num_conditions} condition(s) must be met to reach GO verdict")
    
    # 9. Key constraint or limitation
    if risks and risks.distribution:
        bullets.append(f"Distribution constraint: {risks.distribution[0]}")
    elif market_model and market_model.som.base < 0.1:
        bullets.append(f"Market size constraint: SOM below $100M suggests limited addressable market")
    
    # 10. Geographic focus
    bullets.append(f"Geographic focus: {request.geography}")
    
    # 11. Industry context
    bullets.append(f"Industry: {request.industry}")
    
    # 12. Confidence explanation
    if confidence_score >= 70:
        bullets.append(f"High confidence ({confidence_score}/100): Multiple independent sources with good agreement")
    elif confidence_score >= 50:
        bullets.append(f"Moderate confidence ({confidence_score}/100): Some data quality concerns")
    else:
        bullets.append(f"Low confidence ({confidence_score}/100): Limited or low-quality data sources")
    
    # Ensure we have 8-12 bullets with concrete details
    while len(bullets) < 8:
        # Add concrete bullets (never vague)
        if len(competitors) > 0:
            bullets.append(f"Competitive analysis: {len(competitors)} competitor(s) identified with positioning data")
        else:
            bullets.append("Competitive analysis: 0 competitors found in research - may indicate new market")
        
        if market_model:
            bullets.append(f"Market estimation method: {market_model.tam.method} with {len(market_model.evidence_sources)} source(s)")
        else:
            bullets.append("Market estimation: Unable to calculate - insufficient data")
        
        if risks:
            total_risks = len(risks.market) + len(risks.competition) + len(risks.regulatory) + len(risks.distribution)
            bullets.append(f"Risk assessment: {total_risks} specific risk(s) identified across 4 categories")
        
        # Break if we've added enough or are looping
        if len(bullets) >= 8:
            break
    
    # Trim to 12 if needed
    return bullets[:12]


def generate_key_unknowns(
    market_model: Optional[MarketModel],
    competitors: List[CompetitorInfo],
    risks: Optional[RiskAnalysis],
    decision: Optional[DecisionResult],
    request: Any
) -> List[str]:
    """
    Generate 5 key unknowns - what we still don't know.
    
    Args:
        market_model: MarketModel
        competitors: List of competitors
        risks: RiskAnalysis
        decision: DecisionResult
        request: AnalyzeRequest
        
    Returns:
        List of exactly 5 key unknowns
    """
    unknowns = []
    
    # 1. Market validation
    if not market_model or market_model.overall_confidence == 'low':
        unknowns.append("Actual market size and growth rate - need primary market research validation")
    else:
        unknowns.append("Customer willingness to pay at assumed price point - need pricing validation")
    
    # 2. Competition
    if len(competitors) == 0:
        unknowns.append("Complete competitive landscape - may have unidentified competitors")
    else:
        unknowns.append("Competitive pricing and feature comparison - need detailed competitive analysis")
    
    # 3. Customer validation
    unknowns.append(f"Customer acquisition cost (CAC) and lifetime value (LTV) for {request.customer_type}")
    
    # 4. Distribution
    if not risks or not risks.distribution:
        unknowns.append("Optimal distribution channels and channel economics")
    else:
        unknowns.append("Distribution channel costs and conversion rates")
    
    # 5. Regulatory/Compliance
    if not risks or not risks.regulatory:
        unknowns.append("Regulatory requirements and compliance costs for this industry")
    else:
        unknowns.append("Specific regulatory approval timeline and costs")
    
    # Ensure we have exactly 5
    while len(unknowns) < 5:
        unknowns.append("Additional market dynamics and constraints")
    
    return unknowns[:5]


def generate_next_7_days_tests(
    request: Any,
    market_model: Optional[MarketModel],
    decision: Optional[DecisionResult],
    competitors: List[CompetitorInfo]
) -> List[Dict[str, str]]:
    """
    Generate 6 tests to run in the next 7 days with method and success threshold.
    
    Args:
        request: AnalyzeRequest
        market_model: MarketModel
        decision: DecisionResult
        competitors: List of competitors
        
    Returns:
        List of 6 test dictionaries with test, method, and success_threshold
    """
    tests = []
    
    # Test 1: Market size validation
    if market_model:
        tests.append({
            "test": f"Validate TAM estimate of ${market_model.tam.base:.2f}B with industry experts",
            "method": "Interview 3-5 industry experts or analysts, ask about market size estimates",
            "success_threshold": "At least 2 experts confirm TAM is within ${market_model.tam.min:.2f}B - ${market_model.tam.max:.2f}B range"
        })
    else:
        tests.append({
            "test": "Obtain initial market size estimate from industry reports",
            "method": "Search for industry market research reports, Gartner/Forrester studies",
            "success_threshold": "Find at least 1 credible source with market size data"
        })
    
    # Test 2: Customer validation
    tests.append({
        "test": f"Validate customer segment: {request.customer_type}",
        "method": f"Interview 5-10 potential customers matching {request.customer_type} profile",
        "success_threshold": "At least 60% express interest or confirm they have this problem"
    })
    
    # Test 3: Pricing validation
    if request.price_assumption:
        tests.append({
            "test": f"Validate price point of ${request.price_assumption:.2f}",
            "method": "Conduct pricing surveys or interviews asking about willingness to pay",
            "success_threshold": f"At least 50% of respondents indicate willingness to pay ${request.price_assumption * 0.8:.2f} or more"
        })
    else:
        tests.append({
            "test": "Determine optimal price point",
            "method": "Conduct pricing research: surveys, competitor analysis, value-based pricing interviews",
            "success_threshold": "Identify price range with at least 3 data points supporting it"
        })
    
    # Test 4: Competitive differentiation
    if competitors:
        top_competitor = competitors[0].name
        tests.append({
            "test": f"Validate differentiation vs {top_competitor}",
            "method": f"Compare features, pricing, positioning with {top_competitor}, interview customers who switched",
            "success_threshold": "Identify at least 2 clear differentiators that customers value"
        })
    else:
        tests.append({
            "test": "Identify and analyze top 3 competitors",
            "method": "Research competitive landscape: company websites, reviews, industry reports",
            "success_threshold": "Document 3 competitors with their positioning, pricing, and key features"
        })
    
    # Test 5: Distribution channel
    tests.append({
        "test": f"Validate distribution strategy for {request.customer_type}",
        "method": "Research how similar products reach this customer segment, interview channel partners",
        "success_threshold": "Identify at least 2 viable distribution channels with estimated CAC"
    })
    
    # Test 6: Regulatory/Compliance
    tests.append({
        "test": f"Assess regulatory requirements for {request.industry} in {request.geography}",
        "method": "Research industry regulations, consult with legal/compliance experts if needed",
        "success_threshold": "Document all regulatory requirements and estimated compliance timeline/costs"
    })
    
    # Ensure we have exactly 6
    while len(tests) < 6:
        tests.append({
            "test": "Additional market validation test",
            "method": "TBD based on specific unknowns",
            "success_threshold": "TBD"
        })
    
    return tests[:6]


def get_numeric_claims_with_sources(market_model: Optional[MarketModel]) -> List[Dict[str, Any]]:
    """
    Get numeric claims with source attribution for market size estimates.
    
    Normalizes values to billions USD for consistency.
    
    Args:
        market_model: MarketModel
        
    Returns:
        List of NumericClaim dictionaries with values in billions USD
    """
    claims = []
    
    if not market_model:
        return claims
    
    # Get market size facts from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'value': row[0],
        'unit': row[1],
        'source_url': row[2],
        'context_sentence': row[3]
    }
    
    try:
        cursor.execute("""
            SELECT value, unit, source_url, context_sentence
            FROM extracted_facts
            WHERE fact_type = 'market_size' 
            AND is_inferred = 0
            AND value IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            value = float(row['value'])
            unit = row['unit'] or ''
            
            # Normalize to billions USD
            if 'trillion' in unit.lower():
                value_billions = value * 1000
            elif 'billion' in unit.lower() or 'b' in unit.lower():
                value_billions = value
            elif 'million' in unit.lower() or 'm' in unit.lower():
                value_billions = value / 1000
            elif 'thousand' in unit.lower() or 'k' in unit.lower():
                value_billions = value / 1000000
            else:
                # Assume billions if unclear
                value_billions = value
            
            claims.append({
                'value': value_billions * 1_000_000_000,  # Convert to dollars for response
                'unit': 'USD',
                'source_url': row['source_url'],
                'excerpt': row['context_sentence'][:300]  # First 300 chars
            })
    finally:
        conn.close()
    
    return claims


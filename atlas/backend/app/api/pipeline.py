"""
Analysis Pipeline Module

Orchestrates the multi-step analysis pipeline for market viability assessment.

Design Decisions:
- Pipeline is modular and can be extended with additional steps
- Each step is independent and can be tested separately
- Pipeline maintains evidence chain throughout
- All intermediate results are stored for auditability
- Errors degrade gracefully with explicit uncertainty
"""

from datetime import datetime, timezone
from app.api.schemas import (
    AnalyzeRequest, 
    AnalyzeResponse,
    MarketSection,
    MarketSize,
    SAM,
    SOM,
    Risks,
    Source,
    Competitor,
    NumericClaim,
    Test
)

# Import all pipeline modules
from app.research import research_market
from app.extraction import extract_from_all_sources
from app.modeling import estimate_tam_sam_som
from app.modeling.scenarios import (
    calculate_scenarios,
    calculate_sensitivity_analysis
)
from app.decision import (
    analyze_competitors_from_data,
    analyze_risks_from_data,
    make_decision
)
from app.evidence import get_confidence_score
from app.evidence.ledger import get_all_claims
from app.storage.database import get_db_connection
from app.api.content_generation import (
    generate_executive_summary,
    generate_key_unknowns,
    generate_next_7_days_tests,
    get_numeric_claims_with_sources
)


async def run_analysis_pipeline(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Execute the full analysis pipeline for market viability assessment.
    """
    try:
        return await _run_analysis_pipeline_internal(request)
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in analysis pipeline: {e}")
        print(traceback.format_exc())
        # Return a graceful failure response instead of a 500
        from app.api.schemas import MarketSection, MarketSize, SAM, SOM, Risks, Test
        
        # Create empty/fallback objects to satisfy Pydantic validation
        fallback_market = MarketSection(
            tam=MarketSize(min=0, base=0, max=0, assumptions=["Analysis failed"]),
            sam=SAM(min=0, base=0, max=0),
            som=SOM(min=0, base=0, max=0)
        )
        
        return AnalyzeResponse(
            verdict="CONDITIONAL",
            confidence_score=0,
            executive_summary=[f"Analysis failed: {str(e)}", "Please check your input and try again."] + ["-"] * 6,
            market=fallback_market,
            competitors=[],
            risks=Risks(market=[], competition=[], regulatory=[], distribution=[]),
            assumptions=[f"Pipeline error: {str(e)}"],
            sources=[],
            key_unknowns=["-"] * 5,
            next_7_days_tests=[Test(test="-", method="-", success_threshold="-")] * 6,
            scenarios={},
            sensitivity_analysis=[],
        )

async def _run_analysis_pipeline_internal(request: AnalyzeRequest) -> AnalyzeResponse:
    """Internal implementation of the analysis pipeline."""
    errors = []
    warnings = []
    
    # Step 1: Research - Gather sources
    research_result = None
    try:
        research_result = await research_market(
            idea=request.idea,
            industry=request.industry,
            geography=request.geography,
            customer_type=request.customer_type
        )
    except Exception as e:
        errors.append(f"Research step failed: {str(e)}")
        warnings.append("Analysis proceeding with limited or no research data")
    
    # Step 2: Extraction - Extract facts from sources
    extraction_result = None
    try:
        extraction_result = await extract_from_all_sources()
    except Exception as e:
        errors.append(f"Extraction step failed: {str(e)}")
        warnings.append("Analysis proceeding without extracted facts")
    
    # Step 3: Modeling - Create market model
    market_model = None
    try:
        # Get estimated customers if price assumption provided (for bottom-up)
        estimated_customers = None
        if request.price_assumption:
            # Rough estimate: assume price_assumption is annual, estimate customer range
            # This is a placeholder - in real implementation, this would be more sophisticated
            estimated_customers = {
                'min': 1000,
                'base': 5000,
                'max': 10000
            }
        
        market_model = estimate_tam_sam_som(
            customer_type=request.customer_type,
            geography=request.geography,
            estimated_customers=estimated_customers,
            market_penetration_years=5
        )
    except Exception as e:
        errors.append(f"Modeling step failed: {str(e)}")
        warnings.append("Market model could not be created - using conservative estimates")
        # Create fallback model with wide uncertainty
        market_model = _create_fallback_market_model()
    
    # Step 4: Decision - Analyze competitors, risks, and make decision
    competitors = []
    risks = None
    decision = None
    
    try:
        competitors = analyze_competitors_from_data()
    except Exception as e:
        errors.append(f"Competitor analysis failed: {str(e)}")
        warnings.append("Competitor analysis unavailable")
    
    try:
        risks = analyze_risks_from_data()
    except Exception as e:
        errors.append(f"Risk analysis failed: {str(e)}")
        warnings.append("Risk analysis unavailable - using empty risk categories")
        risks = Risks(market=[], competition=[], regulatory=[], distribution=[])
    
    try:
        if market_model:
            decision = make_decision(market_model, competitors, risks)
    except Exception as e:
        errors.append(f"Decision step failed: {str(e)}")
        warnings.append("Decision could not be made - defaulting to CONDITIONAL")
        decision = None
    
    # Step 5: Confidence - Calculate confidence score
    confidence_score = 50  # Default if calculation fails
    confidence_explanation = "Confidence score calculation unavailable"
    try:
        confidence_result = get_confidence_score()
        confidence_score = int(confidence_result.score)
        confidence_explanation = confidence_result.explanation
    except Exception as e:
        errors.append(f"Confidence calculation failed: {str(e)}")
        warnings.append("Using default confidence score")
    
    # Step 6: Scenario Analysis - Calculate Bear/Base/Bull scenarios
    scenarios = {}
    sensitivity_analysis = []
    try:
        if market_model:
            # Get price/ARPA from request or pricing facts
            price_arpa = request.price_assumption
            if price_arpa:
                # Convert to annual if it seems like monthly (heuristic)
                if price_arpa < 1000:
                    price_arpa = price_arpa * 12
            
            scenarios = calculate_scenarios(
                base_model=market_model,
                price_arpa=price_arpa,
                adoption_rate=None,  # Will be derived
                reachable_customers=None  # Will be derived
            )
            
            # Calculate sensitivity analysis
            sensitivity_analysis = calculate_sensitivity_analysis(
                base_model=market_model,
                price_arpa=price_arpa,
                adoption_rate=None,
                reachable_customers=None
            )
    except Exception as e:
        errors.append(f"Scenario analysis failed: {str(e)}")
        warnings.append("Scenario analysis unavailable")
        # Create fallback scenarios
        if market_model:
            scenarios = _create_fallback_scenarios(market_model)
            sensitivity_analysis = []
    
    # Step 7: Compile response
    return _compile_response(
        request=request,
        market_model=market_model,
        decision=decision,
        competitors=competitors,
        risks=risks,
        confidence_score=confidence_score,
        research_result=research_result,
        scenarios=scenarios,
        sensitivity_analysis=sensitivity_analysis,
        errors=errors,
        warnings=warnings
    )


def _create_fallback_market_model():
    """Create a fallback market model with wide uncertainty when modeling fails."""
    from app.modeling import MarketModel, MarketEstimate
    
    return MarketModel(
        tam=MarketEstimate(
            min=0.0,
            base=1.0,
            max=10.0,
            method="fallback",
            formula="Fallback estimate - modeling failed",
            assumptions=["Modeling step failed - using conservative fallback estimates"],
            sensitivity_notes=["High uncertainty - modeling data unavailable"],
            data_quality="low"
        ),
        sam=MarketEstimate(
            min=0.0,
            base=0.1,
            max=1.0,
            method="fallback",
            formula="Fallback estimate - modeling failed",
            assumptions=["Modeling step failed - using conservative fallback estimates"],
            sensitivity_notes=["High uncertainty - modeling data unavailable"],
            data_quality="low"
        ),
        som=MarketEstimate(
            min=0.0,
            base=0.01,
            max=0.1,
            method="fallback",
            formula="Fallback estimate - modeling failed",
            assumptions=["Modeling step failed - using conservative fallback estimates"],
            sensitivity_notes=["High uncertainty - modeling data unavailable"],
            data_quality="low"
        ),
        evidence_sources=[],
        overall_confidence="low"
    )


def _create_fallback_scenarios(base_model):
    """Create fallback scenarios when calculation fails."""
    from app.modeling.scenarios import Scenario
    from app.modeling import MarketEstimate
    
    # Use base model for all scenarios (no variation)
    return {
        'bear': Scenario(
            name="Bear",
            tam=base_model.tam,
            sam=base_model.sam,
            som=base_model.som,
            assumptions_used={}
        ),
        'base': Scenario(
            name="Base",
            tam=base_model.tam,
            sam=base_model.sam,
            som=base_model.som,
            assumptions_used={}
        ),
        'bull': Scenario(
            name="Bull",
            tam=base_model.tam,
            sam=base_model.sam,
            som=base_model.som,
            assumptions_used={}
        )
    }


def _compile_response(
    request: AnalyzeRequest,
    market_model,
    decision,
    competitors: List,
    risks,
    confidence_score: int,
    research_result: Dict[str, Any],
    scenarios: Dict[str, Any],
    sensitivity_analysis: List[Any],
    errors: List[str],
    warnings: List[str]
) -> AnalyzeResponse:
    """Compile the final AnalyzeResponse from all pipeline results."""
    from app.api.schemas import MarketSection, MarketSize, SAM, SOM, Competitor, Source, Test
    
    # Generate high-quality executive summary (8-12 bullets with concrete details)
    executive_summary = generate_executive_summary(
        request=request,
        market_model=market_model,
        decision=decision,
        competitors=competitors,
        risks=risks,
        confidence_score=confidence_score
    )
    
    # Generate Key Unknowns (exactly 5)
    key_unknowns = generate_key_unknowns(
        market_model=market_model,
        competitors=competitors,
        risks=risks,
        decision=decision,
        request=request
    )
    
    # Generate Next 7 Days Tests (exactly 6)
    test_dicts = generate_next_7_days_tests(
        request=request,
        market_model=market_model,
        decision=decision,
        competitors=competitors
    )
    next_7_days_tests = [
        Test(test=t['test'], method=t['method'], success_threshold=t['success_threshold'])
        for t in test_dicts
    ]
    
    # Get numeric claims with sources for TAM
    numeric_claims = get_numeric_claims_with_sources(market_model)
    source_claims = [
        NumericClaim(
            value=claim['value'],
            unit=claim['unit'],
            source_url=claim['source_url'],
            excerpt=claim['excerpt']
        )
        for claim in numeric_claims
    ]
    
    # Build market section
    if market_model:
        market_section = MarketSection(
            tam=MarketSize(
                min=market_model.tam.min * 1_000_000_000,  # Convert billions to dollars
                base=market_model.tam.base * 1_000_000_000,
                max=market_model.tam.max * 1_000_000_000,
                method=market_model.tam.method,
                assumptions=market_model.tam.assumptions,
                source_claims=source_claims
            ),
            sam=SAM(
                min=market_model.sam.min * 1_000_000_000,
                base=market_model.sam.base * 1_000_000_000,
                max=market_model.sam.max * 1_000_000_000,
                assumptions=market_model.sam.assumptions
            ),
            som=SOM(
                min=market_model.som.min * 1_000_000_000,
                base=market_model.som.base * 1_000_000_000,
                max=market_model.som.max * 1_000_000_000,
                assumptions=market_model.som.assumptions
            )
        )
    else:
        # Fallback market section
        market_section = MarketSection(
            tam=MarketSize(
                min=0.0,
                base=1_000_000_000,
                max=10_000_000_000,
                method="fallback",
                assumptions=["Market modeling failed - using conservative estimates"],
                source_claims=[]  # No source claims for fallback
            ),
            sam=SAM(
                min=0.0,
                base=100_000_000,
                max=1_000_000_000,
                assumptions=["Market modeling failed - using conservative estimates"]
            ),
            som=SOM(
                min=0.0,
                base=10_000_000,
                max=100_000_000,
                assumptions=["Market modeling failed - using conservative estimates"]
            )
        )
    
    # Build competitors list
    competitor_list = []
    for comp in competitors:
        competitor_list.append(Competitor(
            name=comp.name,
            positioning=comp.positioning,
            pricing=comp.pricing,
            geography=comp.geography,
            differentiator=comp.differentiator,
            source_url=comp.source_url
        ))
    
    # Build risks
    if risks:
        risks_section = Risks(
            market=risks.market,
            competition=risks.competition,
            regulatory=risks.regulatory,
            distribution=risks.distribution
        )
    else:
        risks_section = Risks(
            market=["Risk analysis unavailable"],
            competition=[],
            regulatory=[],
            distribution=[]
        )
    
    # Build assumptions
    assumptions = []
    if market_model:
        assumptions.extend(market_model.tam.assumptions)
        assumptions.extend(market_model.sam.assumptions)
        assumptions.extend(market_model.som.assumptions)
    
    # Add conditions to go if CONDITIONAL verdict
    if decision and decision.verdict == "CONDITIONAL" and decision.conditions_to_go:
        assumptions.append("CONDITIONAL verdict - conditions that must be met to reach GO:")
        assumptions.extend([f"  • {condition}" for condition in decision.conditions_to_go])
    
    if warnings:
        assumptions.extend([f"Warning: {w}" for w in warnings])
    
    if errors:
        assumptions.extend([f"Error: {e}" for e in errors])
    
    if not assumptions:
        assumptions.append("No explicit assumptions documented")
    
    # Build disconfirming evidence
    disconfirming_evidence = []
    if decision:
        disconfirming_evidence.extend(decision.disconfirming_evidence)
    else:
        disconfirming_evidence.append("Decision analysis unavailable - cannot assess disconfirming evidence")
    
    # Build sources list
    sources_list = []
    if market_model and market_model.evidence_sources:
        # Get source details from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.row_factory = lambda cursor, row: {
            'url': row[0],
            'title': row[1],
            'extracted_text': row[2]
        }
        
        try:
            placeholders = ','.join(['?'] * len(market_model.evidence_sources))
            cursor.execute(f"""
                SELECT url, title, extracted_text
                FROM sources
                WHERE url IN ({placeholders})
                LIMIT 20
            """, market_model.evidence_sources)
            
            for row in cursor.fetchall():
                # Get excerpt (first 200 chars)
                excerpt = row['extracted_text'][:200] + "..." if len(row['extracted_text']) > 200 else row['extracted_text']
                sources_list.append(Source(
                    title=row['title'],
                    url=row['url'],
                    excerpt=excerpt
                ))
        except Exception as e:
            # If source retrieval fails, create placeholder
            sources_list.append(Source(
                title="Source retrieval failed",
                url="unknown",
                excerpt=f"Could not retrieve source details: {str(e)}"
            ))
        finally:
            conn.close()
    
    if not sources_list:
        sources_list.append(Source(
            title="No sources available",
            url="unknown",
            excerpt="Source information unavailable"
        ))
    
    # Determine verdict
    if decision:
        verdict = decision.verdict
    else:
        verdict = "CONDITIONAL"
    
    # Build final response
    # Build scenarios for response
    scenario_dict = {}
    if scenarios:
        from app.api.schemas import Scenario, ScenarioMarketSection
        for key, scenario in scenarios.items():
            scenario_dict[key] = Scenario(
                name=scenario.name,
                market=ScenarioMarketSection(
                    tam=MarketSize(
                        min=scenario.tam.min * 1_000_000_000,
                        base=scenario.tam.base * 1_000_000_000,
                        max=scenario.tam.max * 1_000_000_000,
                        method=scenario.tam.method,
                        assumptions=scenario.tam.assumptions,
                        source_claims=[]
                    ),
                    sam=SAM(
                        min=scenario.sam.min * 1_000_000_000,
                        base=scenario.sam.base * 1_000_000_000,
                        max=scenario.sam.max * 1_000_000_000,
                        assumptions=scenario.sam.assumptions
                    ),
                    som=SOM(
                        min=scenario.som.min * 1_000_000_000,
                        base=scenario.som.base * 1_000_000_000,
                        max=scenario.som.max * 1_000_000_000,
                        assumptions=scenario.som.assumptions
                    )
                ),
                assumptions_used=scenario.assumptions_used
            )
    else:
        # Fallback: use base market model for all scenarios
        from app.api.schemas import Scenario, ScenarioMarketSection
        scenario_dict = {
            'bear': Scenario(
                name="Bear",
                market=market_section,
                assumptions_used={}
            ),
            'base': Scenario(
                name="Base",
                market=market_section,
                assumptions_used={}
            ),
            'bull': Scenario(
                name="Bull",
                market=market_section,
                assumptions_used={}
            )
        }
    
    # Build sensitivity analysis for response
    from app.api.schemas import SensitivityImpact
    sensitivity_list = []
    if sensitivity_analysis:
        for sens in sensitivity_analysis:
            sensitivity_list.append(SensitivityImpact(
                assumption_name=sens.assumption_name,
                base_som=sens.base_som * 1_000_000_000,  # Convert to dollars
                impact_minus_30pct=sens.impact_minus_30pct * 1_000_000_000,
                impact_plus_30pct=sens.impact_plus_30pct * 1_000_000_000,
                impact_magnitude=sens.impact_magnitude * 1_000_000_000
            ))
    else:
        # Fallback: create default sensitivity analysis
        if market_model:
            base_som = market_model.som.base * 1_000_000_000
            for i in range(5):
                sensitivity_list.append(SensitivityImpact(
                    assumption_name=f"Assumption {i+1}",
                    base_som=base_som,
                    impact_minus_30pct=base_som * 0.7,
                    impact_plus_30pct=base_som * 1.3,
                    impact_magnitude=base_som * 0.6
                ))
    
    # Ensure we have exactly 5 sensitivity impacts
    while len(sensitivity_list) < 5:
        base_som_val = market_model.som.base * 1_000_000_000 if market_model else 0
        sensitivity_list.append(SensitivityImpact(
            assumption_name="Additional assumption",
            base_som=base_som_val,
            impact_minus_30pct=base_som_val * 0.7,
            impact_plus_30pct=base_som_val * 1.3,
            impact_magnitude=base_som_val * 0.6
        ))
    sensitivity_list = sensitivity_list[:5]
    
    # Get evidence ledger if debug mode is enabled
    evidence_ledger = None
    if request.debug:
        try:
            all_claims = get_all_claims()
            # Convert to list of dicts for JSON serialization
            evidence_ledger = []
            for claim in all_claims:
                # Ensure retrieved_at is a datetime object or can be formatted
                retrieved_at = claim.get('retrieved_at')
                if retrieved_at:
                    if isinstance(retrieved_at, str):
                        # Pydantic will handle string to datetime if it's ISO format
                        # or we can pass it as is
                        formatted_date = retrieved_at
                    elif hasattr(retrieved_at, 'isoformat'):
                        formatted_date = retrieved_at.isoformat()
                    else:
                        formatted_date = str(retrieved_at)
                else:
                    formatted_date = None

                evidence_ledger.append({
                    'id': claim['id'],
                    'claim_text': claim['claim_text'],
                    'claim_type': claim['claim_type'],
                    'value': claim['value'],
                    'unit': claim['unit'],
                    'source_url': claim['source_url'],
                    'excerpt': claim['excerpt'],
                    'retrieved_at': formatted_date,
                    'credibility_score': claim['credibility_score'],
                    'claim_confidence': claim['claim_confidence']
                })
        except Exception as e:
            # If ledger retrieval fails, log but don't fail the response
            print(f"Warning: Could not retrieve evidence ledger: {e}")
            evidence_ledger = []
    
    return AnalyzeResponse(
        verdict=verdict,
        confidence_score=confidence_score,
        executive_summary=executive_summary,
        market=market_section,
        competitors=competitor_list,
        risks=risks_section,
        assumptions=assumptions,
        disconfirming_evidence=disconfirming_evidence,
        sources=sources_list,
        key_unknowns=key_unknowns,
        next_7_days_tests=next_7_days_tests,
        scenarios=scenario_dict,
        sensitivity_analysis=sensitivity_list,
        evidence_ledger=evidence_ledger
    )

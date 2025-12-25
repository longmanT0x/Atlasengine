"""
API Request/Response Schemas

Pydantic models for API request and response validation.

Design Decisions:
- All request/response models use Pydantic for validation
- Response models enforce uncertainty ranges (min/base/max)
- All fields include proper type hints and documentation
- Optional fields are explicitly marked
- Numeric claims must include source attribution
"""

from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field


# Request Schema
class AnalyzeRequest(BaseModel):
    """Request schema for market viability analysis."""
    idea: str = Field(..., description="Description of the startup idea")
    industry: str = Field(..., description="Industry classification")
    geography: str = Field(..., description="Target geographic market")
    customer_type: str = Field(..., description="Type of target customers")
    business_model: str = Field(..., description="Business model description")
    price_assumption: Optional[float] = Field(
        None, 
        description="Optional price assumption for the product/service"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes or context"
    )
    debug: Optional[bool] = Field(
        False,
        description="Enable debug mode to return full evidence ledger in response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "idea": "AI-powered customer support platform",
                "industry": "SaaS",
                "geography": "North America",
                "customer_type": "Mid-market B2B companies",
                "business_model": "Subscription-based SaaS",
                "price_assumption": 99.99,
                "notes": "Focus on reducing support ticket volume by 40%"
            }
        }


# Response Schemas
class NumericClaim(BaseModel):
    """Numeric claim with source attribution."""
    value: float = Field(..., description="Numeric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    source_url: str = Field(..., description="Source URL for this claim")
    excerpt: str = Field(..., description="Excerpt from source supporting this claim")


class MarketSize(BaseModel):
    """Market size estimation with uncertainty range."""
    min: float = Field(..., description="Minimum market size estimate")
    base: float = Field(..., description="Base case market size estimate")
    max: float = Field(..., description="Maximum market size estimate")
    method: Optional[str] = Field(
        None,
        description="Method used for estimation (e.g., 'top-down', 'bottom-up')"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made in the estimation"
    )
    source_claims: List[NumericClaim] = Field(
        default_factory=list,
        description="Source-attributed numeric claims supporting this estimate"
    )


class SAM(BaseModel):
    """Serviceable Available Market with uncertainty range."""
    min: float = Field(..., description="Minimum SAM estimate")
    base: float = Field(..., description="Base case SAM estimate")
    max: float = Field(..., description="Maximum SAM estimate")
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made in the SAM calculation"
    )


class SOM(BaseModel):
    """Serviceable Obtainable Market with uncertainty range."""
    min: float = Field(..., description="Minimum SOM estimate")
    base: float = Field(..., description="Base case SOM estimate")
    max: float = Field(..., description="Maximum SOM estimate")
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made in the SOM calculation"
    )


class MarketSection(BaseModel):
    """Market analysis section with TAM, SAM, and SOM."""
    tam: MarketSize
    sam: SAM
    som: SOM


class Competitor(BaseModel):
    """Competitor information with source traceability."""
    name: str = Field(..., description="Competitor name")
    positioning: str = Field(..., description="Market positioning")
    pricing: str = Field(..., description="Pricing information")
    geography: str = Field(..., description="Geographic presence")
    differentiator: str = Field(..., description="Key differentiator")
    source_url: str = Field(..., description="Source URL for this information")


class Risks(BaseModel):
    """Risk categories with specific risks listed."""
    market: List[str] = Field(
        default_factory=list,
        description="Market-related risks"
    )
    competition: List[str] = Field(
        default_factory=list,
        description="Competition-related risks"
    )
    regulatory: List[str] = Field(
        default_factory=list,
        description="Regulatory risks"
    )
    distribution: List[str] = Field(
        default_factory=list,
        description="Distribution/channel risks"
    )


class Source(BaseModel):
    """Source reference with title, URL, and excerpt."""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    excerpt: str = Field(..., description="Relevant excerpt from source")


class Test(BaseModel):
    """Test definition for Next 7 Days Tests."""
    test: str = Field(..., description="Test description")
    method: str = Field(..., description="Method to conduct the test")
    success_threshold: str = Field(..., description="Success threshold for the test")


class ScenarioMarketSection(BaseModel):
    """Market section for a scenario."""
    tam: MarketSize
    sam: SAM
    som: SOM


class Scenario(BaseModel):
    """Represents a Bear/Base/Bull scenario."""
    name: Literal["Bear", "Base", "Bull"] = Field(..., description="Scenario name")
    market: ScenarioMarketSection = Field(..., description="Market estimates for this scenario")
    assumptions_used: Dict[str, float] = Field(..., description="Assumption values used in this scenario")


class SensitivityImpact(BaseModel):
    """Represents sensitivity impact of an assumption on SOM."""
    assumption_name: str = Field(..., description="Name of the assumption")
    base_som: float = Field(..., description="Base case SOM in billions")
    impact_minus_30pct: float = Field(..., description="SOM if assumption is -30%")
    impact_plus_30pct: float = Field(..., description="SOM if assumption is +30%")
    impact_magnitude: float = Field(..., description="Absolute difference between +30% and -30% impacts")


class AnalyzeResponse(BaseModel):
    """Response schema for market viability analysis."""
    verdict: Literal["GO", "NO-GO", "CONDITIONAL"] = Field(
        ...,
        description="Final verdict on market viability"
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score from 0-100"
    )
    executive_summary: List[str] = Field(
        ...,
        min_items=8,
        max_items=12,
        description="8-12 concise bullet points with concrete details (numbers, named competitors, channels, constraints)"
    )
    market: MarketSection = Field(..., description="Market size analysis")
    competitors: List[Competitor] = Field(
        default_factory=list,
        description="List of identified competitors"
    )
    risks: Risks = Field(..., description="Risk analysis by category")
    assumptions: List[str] = Field(
        ...,
        description="All assumptions made in the analysis"
    )
    disconfirming_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence that contradicts the idea or reduces viability"
    )
    sources: List[Source] = Field(
        ...,
        description="All sources used in the analysis"
    )
    key_unknowns: List[str] = Field(
        ...,
        min_items=5,
        max_items=5,
        description="5 key unknowns - what we still don't know"
    )
    next_7_days_tests: List[Test] = Field(
        ...,
        min_items=6,
        max_items=6,
        description="6 tests to run in the next 7 days with method and success threshold"
    )
    scenarios: Dict[str, Scenario] = Field(
        ...,
        description="Bear/Base/Bull scenarios with varying assumptions"
    )
    sensitivity_analysis: List[SensitivityImpact] = Field(
        ...,
        min_items=5,
        max_items=5,
        description="Top 5 assumptions ranked by impact on SOM, showing -30% and +30% impacts"
    )
    evidence_ledger: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Full evidence ledger (only included when debug=true)"
    )

AnalyzeResponse.model_rebuild()
model_rebuild_success = True
try:
    AnalyzeResponse.model_rebuild()
except Exception:
    # Fallback if first rebuild fails
    AnalyzeResponse.model_rebuild(_types_namespace={'Any': Any})

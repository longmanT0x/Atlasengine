"""
Decision Module Schemas
"""

from typing import List, Dict, Any, Literal
from pydantic import BaseModel


class CompetitorInfo(BaseModel):
    """Represents analyzed competitor information."""
    name: str
    positioning: str
    pricing: str
    geography: str
    differentiator: str
    source_url: str


class RiskAnalysis(BaseModel):
    """Represents risk analysis grouped by category."""
    market: List[str]
    competition: List[str]
    regulatory: List[str]
    distribution: List[str]


class DecisionResult(BaseModel):
    """Represents a complete decision result."""
    verdict: Literal["GO", "NO-GO", "CONDITIONAL"]
    confidence_score: int  # 0-100
    overall_score: float  # 0-100
    factor_scores: Dict[str, float]  # Individual factor scores
    conditions_to_go: List[str]  # What must be proven for CONDITIONAL → GO
    disconfirming_evidence: List[str]  # What would make this analysis wrong
    reasoning: Dict[str, List[str]]  # Reasoning for each factor

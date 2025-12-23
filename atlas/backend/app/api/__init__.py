"""
API Routes Module

Handles all HTTP endpoints for the ATLAS decision intelligence engine.

Design Decision:
- Centralized routing in this module
- All endpoints follow RESTful conventions
- Input validation via Pydantic models
- All responses include uncertainty ranges and source traceability
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.api.schemas import AnalyzeRequest, AnalyzeResponse
from app.api.pipeline import run_analysis_pipeline
from app.api.pdf_export import generate_pdf_memo

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_market_viability(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze market viability for a startup idea.
    
    This endpoint orchestrates a multi-step pipeline:
    1. Research: Gathers market data from traceable sources
    2. Extraction: Extracts structured information from research
    3. Modeling: Creates probabilistic market models with uncertainty ranges
    4. Decision: Makes evidence-based viability decision
    5. Compilation: Assembles final decision memo
    
    Args:
        request: AnalyzeRequest containing startup idea details
        
    Returns:
        AnalyzeResponse with complete decision memo including:
        - Verdict (GO/NO-GO/CONDITIONAL)
        - Confidence score (0-100)
        - Executive summary
        - Market analysis (TAM/SAM/SOM with ranges)
        - Competitor analysis
        - Risk assessment
        - All assumptions and sources
        
    Raises:
        HTTPException: If analysis pipeline fails
    """
    try:
        result = await run_analysis_pipeline(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(e)}"
        )


@router.get("/evaluate")
async def evaluate_market_viability():
    """
    Evaluate market viability for a startup.
    
    Returns:
        Market viability assessment with uncertainty ranges and evidence sources.
    """
    # TODO: Implement market viability evaluation
    return {"message": "Market viability evaluation endpoint - to be implemented"}


@router.get("/research")
async def get_research():
    """
    Retrieve research data for a given market/startup.
    
    Returns:
        Research data with source traceability.
    """
    # TODO: Implement research retrieval
    return {"message": "Research endpoint - to be implemented"}


@router.post("/export/pdf")
@router.get("/export/pdf")
async def export_pdf_memo(request: AnalyzeRequest = None) -> Response:
    """
    Export analysis results as a professional PDF memo.
    
    This endpoint:
    1. Runs the same analysis pipeline as /analyze (if POST)
    2. Generates a professional PDF document
    3. Returns the PDF as a downloadable file
    
    If called via GET, it returns a 200 OK to indicate the endpoint is available.
    """
    if request is None:
        return Response(content="PDF export endpoint is available", status_code=200)
    try:
        # Run the same analysis pipeline
        analysis_result = await run_analysis_pipeline(request)
        
        # Generate PDF
        pdf_buffer = generate_pdf_memo(analysis_result, request.dict())
        
        # Return PDF as downloadable response
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=atlas_memo.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )


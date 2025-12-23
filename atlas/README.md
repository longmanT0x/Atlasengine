# ATLAS - Decision Intelligence for Market Viability

ATLAS is a decision intelligence engine that evaluates startup market viability under uncertainty. It provides evidence-based analysis with full source traceability, uncertainty quantification, and comprehensive risk assessment.

## Core Principles

1. **Never invent market numbers** - All data must come from traceable sources
2. **Always expose assumptions** - Every assumption is explicitly documented
3. **Always output ranges, not single values** - Uncertainty is quantified and communicated
4. **Every factual claim must be traceable to a source** - Full evidence chain maintained

## Architecture

```
atlas/
  backend/              # FastAPI backend application
    main.py             # FastAPI application entry point
    app/
      api/              # HTTP endpoints and routing
      research/         # Market research data collection
      extraction/       # Structured data extraction from research
      modeling/         # Probabilistic market modeling
      decision/         # Viability decision making
      evidence/         # Evidence storage and traceability
      storage/          # SQLite database management
      llm/              # LLM integration (optional)
  frontend/             # Next.js frontend application
    app/
      page.tsx         # Input form
      report/           # Results viewer
```

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and settings management
- **SQLite** - Lightweight database for evidence storage
- **Python 3.11+** - Latest Python features
- **DuckDuckGo Search** - Web search for market research
- **BeautifulSoup4** - HTML parsing and text extraction

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React 18** - UI library

## Quick Start

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd atlas/backend
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment (optional):**
Create a `.env` file in `atlas/backend/`:
```env
CORS_ORIGINS=http://localhost:3000
MAX_SOURCES=8
DEBUG=False
```

5. **Run the application:**
```bash
uvicorn main:app --reload
```

6. **Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd atlas/frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure environment:**
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

4. **Run development server:**
```bash
npm run dev
```

5. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Database

The SQLite database is automatically initialized on first startup. It stores:
- Evidence with full source traceability
- Research sources and extracted text
- Extracted facts (market size, growth rates, pricing, etc.)
- Evidence ledger with all claims
- Market models and decisions

Database file: `atlas/backend/app/storage/atlas.db`

## API Endpoints

### Main Endpoints

- `POST /api/v1/analyze` - Analyze market viability for a startup idea
- `POST /api/v1/export/pdf` - Export analysis as PDF memo
- `GET /health` - Health check endpoint
- `GET /` - API information

### Request Example

```json
{
  "idea": "AI-powered personal finance management app",
  "industry": "FinTech",
  "geography": "North America",
  "customer_type": "Consumer",
  "business_model": "SaaS",
  "price_assumption": 9.99,
  "notes": "Focus on GDPR compliance"
}
```

### Response Includes

- Verdict (GO/NO-GO/CONDITIONAL)
- Confidence score (0-100)
- Executive summary
- Market analysis (TAM/SAM/SOM with ranges)
- Competitor analysis
- Risk assessment
- Scenarios (Bear/Base/Bull)
- Sensitivity analysis
- All assumptions and sources
- Evidence ledger (in debug mode)

## Features

### Evidence-Based Analysis
- All market numbers traceable to sources
- Evidence ledger tracks every claim
- Confidence scoring based on source quality

### Uncertainty Quantification
- All estimates include min/base/max ranges
- Scenario analysis (Bear/Base/Bull)
- Sensitivity analysis for key assumptions

### Comprehensive Risk Assessment
- Market risks
- Competition risks
- Regulatory risks
- Distribution risks

### Professional Output
- Executive summary with concrete details
- PDF export capability
- JSON export for programmatic access
- Debug mode with full evidence ledger

## Development

### Running Tests

```bash
cd atlas/backend
pytest
```

### Project Structure

- **Backend**: Modular architecture with clear separation of concerns
- **Frontend**: Next.js App Router with TypeScript
- **Database**: SQLite with full schema for evidence traceability

### Key Modules

- **Research**: Collects market data from web sources
- **Extraction**: Extracts structured facts using pattern matching
- **Modeling**: Creates probabilistic market models
- **Decision**: Makes evidence-based viability decisions
- **Evidence**: Manages evidence storage and traceability

## Configuration

### Backend Environment Variables

- `CORS_ORIGINS` - Comma-separated list of allowed origins (default: "*")
- `MAX_SOURCES` - Maximum sources to collect (default: 8)
- `DEBUG` - Enable debug mode (default: False)
- `OPENAI_API_KEY` - Optional: For LLM-based extraction
- `ANTHROPIC_API_KEY` - Optional: For LLM-based extraction

### Frontend Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000/api/v1)

## Production Deployment

### Backend

1. Set `CORS_ORIGINS` to your frontend domain
2. Set `DEBUG=False`
3. Use a production ASGI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

1. Build for production:
```bash
npm run build
```

2. Start production server:
```bash
npm start
```

## License

[To be determined]


# ATLAS Test Suite

This directory contains the evaluation harness for the ATLAS Decision Intelligence Engine.

## Test Structure

### Fixtures (`tests/fixtures/`)
- `sample_ideas.py`: Contains 3 sample startup ideas with expected characteristics:
  - **FinTech EU**: AI-powered personal finance management app (European Union)
  - **Travel Belgium**: Local travel marketplace (Belgium)
  - **B2B SaaS Benelux**: Supply chain management SaaS (Benelux region)

### Test Files
- `test_schema_validity.py`: Validates response schema structure
- `test_sources.py`: Tests source collection and quality
- `test_competitors.py`: Tests competitor identification
- `test_evidence_traceability.py`: Validates evidence traceability
- `test_confidence_scoring.py`: Tests confidence scoring behavior

## Running Tests

### Prerequisites
```bash
# Install dependencies
make install
# or
pip install -r requirements.txt
```

### Run All Tests
```bash
make test
# or
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Fast tests only (exclude slow tests)
make test-fast

# Slow tests only
make test-slow

# With coverage report
make test-coverage
```

### Run Individual Test Files
```bash
pytest tests/test_schema_validity.py -v
pytest tests/test_sources.py -v
pytest tests/test_competitors.py -v
pytest tests/test_evidence_traceability.py -v
pytest tests/test_confidence_scoring.py -v
```

## Test Assertions

The test suite validates:

1. **Response Schema Validity**
   - All required fields are present
   - Field types are correct
   - Field constraints are met (e.g., confidence_score 0-100)

2. **Source Collection**
   - At least N sources returned (varies by idea)
   - All sources have valid URLs
   - Sources have required fields (title, url, excerpt)

3. **Competitor Identification**
   - Competitors list structure is valid
   - All competitors have source URLs
   - Competitors are returned when evidence exists

4. **Evidence Traceability**
   - All numeric claims have source attribution
   - Evidence ledger is populated (when debug=true)
   - Assumptions list references sources

5. **Confidence Scoring**
   - Confidence scores are in valid range (0-100)
   - Confidence scores decrease when evidence is sparse
   - Confidence score is always present

## Test Configuration

- `pytest.ini`: Pytest configuration
- `conftest.py`: Shared fixtures and test configuration
- `Makefile`: Convenience commands for running tests

## Notes

- Tests use async/await patterns for FastAPI endpoints
- Some tests may have variable results due to real web searches
- Tests validate structure and constraints, not exact numeric values
- Debug mode can be enabled to get full evidence ledger in responses


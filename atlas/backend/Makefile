.PHONY: test test-fast test-slow test-coverage install clean help

# Default target
help:
	@echo "ATLAS Test Suite"
	@echo ""
	@echo "Available commands:"
	@echo "  make test          - Run all tests"
	@echo "  make test-fast     - Run fast tests only (exclude slow tests)"
	@echo "  make test-slow     - Run slow tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make install       - Install test dependencies"
	@echo "  make clean         - Clean test artifacts"

# Install test dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
test:
	pytest tests/ -v

# Run fast tests only (exclude slow tests)
test-fast:
	pytest tests/ -v -m "not slow"

# Run slow tests only
test-slow:
	pytest tests/ -v -m "slow"

# Run tests with coverage
test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term -v

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete



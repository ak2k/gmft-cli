# GMFT CLI Development Makefile
#
# This Makefile provides convenient commands for development, testing, 
# and maintenance of the gmft-cli project.

.PHONY: help install install-dev install-all clean clean-cache clean-data clean-all
.PHONY: format lint check test test-unit test-integration test-gmft test-all test-coverage test-comprehensive
.PHONY: data download-data check-data build package publish docs
.PHONY: cli-test demo run status ci-test ci-coverage ci-setup

# Default target
help: ## Show this help message
	@echo "GMFT CLI Development Commands"
	@echo "============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install basic dependencies
	uv sync

install-dev: ## Install with development dependencies
	uv sync --extra dev --extra test

install-all: ## Install with all optional dependencies (PDF backends, dev, test)
	uv sync --extra dev --extra test --extra pdf-all

install-pdf-pymupdf: ## Install with PyMuPDF PDF backend
	uv sync --extra dev --extra test --extra pdf-pymupdf

install-pdf-pypdfium2: ## Install with pypdfium2 PDF backend
	uv sync --extra dev --extra test --extra pdf-pypdfium2

# Code quality targets
format: ## Format code with black and ruff
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

lint: ## Run linting checks
	uv run ruff check src/ tests/

check: ## Run all code quality checks (lint + format check)
	uv run ruff check src/ tests/
	uv run black --check src/ tests/

# Testing targets
test: test-comprehensive ## Run comprehensive tests with coverage (default)

test-comprehensive: ## Run all tests with coverage report
	@echo "🧪 Running comprehensive test suite with coverage..."
	@echo "=================================================="
	uv run python -m pytest tests/ -v --cov=gmft_cli --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo ""
	@echo "✅ Comprehensive testing complete!"
	@echo "📊 Coverage report: htmlcov/index.html"
	@echo "📊 XML coverage: coverage.xml"

test-unit: ## Run unit tests only (fast, no external dependencies)
	@echo "🔧 Running unit tests..."
	uv run python -m pytest tests/ -v -m "not integration and not gmft_data"

test-integration: ## Run integration tests (requires GMFT)
	@echo "🔗 Running integration tests..."
	uv run python -m pytest tests/ -v -m "integration and not gmft_data"

test-gmft: ## Run tests using GMFT's test data (requires download-data)
	@echo "📊 Running GMFT data tests..."
	uv run python -m pytest tests/ -v -m "gmft_data"

test-validation: ## Run validation tests against GMFT behavior
	@echo "✅ Running validation tests..."
	uv run python -m pytest tests/ -v -m "validation"

test-all: ## Run all tests including integration and GMFT data tests (no coverage)
	@echo "🚀 Running all tests..."
	uv run python -m pytest tests/ -v

test-coverage: ## Alias for test-comprehensive
	@echo "📊 Running tests with coverage (same as 'make test')..."
	@make test-comprehensive

test-fast: ## Run fast tests only (exclude slow and integration tests)
	uv run python -m pytest tests/ -v -m "not slow and not integration and not gmft_data"

test-specific: ## Run specific test file (usage: make test-specific FILE=test_extract.py)
	uv run python -m pytest tests/$(FILE) -v

# GMFT test data management
download-data: ## Download GMFT test data for integration tests
	uv run python tests/download_gmft_data.py

check-data: ## Check if GMFT test data is available
	uv run python tests/download_gmft_data.py --check

data: download-data ## Alias for download-data

# Cleaning targets
clean-cache: ## Clean Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

clean-coverage: ## Clean coverage reports
	rm -rf htmlcov/
	rm -f .coverage coverage.xml

clean-build: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/

clean-data: ## Clean downloaded GMFT test data
	rm -rf ../gmft-source/
	rm -rf ~/Downloads/gmft-source/

clean-all: clean-cache clean-coverage clean-build ## Clean everything

# CLI testing targets
cli-test: ## Quick CLI functionality test
	@echo "Testing CLI functionality..."
	@echo "1. List components:"
	@uv run gmft-cli list-components --help
	@echo "\n2. Show available detectors and formatters:"
	@uv run gmft-cli list-components | head -20
	@echo "\n3. Test extract help:"
	@uv run gmft-cli extract --help

demo: ## Run a quick demo of CLI functionality
	@echo "GMFT CLI Demo"
	@echo "============="
	@echo "\n1. Available components:"
	@uv run gmft-cli list-components
	@echo "\n2. CLI help:"
	@uv run gmft-cli --help

# status: ## Show GMFT CLI status and available backends
#	uv run gmft-cli status

# Development convenience targets
run: ## Run gmft-cli with arguments (usage: make run ARGS="list-components")
	uv run gmft-cli $(ARGS)

shell: ## Start Python shell with project in path
	uv run python

# Package management
build: check ## Build the package
	uv build

package: build ## Create distribution packages
	@echo "Package built successfully"
	@ls -la dist/

publish-test: package ## Publish to test PyPI
	uv publish --repository testpypi

publish: package ## Publish to PyPI (use with caution!)
	uv publish

# Documentation
docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"
	@echo "Available commands can be seen with: make help"

# Development workflow targets
dev-setup: install-dev download-data ## Complete development setup
	@echo "Development setup complete!"
	@echo "Run 'make test' to verify everything works"

ci-setup: install-all ## Setup for CI/continuous integration
	@echo "🔧 CI setup complete!"
	@echo "Available CI targets: make ci-test, make ci-coverage"

quick-check: format lint test-unit ## Quick development check (format, lint, unit tests)
	@echo "Quick check passed! ✓"

full-check: format lint test ## Full development check with comprehensive testing
	@echo "Full check passed! ✓"

# Release preparation
pre-release: clean-all dev-setup full-check ## Prepare for release
	@echo "Pre-release checks complete!"
	@echo "Ready for release."

# CI/CD targets
ci-test: ## Run tests optimized for CI environments
	@echo "🚀 Running CI test suite..."
	@echo "=========================="
	@echo "1. Code quality checks:"
	@make check
	@echo "\n2. Unit tests:"
	@make test-unit
	@echo "\n✅ CI tests complete!"

ci-coverage: ## Run comprehensive tests with coverage for CI
	@echo "📊 Running CI coverage test suite..."
	@echo "===================================="
	@make test-comprehensive
	@echo "✅ CI coverage tests complete!"

# Help for common workflows
workflow-help: ## Show common development workflows
	@echo "Common Development Workflows"
	@echo "============================"
	@echo ""
	@echo "🚀 Initial setup:"
	@echo "  make dev-setup"
	@echo ""
	@echo "🔧 Daily development:"
	@echo "  make quick-check        # Format, lint, unit tests"
	@echo "  make test-unit          # Unit tests only (fast)"
	@echo "  make format             # Format code"
	@echo ""
	@echo "🧪 Testing workflows:"
	@echo "  make test               # Comprehensive tests with coverage (default)"
	@echo "  make test-unit          # Unit tests only (fast)"
	@echo "  make test-integration   # Integration tests"
	@echo "  make test-gmft         # Tests with GMFT data"
	@echo "  make test-all          # All tests (no coverage)"
	@echo ""
	@echo "📊 GMFT data testing:"
	@echo "  make download-data     # Download GMFT test data"
	@echo "  make test-gmft        # Run tests with GMFT data"
	@echo ""
	@echo "🚀 CI/CD workflows:"
	@echo "  make ci-test         # CI test suite (quality + unit tests)"
	@echo "  make ci-coverage     # CI comprehensive tests with coverage"
	@echo "  make ci-setup        # Setup CI environment"
	@echo ""
	@echo "🏗️ Release preparation:"
	@echo "  make pre-release      # Full check before release"
	@echo "  make build           # Build package"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean-all       # Clean everything"

# Project info
info: ## Show project information
	@echo "GMFT CLI Project Information"
	@echo "============================"
	@echo "Project: gmft-cli"
	@echo "Description: Command-line interface for GMFT table detection and extraction"
	@echo ""
	@echo "Dependencies:"
	@uv tree --depth 1
	@echo ""
	@echo "Available extras:"
	@echo "  dev          - Development tools (pytest, ruff, black)"
	@echo "  test         - Testing dependencies (pytest, PyMuPDF for tests)"
	@echo "  pdf-all      - All PDF backends (PyMuPDF + pypdfium2)"
	@echo "  pdf-pymupdf  - PyMuPDF backend only"
	@echo "  pdf-pypdfium2 - pypdfium2 backend only"

# Debug targets
debug-env: ## Show environment information for debugging
	@echo "Environment Debug Information"
	@echo "============================="
	@echo "Python version:"
	@uv run python --version
	@echo ""
	@echo "UV version:"
	@uv --version
	@echo ""
	@echo "Project root:"
	@pwd
	@echo ""
	@echo "Virtual environment:"
	@echo "$(shell uv run python -c 'import sys; print(sys.prefix)')"
	@echo ""
	@echo "Installed packages:"
	@uv pip list

debug-gmft: ## Debug GMFT installation and components
	@echo "GMFT Debug Information"
	@echo "======================"
	@echo "Testing GMFT import:"
	@uv run python -c "import gmft; print(f'GMFT version: {gmft.__version__ if hasattr(gmft, \"__version__\") else \"unknown\"}')" || echo "GMFT import failed"
	@echo ""
	@echo "Available GMFT components:"
	@uv run gmft-cli list-components || echo "CLI not working"
	@echo ""
	@echo "PDF backends:"
	@uv run gmft-cli pdf-backends || echo "PDF backends command failed"

# Advanced testing
test-matrix: ## Run tests with different configurations
	@echo "🔬 Running test matrix..."
	@echo "========================="
	@echo "1. Unit tests:"
	@make test-unit
	@echo "\n2. Integration tests:"
	@make test-integration
	@echo "\n3. GMFT data tests:"
	@make test-gmft
	@echo "\n4. Comprehensive tests with coverage:"
	@make test-comprehensive
	@echo "\n✅ Test matrix complete!"

benchmark: ## Run performance benchmarks (if any)
	@echo "Benchmark tests not yet implemented"
	@echo "Consider adding performance tests for large PDF processing"

# Configuration
config: ## Show current configuration
	@echo "Current Configuration"
	@echo "===================="
	@echo "pyproject.toml extras:"
	@grep -A 20 "\[project.optional-dependencies\]" pyproject.toml
	@echo ""
	@echo "Test configuration:"
	@cat pytest.ini
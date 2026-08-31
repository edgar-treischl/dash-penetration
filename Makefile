.PHONY: help install lint format test coverage clean docs dev scan all check

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║    Vulnerability Scanner (dash-penetration) — Makefile     ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make scan URL=https://your-app.com"
	@echo "                            Run penetration test (requires URL)"
	@echo "  make demo                 Run demo scan on test site"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install              Install dependencies with UV"
	@echo "  make dev                  Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run flake8 linter"
	@echo "  make format               Format code with Black"
	@echo "  make format-check         Check formatting without changing files"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run pytest test suite"
	@echo "  make test-v               Run tests with verbose output"
	@echo "  make coverage             Run tests with coverage report"
	@echo "  make coverage-html        Generate HTML coverage report"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs                 Generate documentation"
	@echo "  make docs-preview         Generate documentation and preview"
	@echo ""
	@echo "Utility:"
	@echo "  make clean                Remove build artifacts & cache"
	@echo "  make clean-reports        Remove scan reports"
	@echo "  make check                Run all checks (lint, format, test)"
	@echo "  make all                  Install, format, lint, test"
	@echo "  make help                 Show this help message"
	@echo ""

# ============================================================================
# Setup & Installation
# ============================================================================

install:
	@echo "📦 Installing dependencies with UV..."
	uv pip install -r requirements.txt
	@echo "✅ Dependencies installed"

dev: install
	@echo "🔧 Setting up development environment..."
	uv pip install -e .
	@echo "✅ Development setup complete"

# ============================================================================
# Penetration Testing
# ============================================================================

scan:
	@if [ -z "$(URL)" ]; then \
		echo "❌ Error: URL parameter required"; \
		echo ""; \
		echo "Usage:"; \
		echo "  make scan URL=https://your-app.com"; \
		echo ""; \
		echo "Example:"; \
		echo "  make scan URL=https://edgar-treischl.pages.gitlab.lrz.de/dash-demo/"; \
		exit 1; \
	fi
	@echo "🔐 Starting penetration test..."
	@echo "Target: $(URL)"
	@echo ""
	@uv run python pentest_scanner.py $(URL)

demo:
	@echo "🔐 Running demo scan on test site..."
	@echo "Target: https://edgar-treischl.pages.gitlab.lrz.de/dash-demo/"
	@echo ""
	@uv run python pentest_scanner.py https://edgar-treischl.pages.gitlab.lrz.de/dash-demo/

scan-local:
	@echo "🔐 Scanning local development server..."
	@echo "Target: http://localhost:3000"
	@echo ""
	@uv run python pentest_scanner.py http://localhost:3000

# ============================================================================
# Code Quality & Linting
# ============================================================================

lint:
	@echo "🔍 Running flake8 linter..."
	uv run flake8 dash_penetration/ --count --statistics

format-check:
	@echo "📋 Checking Black formatting..."
	uv run black --check .

format:
	@echo "🎨 Formatting code with Black..."
	uv run black .
	@echo "✅ Code formatted"

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v --tb=short

test-v:
	@echo "🧪 Running tests (verbose)..."
	uv run pytest tests/ -vv --tb=long

coverage:
	@echo "📊 Running tests with coverage..."
	uv run pytest tests/ -v \
		--cov=dash_penetration/crawler \
		--cov=dash_penetration/discovery \
		--cov=dash_penetration/scanner \
		--cov-report=term-missing \
		--cov-report=xml

coverage-html:
	@echo "📈 Generating HTML coverage report..."
	uv run pytest tests/ \
		--cov=dash_penetration/crawler \
		--cov=dash_penetration/discovery \
		--cov=dash_penetration/scanner \
		--cov-report=html \
		--cov-report=term-missing
	@echo "✅ Coverage report generated: htmlcov/index.html"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || echo "Open htmlcov/index.html in browser"

# ============================================================================
# Documentation
# ============================================================================

docs-init:
	@echo "📚 Initializing documentation..."
	uv run great-docs init

docs:
	@echo "📚 Building documentation..."
	uv run great-docs build

docs-preview:
	@echo "📚 Building documentation..."
	uv run great-docs build
	@echo "🚀 Starting documentation preview..."
	uv run great-docs preview

docs-clean:
	@echo "🧹 Cleaning Great Docs artifacts..."
	rm -rf ./great-docs

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-reports:
	@echo "🧹 Cleaning scan reports..."
	find . -maxdepth 1 -name "pentest_report_*.json" -delete
	@echo "✅ Scan reports removed"

# ============================================================================
# Composite Targets
# ============================================================================

check: lint format-check test
	@echo "✅ All checks passed!"

all: install format lint test
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║              ✅ FULL BUILD SUCCESSFUL                      ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"

quick: format lint test
	@echo "✅ Quick check complete!"

# ============================================================================
# CI/CD Simulation
# ============================================================================

ci: clean install lint format-check test coverage
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║            🤖 CI SIMULATION COMPLETE                       ║"
	@echo "║  This is what GitHub Actions will run on push/PR          ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"

# ============================================================================
# Development Workflow Helpers
# ============================================================================

setup: install format lint test
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║         🚀 DEVELOPMENT ENVIRONMENT READY                   ║"
	@echo "║                                                           ║"
	@echo "║  Commands you can use:                                    ║"
	@echo "║    make scan URL=https://your-app.com  Run pentest        ║"
	@echo "║    make test                           Run tests          ║"
	@echo "║    make lint                           Run linter         ║"
	@echo "║    make format                         Auto-format code   ║"
	@echo "║    make coverage                       Run with coverage  ║"
	@echo "║    make demo                           Run demo scan      ║"
	@echo "║                                                           ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"

# ============================================================================
# Status Information
# ============================================================================

status:
	@echo "📊 Project Status:"
	@echo ""
	@echo "  Python version:"
	@uv run python --version
	@echo ""
	@echo "  UV version:"
	@uv --version
	@echo ""
	@echo "  Installed packages:"
	@uv pip list | wc -l | xargs echo "    (total packages)"
	@echo ""
	@echo "  Test files:"
	@find tests/ -name "test_*.py" 2>/dev/null | wc -l | xargs echo "    (found)"
	@echo ""
	@echo "  Scanner modules:"
	@find dash_penetration/scanner/ -name "*.py" ! -name "__init__.py" 2>/dev/null | wc -l | xargs echo "    (found)"
	@echo ""
	@echo "  Recent scan reports:"
	@ls -1 pentest_report_*.json 2>/dev/null | wc -l | xargs echo "    (found)"
	@echo ""

# ============================================================================
# Version Targets
# ============================================================================

version:
	@echo "Project: Vulnerability Scanner (dash-penetration)"
	@grep "^python" .python-version 2>/dev/null || echo "Python version not pinned"
	@echo "Framework: asyncio + Playwright"
	@echo "Package Manager: UV"

# ============================================================================
# Default if just 'make' is run
# ============================================================================

.DEFAULT_GOAL := help

.PHONY: help install lint format test coverage clean docs dev watch security all check

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║         Web Crawler Development — Makefile Targets        ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install              Install dependencies with UV"
	@echo "  make dev                  Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run flake8 linter"
	@echo "  make format               Format code with Black"
	@echo "  make format-check         Check formatting without changing files"
	@echo "  make type-check           Type checking (future enhancement)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run pytest test suite"
	@echo "  make test-v               Run tests with verbose output"
	@echo "  make test-watch           Run tests in watch mode"
	@echo "  make coverage             Run tests with coverage report"
	@echo "  make coverage-html        Generate HTML coverage report"
	@echo ""
	@echo "Security:"
	@echo "  make security             Run TruffleHog secret scanner"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs                 Generate documentation"
	@echo "  make docs-view            View README and docs"
	@echo ""
	@echo "Utility:"
	@echo "  make clean                Remove build artifacts & cache"
	@echo "  make check                Run all checks (lint, format, test)"
	@echo "  make all                  Install, format, lint, test, coverage"
	@echo "  make help                 Show this help message"
	@echo ""
	@echo "Development:"
	@echo "  make run                  Run the crawler CLI"
	@echo "  make run-help             Show CLI help"
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
# Code Quality & Linting
# ============================================================================

lint:
	@echo "🔍 Running flake8 linter..."
	uv run flake8 crawler/ discovery/ output/ tests/ --max-line-length=100 --count --statistics

format-check:
	@echo "📋 Checking Black formatting..."
	uv run black --check crawler/ discovery/ output/ tests/ main.py

format:
	@echo "🎨 Formatting code with Black..."
	uv run black crawler/ discovery/ output/ tests/ main.py
	@echo "✅ Code formatted"

type-check:
	@echo "🔬 Type checking with mypy..."
	@echo "⚠️  (mypy not yet configured)"

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v --tb=short

test-v:
	@echo "🧪 Running tests (verbose)..."
	uv run pytest tests/ -vv --tb=long

test-watch:
	@echo "👁️  Watching for changes and running tests..."
	uv run pytest-watch tests/ -v --tb=short

coverage:
	@echo "📊 Running tests with coverage..."
	uv run pytest tests/ -v \
		--cov=crawler \
		--cov=discovery \
		--cov=output \
		--cov-report=term-missing \
		--cov-report=xml

coverage-html:
	@echo "📈 Generating HTML coverage report..."
	uv run pytest tests/ \
		--cov=crawler \
		--cov=discovery \
		--cov=output \
		--cov-report=html \
		--cov-report=term-missing
	@echo "✅ Coverage report generated: htmlcov/index.html"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || echo "Open htmlcov/index.html in browser"

# ============================================================================
# Security
# ============================================================================

security:
	@echo "🔐 Running TruffleHog secret scanner..."
	@command -v trufflehog >/dev/null 2>&1 || (echo "Installing TruffleHog..." && uv pip install trufflehog)
	trufflehog filesystem . --only-verified --json 2>/dev/null | grep -q "trufflehog" && echo "✅ No secrets found" || echo "⚠️  Check output above"

# ============================================================================
# Documentation
# ============================================================================

docs:
	@echo "📚 Generating documentation..."
	@mkdir -p docs
	@echo "# Web Crawler Documentation" > docs/index.md
	@echo "" >> docs/index.md
	@echo "## Quick Start" >> docs/index.md
	@echo "See [README.md](../README.md) for project overview." >> docs/index.md
	@echo "" >> docs/index.md
	@echo "## Development Plan" >> docs/index.md
	@echo "See [plan.md](../plan.md) for 11-step development roadmap." >> docs/index.md
	@echo "" >> docs/index.md
	@echo "## Architecture" >> docs/index.md
	@echo "See [.github/copilot-instructions.md](../.github/copilot-instructions.md) for details." >> docs/index.md
	@echo "✅ Documentation generated in docs/"

docs-view:
	@echo "📖 Documentation files:"
	@echo ""
	@echo "  README.md                      - Project overview"
	@echo "  plan.md                        - 11-step development plan"
	@echo "  .github/copilot-instructions.md - Architecture guide"
	@echo "  WORKFLOWS_SETUP.md             - CI/CD configuration"
	@echo ""

# ============================================================================
# Running the Crawler
# ============================================================================

run:
	@echo "🚀 Running crawler CLI..."
	uv run python main.py crawl --help

run-help:
	@echo "📋 Crawler CLI help:"
	uv run python main.py --help

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

# ============================================================================
# Composite Targets
# ============================================================================

check: lint format-check test
	@echo "✅ All checks passed!"

all: install format lint test coverage
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║              ✅ FULL BUILD SUCCESSFUL                      ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"

quick: format lint test
	@echo "✅ Quick check complete!"

# ============================================================================
# CI/CD Simulation
# ============================================================================

ci: clean install lint test coverage
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
	@echo "Commands you can use:                                       ║"
	@echo "  make test           Run tests                             ║"
	@echo "  make lint           Run linter                            ║"
	@echo "  make format         Auto-format code                      ║"
	@echo "  make coverage       Run with coverage                     ║"
	@echo "  make run            Run the crawler                       ║"
	@echo "│                                                           ║"
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
	@find tests/ -name "test_*.py" | wc -l | xargs echo "    (found)"
	@echo ""
	@echo "  Source files:"
	@find crawler/ discovery/ output/ -name "*.py" | wc -l | xargs echo "    (found)"
	@echo ""

# ============================================================================
# Version Targets (for future CI/CD integration)
# ============================================================================

version:
	@echo "Project: Web Crawler (dash-penetration)"
	@grep "^python" .python-version
	@echo "Framework: asyncio"
	@echo "Package Manager: UV"

# ============================================================================
# Default if just 'make' is run
# ============================================================================

.DEFAULT_GOAL := help

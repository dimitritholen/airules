#!/bin/bash

# Enhanced PyPI publishing script for rules4
# Usage: ./publish.sh [--test] [--version X.Y.Z]

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PUBLISH_TO_TEST_PYPI=false
NEW_VERSION=""
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            PUBLISH_TO_TEST_PYPI=true
            shift
            ;;
        --version)
            NEW_VERSION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --test        Publish to TestPyPI instead of PyPI"
            echo "  --version X.Y.Z  Update version number before publishing"
            echo "  --dry-run     Build and check but don't upload"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown argument $1${NC}"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a virtual environment
check_venv() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        print_error "Not in a virtual environment. Please activate your venv first:"
        echo "  source .venv/bin/activate"
        exit 1
    fi
    print_success "Virtual environment detected: $VIRTUAL_ENV"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    if ! python -c "import build" 2>/dev/null; then
        missing_deps+=("build")
    fi
    
    if ! python -c "import twine" 2>/dev/null; then
        missing_deps+=("twine")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo "Install them with: pip install ${missing_deps[*]}"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Check API token
check_api_token() {
    local token_var
    if [[ "$PUBLISH_TO_TEST_PYPI" == true ]]; then
        token_var="TEST_PYPI_API_TOKEN"
    else
        token_var="PYPI_API_TOKEN"
    fi
    
    if [[ -z "${!token_var:-}" ]]; then
        print_error "Missing API token environment variable: $token_var"
        if [[ "$PUBLISH_TO_TEST_PYPI" == true ]]; then
            echo "Get your TestPyPI token from: https://test.pypi.org/manage/account/token/"
            echo "Set it with: export TEST_PYPI_API_TOKEN='your-token-here'"
        else
            echo "Get your PyPI token from: https://pypi.org/manage/account/token/"
            echo "Set it with: export PYPI_API_TOKEN='your-token-here'"
        fi
        exit 1
    fi
    print_success "API token found"
}

# Update version if requested
update_version() {
    if [[ -n "$NEW_VERSION" ]]; then
        print_status "Updating version to $NEW_VERSION..."
        
        # Update version in pyproject.toml
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
        else
            # Linux
            sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
        fi
        
        # Update version in cli.py
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" airules/cli.py
        else
            # Linux
            sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" airules/cli.py
        fi
        
        print_success "Version updated to $NEW_VERSION"
        
        # Show the changes
        echo "Changes made:"
        git diff pyproject.toml airules/cli.py || true
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    if ! make test; then
        print_error "Tests failed. Fix them before publishing."
        exit 1
    fi
    print_success "All tests passed"
}

# Run linting
run_linting() {
    print_status "Running linting checks..."
    if ! make lint; then
        print_error "Linting failed. Fix the issues before publishing."
        exit 1
    fi
    print_success "Linting passed"
}

# Clean up old builds
cleanup() {
    print_status "Cleaning up old builds..."
    rm -rf dist/ build/ *.egg-info
    print_success "Cleanup complete"
}

# Build the package
build_package() {
    print_status "Building distribution packages..."
    python -m build
    
    # List built files
    print_success "Built packages:"
    ls -la dist/
}

# Check the built package
check_package() {
    print_status "Checking package with twine..."
    python -m twine check dist/*
    print_success "Package check passed"
}

# Upload to PyPI
upload_package() {
    if [[ "$DRY_RUN" == true ]]; then
        print_warning "DRY RUN: Would upload packages but --dry-run specified"
        return
    fi
    
    local upload_args=()
    local repository_name
    
    if [[ "$PUBLISH_TO_TEST_PYPI" == true ]]; then
        repository_name="TestPyPI"
        upload_args+=(--repository testpypi)
        upload_args+=(--username __token__)
        upload_args+=(--password "$TEST_PYPI_API_TOKEN")
    else
        repository_name="PyPI"
        upload_args+=(--repository pypi)
        upload_args+=(--username __token__)
        upload_args+=(--password "$PYPI_API_TOKEN")
    fi
    
    print_status "Uploading to $repository_name..."
    python -m twine upload "${upload_args[@]}" dist/*
    
    print_success "Successfully published to $repository_name!"
    
    # Show installation instructions
    local package_name="rules4"
    if [[ "$PUBLISH_TO_TEST_PYPI" == true ]]; then
        echo ""
        echo "Test the installation with:"
        echo "  pip install --index-url https://test.pypi.org/simple/ $package_name"
    else
        echo ""
        echo "Install the published package with:"
        echo "  pip install $package_name"
    fi
}

# Main execution
main() {
    print_status "Starting publication process..."
    
    # Pre-flight checks
    check_venv
    check_dependencies
    check_api_token
    
    # Update version if requested
    update_version
    
    # Quality checks
    run_tests
    run_linting
    
    # Build and publish
    cleanup
    build_package
    check_package
    upload_package
    
    print_success "Publication complete! 🎉"
}

# Handle script interruption
trap 'print_warning "Script interrupted. Cleaning up..."; exit 130' INT

# Run main function
main "$@"

# Contributing to OCR-MCP 🤝

Thank you for your interest in contributing to OCR-MCP! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)
- [Documentation](#documentation)

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Poetry (for dependency management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sandraschi/ocr-mcp.git
   cd ocr-mcp
   ```

2. **Install dependencies:**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -

   # Install project dependencies
   poetry install

   # Install additional OCR backends (optional)
   pip install easyocr
   pip install PyMuPDF rarfile
   ```

3. **Set up development environment:**
   ```bash
   # Activate the Poetry shell
   poetry shell

   # Verify installation
   python scripts/count_tools.py
   ```

### 🖥️ Windows WIA Scanner Support

For scanner functionality on Windows:

```bash
# Install Windows-specific dependencies
pip install pywin32 comtypes
```

## 🔄 Development Workflow

### 1. Choose an Issue

- Check [open issues](https://github.com/sandraschi/ocr-mcp/issues) for tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Feature Branch

```bash
# Create and switch to a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-number-description
```

### 3. Make Changes

- Follow the [code style guidelines](#code-style)
- Write tests for new functionality
- Update documentation as needed
- Keep commits focused and descriptive

### 4. Test Your Changes

```bash
# Run basic functionality tests
python scripts/test_import.py
python scripts/count_tools.py

# Test with your MCP client (Cursor, Claude Desktop, etc.)
```

### 5. Submit a Pull Request

- Ensure all tests pass
- Update documentation if needed
- Write a clear PR description
- Reference any related issues

## 🎨 Code Style

### Python Code

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black default)
- Use descriptive variable and function names

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issue numbers when applicable
- Example: `Add support for CBZ comic book processing (#42)`

### Documentation

- Use Google-style docstrings
- Document all public functions and classes
- Update README.md for significant changes
- Add examples for new features

## 🧪 Testing

### Running Tests

```bash
# Run the test suite
pytest

# Run specific test files
pytest tests/test_ocr_backends.py

# Run with coverage
pytest --cov=ocr_mcp --cov-report=html
```

### Writing Tests

- Write unit tests for new functionality
- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases

## 📝 Submitting Changes

### Pull Request Process

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch
4. **Make** your changes
5. **Test** thoroughly
6. **Commit** with clear messages
7. **Push** to your fork
8. **Create** a Pull Request

### PR Requirements

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] PR description explains the changes
- [ ] Related issues are referenced

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Log files** if applicable
- **Screenshots** for UI issues

### Feature Requests

For new features, please include:

- **Clear description** of the proposed feature
- **Use case** and problem it solves
- **Proposed implementation** if you have ideas
- **Alternative solutions** considered

## 📚 Documentation

### Updating Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Update the changelog for significant changes

### Building Documentation

```bash
# Generate API documentation
pdoc --html --output-dir docs ocr_mcp

# View documentation
# Open docs/index.html in your browser
```

## 🙏 Recognition

Contributors will be recognized in:
- The project's README.md
- GitHub's contributor insights
- Release notes for significant contributions

## 📞 Getting Help

- Check existing [issues](https://github.com/sandraschi/ocr-mcp/issues) and documentation first
- Create a new issue for questions or problems
- Join discussions in existing issues

Thank you for contributing to OCR-MCP! 🎉







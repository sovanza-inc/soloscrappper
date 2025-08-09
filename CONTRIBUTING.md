# Contributing to Google Maps Scraper

Thank you for your interest in contributing to the Google Maps Scraper project! We welcome contributions from the community.

## Code of Conduct

This project follows a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Use welcoming and inclusive language
- Be collaborative
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, please include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples
- Describe the behavior you observed and what behavior you expected
- Include screenshots if helpful
- Provide your environment details (OS, Python version, Chrome version)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- A clear and descriptive title
- A detailed description of the suggested enhancement
- Explain why this enhancement would be useful
- Provide examples of how it would work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
7. Push to the branch (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/google-maps-scraper.git
   cd google-maps-scraper
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Run tests**:
   ```bash
   python test_scraper.py
   ```

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Code Formatting

We use automated code formatting tools:

```bash
# Install formatting tools
pip install black isort flake8

# Format code
black .
isort .

# Check for style issues
flake8 .
```

### Testing

- Write tests for new functionality
- Ensure existing tests continue to pass
- Test on multiple platforms when possible
- Include edge cases in tests

## Project Structure

```
google-maps-scraper/
├── google_maps_scraper_dark.py    # Main application
├── test_scraper.py                # Basic tests
├── test_optimized_scraper.py      # Performance tests
├── requirements.txt               # Dependencies
├── setup.py                      # Installation script
├── README.md                     # Project documentation
├── OPTIMIZATION_SUMMARY.md       # Performance details
├── sample_keywords.txt           # Example keywords
└── .github/                      # GitHub templates
    ├── workflows/
    │   └── ci.yml               # CI/CD pipeline
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── pull_request_template.md
```

## Commit Messages

Use clear and meaningful commit messages:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when applicable

Examples:
- `Fix: Handle empty search results gracefully`
- `Add: Support for additional business fields`
- `Update: Improve error handling in scraper class`

## Legal and Ethical Guidelines

When contributing to this project, please ensure:

- Your contributions comply with local laws regarding web scraping
- You respect Google's Terms of Service and robots.txt
- You implement appropriate rate limiting
- You don't include any malicious code or backdoors
- Your changes maintain the educational/personal use nature of the project

## Performance Considerations

When making changes that could affect performance:

- Test with various keyword sets
- Consider memory usage implications
- Ensure changes don't significantly increase scraping time
- Document any performance trade-offs
- Include performance benchmarks if relevant

## Documentation

- Update README.md if you add new features
- Update OPTIMIZATION_SUMMARY.md for performance changes
- Add inline comments for complex logic
- Update docstrings when changing function behavior

## Getting Help

If you need help with contributing:

- Check existing issues and documentation
- Create a discussion thread for questions
- Reach out to maintainers for guidance

## Recognition

Contributors will be recognized in:

- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section

Thank you for contributing to make this project better! 🚀

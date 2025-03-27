# SiteCheck-py

Python implementation of SiteCheck - A tool for website monitoring and analysis.

## Features

- Website availability monitoring
- Performance metrics collection
- Security headers analysis
- SEO optimization checks
- Accessibility testing

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from sitecheck.core import SiteChecker

checker = SiteChecker(url='https://example.com')
results = checker.analyze()
print(results.summary())
```

## Development

1. Clone the repository
2. Create a virtual environment
3. Install development dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Testing

```bash
pytest tests/
```

## License

MIT License
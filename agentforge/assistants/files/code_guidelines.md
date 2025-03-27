# Code Review and Development Guidelines

## Code Review Checklist

- Check for proper error handling and edge cases
- Ensure code follows language-specific best practices
- Look for potential security vulnerabilities
- Verify proper input validation
- Check for code efficiency and performance
- Ensure proper documentation and comments
- Verify test coverage

## Debugging Guidelines

- Analyze error messages and stack traces
- Check common error patterns
- Verify variable states and data flow
- Look for race conditions in async code
- Check for memory leaks
- Verify API usage and integration points

## Implementation Best Practices

- Follow SOLID principles
- Use proper design patterns
- Implement proper error handling
- Write clean, maintainable code
- Add comprehensive documentation
- Include unit tests
- Follow security best practices

# Code Assistant Instructions

## Core Competencies

### 1. Programming Languages

- Python, JavaScript/TypeScript, Java, C++, Go
- Web technologies (HTML, CSS, React, Node.js)
- Database languages (SQL, MongoDB queries)
- Shell scripting (Bash, PowerShell)

### 2. Development Tasks

- Code implementation
- Debugging and troubleshooting
- Performance optimization
- Code review and refactoring
- API design and integration

### 3. Software Architecture

- Design patterns
- System architecture
- Microservices
- Cloud services
- Containerization

## Code Review Guidelines

### 1. Code Quality

- Clean code principles
- SOLID principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)

### 2. Performance

- Time complexity analysis
- Space complexity analysis
- Memory management
- Resource utilization
- Caching strategies

### 3. Security

- Input validation
- Authentication/Authorization
- Data encryption
- Secure communication
- Common vulnerabilities (OWASP)

### 4. Testing

- Unit tests
- Integration tests
- End-to-end tests
- Test coverage
- Mocking and stubbing

## Debugging Protocol

### 1. Error Analysis

1. Read error message carefully
2. Identify error type and location
3. Check stack trace
4. Review related code
5. Consider common causes

### 2. Investigation Steps

1. Reproduce the issue
2. Add logging/debugging statements
3. Check variable states
4. Review data flow
5. Test assumptions

### 3. Solution Approach

1. Identify root cause
2. Consider multiple solutions
3. Evaluate trade-offs
4. Implement fix
5. Verify solution
6. Add regression tests

## Implementation Best Practices

### 1. Code Organization

```python
# File structure
project/
├── src/
│   ├── core/
│   ├── modules/
│   └── utils/
├── tests/
├── docs/
└── README.md

# Module structure
"""Module docstring explaining purpose"""

# Imports
from typing import List, Dict
import standard_libs
import third_party_libs
from . import local_libs

# Constants
MAX_RETRIES = 3

# Classes
class MyClass:
    """Class docstring"""
    
    def __init__(self):
        """Constructor docstring"""
        pass

# Functions
def my_function(param: str) -> bool:
    """Function docstring"""
    return True
```

### 2. Naming Conventions

- Classes: PascalCase
- Functions/Methods: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private members: _prefix

### 3. Documentation

- Module docstrings
- Class docstrings
- Function docstrings
- Type hints
- Inline comments for complex logic

### 4. Error Handling

```python
try:
    # Specific operation that might fail
    result = risky_operation()
except SpecificException as e:
    # Handle specific error case
    logger.error(f"Operation failed: {e}")
    raise CustomException("Meaningful message") from e
finally:
    # Cleanup if needed
    cleanup_resources()
```

## API Design Principles

### 1. RESTful APIs

- Use appropriate HTTP methods
- Follow resource naming conventions
- Implement proper status codes
- Include error responses
- Version your APIs

### 2. GraphQL APIs

- Schema design
- Query optimization
- Mutation handling
- Subscription setup
- Error handling

### 3. Authentication

- JWT implementation
- OAuth 2.0 flow
- API key management
- Session handling
- Rate limiting

## Performance Optimization

### 1. Code Level

- Algorithm efficiency
- Data structure selection
- Memory management
- Caching strategies
- Async/await patterns

### 2. Database

- Query optimization
- Indexing
- Connection pooling
- N+1 query prevention
- Batch operations

### 3. System Level

- Load balancing
- Caching layers
- Message queues
- Horizontal scaling
- Vertical scaling

## Security Guidelines

### 1. Input Validation

```python
def validate_user_input(data: Dict[str, Any]) -> bool:
    """Validate user input against security rules"""
    if not isinstance(data.get('username'), str):
        raise ValidationError("Username must be a string")
    if len(data.get('password', '')) < 8:
        raise ValidationError("Password too short")
    # More validation rules...
    return True
```

### 2. Authentication

- Password hashing
- Session management
- Token validation
- 2FA implementation
- Rate limiting

### 3. Data Protection

- Encryption at rest
- Encryption in transit
- PII handling
- Secure configuration
- Audit logging

## Testing Strategy

### 1. Unit Tests

```python
def test_user_validation():
    """Test user input validation"""
    # Arrange
    test_data = {"username": "test", "password": "short"}
    
    # Act & Assert
    with pytest.raises(ValidationError):
        validate_user_input(test_data)
```

### 2. Integration Tests

- API endpoints
- Database operations
- External services
- Authentication flow
- Error scenarios

### 3. Performance Tests

- Load testing
- Stress testing
- Endurance testing
- Spike testing
- Scalability testing

## Version Control

### 1. Git Best Practices

- Clear commit messages
- Feature branching
- Pull request reviews
- Merge conflict resolution
- Release tagging

### 2. Workflow

1. Create feature branch
2. Make focused commits
3. Write tests
4. Update documentation
5. Create pull request
6. Address review comments
7. Merge to main branch

## Continuous Integration/Deployment

### 1. CI Pipeline

- Automated testing
- Code quality checks
- Security scanning
- Documentation generation
- Version management

### 2. CD Pipeline

- Environment management
- Deployment automation
- Rollback procedures
- Monitoring setup
- Alert configuration

## Response Format

### 1. Code Solutions

```python
# Problem: [Brief description]
# Solution approach:
# 1. [Step 1]
# 2. [Step 2]
# ...

def solution():
    """Docstring explaining the solution"""
    # Implementation
    pass

# Usage example:
# [Example code]
```

### 2. Error Resolution

```
Error: [Error message]
Cause: [Explanation]
Solution:
1. [Step 1]
2. [Step 2]
...
Prevention:
- [Recommendation 1]
- [Recommendation 2]
```

### 3. Code Review

```
File: [filename]
Review comments:
1. Line [X]: [Comment]
   Suggestion: [Code suggestion]
2. Line [Y]: [Comment]
   Suggestion: [Code suggestion]
...
Overall recommendations:
- [Recommendation 1]
- [Recommendation 2]
```

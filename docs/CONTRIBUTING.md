# Contributing to HIPAA Training System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### HIPAA-Focused Conduct

As a project handling sensitive compliance training, all contributors must also:

- **Protect Sensitive Information:** Never post real patient data, internal configuration details, or any other sensitive information in issues, pull requests, or discussions.
- **Report Violations:** Confidentially report any concerns about unethical conduct or potential privacy/security violations to the project maintainers.
- **Exercise Professional Judgment:** Understand that actions within the project can have real-world implications for healthcare organizations and patient privacy.
  

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/Saranoah/HIPAA-Training-System-for-Pharmacy-Staff-V2.0.git
cd HIPAA-Training-System-for-Pharmacy-Staff-V2.0
```

### 2. Set Up Development Environment

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.8+

# Run tests to ensure everything works
python test_hipaa_training_v2.py
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

## 💻 Development Process

### Branch Naming Conventions

- **Features**: `feature/add-new-lesson-module`
- **Bug fixes**: `fix/correct-score-calculation`
- **Documentation**: `docs/update-testing-guide`
- **Refactoring**: `refactor/improve-error-handling`
- **Tests**: `test/add-edge-case-coverage`

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): Brief description

Detailed explanation if necessary

Fixes #issue_number
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples**:
```
feat(quiz): Add 5 new pharmacy scenarios

Added scenarios covering:
- Medication disposal
- Patient counseling
- Insurance verification
- Prescription transfers
- Adverse event reporting

Fixes #42
```

```
fix(checklist): Correct percentage calculation for empty responses

Previously returned NaN, now correctly returns 0.0

Fixes #38
```

## 📝 Coding Standards

### Python Style Guide (PEP 8)

```python
# ✅ Good
def calculate_score(responses: Dict[str, bool]) -> float:
    """Calculate percentage score from responses."""
    completed = sum(responses.values())
    total = len(responses)
    return (completed / total) * 100 if total > 0 else 0.0

# ❌ Bad
def calc(r):
    c=sum(r.values())
    return (c/len(r))*100
```

## 🔒 HIPAA & Security Guidelines

### Handling Protected Health Information (PHI)
- **No Real PHI in Development or Testing:** Never use real patient data for testing, debugging, or in sample files:cite[9]. Generate realistic but completely fictional mock data.
- **Secure Data Practices:** Be mindful of how data is handled, stored, and logged. Avoid printing sensitive information to consoles or logs, even during development.
- **Reporting Security Concerns:** All contributors are obligated to report any potential security flaws or privacy concerns immediately by emailing [your designated security contact]. Do not publicly disclose the issue on GitHub issues:cite[7].

### Security-First Development
- **Risk Assessment:** Consider the privacy and security implications of any new feature or code change.
- **Dependency Management:** Regularly update dependencies to patch known vulnerabilities. PRs that address security vulnerabilities in dependencies are highly prioritized.


### Type Hints Required

All functions must include type hints:

```python
from typing import Dict, List, Optional, Any

def process_data(
    items: List[str],
    options: Dict[str, Any],
    timeout: Optional[int] = None
) -> bool:
    """Process data with given options."""
    pass
```

### Documentation Standards

Every function needs a clear docstring:

```python
def calculate_quiz_score(correct_answers: int, total_questions: int) -> float:
    """
    Calculate quiz score percentage.
    
    Calculates the percentage of correct answers out of total questions,
    with protection against division by zero.
    
    Args:
        correct_answers: Number of questions answered correctly
        total_questions: Total number of questions in the quiz
    
    Returns:
        Percentage score as a float (0.0 to 100.0)
    
    Example:
        >>> calculate_quiz_score(3, 5)
        60.0
        >>> calculate_quiz_score(0, 0)
        0.0
    """
    return (correct_answers / total_questions) * 100 if total_questions > 0 else 0.0
```

### Code Organization

```python
# 1. Standard library imports
import json
from datetime import datetime
from typing import Dict, List

# 2. Third-party imports (if any)
# import requests

# 3. Local imports
# from .module import function

# 4. Constants
PASS_THRESHOLD: int = 80
GOOD_THRESHOLD: int = 60

# 5. Functions/Classes
def function_name():
    pass
```

## 🧪 Testing Requirements

### All Changes Must Include Tests

### HIPAA Compliance Verification
In addition to functional tests, the following must be verified:
- **Data Anonymity:** All test data is demonstrably fictional and cannot be linked to real individuals.
- **Audit Trail:** New features that handle user data maintain a clear audit trail where appropriate.
- **Error Handling:** Systems fail securely, without leaking internal information or PHI in error messages:cite[1].
For new features:
```python
class TestNewFeature(unittest.TestCase):
    """Test suite for new feature"""
    
    def test_feature_basic_case(self):
        """Test basic functionality"""
        result = new_feature(input_data)
        self.assertEqual(result, expected_output)
    
    def test_feature_edge_case(self):
        """Test edge cases"""
        result = new_feature(edge_case_data)
        self.assertIsNotNone(result)
    
    def test_feature_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            new_feature(invalid_data)
```

### Running Tests

```bash
# Run all tests
python test_hipaa_training_v2.py

# Run specific test class
python -m unittest test_hipaa_training_v2.py.TestClassName

# Run specific test method
python -m unittest test_hipaa_training_v2.py.TestClassName.test_method_name

# Run with verbose output
python test_hipaa_training_v2.py -v
```

### Test Coverage Requirements

- ✅ All tests must pass before PR submission
- ✅ New features require new tests
- ✅ Bug fixes require regression tests
- ✅ Edge cases must be tested
- ✅ Error handling must be tested

## 🔄 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (PEP 8)
- [ ] All tests pass locally
- [ ] New tests added for changes
- [ ] Documentation updated
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] No debug code or print statements
- [ ] **No Real PHI:** I confirm that no real Protected Health Information is used in my code or tests.
- [ ] **Security Review:** I have considered the security and privacy implications of my changes.


### PR Template

When opening a PR, use this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed
- [ ] Edge cases considered

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Type hints added
- [ ] Docstrings added/updated

## Related Issues
Fixes #issue_number
```

### Review Process

1. **Automated Checks**: GitHub Actions runs tests automatically
2. **Code Review**: Maintainers review code and provide feedback
3. **Revisions**: Make requested changes and push updates
4. **Approval**: Once approved, PR will be merged
5. **Merge**: Squash and merge to main branch

## 🐛 Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear and concise description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04, macOS 13.0, Windows 11]
- Python Version: [e.g., 3.10.12]
- Version: [e.g., 1.0.0]

**Screenshots**
If applicable, add screenshots

**Additional Context**
Any other relevant information
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why this feature is needed and who would use it

**Proposed Solution**
How you think it should work

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other information, mockups, or examples
```

## 🎯 Areas for Contribution

### High Priority

- **Content**: Additional HIPAA scenarios and lessons
  - Real-world pharmacy situations
  - Updated compliance requirements
  - State-specific regulations
  
- **Testing**: More edge cases and integration tests
  - Boundary condition tests
  - Stress testing
  - Security testing

- **Documentation**: Usage examples and tutorials
  - Video tutorials
  - Step-by-step guides
  - FAQ section

- **Accessibility**: Improvements for all users
  - Screen reader support
  - Keyboard navigation
  - High contrast mode

### Medium Priority

- **Features**: 
  - Certificate generation (PDF)
  - Admin dashboard for tracking
  - Email notifications
  - Multi-language support

- **Performance**: 
  - Optimization for large datasets
  - Faster file I/O
  - Memory usage improvements

- **Security**: 
  - Enhanced encryption
  - Audit logging improvements
  - Session management

### Good First Issues

Look for issues labeled `good-first-issue`:

- Documentation improvements
- Adding new training scenarios
- Writing additional unit tests
- Fixing typos or formatting
- Updating dependencies

## 📚 Resources

### HIPAA Information

- [HHS HIPAA Website](https://www.hhs.gov/hipaa)
- [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security)
- [Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification)

### Python Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 💬 Communication

### Getting Help

- **GitHub Discussions**: For questions and general discussions
- **GitHub Issues**: For bugs and feature requests
- **Pull Request Comments**: For code-specific discussions

### Response Times

We aim to respond within:
- **Issues**: 48-72 hours
- **Pull Requests**: 3-7 days
- **Discussions**: 72 hours

## 🎖️ Recognition

Contributors will be:

- Listed in AUTHORS.md (create if contributing)
- Mentioned in release notes
- Credited in documentation
- Added to README contributors section

### How to Add Yourself

When making your first contribution, add yourself to the contributors list:

```markdown
## Contributors

- [@Saranoah](https://github.com/Saranoah) - Creator and maintainer
- [@YourUsername](https://github.com/YourUsername) - Brief description of contribution
```

## ⚖️ Legal

By contributing, you agree that:

- Your contributions will be licensed under the MIT License
- You have the right to contribute the code/content
- Your contributions are your original work or properly attributed

## 🎉 Thank You!

Every contribution helps improve healthcare compliance training for pharmacy professionals. Whether it's:

- 🐛 Reporting a bug
- 💡 Suggesting a feature
- 📝 Improving documentation
- 🧪 Adding tests
- 💻 Contributing code

**Your efforts make a difference!**

---

**Questions?** Feel free to open a discussion or issue. We're here to help!

*Last updated: October 2025*

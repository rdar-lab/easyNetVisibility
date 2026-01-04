# Contributing to Easy Net Visibility

Thank you for your interest in contributing to Easy Net Visibility! This document provides guidelines and instructions for contributing to the project.

**Related Documentation**: [README.md](README.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [API.md](API.md) | [PUSHOVER.md](PUSHOVER.md)

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Be respectful and considerate in communication
- Welcome diverse perspectives and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or inflammatory comments
- Personal or political attacks
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, make sure you have:

- Git installed and configured
- Docker installed (for containerized testing)
- Python 3.8 or higher
- Basic understanding of Django (for server contributions)
- Basic understanding of network scanning concepts (for sensor contributions)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
```bash
git clone https://github.com/YOUR_USERNAME/easyNetVisibility.git
cd easyNetVisibility
```

3. **Add upstream remote**:
```bash
git remote add upstream https://github.com/rdar-lab/easyNetVisibility.git
```

4. **Create a branch** for your changes:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Environment

### Server Development Setup

1. **Navigate to server directory**:
```bash
cd easyNetVisibility/server/server_django
```

2. **Create Python virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install flake8 bandit[toml]  # Linting tools
```

4. **Create development configuration**:
```bash
cd easy_net_visibility
mkdir -p conf
cat > conf/settings.json << 'EOF'
{
  "DATABASES": {
    "default": {
      "ENGINE": "django.db.backends.sqlite3",
      "NAME": "db/db.sqlite3"
    }
  },
  "SECRET_KEY": "dev-secret-key-for-testing-only",
  "DEBUG": "True",
  "STATIC_ROOT": "static"
}
EOF
```

5. **Initialize database**:
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Run development server**:
```bash
python manage.py runserver 0.0.0.0:8000
```

### Sensor Development Setup

1. **Navigate to client directory**:
```bash
cd easyNetVisibility/client
```

2. **Create Python virtual environment**:
```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install pytest pytest-mock flake8
```

4. **Configure development sensor**:
```bash
# Edit sensor/config/config.ini
[ServerAPI]
serverURL=http://localhost:8000
serverUsername=admin
serverPassword=your_dev_password
validateServerIdentity=False

[General]
interface=eth0
```

5. **Run sensor** (requires nmap installed):
```bash
cd sensor
python sensor.py
```

### Docker Development

**Build and test server**:
```bash
cd easyNetVisibility/server/server_django
docker build -t rdxmaster/easy-net-visibility-server-django:dev .
docker run -it --rm -p 8000:8000 \
  -v "$(pwd)/conf:/opt/app/easy_net_visibility/conf:ro" \
  -v "$(pwd)/db:/opt/app/easy_net_visibility/db:rw" \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_PASSWORD=test \
  -e DJANGO_SUPERUSER_EMAIL=test@test.com \
  rdxmaster/easy-net-visibility-server-django:dev
```

**Build and test sensor**:
```bash
cd easyNetVisibility/client
docker build -t rdxmaster/easy-net-visibility-sensor:dev .
docker run -it --rm --net=host \
  -v "$(pwd)/sensor/config:/opt/sensor/config" \
  rdxmaster/easy-net-visibility-sensor:dev
```

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

1. **Bug Fixes**: Fix issues identified in the issue tracker
2. **New Features**: Implement new functionality
3. **Documentation**: Improve README, add examples, fix typos
4. **Tests**: Add or improve test coverage
5. **Performance**: Optimize code for better performance
6. **Code Quality**: Refactoring, code cleanup, improving maintainability
7. **Security**: Fix security vulnerabilities
8. **Platform Support**: Improve compatibility with different platforms

### Contribution Workflow

1. **Check existing issues**: Look for existing issues or create a new one
2. **Discuss major changes**: For large features, discuss in an issue first
3. **Make changes**: Write code following our coding standards
4. **Add tests**: Write tests for new functionality
5. **Run tests**: Ensure all tests pass
6. **Update documentation**: Document new features or changes
7. **Submit PR**: Create a pull request with clear description

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: Maximum 200 characters (instead of 79)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Group in order: standard library, third-party, local
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: `_leading_underscore`

### Django Best Practices

- Use Django ORM instead of raw SQL
- Validate data at model level
- Use Django forms for input validation
- Follow Django's URL pattern conventions
- Use Django's built-in authentication
- Write docstrings for views and models

### Code Quality

**Required before committing**:
```bash
# Run linting
flake8 . --count --max-line-length=200 --show-source --statistics --exclude='*/migrations/*,*/tests/*'

# Run security checks
bandit -r . -ll -x "*/migrations/*,*/tests/*"
```

**Use the check script**:
```bash
# From repository root
./check_code.sh
```

### Documentation Standards

- **Docstrings**: Use for all public functions, classes, and methods
- **Comments**: Explain why, not what (code should be self-explanatory)
- **README updates**: Update README.md for user-facing changes
- **API documentation**: Update API docs for API changes

**Docstring format**:
```python
def my_function(param1, param2):
    """
    Brief description of function.

    Longer description if needed, explaining what the function does,
    any important details, and usage examples.

    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

## Testing Guidelines

### Writing Tests

**Server tests** (Django):
```python
from django.test import TestCase
from easy_net_visibility_server.models import Device

class DeviceTestCase(TestCase):
    def test_device_creation(self):
        """Test that devices can be created with valid data."""
        device = Device.objects.create(
            mac='00:11:22:33:44:55',
            ip='192.168.1.100',
            hostname='test.local'
        )
        self.assertEqual(device.mac, '00:11:22:33:44:55')
        self.assertEqual(device.ip, '192.168.1.100')
```

**Client tests** (pytest):
```python
import pytest
from sensor import network_utils

def test_mac_address_detection(mocker):
    """Test MAC address detection from network interface."""
    # Mock the subprocess call
    mocker.patch('subprocess.check_output', return_value=b'00:11:22:33:44:55')
    
    mac = network_utils.get_mac_address('eth0')
    assert mac == '00:11:22:33:44:55'
```

### Running Tests

**Server tests**:
```bash
cd easyNetVisibility/server/server_django/easy_net_visibility
python manage.py test
python manage.py test --verbosity=2  # Verbose output
python manage.py test tests.test_validators  # Specific module
```

**Client tests**:
```bash
cd easyNetVisibility/client
pytest tests/ -v
pytest tests/test_network_utils.py -v  # Specific file
pytest tests/ --cov=sensor --cov-report=html  # With coverage
```

### Test Coverage

- **New features**: Must include tests
- **Bug fixes**: Add tests to prevent regression
- **Code coverage**: Aim for >80% coverage on new code
- **Edge cases**: Test boundary conditions and error cases

### Continuous Integration

All pull requests automatically run:
- Server tests (152 tests)
- Client tests (63 tests)
- Code linting (flake8)
- Security checks (bandit)

Tests must pass before merging.

## Pull Request Process

### Before Submitting

1. **Update your branch**:
```bash
git fetch upstream
git rebase upstream/main
```

2. **Run all tests**:
```bash
./check_code.sh  # Linting
cd easyNetVisibility/server/server_django/easy_net_visibility && python manage.py test
cd easyNetVisibility/client && pytest tests/
```

3. **Update documentation**: Ensure README and docs are current

4. **Commit messages**: Write clear, descriptive commit messages
```
Short summary (50 chars or less)

Detailed explanation if needed. Explain what changed and why.
Reference issue numbers if applicable.

Fixes #123
```

### Creating a Pull Request

1. **Push to your fork**:
```bash
git push origin feature/your-feature-name
```

2. **Create PR on GitHub**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select base: `main`, compare: `your-branch`
   - Fill out the PR template

3. **PR description should include**:
   - Clear description of changes
   - Motivation and context
   - Testing performed
   - Screenshots (for UI changes)
   - Related issues (Fixes #123)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new functionality
- [ ] Tested on [platform/environment]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Commented complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks**: CI must pass
2. **Code review**: Maintainer will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainer will merge
5. **Credit**: You will be credited in release notes

### After Merge

1. **Update your fork**:
```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

2. **Delete feature branch**:
```bash
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Reporting Bugs

### Before Reporting

1. **Check existing issues**: Search for similar reports
2. **Verify bug**: Ensure it's reproducible
3. **Test latest version**: Bug may be fixed in latest code

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen

**Actual Behavior**
What actually happened

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Docker version: [e.g., 20.10.8]
- Component: [Server/Sensor]
- Version/commit: [e.g., v1.2.3 or commit abc123]

**Logs**
```
Paste relevant logs here
```

**Screenshots**
If applicable, add screenshots

**Additional Context**
Any other relevant information
```

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of desired functionality

**Describe alternatives you've considered**
Other solutions you've thought about

**Use Cases**
How would this feature be used?

**Additional Context**
Any other relevant information

**Would you like to implement this?**
- [ ] Yes, I can work on this
- [ ] No, just suggesting
```

### Feature Discussion

For major features:
1. **Open issue**: Describe the feature
2. **Discuss**: Get feedback from maintainers
3. **Design**: Work out implementation details
4. **Implement**: Once approved, start coding

## Documentation

### Documentation Changes

Documentation improvements are always welcome:

- Fix typos and grammar
- Improve clarity and examples
- Add missing documentation
- Update outdated information
- Translate documentation

### Documentation Standards

- **Clear and concise**: Easy to understand
- **Complete examples**: Show working code
- **Up-to-date**: Matches current implementation
- **Well-organized**: Logical structure
- **Tested**: Verify examples work

### Documentation Locations

- **README.md**: Overview, installation, quick start
- **ARCHITECTURE.md**: System design and internals
- **CONTRIBUTING.md**: This file
- **PUSHOVER.md**: Pushover integration details
- **Code comments**: Inline documentation
- **Docstrings**: API documentation

## Release Process

### For Maintainers

Easy Net Visibility uses automated releases via GitHub Actions. The process is designed to be simple and reliable.

#### Versioning

We follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes or major new features
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Examples: `v1.0.0`, `v1.2.3`, `v2.0.0`

#### Creating a Release

1. **Ensure quality standards**:
   - All tests pass
   - Code quality checks pass
   - Documentation is updated
   - CHANGELOG or release notes prepared

2. **Create and push a version tag**:
   ```bash
   # Create an annotated tag with version number
   git tag -a v1.0.0 -m "Release version 1.0.0 - Description of changes"
   
   # Push the tag to GitHub
   git push origin v1.0.0
   ```

3. **Automated Release Workflow**:
   Once the tag is pushed, GitHub Actions will automatically:
   - Build Docker images for server and sensor
   - Tag images with the version (e.g., `1.0.0`) and `latest`
   - Push images to Docker Hub:
     - `rdxmaster/easy-net-visibility-server-django`
     - `rdxmaster/easy-net-visibility-sensor`
   - Create a GitHub Release with auto-generated changelog
   - Attach version information to the release

4. **Verify the release**:
   - Check [GitHub Actions](https://github.com/rdar-lab/easyNetVisibility/actions) for workflow status
   - Verify [GitHub Releases](https://github.com/rdar-lab/easyNetVisibility/releases)
   - Confirm Docker Hub images:
     - https://hub.docker.com/r/rdxmaster/easy-net-visibility-server-django
     - https://hub.docker.com/r/rdxmaster/easy-net-visibility-sensor

#### Manual Release Trigger

Releases can also be triggered manually:

1. Navigate to [GitHub Actions](https://github.com/rdar-lab/easyNetVisibility/actions)
2. Select "Release" workflow
3. Click "Run workflow"
4. Enter version tag (e.g., `v1.0.0`)
5. Click "Run workflow" button

#### Required Secrets

The following GitHub secrets must be configured (one-time setup):

- `DOCKERHUB_USERNAME`: Docker Hub username (rdxmaster)
- `DOCKERHUB_TOKEN`: Docker Hub access token

**Setting up Docker Hub token** (for administrators):
1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to Account Settings → Security
3. Click "New Access Token"
4. Name: "GitHub Actions Release"
5. Permissions: Read & Write
6. Copy the token
7. Add to GitHub: Repository Settings → Secrets and variables → Actions → New repository secret

#### Release Checklist

Before creating a release:

- [ ] All tests pass on main branch
- [ ] Documentation is up to date
- [ ] Version number follows semantic versioning
- [ ] Breaking changes are documented (if any)
- [ ] CHANGELOG entries prepared (auto-generated, but can be edited)
- [ ] Docker Hub credentials are configured in GitHub secrets

## Questions?

If you have questions:

1. **Check documentation**: README, ARCHITECTURE, etc.
2. **Search issues**: Look for similar questions
3. **Open discussion**: Create a GitHub issue with question

## Recognition

Contributors will be:
- Listed in release notes
- Credited in commits
- Recognized in the community

Thank you for contributing to Easy Net Visibility!

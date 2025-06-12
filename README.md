# GitAuto AI 🤖

[![PyTest](https://github.com/gitautoai/gitauto/actions/workflows/pytest.yml/badge.svg)](https://github.com/gitautoai/gitauto/actions/workflows/pytest.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

> **AI-powered GitHub coding agent that automatically creates pull requests from issue descriptions**

GitAuto is an intelligent GitHub app that transforms your issue backlog into actionable pull requests. Simply describe what you want, and GitAuto will analyze your codebase, understand the requirements, and generate the necessary code changes.

## 🚀 Quick Start

### For Users (No Setup Required)

1. **Install GitAuto** from the [GitHub Marketplace](https://github.com/apps/gitauto-ai)
2. **Create an issue** in your repository describing what you want to build or fix
3. **Check the checkbox** in GitAuto's comment or add the `gitauto` label
4. **Wait for the magic** ✨ - GitAuto will create a pull request for you!

### For Developers (Local Development)

```bash
# Clone the repository
git clone https://github.com/gitautoai/gitauto.git
cd gitauto

# Set up Python environment
python3 -m venv --upgrade-deps venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Get .env file from maintainer and run the server
uvicorn main:app --reload --port 8000 --log-level warning
```

## 📖 Table of Contents

- [What is GitAuto?](#-what-is-gitauto)
- [How It Works](#-how-it-works)
- [Features](#-features)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [Support](#-support)

## 🎯 What is GitAuto?

[GitAuto](https://gitauto.ai) is a GitHub coding agent designed for software engineering managers and developers who want to:

- **Accelerate development** by automating routine coding tasks
- **Focus on complex problems** while GitAuto handles the straightforward implementations
- **Maintain code quality** with AI-generated, reviewable pull requests
- **Reduce backlog** by converting issues into actionable code changes

### Perfect For:
- 🐛 **Bug fixes** - Describe the issue, get a fix
- ✨ **Feature requests** - Outline requirements, receive implementation
- 🔧 **Refactoring** - Specify improvements, get clean code
- 📚 **Documentation** - Request docs, get comprehensive updates

## 🔄 How It Works

```mermaid
graph LR
    A[Create Issue] --> B[GitAuto Analyzes]
    B --> C[Code Generation]
    C --> D[Pull Request]
    D --> E[Review & Merge]
```

1. **Issue Creation**: Describe your requirements in a GitHub issue
2. **AI Analysis**: GitAuto analyzes your codebase and understands the context
3. **Code Generation**: Creates the necessary code changes using advanced AI models
4. **Pull Request**: Opens a PR with the implementation for your review
5. **Review & Merge**: You review, provide feedback, and merge when ready

## ✨ Features

### 🎯 **Smart Code Understanding**
- Analyzes your entire codebase for context
- Understands project structure and patterns
- Maintains consistency with existing code style

### 🔧 **Multi-Language Support**
- Python, JavaScript, TypeScript, Java, Go, Rust, and more
- Framework-aware (React, Django, FastAPI, etc.)
- Handles configuration files and dependencies

### 🚀 **Intelligent Automation**
- Automatic branch creation and management
- Comprehensive test coverage analysis
- Dependency management and updates

### 🔍 **Quality Assurance**
- Code review integration
- Automated testing workflows
- Security-conscious implementations

## 🏁 Getting Started

### Step 1: Installation

Visit the [GitAuto GitHub App](https://github.com/apps/gitauto-ai) and install it on your repositories.

### Step 2: Create Your First Issue

Create a new issue with a clear description:

```markdown
## Feature Request: Add User Authentication

I need to implement user authentication for my web application.

### Requirements:
- Login/logout functionality
- Password hashing
- Session management
- Protected routes

### Tech Stack:
- Backend: FastAPI
- Database: PostgreSQL
- Frontend: React
```

### Step 3: Activate GitAuto

GitAuto will automatically comment on your issue. Simply:
- ✅ Check the checkbox in GitAuto's comment, OR
- 🏷️ Add the `gitauto` label to your issue

### Step 4: Review the Pull Request

GitAuto will create a pull request with:
- 📝 Detailed implementation
- 🧪 Test cases (when applicable)
- 📖 Documentation updates
- 🔗 Reference to the original issue

## 🛠 Development Setup

### Prerequisites

- **Python 3.12+**
- **Git**
- **ngrok** (for webhook tunneling)
- **GitHub App** (for local development)

### Detailed Setup Guide

#### 1. Create Your GitHub App

1. Go to [GitHub Apps Settings](https://github.com/settings/apps)
2. Click **"New GitHub App"**
3. Configure your app:
   ```
   App name: GitAuto Dev {Your Name}
   Homepage URL: http://localhost:8000
   Webhook URL: https://your-ngrok-url.ngrok.dev/webhook
   Webhook secret: your-secret-here
   ```

4. Set **Repository Permissions**:
   - Actions: Read & Write
   - Checks: Read & Write
   - Contents: Read & Write
   - Issues: Read & Write
   - Pull requests: Read & Write
   - And more (see full list in original README)

5. Subscribe to **Events**:
   - Issues, Pull requests, Check runs, etc.

#### 2. Environment Setup

```bash
# Clone and navigate
git clone https://github.com/gitautoai/gitauto.git
cd gitauto

# Create virtual environment
python3 -m venv --upgrade-deps venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Get .env file from maintainer
# Contact @hiroshinishio for the .env file
```

#### 3. Webhook Tunneling with ngrok

```bash
# Create ngrok.yml in root directory
echo "authtoken: YOUR_NGROK_AUTH_TOKEN\nversion: 2" > ngrok.yml

# Start ngrok tunnel
ngrok http --config=ngrok.yml --domain=your-domain.ngrok.dev 8000
```

#### 4. Run the Application

```bash
# Start the development server
uvicorn main:app --reload --port 8000 --log-level warning
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
```

### Git Workflow

```bash
# Keep your branch updated
git checkout your-branch
git pull origin main

# If you have uncommitted changes
git stash
git pull origin main
git stash pop
```

## 🏗 Architecture

GitAuto is built with modern, scalable technologies:

### Core Technologies
- **FastAPI** - High-performance web framework
- **Python 3.12** - Latest Python features
- **AWS Lambda** - Serverless deployment
- **Supabase** - Database and authentication
- **Anthropic Claude** - AI code generation

### Key Components

```
gitauto/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── services/              # Core business logic
│   ├── anthropic/         # AI model integration
│   ├── github/           # GitHub API interactions
│   ├── webhook/          # Webhook event handling
│   └── gitauto_handler.py # Main processing logic
├── utils/                # Utility functions
├── tests/               # Test suite
└── constants/           # Application constants
```

### Data Flow

1. **Webhook Reception** (`main.py`) - Receives GitHub events
2. **Event Processing** (`webhook_handler.py`) - Routes events to handlers
3. **AI Analysis** (`anthropic/`) - Analyzes code and generates solutions
4. **GitHub Integration** (`github/`) - Creates branches, commits, PRs
5. **Database Operations** (`supabase/`) - Tracks usage and state

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 1. Fork & Clone
```bash
git clone https://github.com/your-username/gitauto.git
cd gitauto
```

### 2. Set Up Development Environment
Follow the [Development Setup](#-development-setup) guide above.

### 3. Make Your Changes
- 🐛 **Bug fixes** - Include tests and clear descriptions
- ✨ **Features** - Discuss in issues before implementing
- 📚 **Documentation** - Help improve our guides
- 🧪 **Tests** - Add coverage for new functionality

### 4. Testing
```bash
# Run the test suite
python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info

# Run specific tests
python -m pytest tests/services/github/test_branch_manager.py
```

### 5. Submit Pull Request
- Clear title and description
- Reference related issues
- Include tests for new features
- Follow existing code style

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings for functions
- Keep functions focused and small

## 📞 Support

### 🔗 Quick Links
- 🏠 **Homepage**: [gitauto.ai](https://gitauto.ai)
- 📺 **Demo Videos**: [YouTube Channel](https://www.youtube.com/@gitauto)
- 📧 **Email**: [info@gitauto.ai](mailto:info@gitauto.ai)
- 🐛 **Issues**: [GitHub Issues](https://github.com/gitautoai/gitauto/issues)

### 🌐 Connect With Us
- 🐦 **Twitter**: [@gitautoai](https://x.com/gitautoai)
- 💼 **LinkedIn**: [GitAuto Company](https://www.linkedin.com/company/gitauto/)
- 👨‍💻 **Admin**: [@hiroshinishio](https://github.com/hiroshinishio)

### 💡 Getting Help

1. **Check existing issues** - Your question might already be answered
2. **Create a new issue** - Use our issue templates for bug reports or feature requests
3. **Join discussions** - Participate in GitHub Discussions
4. **Contact us directly** - Email us for business inquiries or complex technical questions

### 🎯 Use Cases & Examples

**Bug Fix Example:**
```markdown
## Bug: Login form validation not working

The login form accepts empty passwords and doesn't show error messages.

### Expected Behavior:
- Show error for empty email/password
- Validate email format
- Display user-friendly error messages

### Current Behavior:
- Form submits with empty fields
- No validation feedback
```

**Feature Request Example:**
```markdown
## Feature: Add dark mode toggle

Add a dark mode option to improve user experience.

### Requirements:
- Toggle button in header
- Persist user preference
- Smooth transition animation
- Update all components consistently
```

---

<div align="center">

**Made with ❤️ by the GitAuto team**

[⭐ Star us on GitHub](https://github.com/gitautoai/gitauto) • [🚀 Try GitAuto](https://github.com/apps/gitauto-ai) • [📖 Learn More](https://gitauto.ai)

</div>
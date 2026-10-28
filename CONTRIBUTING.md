# Contributing to OKF vs Vector RAG

Thank you for your interest in contributing to **OKF vs Vector RAG**! We welcome community contributions, architectural refinements, benchmark metrics, bug fixes, and documentation improvements.

---

## 🛡️ Repository Protection & Contribution Model

To ensure benchmark reproducibility, code stability, security, and project integrity, **OKF vs Vector RAG operates under a strictly protected Fork & Pull Request model**:

1. **Direct Commits Prohibited**: Direct pushes to `main` are permanently blocked by branch protection rules.
2. **Upstream Branch Creation Restricted**: Contributors cannot create branches directly in `karthikrameshdev/okf-vs-rag`. All development branches must live in your own personal fork.
3. **Mandatory Code Review**: Every Pull Request requires automated CI checks to pass and explicit review and approval from `@karthikrameshdev` (enforced via [`CODEOWNERS`](.github/CODEOWNERS)).
4. **Squash Merging**: Pull requests are merged using squash commits to keep Git history clean, atomic, and readable.

---

## 🚀 Step-by-Step Contribution Workflow

### 1. Fork the Repository
Click the **Fork** button at the top-right corner of [https://github.com/karthikrameshdev/okf-vs-rag](https://github.com/karthikrameshdev/okf-vs-rag) to create a copy of the repository under your GitHub account.

### 2. Clone Your Fork
Clone your fork locally and configure the upstream remote:

```bash
# Clone your fork
git clone https://github.com/<your-username>/okf-vs-rag.git
cd okf-vs-rag

# Add upstream remote
git remote add upstream https://github.com/karthikrameshdev/okf-vs-rag.git
git fetch upstream
```

### 3. Create a Feature Branch on Your Fork
Always branch off the latest `upstream/main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/issue-description
```

### 4. Set Up the Local Development Environment
Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and test harness
pip install --upgrade pip
pip install -r requirements.txt pytest
```

Copy the example environment file if you plan to connect to live Gemini or OpenAI endpoints:

```bash
cp .env.example .env
```

*(Note: The built-in benchmark harness includes deterministic mock fallbacks and runs fully offline without requiring API keys or live vector database instances).*

### 5. Make Your Changes and Run Tests
Ensure all code adheres to PEP 8 standards and passes the automated test suite before opening a PR:

```bash
# Run the complete test suite
pytest tests -v
```

### 6. Commit Your Changes
Write clear, conventional commit messages:

```bash
git add .
git commit -m "feat(benchmark): add multi-hop traversal graph density metric"
```

Prefix commits appropriately:
- `feat:` New features or benchmark scenarios
- `fix:` Bug fixes or data alignment corrections
- `docs:` Documentation and architecture updates
- `test:` Adding or updating tests
- `refactor:` Code improvements without behavioral changes

### 7. Push to Your Fork
Push your branch to your personal GitHub fork:

```bash
git push origin feature/your-feature-name
```

### 8. Open a Pull Request
1. Navigate to [https://github.com/karthikrameshdev/okf-vs-rag](https://github.com/karthikrameshdev/okf-vs-rag).
2. Click **Compare & pull request**.
3. Fill out the provided [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) in full.
4. Link any related issues (e.g., `Fixes #12`).
5. Wait for the automated CI tests to complete and for review from the project maintainers.

---

## 📜 Code of Conduct

All contributors are expected to uphold the [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all community members with respect, kindness, and professionalism.

## 🔒 Security Vulnerabilities

Please **do not** open public GitHub issues for security vulnerabilities. Instead, follow our responsible disclosure process in [SECURITY.md](SECURITY.md).

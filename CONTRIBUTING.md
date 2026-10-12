# Contributing to PPC Waste Detector

Thank you for your interest in contributing to `ppc-waste-detector`! We welcome contributions from digital marketers, PPC specialists, data engineers, and Python developers.

---

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hamid-digitalmarketer/ppc-waste-detector.git
   cd ppc-waste-detector
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

---

## Code Quality Standards

Before submitting a Pull Request, ensure that all linting, formatting, type checking, and tests pass:

```bash
# Run test suite
pytest

# Check code formatting & linting
ruff check .

# Run static type checking
mypy src
```

---

## Adding New Detectors

To implement a new waste detector:
1. Inherit from `BaseDetector` in `src/ppc_waste_detector/detectors/`.
2. Define the corresponding `LeakCategory` member in `src/ppc_waste_detector/models.py`.
3. Add unit test coverage in `tests/test_detectors.py`.
4. Document the new detector in `docs/waste_categories.md`.

---

## Pull Request Guidelines

1. Create a descriptive branch: `feature/new-detector-name` or `fix/issue-description`.
2. Commit with conventional commit messages (e.g., `feat(detectors): ...`, `fix(cli): ...`, `docs: ...`).
3. Ensure CI checks pass on GitHub Actions.

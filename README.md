# PrismSNV User Documentation (Sphinx + Read the Docs + Shibuya)

This repository contains the standalone PrismSNV user documentation project built with:

- Sphinx
- Read the Docs
- Shibuya theme

The documentation targets the current PrismSNV 0.1.0 source checkout, reviewed
on 2026-10-08. Runtime requirements and examples follow the application
`pyproject.toml`, CLI parsers, and packaged configuration template. The current
package requires Python 3.12+ and bundles VarScan v2.4.6.

## Local Preview

From Linux or WSL with Python 3.12 available:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

After a successful build, open: `docs/_build/html/index.html`

On Windows PowerShell, activate the environment with
`.\.venv\Scripts\Activate.ps1` instead.

If you changed `index.md` toctree structure (added/reordered pages), run a full forced rebuild to avoid stale sidebar navigation:

```bash
sphinx-build -E -a -b html docs docs/_build/html
```

## Read the Docs

The project root already includes `.readthedocs.yaml`, so it is ready for RTD builds.

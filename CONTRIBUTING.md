# Contributing to Mercury

Thank you for your interest in contributing to **Mercury**! 🎉
Mercury is an open-source framework for turning Python notebooks into interactive web apps. It includes:

* a widget system built on **ipywidgets** and **anywidget** (`mercury/`)
* a **JupyterLab ≥ 4** extension for live preview (`packages/lab/`)
* an application bundle built on top of the extension (`packages/application/`)
* a lightweight frontend loader (`app/`)
* a server component (`mercury_app/`)

This document explains how to set up your development environment and how to work on each part of the project.

---

## 🧱 Project Structure Overview

```
mercury/                 # Python package with widgets (ipywidgets + anywidget)
packages/
    lab/                 # JupyterLab extension (frontend TypeScript code)
    application/         # Application built using the extension
app/                     # Standalone web app wrapper, handles dynamic loading
mercury_app/             # Python server backend
dist/                    # Python wheels and sdist
docs/                    # Documentation using Astro
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/mljar/mercury.git
cd mercury
```

## 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## 3. Install JS dependencies

Mercury uses Yarn (via `jlpm`) for frontend work.

```bash
jlpm install
```

---

# 🛠️ How to Develop Mercury

Mercury has multiple components. Each part has a slightly different workflow.

Below is a guide for the most common development tasks.

---

# 1. 🧩 Developing Python Widgets (`mercury/`)

The `mercury` directory contains Python widget definitions implemented using **ipywidgets** and **anywidget**.

### How to work on them

1. Make changes in the Python files under `mercury/`.
2. Open a notebook using Mercury.
3. **Reload the notebook kernel** and re-import:

```python
from mercury import *
```

4. Your widget changes will appear immediately.

👉 **No build step required.**
👉 Mercury automatically picks up widget changes through Python import.


### Widget tests

Widget tests are located in `mercury/tests` directory.

---

#### Venv available in JupyterLab

```
python -m ipykernel install --user --name venv
```

# 2. 🧪 Developing the JupyterLab Extension (`packages/lab/`)

This is the TypeScript code that:

* integrates Mercury widgets into JupyterLab
* creates the **live preview panel**
* handles communication between cells and the app

### Setup:

Install editable Python package:

```bash
pip install -e .
jupyter labextension develop . --overwrite
jlpm install
jlpm build
```

Please go into the extension directory:

```bash
cd packages/lab
```

and start watching the extension:

```bash
jlpm run watch
```

This runs the build in watch mode and automatically recompiles as you edit.

### Use the extension in JupyterLab

Open another terminal in the project root:

```bash
jupyter lab
```

The extension should load automatically via federated extensions.

If not, rebuild everything:

```bash
jlpm run build
```

### Summary

* Edit TypeScript files in `packages/lab`
* `pip install -e .`
* `jlpm run watch`
* Reload JupyterLab

---

# 3. 📦 Developing Application Package (`packages/application/`)

This directory contains the “standalone Mercury app” used when exporting or embedding.

### Workflow

1. Go to the directory:

```bash
cd packages/application
```

2. Install dependencies (please run in main directory):

```bash
jlpm install
```

3. Start watch mode:

```bash
jlpm run watch
```

4. In another terminal, run JupyterLab or the Mercury server.

---

# 4. 🌐 Frontend Wrapper (`app/`)

The `app/` folder is responsible for:

* bundling the standalone Mercury app
* enabling **federated extension dynamic loading**
* packaging production builds

### Development workflow

```bash
cd app
jlpm install
jlpm run build       # or jlpm run watch for development
```

---

# 5. 🖥️ Server Backend (`mercury_app/`)

This directory contains the custom Python server used for:

* serving Mercury apps
* handling notebook metadata
* rendering static assets
* managing session state

### Workflow

1. Make changes in Python files under `mercury_app/`.
2. Restart the Mercury server:

```bash
mercury
```

(or if running inside JupyterLab, restart JupyterLab)

👉 No frontend build is needed unless you edit static assets.

---

# 🔄 Full Development Workflow Cheat Sheet

| Component              | Path                    | How to Develop                                     |
| ---------------------- | ----------------------- | -------------------------------------------------- |
| **Widgets (Python)**   | `mercury/`              | Edit → reload notebook → re-import                 |
| **JupyterLab Ext.**    | `packages/lab/`         | `pip install -e .` → `jlpm run watch` → reload Lab |
| **Application Bundle** | `packages/application/` | `jlpm run watch`                                   |
| **Standalone Web App** | `app/`                  | `jlpm run build` or `jlpm run watch`               |
| **Backend Server**     | `mercury_app/`          | Edit Python → restart server                       |

---

# 🧪 Running Tests (if applicable)

Add instructions here once tests are added.

---

# 📦 Building All Artifacts

To build all packages:

```bash
jlpm run build
```

or production build:

```bash
jlpm run build:prod
```

This will:

* clean build artifacts
* build workspaces
* check that all expected output files exist

---

# 🧹 Linting & Formatting

### Python:

```bash
ruff check .
black .
```

### TypeScript:

```bash
jlpm lint
```

---

# 📚 Documentation

Docs are inside the `docs/` directory and built using **Astro**.

```
cd docs
npm install
npm run dev
```

---

# 🤝 How to Contribute

1. Fork the repo.
2. Create a new branch:

```bash
git checkout -b feature/my-improvement
```

3. Make your changes.
4. Add or update tests (if available).
5. Run builds/lints.
6. Create a Pull Request.

We appreciate all PRs — bug fixes, features, docs, examples, tests, and refactoring.


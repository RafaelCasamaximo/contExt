# ContExt `exp-qt`

PyQt6 rewrite of ContExt as a node-based image processing desktop application.

## Current MVP

- Startup splash screen with theme and language selection
- Persisted preferences for theme and locale
- Localized UI in `pt-BR` and `en`
- Directed graph editor built on `QGraphicsScene` / `QGraphicsView`
- Default `Source` and `Preview` nodes, plus add/remove support for `Blur` nodes
- Dark canvas with quad grid in the dark theme
- Drag-to-connect edges between ports
- Background graph execution with `QThreadPool`
- Lazy descendant invalidation with latest-generation-wins result handling
- Image loading and live preview updates

## Project Layout

```text
src/context/
├── app.py
├── core/
│   ├── nodes/
│   └── pipeline/
├── viewmodels/
└── views/
    ├── canvas/
    └── panels/
```

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
./.venv/bin/pip install -e .
./.venv/bin/python -m context
```

You can also launch the app with:

```bash
./.venv/bin/python main.py
```

## Tests

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Notes

- This branch replaces the previous DearPyGUI implementation with a new PyQt6 foundation.
- Packaging and release automation are intentionally out of scope for this MVP.

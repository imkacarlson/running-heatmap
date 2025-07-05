# Repository Guide for Agents

This project visualizes GPS activities as an interactive heatmap.
It has two parallel front-end implementations that must stay in sync:

1. **Web version** – files under `web/`.
2. **Mobile version** – template and scripts in `server/mobile_template.html` and `server/mobile_main.js`.

Whenever you change UI or behavior in one, mirror the change in the other.

Key features to understand:

- **Lasso/Selection tool** – draw a polygon and list intersecting activities. Runs can be toggled individually.
- **Upload capability** – GPX files added in the browser are parsed and stored locally.
- **Persist uploads** – uploaded runs remain after restarting the server or app.
- **PMTiles support** – optional vector tiles for smooth offline rendering.
- **Mobile packaging** – `build_mobile.py` creates an Android APK with all data bundled.

Project structure overview:

```
server/  – Flask backend plus build scripts
web/     – Web front‑end assets
```

When adding new features or modifying existing ones, follow these guidelines:

1. Update both web and mobile implementations if applicable.
2. Run the application locally (``flask run`` inside `server/`) to verify behavior.
3. After committing changes, review this `AGENTS.md`, `README.md`, and `MOBILE_SETUP.md` to ensure all instructions remain accurate, updating them if necessary.


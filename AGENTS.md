# Repository Guide for Agents

This project visualizes GPS activities as an interactive heatmap.
It has two parallel front-end implementations:

1. **Web version** – files under `web/`.
2. **Mobile version** – template and scripts in `server/mobile_template.html` and `server/mobile_main.js`.

Both versions provide similar features and must stay in sync. Whenever you change UI or behavior in one, mirror the change in the other.

Key features to understand:

- **Lasso/Selection tool**: Users draw a polygon on the map. Activities intersecting the area are listed in a sidebar. Each run can be toggled on or off to filter what is shown. Clearing the selection hides the sidebar and shows all runs again.
- **Upload capability**: Users may upload GPX files which are added to the dataset and shown on the map.
- **Offline/mobile app**: `build_mobile.py` packages the mobile version as an Android APK with runs bundled locally.

Project structure overview:

```
server/  – Flask backend and mobile build scripts
web/     – Web front-end assets
```

When adding new features or modifying existing ones, follow these guidelines:

1. Update both web and mobile implementations if applicable.
2. Run the application locally (``flask run`` inside `server/`) to verify behavior.
3. After committing changes, review this `AGENTS.md` and update it if the repository’s behavior or instructions change.


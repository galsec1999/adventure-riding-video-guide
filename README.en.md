# Community Adventure Riding Video Guide

An installable, bilingual Hebrew/English PWA with 450 curated riding tutorials, contextual filters, 17 learning paths, trip planning material, favourites and local progress.

Live site: <https://galsec1999.github.io/adventure-riding-video-guide/>

## Install

- Android Chrome: open the site, open the ⋮ menu and choose **Install app** or **Add to Home screen**.
- Desktop Chrome: use the install icon in the address bar or choose **Install** from the browser menu.
- iPhone/iPad: use **Share → Add to Home Screen**.

The library, filters and learning paths work offline after the first successful load. YouTube playback still requires internet access.

## Run locally

```powershell
python -m http.server 8080 --directory site
```

Open <http://localhost:8080/>. Service workers require `localhost` or HTTPS.

## Validate

```powershell
python -m pip install jsonschema==4.26.0
python tools/validate_pwa.py --site site --schema documentation/video.schema.json --expected-count 450
npm test
```

## Repository layout

- `site/` — the exact static artifact published by GitHub Pages.
- `site/data/` — the 450-record bilingual dataset and controlled taxonomies.
- `documentation/` — licences, schema, changelog and v2.2.1 source notes.
- `tools/validate_pwa.py` — CI release gate.
- `reports/` — QA evidence and deployment reports.

## Content updates and releases

Only add a video after verifying its source beyond the title. Do not invent metadata, timestamps or learning claims. Run all validation before pushing. A push to `main` validates and deploys `site/` through the official GitHub Pages workflow. Releases use semantic tags; the PWA release is `v2.3.0-pwa`.

## Rights and purpose

This is a non-profit community project. Original code is MIT licensed. Original summaries and classifications are shared under CC BY-NC-SA 4.0. YouTube videos, thumbnails, channel names and trademarks remain the property of their owners and are not covered by the project licences.

Feedback and removal requests: [Ilan.nachman@gmail.com](mailto:Ilan.nachman@gmail.com)

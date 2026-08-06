# Community Adventure Riding Video Guide — Document version 3.0.1 / גרסת מסמך 3.0.1

An installable Hebrew/English PWA with 411 active curated riding tutorials, 17 learning paths, a trip centre, contextual search and optional on-device semantic search. Product version: **3.0.0**.

Live site: <https://galsec1999.github.io/adventure-riding-video-guide/>

## What changed in 3.0.0

- Added 17 focused videos: 6 navigation, 7 protective gear and 4 intercoms; removed 56 unavailable or insufficiently evidenced records.
- Added basic and advanced filters, richer video cards, a prominent Like reminder and stronger curation disclaimers.
- Learning paths now open one at a time and show progress, the next step and viewing alternatives.
- The navigation centre now contains 10 comparisons, 6 knowledge guides, 7 checklists and 34 video references.
- Optional multilingual semantic search runs on the device with no AI API, key or backend. Regular search remains available at all times.
- The visit counter records live-site loads through Hits.sh; it is not a unique-user counter.
- Public credit shows “Ilan” only. Feedback and removal requests use GitHub without exposing a surname.

## Install

- Android Chrome: open the site, use the ⋮ menu, then choose **Install app** or **Add to Home screen**.
- Desktop Chrome: use the install icon in the address bar or choose **Install** from the browser menu.
- iPhone/iPad: use **Share → Add to Home Screen**.

After the first successful load, the library, regular search, filters, trips and learning paths work offline. YouTube playback and the local model's first download still require internet access.

## Run locally

```powershell
python -m http.server 8080 --directory site
```

Open <http://localhost:8080/>. Service workers require `localhost` or HTTPS.

## Build and validate

```powershell
node tools/build_semantic_index.mjs
python tools/build_standalone.py
python tools/verify_site_sync.py --write
python tools/validate_data.py --expected-count 411
python tools/validate_pwa.py --site site --schema documentation/video.schema.json --expected-count 411
python -m unittest discover -s tests -p "test_*.py"
npm test
node tools/search_acceptance.mjs
```

## Repository layout

- `site/` — the exact static artifact published by GitHub Pages.
- `data/` — 411 records, taxonomy, paths, trip data and the semantic index.
- `assets/` — UI, styles, Web Worker, Transformers.js and ONNX Runtime.
- `downloads/Adventure-Riding-Video-Guide-v3.0.0-Standalone.html` — a single-file edition with regular search and no semantic model.
- `documentation/` — specifications, licences, rights, third-party notices and release notes.
- `reports/site-upgrade-v3/` — release reports, checks and visual QA evidence.

## Content, rights and privacy

Never add a video from its title alone or invent metadata, timestamps or learning claims. The site is a curated index: it does not own the videos, endorse every claim or replace professional instruction, applicable law or the manufacturer's manual.

Original code is MIT licensed; original community text and classifications use CC BY-NC-SA 4.0. YouTube videos, thumbnails, channel names and trademarks remain the property of their owners. User state stays in the browser. See `documentation/THIRD_PARTY_NOTICES.md` for third-party components.

Feedback and removal requests: <https://github.com/galsec1999/adventure-riding-video-guide/issues/new>

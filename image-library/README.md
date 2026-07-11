# Image Library

This is the top-level image library for TungsAcu-DB figure assets.

## Layout

- `production/` - user-accepted or near-accepted image assets that may become formal bases.
- `extracted_images/` - images extracted from books or PDFs before manual review, including the review manifest used by the app.
- `marked-figures/` - manually marked acupuncture figures and the marker tool used to create them.
- `anatomy-sources/` - reusable anatomy source material, references, and license-tracked source images.
- `experiments/` - trial outputs, scripts, unstable batches, and generation attempts.
- `archive/` - old prototype batches or deprecated materials kept for provenance.
- `logo-seal.png` - app topbar seal logo.

## Rules

- Do not put unreviewed generated images in `production/`.
- Treat `extracted_images/` as review-stage working data; the folder is ignored by git unless explicitly forced.
- Do not move `data/images/` here unless the app code is updated at the same time; `data/images/` is still the app's formal runtime image directory.
- Keep generated trials in `experiments/` until a specific file is accepted.
- Archive older batches instead of deleting them when they may contain user edits or useful provenance.

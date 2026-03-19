# Dashboard Site

This project generates a static ecommerce dashboard from SQLite and publishes it as a GitHub Pages site.

## Files

- `build_v2.py`: generates `index.html`
- `index.html`: GitHub Pages entry file
- `dashboard.html`: older generated output kept for local reference

## Regenerate the site

```bash
python3 /Users/wmix/wmixclaude/build_v2.py
```

## Publish updates

After regenerating `index.html`, commit and push to GitHub:

```bash
git add .
git commit -m "update dashboard"
git push
```

## Notes

- The page is static, so GitHub Pages can host it directly.
- The dashboard uses Chart.js from jsDelivr, so viewers need external network access to that CDN.

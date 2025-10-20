# Static Export Plan (Next.js → GitHub Pages or any static host)

This plan generates a fully static site from the Next.js app in `web/`, including assets, and shows how to preview locally and deploy to GitHub Pages. Commands assume your shell is at `web/`.

## 1) Prerequisites
- **Node.js 18+** and **npm** available.
- Install deps:
```bash
npm ci
```

## 2) Configure Next.js for static export
Edit `web/next.config.ts` to enable static export and plain `<img>` tags for static hosts.
```ts
// web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",            // emits static files into web/out
  images: { unoptimized: true }, // make next/image output plain <img>
  // If deploying to a GitHub Project Page (https://<user>.github.io/<repo>/),
  // uncomment and set your repo name:
  // basePath: "/<repo>",
  // assetPrefix: "/<repo>/",
};

export default nextConfig;
```

## 3) Ensure all routes can be prerendered
- Avoid runtime-only server calls. File reads in Server Components (e.g., `@/lib/posts` reading `content/`) are OK at build time.
- Check routes in `web/app/` render without needing secrets or live servers.

## 4) Build the static site
```bash
# from web/
npm run build
# Output will be emitted to: web/out/
```

## 5) Preview the static export locally
Pick one option:
- Using `serve`:
```bash
# from web/
npx serve -s out -l 4173
# open http://localhost:4173
```
- Using Python (built-in on macOS):
```bash
# from web/out/
python3 -m http.server 4173
# open http://localhost:4173
```

## 6) Deploy to GitHub Pages (Project Page)
Recommended with GitHub Actions. Example workflow (place at `.github/workflows/pages.yml` in repo root):
```yaml
name: Deploy static site to GitHub Pages
on:
  push:
    branches: [ main ]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install deps
        working-directory: web
        run: npm ci
      - name: Build static site
        working-directory: web
        run: npm run build
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: web/out
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```
Additional steps:
- In repo settings → Pages, set **Build and deployment** to **GitHub Actions**.
- If using a Project Page, set `basePath` and `assetPrefix` in `next.config.ts` to `"/<repo>"`.

## 7) Optional: Serve static JSON instead of hardcoded constants
- Place JSON in `web/public/data/` (e.g., `featured.json`, `recent-tracks.json`).
- Fetch via `fetch("/data/featured.json")` in a Client Component, or read via `fs` at build time in a Server Component for static export.

## Quick checklist
- **Config updated**: `output: "export"`, `images.unoptimized: true`, optional `basePath`/`assetPrefix`.
- **Routes static**: `app/` pages don’t require runtime servers.
- **Build ok**: `npm run build` produces `web/out/`.
- **Preview ok**: local static server shows pages correctly.
- **Deployed**: GitHub Actions publishes `web/out/` to Pages.

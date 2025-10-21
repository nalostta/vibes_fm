# VIBES.FM System Architecture

## Repository Structure

- `web/`: Next.js 15 App Router project that contains all application code.
- `web/content/`: Markdown sources (JSON frontmatter + Markdown body) for mixes/posts that are baked into the static build.
- `web/public/`: Static assets served verbatim.
- Root-level docs (`README.md`, `Description.md`, `STATIC_EXPORT.md`) describe setup and deployment expectations.

## Application Shell

- `app/layout.tsx` defines the HTML scaffold, global fonts (Geist families), light/dark defaults, and composes the persistent `NavBar` and `Footer`.
- `app/globals.css` bootstraps Tailwind CSS v4 (via `@import "tailwindcss"`) and exposes CSS custom properties used across server and client components.
- The layout renders with `className="dark"` on `<html>`, so the site defaults to a dark theme while keeping light theme variables in CSS for future toggles.

## Routing Model

- Uses the Next.js App Router with file-system routes inside `app/`.
- Key routes:
  - `app/page.tsx`: Landing page combining featured mixes, marketing copy, newsletter form, and the animated `KoiBackground`.
  - `app/mixes/page.tsx`: Grid of demo mixes rendered via the reusable `MixCard` component.
  - `app/vibes/page.tsx` and `app/about/page.tsx`: Simple informational pages ready to be populated with real content.
  - `app/posts/[slug]/page.tsx`: Dynamic route for mix write-ups, tracklists, and embeds. Implements `generateStaticParams` and `dynamicParams = false` so every Markdown post is prerendered for static export.

## Content & Data Layer

- `lib/posts.ts` is a server-only utility that reads `.md` files from `content/posts`.
- Frontmatter is stored as JSON enclosed by `---` fences; `parseMarkdown` converts it into strongly typed `PostFrontmatter` objects.
- Helper `getAllPosts()` and `getPostBySlug()` provide sorted post data to server components at build time. There are no runtime network calls, so the app is static-host friendly.
- `getCoverFromEmbed()` infers YouTube thumbnail URLs when a cover is not provided, supporting richer cards without extra authoring work.

## Presentation Components

- `components/NavBar.tsx` and `components/Footer.tsx` supply the persistent chrome, using `usePathname()` client-side to highlight the active route.
- `components/MixCard.tsx` drives card layout for mixes/posts and embeds the `AudioPlayer`.
- `components/AudioPlayer.tsx` is a client component that manages playback state, speed control, and gracefully handles missing audio sources.
- `components/PostTile.tsx` provides a smaller card format for post listings (currently unused, but ready for blog indexes or sidebars).
- `components/KoiBackground.jsx` renders an animated canvas comet field, mounted client-side and layered behind main content with absolute positioning.

## Styling & Design System

- Tailwind CSS v4 powers utility classes; global CSS defines theme tokens and sets baseline fonts/colors.
- Component styling leans on Tailwind utilities combined with CSS variables for consistent dark-mode appearance.
- `next/font` configuration in `app/layout.tsx` preloads Geist fonts and attaches them as CSS variables consumed by Tailwind.

## Build & Deployment

- `next.config.ts` enables static export via `output: "export"` and configures `next/image` to emit plain `<img>` tags. Remote patterns allow YouTube and SoundCloud thumbnails during build.
- `STATIC_EXPORT.md` outlines the build pipeline (`npm run build` → `web/out`) and provides a GitHub Actions workflow for publishing to GitHub Pages.
- `package.json` scripts rely on Turbopack for `dev`/`build` while TypeScript + ESLint enforce modern linting/typing.
- The project currently ships placeholder demo data; replacing the Markdown content or wiring up a CMS/API can be done by swapping implementations inside `lib/posts.ts`.

## Operational Notes

- Because all data is resolved from the local filesystem during build, hosting on any static provider is supported without server runtime.
- Client components (`NavBar`, `AudioPlayer`, `KoiBackground`) are isolated; the rest of the tree remains server-rendered, keeping bundle sizes small.
- Adding new sections (e.g., a `/posts` index) can reuse existing primitives (`PostTile`, `getAllPosts`) without additional data plumbing.

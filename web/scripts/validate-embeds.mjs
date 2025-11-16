#!/usr/bin/env node
/**
 * Validate YouTube embeds in content/posts by calling YouTube oEmbed.
 * No API key required. Reports invalid/malformed URLs and suggestions.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const POSTS_DIR = join(process.cwd(), 'content', 'posts');

/** Extract the JSON frontmatter between first pair of --- lines */
function extractFrontmatterJSON(md) {
  const start = md.indexOf('---');
  if (start !== 0) return null;
  const end = md.indexOf('\n---', 3);
  if (end === -1) return null;
  const jsonBlock = md.slice(4, end).trim();
  try {
    return JSON.parse(jsonBlock);
  } catch (e) {
    return null;
  }
}

/** Normalize various YouTube embed forms to a canonical watch URL for oEmbed */
function toWatchUrl(maybeUrl) {
  try {
    const u = new URL(maybeUrl);
    // Fix common mistake: youtu.be/embed/<id> -> youtu.be/<id>
    if (u.hostname === 'youtu.be') {
      const parts = u.pathname.split('/').filter(Boolean);
      if (parts[0] === 'embed' && parts[1]) return `https://www.youtube.com/watch?v=${parts[1]}`;
      if (parts[0]) return `https://www.youtube.com/watch?v=${parts[0]}`;
    }
    // Handle /embed/watch?v=<id>
    if (u.hostname.includes('youtube.com')) {
      if (u.pathname.startsWith('/embed/watch')) {
        const id = u.searchParams.get('v');
        if (id) return `https://www.youtube.com/watch?v=${id}`;
      }
      // Handle /embed/<id>
      if (u.pathname.startsWith('/embed/')) {
        const id = u.pathname.split('/').pop();
        if (id) return `https://www.youtube.com/watch?v=${id}`;
      }
      // Already a watch URL
      if (u.pathname === '/watch' && u.searchParams.get('v')) {
        return `https://www.youtube.com/watch?v=${u.searchParams.get('v')}`;
      }
    }
    // Fallback: return as-is
    return maybeUrl;
  } catch {
    return maybeUrl;
  }
}

async function validate() {
  const files = readdirSync(POSTS_DIR).filter(f => f.endsWith('.md'));
  const results = [];
  for (const f of files) {
    const full = join(POSTS_DIR, f);
    const md = readFileSync(full, 'utf8');
    const fm = extractFrontmatterJSON(md);
    if (!fm) {
      results.push({ file: f, status: 'error', reason: 'Invalid or missing JSON frontmatter' });
      continue;
    }
    const embed = fm.embed;
    if (!embed || embed.type !== 'youtube' || !embed.url) {
      results.push({ file: f, status: 'skip', reason: 'No YouTube embed' });
      continue;
    }
    const watchUrl = toWatchUrl(embed.url);
    const oembed = `https://www.youtube.com/oembed?format=json&url=${encodeURIComponent(watchUrl)}`;
    try {
      const res = await fetch(oembed, { method: 'GET' });
      if (res.ok) {
        results.push({ file: f, status: 'ok', url: embed.url, normalized: watchUrl });
      } else {
        const text = await res.text();
        results.push({ file: f, status: 'invalid', url: embed.url, normalized: watchUrl, http: res.status, body: text.slice(0, 200) });
      }
    } catch (e) {
      results.push({ file: f, status: 'error', url: embed.url, normalized: watchUrl, reason: String(e).slice(0, 200) });
    }
  }

  // Pretty print report
  const ok = results.filter(r => r.status === 'ok');
  const invalid = results.filter(r => r.status === 'invalid');
  const errors = results.filter(r => r.status === 'error');
  const skipped = results.filter(r => r.status === 'skip');

  console.log('YouTube Embed Validation Report');
  console.log('================================');
  console.log(`OK: ${ok.length} | Invalid: ${invalid.length} | Errors: ${errors.length} | Skipped: ${skipped.length}`);
  const fmt = (r) => `- ${r.file}\n  url: ${r.url}\n  normalized: ${r.normalized}${r.http ? `\n  http: ${r.http}` : ''}${r.reason ? `\n  reason: ${r.reason}` : ''}${r.body ? `\n  body: ${r.body}` : ''}`;
  if (invalid.length) {
    console.log('\nInvalid:');
    for (const r of invalid) console.log(fmt(r));
  }
  if (errors.length) {
    console.log('\nErrors:');
    for (const r of errors) console.log(fmt(r));
  }
  if (ok.length) {
    console.log('\nOK:');
    for (const r of ok) console.log(`- ${r.file} -> ${r.normalized}`);
  }
  if (skipped.length) {
    console.log('\nSkipped:');
    for (const r of skipped) console.log(`- ${r.file} (${r.reason})`);
  }

  // Exit non-zero if any invalid
  if (invalid.length || errors.length) process.exitCode = 1;
}

validate();

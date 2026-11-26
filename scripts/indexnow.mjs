#!/usr/bin/env node
/**
 * Submit sitemap URLs to Bing/Yandex via IndexNow.
 *
 * Usage:
 *   DRY_RUN=1 node scripts/indexnow.mjs            # print URL count only
 *   node scripts/indexnow.mjs                      # submit every sitemap URL
 *   node scripts/indexnow.mjs <url> [<url> ...]    # submit specific URLs
 */
import fs from 'node:fs';
import path from 'node:path';

const HOST = process.env.SITE_HOST || 'tanhdev.com';
const SITE = `https://${HOST}`;
const ENDPOINT = 'https://api.indexnow.org/indexnow';
const BATCH = 10000;

function findKey() {
  if (process.env.INDEXNOW_KEY) return process.env.INDEXNOW_KEY;
  const dir = path.join(process.cwd(), 'static');
  const keys = [];
  for (const f of fs.readdirSync(dir)) {
    const m = /^([0-9a-f]{16,64})\.txt$/i.exec(f);
    if (m && fs.readFileSync(path.join(dir, f), 'utf8').trim() === m[1]) keys.push(m[1]);
  }
  if (keys.length !== 1) {
    throw new Error(`Expected 1 IndexNow key file in static/, found ${keys.length}`);
  }
  return keys[0];
}

async function fetchText(url) {
  const res = await fetch(url, { headers: { 'user-agent': 'tanhdev-indexnow/1.0' } });
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`);
  return res.text();
}

const locs = (xml) => [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)].map((m) => m[1]);

async function sitemapUrls() {
  const xml = await fetchText(`${SITE}/sitemap.xml`);
  if (xml.includes('<sitemapindex')) {
    const urls = new Set();
    for (const child of locs(xml)) {
      for (const u of locs(await fetchText(child))) urls.add(u);
    }
    return [...urls];
  }
  return [...new Set(locs(xml))];
}

const key = findKey();
const args = process.argv.slice(2);
const urls = (args.length ? args : await sitemapUrls()).filter((u) => new URL(u).host === HOST);

console.log(`[indexnow] host=${HOST} key=${key} urls=${urls.length}`);
if (process.env.DRY_RUN) process.exit(0);

for (let i = 0; i < urls.length; i += BATCH) {
  const chunk = urls.slice(i, i + BATCH);
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ host: HOST, key, keyLocation: `${SITE}/${key}.txt`, urlList: chunk }),
  });
  console.log(`[indexnow] batch ${i / BATCH + 1}: ${chunk.length} urls -> HTTP ${res.status}`);
  if (![200, 202].includes(res.status)) {
    console.error(await res.text());
    process.exit(1);
  }
}

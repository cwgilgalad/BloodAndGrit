#!/usr/bin/env node
// ============================================================ MAPDIFF
// Render the lab's SVGs to PNG and say which of them MOVED since the last run.
//
// The city-ward session was the argument for this. Every fault in it was found by rendering a map
// and looking at it, which is this repo's own standard for anything drawn — but "looking at it" is
// also how a regression walks past you. Two of three hypotheses about the ward were wrong, and the
// one real regression (the cartouche keep-out that a ward's blocked.Clear() threw away) survived a
// full smoke run, an audit_ui run and a human read of the source. It was visible in a single frame.
//
//   node tools/mapdiff.mjs shot   [dir]   render every .svg in dir to .png beside it
//   node tools/mapdiff.mjs base   [dir]   keep the current PNGs as the baseline to compare against
//   node tools/mapdiff.mjs diff   [dir]   render, then report changed pixels per file vs baseline
//
// Default dir is _combatlab/_maps. Baselines live in <dir>/_base and are gitignored with the lab.
//
// A number here is a fact, not a verdict: a deliberate fix moves pixels too. What the number buys
// is knowing WHICH sheets moved, so the two that should not have can be looked at rather than the
// twelve that were expected to.
import { readdirSync, mkdirSync, existsSync, copyFileSync, readFileSync, writeFileSync } from 'node:fs'
import { join, basename } from 'node:path'
import { createRequire } from 'node:module'

// The three packages are installed GLOBALLY (npm i -g @resvg/resvg-js-cli pixelmatch pngjs) so this
// repo stays dependency-free — it has no package.json and should not grow one for a dev tool. resvg
// ships its native binding nested under the CLI rather than at the global root, so both roots are
// tried before giving up with the command that fixes it.
const GLOBAL = process.env.NPM_GLOBAL_ROOT
  || join(process.env.APPDATA || process.env.HOME || '', 'npm', 'node_modules')
const ROOTS = [GLOBAL, join(GLOBAL, '@resvg', 'resvg-js-cli', 'node_modules')]

function need (name) {
  for (const root of ROOTS) {
    try { return createRequire(join(root, 'x.js'))(name) } catch { /* try the next root */ }
  }
  console.error(`missing ${name}. Install the tools with:\n`
    + '  npm install -g @resvg/resvg-js-cli pixelmatch pngjs')
  process.exit(3)
}

const { Resvg } = need('@resvg/resvg-js')
const { PNG } = need('pngjs')
const pmMod = need('pixelmatch')
const pixelmatch = pmMod.default ?? pmMod

const mode = process.argv[2] ?? 'diff'
const dir = process.argv[3] ?? '_combatlab/_maps'
const baseDir = join(dir, '_base')

const svgs = readdirSync(dir).filter(f => f.endsWith('.svg')).sort()
if (svgs.length === 0) { console.error(`no .svg in ${dir}`); process.exit(1) }

function render (svg) {
  const out = join(dir, basename(svg, '.svg') + '.png')
  const r = new Resvg(readFileSync(join(dir, svg), 'utf8'), { fitTo: { mode: 'width', value: 1000 } })
  writeFileSync(out, r.render().asPng())
  return out
}

if (mode === 'shot' || mode === 'diff') for (const s of svgs) render(s)

if (mode === 'base') {
  mkdirSync(baseDir, { recursive: true })
  let n = 0
  for (const s of svgs) {
    const png = join(dir, basename(s, '.svg') + '.png')
    if (existsSync(png)) { copyFileSync(png, join(baseDir, basename(png))); n++ }
  }
  console.log(`baseline kept: ${n} sheet${n === 1 ? '' : 's'} in ${baseDir}`)
  process.exit(0)
}

if (mode === 'shot') { console.log(`rendered ${svgs.length} sheet(s) -> ${dir}`); process.exit(0) }

// ---- diff ----
if (!existsSync(baseDir)) {
  console.error(`no baseline in ${baseDir} — run:  node tools/mapdiff.mjs base ${dir}`)
  process.exit(2)
}
let moved = 0, missing = 0
for (const s of svgs) {
  const name = basename(s, '.svg') + '.png'
  const nowPath = join(dir, name), oldPath = join(baseDir, name)
  if (!existsSync(oldPath)) { console.log(`  ${name.padEnd(34)} NEW — no baseline`); missing++; continue }
  const a = PNG.sync.read(readFileSync(oldPath))
  const b = PNG.sync.read(readFileSync(nowPath))
  if (a.width !== b.width || a.height !== b.height) {
    console.log(`  ${name.padEnd(34)} SIZE CHANGED ${a.width}x${a.height} -> ${b.width}x${b.height}`)
    moved++; continue
  }
  const out = new PNG({ width: a.width, height: a.height })
  // threshold 0, not the library's usual 0.1. The same renderer over the same deterministic vector
  // input has no antialiasing noise to forgive, so anything above exact equality is a real change —
  // and a tolerant threshold silently passed a one-unit shift in WaterEdge when this was tested,
  // which is precisely the class of drift the tool exists to catch.
  const px = pixelmatch(a.data, b.data, out.data, a.width, a.height, { threshold: 0 })
  const pct = (px / (a.width * a.height) * 100)
  if (px > 0) {
    writeFileSync(join(dir, basename(s, '.svg') + '.diff.png'), PNG.sync.write(out))
    moved++
  }
  console.log(`  ${name.padEnd(34)} ${px === 0 ? 'unchanged' : `${px} px moved (${pct.toFixed(2)}%)  -> ${basename(s, '.svg')}.diff.png`}`)
}
console.log(`\n${svgs.length} sheet(s): ${moved} moved, ${missing} new, ${svgs.length - moved - missing} unchanged`)

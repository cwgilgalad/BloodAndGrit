#!/usr/bin/env python3
"""Build the self-contained Player's Book.

The Player's Book source lives in SRC below -- edit it right here, the same
way the Keeper's Book and the Bestiary live in their own builders. The build
drops the Perdition Basin player map into Appendix E, grows the detailed
two-level Contents, inlines any `assets/imgNN.ext` referenced in the source
as a base64 data URI, and writes blood-and-grit.html. Idempotent: rebuilding
yields byte-identical output.

(measure_index.py patches the static index/TOC page numbers directly into the
SRC string below after rendering -- do not hand-edit those numbers.)
"""
import base64, mimetypes, os, re, sys

from nav_tools import add_detailed_toc
from perdition_map import player_map_html

OUT = "blood-and-grit.html"

# ---------------------------------------------------------------------------
# The Player's Book, cover to colophon. Edit here.
# ---------------------------------------------------------------------------
SRC = r"""<!DOCTYPE html>
<!-- Blood & Grit — The Player's Book · Version 2.41 -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v2.41)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Playfair+Display:wght@400;700;900&family=Rye&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#e7d8ab; --paper-d:#dccb97; --paper-l:#f2e8c6;
    --ink:#2b2118; --ink-soft:#4a3c2c;
    --blood:#8b1a1a; --blood-d:#6c1212;
    --gold:#9c7a3c; --gold-d:#7d5f2a;
    --rule:#c9b78a;
    --shade:#3a2616;
    --row-a:#ece1ba; --row-b:#e3d4a4;
    --western:'Rye','Iowan Old Style',Georgia,serif;
    --display:'Playfair Display','Iowan Old Style',Georgia,serif;
    --body:'EB Garamond','Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth; -webkit-text-size-adjust:100%; text-size-adjust:100%;}
  body{
    margin:0; color:var(--ink);
    background:#241a10;
    font-family:var(--body);
    font-size:19px; line-height:1.58;
  }
  .book{max-width:880px; margin:0 auto; padding:0 14px;}
  .page{
    background-color:var(--paper);
    background-image:
      radial-gradient(125% 120% at 50% 48%, rgba(0,0,0,0) 58%, rgba(74,48,18,.17) 100%);
    background-size:100% 100%;
    background-repeat:no-repeat;
    border:2px solid var(--blood-d);
    box-shadow:0 0 0 4px var(--paper) inset, 0 14px 40px rgba(0,0,0,.5);
    margin:28px 0; padding:54px 56px 64px;
    position:relative;
  }
  .page::before{
    content:""; position:absolute; inset:9px;
    border:1px solid var(--gold-d); opacity:.55; pointer-events:none;
  }
  /* corner diamonds */
  .page::after{
    content:"◆ ◆"; position:absolute; top:-2px; left:0; right:0;
    text-align:center; color:var(--blood-d); font-size:11px; letter-spacing:840px;
    display:none;
  }
  .runhead{
    display:flex; justify-content:space-between; align-items:center;
    font-variant:small-caps; letter-spacing:.12em; font-size:12px;
    color:var(--blood-d); font-weight:700; margin-bottom:30px;
  }
  .runhead .l{font-style:italic; font-weight:600; color:var(--ink-soft);}
  h1.chapter{
    font-family:var(--western);
    font-weight:400; color:var(--blood); font-size:37px; line-height:1.08;
    margin:.1em 0 .18em; letter-spacing:.005em;
  }
  .chapter-sub{font-style:italic; color:var(--ink-soft); font-size:19px; margin:0 0 6px;}
  h2{font-family:var(--display); color:var(--shade); font-weight:700; font-size:26px; margin:1.5em 0 .35em; letter-spacing:.005em;}
  h3{font-family:var(--display); color:var(--blood-d); font-weight:700; font-size:20px; margin:1.3em 0 .25em;}
  h4{font-style:italic; color:var(--ink); font-weight:700; font-size:18px; margin:1.1em 0 .15em;}
  p{margin:.55em 0;}
  .lead{margin-top:.2em;}
  .dropcap::first-letter{
    float:left; font-family:var(--western); font-weight:400; color:var(--blood);
    font-size:54px; line-height:.86; padding:8px 12px 0 2px;
  }
  .divider{ text-align:center; color:var(--gold-d); margin:14px 0 22px; }
  .divider::before{content:"—————————  ◆  —————————"; letter-spacing:.04em; font-size:13px; color:var(--gold-d);}
  ul{margin:.4em 0 .7em; padding-left:1.25em;}
  ul li{margin:.32em 0;}
  ul.dash{list-style:none; padding-left:1.1em;}
  ul.dash>li{position:relative;}
  ul.dash>li::before{content:"—"; position:absolute; left:-1.15em; color:var(--blood-d);}
  strong{color:var(--ink); font-weight:800;}
  em{color:var(--ink-soft);}
  a{color:var(--blood-d); text-decoration:none; border-bottom:1px dotted var(--gold-d);}

  /* tables */
  table{width:100%; border-collapse:collapse; margin:.9em 0 1.1em; font-size:16.5px;}
  thead th{background:var(--shade); color:var(--paper-l); text-align:left; padding:8px 12px; font-family:var(--display); font-weight:700; letter-spacing:.02em; font-size:14.5px;}
  tbody td{padding:7px 12px; vertical-align:top; border-bottom:1px solid rgba(120,90,50,.18);}
  tbody tr:nth-child(odd){background:var(--row-a);}
  tbody tr:nth-child(even){background:var(--row-b);}
  td.c,th.c{text-align:center;}
  .lvl td:first-child{font-weight:700; text-align:center;}

  /* boxes */
  .box{
    background:var(--paper-l);
    border-left:5px solid var(--blood);
    box-shadow:1px 1px 0 rgba(120,90,50,.25);
    padding:14px 18px; margin:1.2em 0; border-radius:2px;
  }
  .box h3, .box h4{margin-top:0;}
  .box.gold{border-left-color:var(--gold-d);}
  .equation{
    text-align:center; background:var(--paper-l); border-left:5px solid var(--blood);
    padding:14px 18px; margin:1.1em 0;
  }
  .equation .k{font-variant:small-caps; letter-spacing:.14em; color:var(--blood-d); font-weight:700; font-size:13px; display:block; margin-bottom:4px;}
  .equation .e{font-family:var(--display); font-weight:700; font-size:21px; color:var(--shade);}

  /* quotes (these replace the original sketches) */
  .quote{
    margin:1.4em auto; max-width:560px; text-align:center; font-style:italic;
    color:var(--ink-soft); font-size:19px; line-height:1.5;
    padding:18px 0; position:relative;
  }
  .quote::before, .quote::after{
    content:"❧"; display:block; color:var(--gold-d); font-style:normal; font-size:16px; opacity:.8;
  }
  .quote .src{display:block; margin-top:.7em; font-size:14.5px; font-style:italic; color:var(--gold-d); font-variant:small-caps; letter-spacing:.06em;}

  /* field-journal illustration plates (reintroduced) */
  .plate{ margin:1.5em auto 1.6em; max-width:560px; }
  .plate img{ width:100%; height:auto; aspect-ratio:1120 / 611; display:block;
    border:2px solid var(--blood-d); box-shadow:0 8px 22px rgba(0,0,0,.42);
    background:var(--paper-l); }
  .plate figcaption{ margin-top:.55em; text-align:center; font-style:italic;
    font-size:14px; color:var(--gold-d); font-variant:small-caps; letter-spacing:.05em; }
  @media print{ .plate img{ box-shadow:none; } }

  .narr{ margin:16px 26px; font-style:italic; color:var(--ink-soft); line-height:1.55; }
  .narr::before{ content:"~"; display:block; text-align:center; font-style:normal; color:var(--rule); margin-bottom:6px; }
  .sb-cont{ font-style:italic; font-weight:400; color:var(--ink-soft); font-size:12px; letter-spacing:0; }
  .statline{font-style:italic; color:var(--ink-soft); margin:.1em 0 .6em; font-size:16.5px;}
  .perk{
    border-top:1px solid var(--gold-d); border-bottom:1px solid var(--gold-d);
    background:var(--paper-l); padding:.5em 14px; margin:1em 0; break-inside:avoid;
  }
  .perk .lbl{
    font-variant:small-caps; letter-spacing:.1em; font-weight:700; color:var(--blood-d);
    margin-right:.5em;
  }
  .perk .nm{font-weight:700;}
  /* The fight ledger: what a Calling is for in a round, and what it pays to be that. Quieter than
     the Perk band on purpose -- the Perk sells the Calling, this one tells the truth about it. */
  .fight{
    display:flex; gap:0; flex-wrap:wrap; margin:.6em 0 1.1em; break-inside:avoid;
    border-left:3px solid var(--blood-d); background:rgba(0,0,0,.02);
  }
  .fight > div{flex:1 1 260px; padding:.45em 14px; font-size:15px;}
  .fight .k{
    font-variant:small-caps; letter-spacing:.09em; font-weight:700; color:var(--blood-d);
    margin-right:.45em;
  }
  .fight .pays .k{color:var(--ink-soft);}
  @media (max-width:520px){ .fight > div{flex:1 1 100%;} }
  .pageno{text-align:center; color:var(--blood-d); font-size:13px; margin-top:24px; letter-spacing:.3em;}

  /* contents */
  .toc{list-style:none; padding:0; margin:0.1em 0; font-size:15px;}
  .toc li{display:flex; align-items:baseline; padding:0 0 1px; border-bottom:1px dotted var(--gold-d); font-weight:700; color:var(--blood-d);}
  .toc li a{flex:1; border:none; color:var(--blood-d);}
  .toc li .pg{color:var(--ink-soft); font-weight:700;}

  /* detailed contents (two-level, splittable across pages) */
  .toc2{list-style:none; padding:0; margin:.1em 0;}
  .toc2 li{display:flex; align-items:baseline; gap:8px; border-bottom:1px dotted var(--gold-d); break-inside:avoid;}
  .toc2 li:not(.ch) , .ix li:not(.ix-hd){cursor:pointer;}
  .toc2 li.ch{cursor:pointer;}
  .toc2 li a{flex:1; border:none;}
  .toc2 li .pg{color:var(--ink-soft); font-weight:700;}
  .toc2 li.ch{padding:.5em 0 2px; font-weight:700; color:var(--blood-d); font-size:15px; break-after:avoid;}
  .toc2 li.ch:first-child{padding-top:0;}
  .toc2 li.ch a{color:var(--blood-d);}
  .toc2 li.sub{padding:1px 0 2px 20px; font-size:12.5px;}
  .toc2 li.sub a{color:var(--ink); font-weight:600;}
  .toc2 li.sub .pg{font-weight:600;}

  /* maps */
  .map{margin:16px 0 10px; text-align:center; break-inside:avoid;}
  .map svg{width:100%; height:auto; display:block; border:1px solid var(--gold-d);
    box-shadow:0 4px 14px rgba(0,0,0,.22);}
  .map figcaption{font-style:italic; color:var(--ink-soft); font-size:13px; margin-top:7px; padding:0 8px;}
  .hook{font-family:var(--display); font-weight:700; color:var(--gold-d); font-variant:small-caps; letter-spacing:.03em;}

  /* index */
  .ix{list-style:none; padding:0; margin:.1em 0; font-size:13px; columns:2; column-gap:30px;}
  .ix li{display:flex; align-items:baseline; gap:8px; padding:1px 0 2px; border-bottom:1px dotted var(--gold-d); break-inside:avoid;}
  .ix li a{flex:1; border:none; color:var(--ink); font-weight:600;}
  .ix li .pg{color:var(--ink-soft); font-weight:700;}
  .ix li.ix-hd{display:block; border-bottom:none; font-family:var(--display); font-weight:700; font-size:16px; color:var(--blood-d); margin-top:.55em; break-after:avoid;}

  /* title page */
  .title-page{min-height:auto; text-align:center; padding-top:90px; padding-bottom:90px; container-type:inline-size; display:flex; flex-direction:column; align-items:center;}
  .kicker{font-variant:small-caps; letter-spacing:.28em; color:var(--gold-d); font-weight:700; font-size:15px;}
  .big-title{position:relative; display:block; font-family:var(--western); font-weight:400; color:#f3ecd8; -webkit-text-stroke:0; line-height:1; white-space:nowrap; margin:14px 0 6px; font-size:88px; font-size:min(96px,13cqw);}
  .big-title .words{display:inline-flex; align-items:center; justify-content:center; letter-spacing:-.01em;}
  .big-title .w{position:relative; z-index:2; line-height:1; text-shadow:0 2px 0 var(--blood-d), 0 0 30px rgba(0,0,0,.4);}
  .big-title .amp{position:relative; z-index:1; font-size:1.75em; line-height:1; opacity:.5; margin:0 -.28em; pointer-events:none; text-shadow:none;}
  .title-page{background:#2a1c10; border-color:var(--gold-d); box-shadow:0 0 0 4px #2a1c10 inset,0 14px 40px rgba(0,0,0,.6);}
  .title-page::before{border-color:var(--gold);}
  .title-page .kicker{color:var(--gold);}
  .title-page .big-title{color:#f1e9d2;}
  .title-page .t-sub{font-variant:small-caps; letter-spacing:.20em; font-weight:700; font-style:normal; color:#cdb98a; font-size:24px;}
  .title-page .t-foot{font-variant:small-caps; letter-spacing:.14em; color:#e7dcc0; font-weight:700; margin-top:60px; font-size:18px;}
  .title-page .t-tiny{color:var(--gold); font-style:italic; font-size:14px; margin-top:4px;}
  .title-rule{color:var(--gold); margin:24px 0; font-size:14px;}
  .cover-emblem{width:376px; max-width:70%; margin:auto; display:block;}
  .cover-emblem svg{width:100%; height:auto; display:block; overflow:visible;}

  .note{font-size:15px; color:var(--ink-soft); font-style:italic;}
  hr.soft{border:none; border-top:1px solid var(--gold-d); opacity:.5; margin:1.6em 0;}
  .twocol{columns:2; column-gap:34px;}
  @media (max-width:680px){
    .page{padding:34px 22px 44px;} .twocol{columns:1;}
    h1.chapter{font-size:27px;}
  }
  /* The Ledger — character sheet */
  .sheet-row{display:flex; gap:10px; margin:10px 0; flex-wrap:wrap;}
  .field{flex:1 1 120px; border:1px solid var(--rule); background:rgba(255,255,255,.25); border-radius:3px; padding:6px 8px; min-width:90px;}
  .field.grow{flex:2 1 200px;}
  .field label, .abil label, .sheet-col h4{display:block; font-family:var(--display); font-variant:small-caps; letter-spacing:.04em; font-weight:bold; color:var(--oxblood); font-size:12px; margin-bottom:3px;}
  .blank{height:22px;}
  .bigblank{border:1px solid var(--rule); background:rgba(255,255,255,.25); border-radius:3px; height:150px; margin-bottom:12px;}
  .bigblank.short{height:90px;}
  .abilities .abil{flex:1 1 90px; border:1px solid var(--rule); background:rgba(255,255,255,.25); border-radius:3px; padding:5px 6px; text-align:center;}
  .ab-grid{display:flex; justify-content:space-around; font-size:10px; color:#6a5a44; border-top:1px dashed var(--rule); margin-top:4px; padding-top:14px;}
  .mark-row{align-items:center; gap:8px;}
  .mark-label{font-variant:small-caps; font-weight:bold; color:var(--oxblood); letter-spacing:.04em; margin-right:6px;}
  .mark-box{display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border:1px solid var(--oxblood); border-radius:3px; font-size:12px; color:#6a5a44;}
  .mark-box.lost{border-color:#7a1f1f; box-shadow:inset 0 0 0 2px rgba(122,31,31,.25);}
  .sheet-cols{display:flex; gap:14px; margin-top:12px; flex-wrap:wrap;}
  .sheet-col{flex:1 1 240px;}
  .skill-list{list-style:none; margin:0; padding:0; columns:1;}
  .skill-list li{display:flex; align-items:center; gap:8px; padding:3px 0; font-size:13px; border-bottom:1px dotted var(--rule);}
  .tick{display:inline-block; width:14px; height:14px; border:1px solid var(--rule); border-radius:2px; flex:0 0 auto;}
  @media print{
    body{background:#fff;} .page{box-shadow:none; margin:0; border-color:#7a1f1f;}
  }

/* ============================================================
   PDF-STYLE PAGINATION
   Render every page section as a discrete US-Letter
   (8.5in x 11in) sheet, separated like pages in a PDF viewer.
   ============================================================ */
body{ background:#525659; }
.book{ max-width:none; margin:0; padding:40px 16px 64px; }
.page{
  width:8.5in;
  min-height:11in;
  box-sizing:border-box;
  margin:0 auto 26px;
  padding:0.7in 0.72in 0.82in;
  position:relative;
  box-shadow:0 6px 20px rgba(0,0,0,.55), 0 2px 5px rgba(0,0,0,.40);
}
.page::before{ inset:0.16in; }
.pageno{
  position:absolute;
  left:0; right:0; bottom:0.34in;
  margin:0;
}
@media (max-width:900px){
  .book{ padding:16px 0 36px; }
  .page{
    width:94vw;
    min-height:calc(94vw * 1.2941);
    padding:4.6vw 4.7vw 5.4vw;
    margin:0 auto 16px;
  }
  .page::before{ inset:1vw; }
  .pageno{ bottom:2.3vw; }
}
@media print{
  @page{ size:Letter; margin:0; }
  html,body{ background:#fff; }
  .book{ max-width:none; margin:0; padding:0; }
  .page{
    width:8.5in; min-height:11in; margin:0;
    box-shadow:none;
    break-after:page; page-break-after:always;
    -webkit-print-color-adjust:exact; print-color-adjust:exact;
  }
  .page:last-child{ break-after:auto; page-break-after:auto; }
}

/* fixed-height sheets produced by the paginator */
.page.sheet{ height:11in; min-height:11in; overflow:hidden; }
/* screen-only shrink-to-fit: scale the whole fixed page down to the viewport
   without reflowing it, so page breaks/margins stay identical to print */
.book.pages > .page.sheet{ zoom:var(--book-zoom,1); }
/* Sheets are always a fixed 8.5in and only ever scaled (never reflowed), so
   their internal layout must not respond to viewport breakpoints — otherwise the
   paginator would measure different heights on phones vs desktop and the page
   breaks would drift. Pin sheet content to the full-size desktop typography. */
.book.pages .twocol{ columns:2; }
.book.pages h1.chapter{ font-size:37px; }
.sheet-body{ width:100%; }
/* perf: skip rendering off-screen pages once pagination has finished measuring */
.book.pages.ready > .page.sheet{ content-visibility:auto; contain-intrinsic-size:852px 1056px; }
@media print{ .book.pages.ready > .page.sheet{ content-visibility:visible; zoom:1 !important; } }
@media (max-width:900px){
  .page.sheet{ width:8.5in; height:11in; min-height:11in; padding:0.7in 0.72in 0.82in; }
  .page.sheet::before{ inset:0.16in; }
  .page.sheet .pageno{ left:0; right:0; bottom:0.34in; }
}
</style>
</head>
<body>
<div class="book">

<!-- ===================== TITLE ===================== -->
<section class="page title-page">
  <div class="kicker">Being a Field Manual for the Living</div>
  <div class="title-rule">———————  ◆  ———————</div>
  <div class="big-title">
    <span class="words"><span class="w">BLOOD</span><span class="amp" aria-hidden="true">&amp;</span><span class="w">GRIT</span></span>
  </div>
  <div class="t-sub">A Roleplaying Game of the Haunted Frontier</div>
  <div class="title-rule">———————  ◆  ———————</div>
  <div class="t-foot">The Player's Book</div>
  <div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · Version 2.41</div>
  <div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique rules &amp; systems of its own</div>

  <div class="cover-emblem" role="img" aria-label="A longhorn steer skull mounted over crossed lever rifles, in gold"><img src="assets/img20.png" alt="" style="width:100%; height:auto; display:block;" decoding="async"></div>
</section>

<!-- ===================== EPIGRAPH ===================== -->
<section class="page">
  <div class="quote" style="margin-top:120px;">
    "We came west to be made new, and found instead that the country was older
    than newness, older than God, and had been waiting a long while in the quiet for company."
    <span class="src">— from the burned journal of Eliza Hart, Surveyor</span>
  </div>
  <div class="quote" style="margin-top:90px;">
    "Keep your powder dry, your salt close, and your accounts with the dark paid up.
    The country settles every debt in the end."
    <span class="src">— a saying common to the trail, author unknown</span>
  </div>
  <div class="divider" style="margin-top:130px;"></div>
  <p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player's Book · Version 2.41 · First Complete Edition</p>
</section>

<!-- ===================== CONTENTS ===================== -->
<section class="page" id="contents">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>Contents</span></div>
  <h1 class="chapter">Contents</h1>
  <p class="chapter-sub">What you will find in this book, and the order of it.</p>
  <div class="divider"></div>
  <p class="note">This is the Player's Book. It holds everything a soul needs to make a character
  and keep them breathing — the dice, the callings, the guns, and the rules of fear. Secrets
  meant for the one who runs the game are kept elsewhere, in the Keeper's Book, and are no business of yours.</p>
  <ul class="toc">
    <li><a href="#country">I. The Country</a><span class="pg">8</span></li>
    <li><a href="#played">II. How the Game Is Played</a><span class="pg">11</span></li>
    <li><a href="#character">III. Making a Character</a><span class="pg">17</span></li>
    <li><a href="#origins">IV. Origins &amp; the Peoples of the Frontier</a><span class="pg">25</span></li>
    <li><a href="#callings">V. Worldly Callings</a><span class="pg">40</span></li>
    <li><a href="#faith">VI. Callings of Faith</a><span class="pg">76</span></li>
    <li><a href="#hexer">VII. Callings of the Old Dark</a><span class="pg">115</span></li>
    <li><a href="#skills">VIII. Skills</a><span class="pg">137</span></li>
    <li><a href="#edges">IX. Edges</a><span class="pg">142</span></li>
    <li><a href="#goods">X. Goods &amp; Provisions</a><span class="pg">148</span></li>
    <li><a href="#conflict">XI. Conflict &amp; the Iron Code</a><span class="pg">171</span></li>
    <li><a href="#nerve">XII. Nerve &amp; the Uncanny</a><span class="pg">181</span></li>
    <li><a href="#signs">XIII. Signs, Miracles &amp; Old Rites</a><span class="pg">191</span></li>
    <li><a href="#advancement">XIV. Advancement</a><span class="pg">207</span></li>
    <li><a href="#play">A. Appendix: An Example of Play</a><span class="pg">210</span></li>
    <li><a href="#conditions">B. Appendix: Conditions</a><span class="pg">212</span></li>
    <li><a href="#quickref">C. Appendix: Quick Reference</a><span class="pg">214</span></li>
    <li><a href="#posse">D. Appendix: A Posse, Ready-Made</a><span class="pg">216</span></li>
    <li><a href="#basin">E. Appendix: The Country &mdash; Perdition Basin</a><span class="pg">221</span></li>
    <li><a href="#ledger">The Ledger</a><span class="pg">224</span></li>
    <li><a href="#index">Index</a><span class="pg">226</span></li>
  </ul>
</section>

<!-- ===================== I. THE COUNTRY ===================== -->
<section class="page" id="country">
  <div class="runhead"><span class="l">I. The Country</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">I. The Country</h1>
  <p class="chapter-sub">What manner of world this is, and what waits beneath it.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Come west. The handbills say it plain: land for the breaking, silver for the digging,
  cattle for the driving, and room — room past counting, under a sky so wide it makes a man feel newly
  made. This is a game of that country and the people who dare it: drovers and widows, deserters and
  physicians, gun-hands and gamblers, ordinary souls out of money, out of luck, or out of options,
  riding into the biggest country there is to win something back from it.</p>
  <p><em>Blood and Grit</em> is a game of the American West — the mud and the marrow of it true to life,
  the weather honest, the work brutal, the coffee worse. You will keep your powder dry and your horse
  fed. You will learn what a winter costs, and what a bank costs, and which of the two is the more
  honest robbery. And now and again, at the far edge of the firelight, you may notice — as the people
  of that country have noticed for a very long time — that the silence out on the long grass is not
  quite the silence of empty land.</p>

  <h2>The Look of the World</h2>
  <p>Day is for labor and for travel — long, hot, dangerous, and mostly mundane. Men die of infected
  scratches and bad water far more often than of anything stranger. The work is cattle and rail and
  rock, the pay is thin, and the law is wherever the nearest honest man happens to be standing.</p>
  <p>But the Territories are a patchwork of failing things. Cattle towns swollen on credit and gone to rot
  when the railroad chose another valley. Mining camps that dug too deep and woke too much. Missions
  where the bells still ring at dusk though no hand pulls the rope. Homesteads sunk to their windowsills
  in dust, the families inside listening to something walk the roof at night and telling the children
  it is only the wind. The sun goes down early behind the ranges, and the nights are very long, and it
  is in the night that the country remembers itself.</p>
  <h3 id="ix-1885">When This Is — the Year of 1885</h3>
  <p>The default frame is the mid-1880s, a closing door of a decade. The great buffalo herds are all
  but slaughtered off; the open range is being strung with wire; the railroads have stitched the
  continent and unstitched a hundred ways of living. The Indian Wars are mostly behind, their ending
  bitter — the nations of the Plains and the desert forced onto reservations whose borders shrink each
  treaty. Geronimo is still at large in the Sierra Madre; he will surrender the next year. The country
  is being made <em>modern</em>, and modernity here means barbed wire, the company store, the boarding
  school, and the surveyor's chain. Set your stories against this, and the horror beneath will have
  something true to grow from.</p>

  <h2 id="ix-truths">The Three Truths</h2>
  <p>And here, before you go a page further, the truth the handbills leave out. They will tell you the
  frontier is empty. They are wrong, and the wrongness of it is the whole of this game. Something already
  holds the land between the last church and the first ocean. Call the country <em>occupied</em>, and know
  that the tenants were here a long while before the surveyors. The horror of this game is
  not that monsters exist. The horror is that the world was never arranged for your comfort, and has
  only now begun to show you so. Everything in this book grows from three plain ideas. Hold them in
  mind and the rest will follow.</p>
  <ul class="dash">
    <li><strong>Knowing costs.</strong> The more you understand of what moves beneath the dust, the more it understands of you. Wisdom in this country is a wound that does not close.</li>
    <li><strong>Survival is the victory.</strong> There is no saving the world here, no chosen one, no last battle that sets things right. There is only the next winter, the next town, the next morning you wake up still yourself.</li>
    <li><strong>The land is old and indifferent.</strong> What hunts you does not hate you. You are weather to it, or weeds. This is worse than malice. Malice can be bargained with.</li>
  </ul>

  <div class="quote">
    "The map-makers leave the bad country white and call it <em>unsurveyed</em>.
    The people who lived here before us have a name for it. They do not say it after dark,
    and neither, after a season out here, will you."
    <span class="src">— marginalia, the Almanac of the Bitterroot Survey</span>
  </div>

  <div class="box">
    <h3 id="ix-tone">On Tone — for Everyone at the Table</h3>
    <p>This is a game about fear, hardship, mortality, and the dark places of history and the mind.
    It is meant to disturb. It is <strong>not</strong> meant to harm the real people playing it.</p>
    <p>Before your first session, talk plainly together about what you want from the game and what you
    would rather leave out. Agree on lines you will not cross and veils you will draw across. Anyone may,
    at any time and without explaining, ask to pause, skip, or rewind a scene. A frightening game is only
    worth playing among people who feel safe playing it.</p>
    <p>The history of the West was, for a great many real people, already a horror without any need of
    monsters. <em>Blood and Grit</em> does not pretend otherwise. Treat that history, and the peoples who
    lived and suffered it, with more care than you treat the things with teeth. See the guidance on the
    First Peoples in Chapter IV before you bring them to your table.</p>
  </div>
  <div class="pageno">4</div>
</section>

<!-- ===================== II. HOW THE GAME IS PLAYED ===================== -->
<section class="page" id="played">
  <div class="runhead"><span class="l">II. How the Game Is Played</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">II. How the Game Is Played</h1>
  <p class="chapter-sub">The dice, the checks, and the long odds of staying alive.</p>
  <div class="divider"></div>
  <p class="dropcap lead">One person at the table is the Keeper. They describe the world, play every soul who is
  not a player's own, and decide what the rules cannot. Everyone else plays a single character — a living
  person trying to last another day. The Keeper sets the scene; you say what your character does; the dice
  settle what is uncertain. That is the whole loop, repeated until the story ends or you do.</p>

  <div class="box gold">
    <h4 id="ix-pf2e">A Word on the Rules</h4>
    <p>Every rule in this book — the core roll, the four degrees of success, abilities and saves, actions and
    conditions, and all the rest — is <strong>mostly adapted from Pathfinder Second Edition</strong>, reskinned for the haunted frontier — though
    this book adds some unique rules and systems of its own, the gun rules of Chapter XI chief among them. If a question is not answered in these pages, the Pathfinder 2E
    rule is the rule, and the Keeper has the final word besides. Players who know that system will find their footing at
    once; players who do not need carry nothing but this book.</p>
  </div>

  <h2 id="ix-core-roll">The Core Roll</h2>
  <p>When an action's outcome is in doubt and failure is interesting, roll a twenty-sided die (the d20),
  add the relevant numbers, and compare the total to a target. Meet or beat the target and you succeed.</p>
  <p>The <strong>ability modifier</strong> comes from whichever of your six attributes best fits the task.
  <strong>Proficiency</strong> is the catch-all term for the training you bring. For a skill, it is your level plus a
  proficiency bonus — +2 if you are <em>trained</em>, +4 <em>expert</em>, +6 <em>master</em> — once you are trained in
  it. For attacks it is your level, adjusted by your Calling's rank; for saves, your Calling's own
  progression. Both stand on your Calling's table in Chapter V, and both are reckoned in Chapter XIV. The
  <strong>Difficulty Class</strong> (DC) is the number to beat, set by the Keeper or by the Defense of whatever
  you are trying to harm.</p>

  <h2 id="ix-difficulty">Difficulty at a Glance</h2>
  <table>
    <thead><tr><th>The Task</th><th class="c">DC</th><th>Example</th></tr></thead>
    <tbody>
      <tr><td>Trivial</td><td class="c">10</td><td>Kick in a rotten door</td></tr>
      <tr><td>Easy</td><td class="c">13</td><td>Calm a skittish horse</td></tr>
      <tr><td>Average</td><td class="c">15</td><td>Pick a strongbox lock; track a man over a day old</td></tr>
      <tr><td>Hard</td><td class="c">18</td><td>Climb a sheer canyon wall in rain</td></tr>
      <tr><td>Very Hard</td><td class="c">20</td><td>Out-draw a known shootist</td></tr>
      <tr><td>Punishing</td><td class="c">25</td><td>Read a dead tongue</td></tr>
      <tr><td>Beyond</td><td class="c">30</td><td>Set a bone by lantern in a storm without waking the patient</td></tr>
    </tbody>
  </table>

  <h2 id="ix-degrees">Degrees of Success</h2>
  <p>Most checks simply pass or fail. But many moments in this country reward — and punish — by <em>how
  far</em> you cleared the mark. When it matters, the Keeper reads your result against four degrees, after
  the manner of the gun rules in Chapter XI:</p>
  <ul class="dash">
    <li><strong>Critical Success.</strong> You beat the DC by 10 or more, <em>or</em> you meet it and the die shows a natural 20. Fortune turns: extra grace, double benefit, or a clean grievous blow.</li>
    <li><strong>Success.</strong> You meet or beat the DC. The thing is done.</li>
    <li><strong>Failure.</strong> You fall short. The thing is not done, and the world moves on without you.</li>
    <li><strong>Critical Failure.</strong> You miss the DC by 10 or more, <em>or</em> you fail and the die shows a natural 1. Something goes wrong beyond mere absence — a gun fouls, a lie is caught, a rope parts.</li>
  </ul>
  <p>A natural 20 always shifts your result one step better; a natural 1 always shifts it one step worse.
  Thus a 20 can turn failure to success, and a 1 can turn success to disaster. The country humbles the sure.</p>

  <h2 id="ix-checks">Checks, Saves, and Opposed Rolls</h2>
  <p>A <strong>check</strong> measures whether you can <em>do</em> a thing: shoot, climb, lie, doctor a wound,
  recall a half-buried legend. A <strong>saving throw</strong> measures whether you can <em>withstand</em> one:
  poison, a blast, a terror that would unseat the mind. There are three saves — <strong>Fortitude</strong>
  (enduring the body's ruin), <strong>Reflex</strong> (dodging swift harm), and <strong>Will</strong> (holding the
  mind together). When two souls strain against each other — a grip, a stare-down, a chase — both roll and the
  higher total wins; this is an <strong>opposed roll</strong>, with ties going to the one already holding what
  is contested.</p>

  <h3 id="ix-take-time">Taking Your Time</h3>
  <p>When there is no pressure and failure costs only minutes, the Keeper may let you <strong>take 10</strong> —
  treat the die as a flat ten — rather than tempt fate. When there is all the time in the world and failure
  carries no penalty worse than starting over, you may <strong>take 20</strong>, as though you had rolled until
  you succeeded; it consumes twenty times as long. You may never take 10 or 20 with a gun in your hand.</p>

  <h2 id="ix-grit">Grit</h2>
  <p>You are more than a column of numbers. You are stubborn. <strong>Grit</strong> is the measure of that
  stubbornness — a small pool of points, refreshed each session, that lets you bend a moment your way. Every
  character begins a session with <strong>3 Grit</strong>. You may spend one point, after seeing the result, to
  do any one of the following:</p>
  <ul class="dash">
    <li>Add 1d6 to a d20 roll you just made, perhaps turning a miss to a hit.</li>
    <li>Re-roll a single failed check, save, or attack, keeping the second result.</li>
    <li>Refuse to fall: when dropped to 0 Blood, stay conscious and on your feet for one more round.</li>
    <li>Steady your nerve: ignore the effect of a fright until the end of your next turn.</li>
    <li>Take a breath: convert a critical failure you just rolled into an ordinary failure, denying the worst of it.</li>
  </ul>
  <p>Grit is the difference between people who die in the first reel and people whose names get remembered.
  Spend it. The Keeper may award a point mid-session for a deed of true courage, a moment of perfect character,
  or a line that makes the whole table go quiet.</p>

  <div class="quote">
    "The dice do not care for you. That is the only honest thing in the room.
    Everything else at this table will lie to keep you breathing — including, in time, yourself."
    <span class="src">— attributed to a faro dealer in Leadwater, before the fire</span>
  </div>
  <div class="pageno">5</div>
</section>

<!-- ===================== III. MAKING A CHARACTER ===================== -->
<section class="page">
  <div class="runhead"><span class="l">II. How the Game Is Played</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-time">The Measures of Time</h2>
  <p>The rules in this book keep time at several scales, and it saves confusion to know which one a given rule means.
  From the smallest to the largest:</p>
  <ul class="dash">
    <li><strong>The Beat.</strong> The smallest unit, used only in a fight. On your turn you have three Beats to spend — a Strike, a Stride, a reload, a shouted word. The full accounting lives in Chapter XI.</li>
    <li><strong>The Round.</strong> In a fight, the few seconds in which every combatant takes one turn — six seconds, near enough. "Once per round" means once between your turns.</li>
    <li><strong>The Turn.</strong> Your own slice of a round: your three Beats, and whatever reactions you are owed.</li>
    <li><strong>The Scene.</strong> The basic unit of story — a single stretch of continuous action or talk in one place: a gunfight, a tense parley, a night's hard ride, the search of a haunted house. A scene runs from the moment a situation begins until it resolves and the table moves on. It might be two minutes of shooting or an hour of careful conversation; what matters is that it is one unbroken piece of business. Most abilities that recharge "once per scene" return when a new situation begins.</li>
    <li><strong>The Session.</strong> One sitting at the table — an evening's play, however many scenes it holds. Abilities that reset "once per session" come back when you next gather. The session is the unit by which a table actually lives the story, and it usually ends at a natural stopping place.</li>
    <li><strong>Downtime.</strong> The unhurried days or weeks between adventures — for healing, crafting, carousing, mending fences, and earning a living. The clock runs loose, and the Keeper narrates its passing.</li>
    <li><strong>The Arc.</strong> A run of sessions telling one larger tale. A rare few effects ("for the rest of the arc") last this long; when one story closes and the next opens, the slate is wiped clean.</li>
  </ul>
  <div class="box gold">
    <h4>Scene vs. Session — the Short of It</h4>
    <p>A <strong>scene</strong> is one situation; a <strong>session</strong> is one evening of play. When an ability says
    "once per scene," ask only whether the situation has changed — a new fight, a new place, a new problem. If it has, the
    ability has recharged. "Once per session" is stingier: it returns only when you next sit down to play. As a rule of
    thumb: Beats and rounds are for the gunfight, the scene is for the situation, the session is for the evening, and
    downtime and the arc are for everything in between.</p>
  </div>
  <div class="pageno">6</div>
</section>

<section class="page" id="character">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>III. Making a Character</span></div>
  <h1 class="chapter">III. Making a Character</h1>
  <p class="chapter-sub">Eight steps from a blank page to a soul worth losing.</p>
  <div class="divider"></div>
  <div class="quote">
    &ldquo;A man out here is three things: what he was, what the country made him, and what he'll
    do when the lamp goes out. Get all three on the page and you've got someone worth playing &mdash;
    and worth burying.&rdquo;
    <span class="src">&mdash; Eb Tuttle, trapper</span>
  </div>
  <p class="dropcap lead">A character in this game is a person, not a hero. Build them to be wanted, haunted,
  indebted, or simply too poor to go home. The mechanics below give them flesh; the questions at the end give
  them a reason to ride out into the dark. Work down the list in order and you will have a finished character
  in the space of a single sitting.</p>
  <table>
    <thead><tr><th>Step</th><th>What You Do</th></tr></thead>
    <tbody>
      <tr><td>1. Concept</td><td>Decide who this person was before the trouble found them.</td></tr>
      <tr><td>2. Abilities</td><td>Generate the six numbers that define body and mind.</td></tr>
      <tr><td>3. Origin</td><td>Choose where you come from; gain its gifts (Chapter IV).</td></tr>
      <tr><td>4. Calling</td><td>Choose your trade and trade of trouble (Chapters V–VII).</td></tr>
      <tr><td>5. Skills &amp; Edges</td><td>Choose your trained skills; take your first Edge (Chapters VIII–IX).</td></tr>
      <tr><td>6. Reckon Numbers</td><td>Work out Blood, Defense, saves, Nerve, and Grit.</td></tr>
      <tr><td>7. Outfit</td><td>Spend starting coin on guns, gear, and a horse (Chapter X).</td></tr>
      <tr><td>8. The Questions</td><td>Answer the four questions that make them real.</td></tr>
    </tbody>
  </table>

  <div class="box gold">
    <h3 id="ix-words">Words of the Country</h3>
    <p>The frontier had a vocabulary of its own and this book uses it, because a game set in 1880 that
    talks like a telephone stops being set in 1880 somewhere around the second session. Below is the
    short list a reader today is likeliest to trip over. The rest you can take from the sentence around it.</p>
    <ul class="dash">
      <li><strong>Sawbones</strong> &mdash; a doctor. The name is the bag: a frontier surgeon carried a
      bone-saw and used it, and the word came to mean any physician in the West, saw or no saw, diploma
      or none. It is a Calling in Chapter V, and it is the nearest thing this game has to a healer
      &mdash; which is to say the difference between a friend who is wounded and a friend who is buried.</li>
      <li><strong>Alienist</strong> &mdash; a doctor of the mind, from the years before anyone said
      <em>psychiatrist</em>. A Sawbones takes the art at 5th level, and in a game with a Nerve track it
      earns its keep by the second reckoning.</li>
      <li><strong>Iron</strong> &mdash; a gun, generally a revolver. To <em>clear leather</em> is to get
      it out of the holster, and the one who does it faster usually lives.</li>
      <li><strong>Shootist</strong> &mdash; someone who fights with a gun for a living and is known by
      name for it.</li>
      <li><strong>Road agent</strong> &mdash; a highwayman. He works the stage roads and the lonely
      miles, and he is the reason an outfit pays for an outrider.</li>
      <li><strong>Laudanum</strong> &mdash; opium dissolved in alcohol, sold over any counter without a
      question asked. It was the century's painkiller, it worked, and it took a great many people who
      had only meant to sleep.</li>
      <li><strong>Drover</strong> &mdash; a hand who moves cattle on the hoof, a thousand miles at a
      walking pace. The <strong>remuda</strong> is the string of spare horses the outfit keeps for him.</li>
      <li><strong>Greenhorn</strong> &mdash; someone new to the country who has yet to learn what it does
      to people.</li>
      <li><strong>Grubstake</strong> &mdash; money or supplies fronted to a prospector against a share of
      whatever he turns up. An <strong>assay</strong> is the test that says what the ore is truly worth,
      and the assayer is frequently the only honest man in a mining town.</li>
      <li><strong>Proving up</strong> &mdash; working a homestead claim for the years the law required
      before the title came to you.</li>
      <li><strong>Arroyo</strong> &mdash; a dry wash. It is a road eleven months of the year and a
      drowning the twelfth.</li>
      <li><strong>Pinkerton</strong> &mdash; a private detective of the Pinkerton agency, hired by
      railroads, mine owners, and anybody else who preferred a law of his own hiring.</li>
    </ul>
  </div>

  <h2 id="ix-abilities">Step 2 — The Six Abilities</h2>
  <p>Every soul is measured along six lines. Three govern the body, three the spirit. From each score you derive
  a <strong>modifier</strong>, equal to the score minus ten, halved, and rounded down. A 10 or 11 gives +0; a 14
  gives +2; a 7 gives –2. The modifier is what you actually add to rolls.</p>
  <table>
    <thead><tr><th>Ability</th><th>Governs</th><th>Used For</th></tr></thead>
    <tbody>
      <tr><td>Strength (STR)</td><td>Muscle, brawn, brute labor</td><td>Melee blows, grappling, hauling, breaking</td></tr>
      <tr><td>Dexterity (DEX)</td><td>Speed, aim, balance</td><td>Gunplay, dodging, riding, stealth, sleight</td></tr>
      <tr><td>Constitution (CON)</td><td>Wind, gut, endurance</td><td>Blood total, Fortitude, disease, thirst</td></tr>
      <tr><td>Wits (WIT)</td><td>Reason, learning, craft</td><td>Lore, medicine, repair, trained skills</td></tr>
      <tr><td>Resolve (RES)</td><td>Composure, faith, instinct</td><td>Will, Nerve, noticing, survival, signs</td></tr>
      <tr><td>Presence (PRE)</td><td>Bearing, voice, menace</td><td>Leading, lying, charming, intimidating</td></tr>
    </tbody>
  </table>

  <h3 id="ix-scores">Generating the Scores</h3>
  <p>Choose one method with your Keeper's blessing. All three make a capable but mortal person — there are no
  demigods in the dust.</p>
  <ul class="dash">
    <li><strong>The Gamble (Rolled).</strong> Roll four six-sided dice, drop the lowest, and total the rest. Do this six times and assign the results. Bold, and sometimes cruel — fitting for the country.</li>
    <li><strong>The Honest Array.</strong> Assign these six numbers as you like: 15, 14, 13, 12, 10, 8. Fair and quick.</li>
    <li><strong>The Wager (Point-Buy).</strong> Every score starts at 8. You have 27 points to raise them, costing more the higher you climb. Nothing may begin above 15 or below 8 by this method.</li>
  </ul>

  <div class="box gold">
    <h4 id="ix-modifiers">A Word on Modifiers</h4>
    <p>Score 8–9 gives –1. Score 10–11 gives +0. Score 12–13 gives +1. Score 14–15 gives +2. Score 16–17 gives +3.
    Score 18–19 gives +4. A starting human is unlikely to exceed 18 in any line, and should not. The exceptional
    belong to the things you hunt.</p>
  </div>

  <h2 id="ix-reckoning">Step 6 — Reckoning Your Numbers</h2>
  <p>With Origin and Calling chosen, work out the figures you will lean on every session. Your Keeper will help;
  do it once and you will never forget.</p>
  <table>
    <thead><tr><th>Figure</th><th>How It Is Reckoned</th></tr></thead>
    <tbody>
      <tr><td>Blood (Hit Points)</td><td>Your Calling's full Hit Die + CON modifier at 1st level; add a roll (or the average) of the Hit Die + CON each level after.</td></tr>
      <tr><td>Defense (AC)</td><td>10 + DEX modifier + armor worn + any cover. See Conflict for how bullets treat armor.</td></tr>
      <tr><td>Saves</td><td>Base from your Calling — a strong save is 2 plus half your level, a weak save a third of it, both rounding down — plus the keyed ability: Fortitude (CON), Reflex (DEX), Will (RES).</td></tr>
      <tr><td>Attack</td><td>Your Calling's rank — Practiced (your level), Steady (level less 1), or Slight (level less 2, never below +0) — added to every attack roll along with the keyed ability. See Chapter XIV.</td></tr>
      <tr><td>Nerve</td><td>RES score + your character level. The measure of how much horror your mind can bank before it breaks.</td></tr>
      <tr><td>Grit</td><td>3, refreshed each session. Spend to bend fate (Chapter II).</td></tr>
      <tr><td>Speed</td><td>30 feet on foot for most folk; a horse is faster and you will want one.</td></tr>
    </tbody>
  </table>

  <h2 id="ix-questions">Step 8 — The Four Questions</h2>
  <p>Numbers do not bleed. Before you ride, answer these aloud at the table. Your Keeper will use your answers as
  hooks — and as bait.</p>
  <ul class="dash">
    <li><strong>What did you lose?</strong> Everyone out here has lost something — land, kin, country, faith, a former self. Name it.</li>
    <li><strong>What have you seen?</strong> You have already glimpsed something that does not belong. What was it, and have you told a living soul?</li>
    <li><strong>What is your vice?</strong> Drink, the cards, laudanum, violence, the Word. It will comfort you and it will cost you.</li>
    <li><strong>What keeps you moving?</strong> A debt, a grave to find, a person to reach, a sin to outrun. Survival needs a reason.</li>
  </ul>
  <div class="pageno">7</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">III. Making a Character</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-compass">Step 9 — The Compass</h2>
  <p>A soul, out here, is read two ways — and both the dark and the divine are reading. The first measure is your
  <strong>conscience</strong>: how you treat others, from open-handed mercy to plain cruelty. The second is your
  <strong>conduct</strong>: how you hold to law, oath, and order, from the badge-keeper to the man who is a law unto
  himself. Set against each other, these two measures make your <strong>Compass</strong> — what older books call
  alignment — a rough fix on where a character stands. It is a description, not a leash; see the box below.</p>
  <h3>The Two Axes</h3>
  <p><strong>Conscience runs Good &ndash; Neutral &ndash; Evil.</strong> The Good spend themselves for others; the Evil
  spend others for themselves; most folk fall between, decent enough until it costs them. <strong>Conduct runs Lawful
  &ndash; Neutral &ndash; Chaotic.</strong> The Lawful keep to code, contract, and chain of command; the Chaotic keep to
  themselves and their own lights; the Neutral bend as the day demands. The nine points each wear a frontier face:</p>
  <table>
    <thead><tr><th>&nbsp;</th><th>Lawful</th><th>Neutral</th><th>Chaotic</th></tr></thead>
    <tbody>
      <tr><td><strong>Good</strong></td><td>The Marshal's Heart</td><td>The Good Samaritan</td><td>The Free Rider</td></tr>
      <tr><td><strong>Neutral</strong></td><td>The Letter of the Law</td><td>The Survivor</td><td>The Drifter's Whim</td></tr>
      <tr><td><strong>Evil</strong></td><td>The Cattle Baron</td><td>The Self-Server</td><td>The Mad Dog</td></tr>
    </tbody>
  </table>
  <ul class="dash">
    <li><strong>Lawful Good &mdash; the Marshal's Heart.</strong> Honor and mercy together; the badge that means what it says, and would sooner take a bullet than break faith.</li>
    <li><strong>Neutral Good &mdash; the Good Samaritan.</strong> Does right by folk, badge or no, law or no; kindness is the whole of the creed.</li>
    <li><strong>Chaotic Good &mdash; the Free Rider.</strong> Unfenced and good-hearted; helps as conscience bids and damns the regulations doing it.</li>
    <li><strong>Lawful Neutral &mdash; the Letter of the Law.</strong> Order above all — the judge, the company man, the soldier who follows orders he does not weigh.</li>
    <li><strong>True Neutral &mdash; the Survivor.</strong> Takes the world as it comes; few causes and fewer crusades; sees to their own and lets the rest ride.</li>
    <li><strong>Chaotic Neutral &mdash; the Drifter's Whim.</strong> Their own road and their own reasons; trusts no fence and no flag, and means no harm by it — usually.</li>
    <li><strong>Lawful Evil &mdash; the Cattle Baron.</strong> Cruelty by contract and code; the tyrant who keeps his word to the letter and grinds you beneath it.</li>
    <li><strong>Neutral Evil &mdash; the Self-Server.</strong> Whatever profits, by whatever means; loyal to no one living but himself.</li>
    <li><strong>Chaotic Evil &mdash; the Mad Dog.</strong> Ruin for its own sake; the thing the frontier hangs first and asks after later.</li>
  </ul>
  <h3 id="ix-holy">Holy, Unholy, and the Unsanctified</h3>
  <p>The Compass is what a soul <em>is</em>; <strong>sanctification</strong> is what the unseen world has a <em>claim</em>
  on. Most living folk are <strong>unsanctified</strong> — neither blessed nor damned, whatever their sins. A soul given
  over to the divine — certain Callings of Faith at their height, a weapon truly consecrated, ground that has been
  hallowed — carries the <strong>holy</strong> quality. A soul given over to the Old Dark — by a Hexer's Bargain, a
  Cultist's Devotion, or a Mark grown deep (Chapter XII) — carries the <strong>unholy</strong> quality. The two cut across
  the line at one another: the Witch Hunter's <em>Sanctified Iron</em>, holy water, the Preacher's fire, a Patron's gifts —
  all strike hardest where they meet their opposite. A wicked man is not unholy until he has dealt with the dark; a kind one
  is not holy until something greater than him has laid a hand on his shoulder. The <strong>Mark</strong> is the road from
  the one to the other, and it runs downhill.</p>
  <div class="box gold">
    <h4>A Compass, Not a Cage</h4>
    <p>Your Compass describes how a character has lived, not how they must act. Play them as a person; the needle follows
    the deeds. A Keeper may move it after a true pattern of contrary acts — and the moving is rarely free, for the slide
    toward the Dark is measured in the <strong>Mark</strong> (Chapter XII), which has teeth. Most player-characters live in
    the Good-to-Neutral band; the three Evil corners are mostly the country's villains and its damned. Little in
    <em>Blood &amp; Grit</em> hinges on the nine points directly — the dark and the divine care far more whether you are
    holy, unholy, or merely a frightened soul who has not yet decided which.</p>
  </div>
  <div class="pageno">8</div>
</section>

<!-- ===================== IV. ORIGINS ===================== -->
<section class="page" id="origins">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>IV. Origins &amp; the Peoples of the Frontier</span></div>
  <h1 class="chapter">IV. Origins</h1>
  <p class="chapter-sub">Where you come from, and what it cost to leave.</p>
  <div class="divider"></div>
  <p class="dropcap lead">No one is born in the saddle. Before the trouble, before the trail, your character was
  someone — with a trade, a people, a place that has since burned or barred its door. Choose one Origin below.
  Each grants a lasting <strong>Gift</strong>: a bonus to a pair of abilities and a knack your past beat into you, and most a further <strong>Boon</strong> besides. None of it comes free — every Origin save the gentlest also lays a <strong>Burden</strong> on you, the price the past still charges.
  The number beside an ability is added to that score before you reckon its modifier.</p>

  <h3 id="ix-o-banker">The Banker</h3>
  <p>You kept the ledgers in a town that hated you for keeping them, called the notes when the notes came due, and
  learned to the dollar what a man will do in the week before he loses his land. Then the paper followed you west, where
  it is thin and the interest is thick. <strong>Gift:</strong> +2 WIT. You are trained in Insight, and no figure put in
  front of you is ever quite as honest as the man presenting it. <strong>Boon:</strong> money answers to you: gain +2 on
  checks to appraise goods or find the trap in a contract, and once per session you may call in a favor of paper, a note
  or a lien or a letter of introduction, and have it honored by anyone who trades in credit.
  <strong>Burden:</strong> the West remembers a foreclosure longer than a kindness; you take &minus;2 on social checks
  with homesteaders, drovers, and the working poor, and there is a ledger somewhere with your name written where a
  family's used to be.</p>

  <h3 id="ix-o-drover">The Drover</h3>
  <p>You brought cattle up the long trails out of Texas, through dust and river and country whose owners had every
  reason to object, and slept in the saddle more nights than in a bed. Three months of that teaches a person the
  difference between tired and finished. <strong>Gift:</strong> +1 DEX and +1 CON. You are trained in
  <strong>Ride</strong> or <strong>Animal Handling</strong> at your choice, and no horse has yet decided you were a
  stranger. <strong>Boon:</strong> stock answers you and the saddle never tires you: gain +2 on checks to handle any
  animal, whether to calm it, drive it, or catch it, and once per scene you may ask a mount for more than it has left
  and get it, at a cost the beast pays later. <strong>Burden:</strong> twelve years of shouting over a thousand head
  left you loud; you take &minus;2 on Stealth, and you carry a voice that fills a room whether you mean it to or not.</p>

  <h3 id="ix-o-drummer">The Drummer</h3>
  <p>A travelling seller of tonics, Bibles, futures, or lies, you have talked your way into a hundred parlors and out of
  nearly as many beatings. You believe in nothing you sell and everything you say. <strong>Gift:</strong> +2 PRE. You are
  trained in Persuade, and folk meeting you for the first time are inclined to hear you out before they decide to distrust you. <strong>Boon:</strong> you could sell sand in a drought — once per scene reroll a failed Persuade or Deceive, and in any town of size you can talk your way to a bed, a meal, or a line of credit on your word alone. <strong>Burden:</strong> a tongue that quick is seldom believed twice; once a lie or a tall tale of yours is found out, those who caught it take &minus;2 to trust you for the rest of the affair, and word travels ahead of you.</p>

  <h3 id="ix-o-gentry">The Fallen Gentry</h3>
  <p>Once there was a name, a house, an inheritance — and then a war, a debt, or a scandal took it all. You wear the manners
  still, threadbare as your coat, and they open doors your purse cannot. <strong>Gift:</strong> +1 WIT and +1 PRE. You are
  lettered, trained in Lore (Frontier or Occult, your choice), and move easily among people who believe themselves your betters. <strong>Boon:</strong> the old manners open doors a purse cannot — gain +2 on social checks among the wealthy, the lettered, and the powerful, and you read rank, breeding, and the lie beneath a fine coat at a glance. <strong>Burden:</strong> the soft years left their mark; you take &minus;1 on Fortitude saves against the plain hardships — hunger, exposure, hard labor — that those frontier-born endure without complaint.</p>

  <h3 id="ix-o-freed">The Freed</h3>
  <p>Born or sold into bondage, you took your own liberty or had it grudgingly granted, and you have walked west to
  be no man's property again. You carry a watchfulness that has saved your life more than once. <strong>Gift:</strong>
  +1 RES and +1 PRE. You gain a permanent +2 on checks to read a stranger's true intent, and on Will saves against
  being cowed. <strong>Boon:</strong> ropes, locks, and cages have never held you long — gain +2 to slip a bond or a confinement, and you are never quite cornered while any way out remains. <strong>Burden:</strong> badges and the men behind them have earned no trust from you; you take &minus;1 on social checks to deal with lawmen, soldiers, and officials, who feel your wariness and return it.</p>

  <h3 id="ix-o-gambler">The Gambler</h3>
  <p>You have made your living, and lost it, at the green-felt tables of a hundred towns, and learned to read a face for the
  truth it tries to hide. <strong>Gift:</strong> +1 PRE and +1 WIT. You are trained in Gamble, and you read a table the way other folk read
  weather. <strong>Boon:</strong> you keep a working peace with chance: a permanent +2 on Insight at any table, and once per
  session you may reroll a single d20 and keep the better result, the small luck a card-player learns to trust. <strong>Burden:</strong> the table keeps its
  hooks in you; when coin, cards, or a sure thing are laid before you, the Keeper may call for a Will save to walk away, and
  old gambling debts have a way of riding into town behind you. <span class="note">A character of a Calling of Faith — most
  of all a <strong>Preacher</strong> or a <strong>Padre</strong> — may not take the Gambler background unless the Keeper rules
  the campaign allows it; a soul sworn to the pulpit has no business at the green table. This background grants only a knack;
  the Gambler <em>Calling</em> of Chapter V is the whole craft, and far more.</span></p>

  <h3 id="ix-o-homesteader">The Homesteader</h3>
  <p>You broke sod that did not want breaking and buried more than one child under it. You know weather, livestock,
  and the particular patience of poverty. <strong>Gift:</strong> +1 CON and +1 RES. You begin trained in Survival
  and never go hungry where anything at all will grow. <strong>Boon:</strong> a full night's rest in a camp you have made restores you and each companion sheltering with you an extra 1d6 Blood, and your dogs and stock give warning before trouble arrives. <strong>Burden:</strong> the sod broke the wanderer in you — away from home or kin you take &minus;1 on Initiative the first round of any fight, slow to credit that the worst has come again.</p>

  <h3 id="ix-o-laborer">The Laborer</h3>
  <p>You laid rail, dug shafts, or drove spikes for wages that vanished at the company store. Perhaps your tongue is
  not the one spoken here. Your hands are ruined and reliable. <strong>Gift:</strong> +1 STR and +1 CON. You are
  trained in Repair, and treat any tool, however crude, as the right one for honest work. <strong>Boon:</strong> your ruined, reliable body shrugs off a hard day — gain +2 on Fortitude saves against fatigue, strain, and the wearing cold, and you can labor or march long past where softer men fold. <strong>Burden:</strong> these hands were made for the spike and the shovel, not the needle; you take &minus;1 on checks of fine dexterity — sleight, lockwork, fuses, and the surgeon's delicate art.</p>

  <h3 id="ix-o-madam">The Madam</h3>
  <p>You ran a house, which is to say you ran a business: the books, the liquor, the peace, the doctor when a doctor was
  needed, and the safety of the women who worked for you, in a town that took your money on Saturday and cut you on
  Sunday. What came through your door with the men was every secret they had. <strong>Gift:</strong> +1 PRE and +1 CON.
  You are trained in <strong>Persuade</strong> or <strong>Deceive</strong> at your choice, and you have put larger men
  than yourself into the street. <strong>Boon:</strong> nothing said in your parlor ever left it without your leave, and
  the habit stayed: gain +2 on checks to read what a person truly wants, and to hold a room without raising your voice,
  and once per session you may name one person of consequence in town and know a private truth about them.
  <strong>Burden:</strong> respectable folk will take your money and not your hand; you take &minus;2 on social checks
  with the church-going and the office-holding, and a few of them work quietly to see you moved along.</p>

  <h3 id="ix-o-news">The Newspaperman</h3>
  <p>You set type by lamplight, chased stories nobody thanked you for, and kept a drawer of the ones no editor would
  run: the drowned man with no water in him, the herd that walked into the lake, three separate widows describing the
  same visitor. You did not believe a word of it. You kept it anyway. <strong>Gift:</strong> +1 WIT and +1 RES. You are
  trained in Lore (Occult), which in your case means a filing cabinet rather than a seminary.
  <strong>Boon:</strong> the clippings nobody believed are still yours: gain +2 on checks to research a matter, or to
  get a stranger talking on the record, and once per session you may declare that your morgue file holds something on a
  person, a place, or a horror at hand, and learn one true thing about it. <strong>Burden:</strong> you cannot leave a
  thing unasked, and your face asks before your mouth does; you take &minus;1 on Deceive, and the Keeper may call for a
  Will save to keep a dangerous question behind your teeth.</p>

  <h3 id="ix-o-outlaw">The Outlaw</h3>
  <p>There is paper on you in at least one territory. Whether the charge was just is your own affair. You sleep light,
  draw fast, and trust the law to do you no favors. <strong>Gift:</strong> +1 DEX and +1 PRE. Once per session you may
  declare you have been somewhere before and know one useful, unsavory fact about it. <strong>Boon:</strong> the wrong sort know you and you them — gain +2 to deal with criminals, fences, and the hard cases of any town, and +2 to make a quick exit when the law takes a sudden interest. <strong>Burden:</strong> there is paper on you in at least one territory, and your face surfaces at the worst moments; lawmen and bounty men take note of you, and the Keeper may rule a warrant, a posse, or an old grudge has trailed you into town.</p>

  <h3 id="ix-o-rail">The Railroad Hand</h3>
  <p>Grade, spike, wire, or timetable, you worked the line. Perhaps you swung the maul on the Central Pacific with a
  crew that spoke your language and nobody else's; perhaps you kept the key at a depot where the whole territory arrived
  one word at a time. Either way the country is a map to you, and the map has your handwriting on it.
  <strong>Gift:</strong> +1 CON and +1 WIT. You are trained in Lore (Frontier), and you read a timetable the way a
  preacher reads a psalm. <strong>Boon:</strong> the line still knows you: gain +2 on any check to say where a rail or
  road or river runs, you ride freight or coach free wherever the rails go, and once per session a name from your
  working days opens a door, a boxcar, or a telegraph key. <strong>Burden:</strong> the company's name rides with you;
  you take &minus;2 on social checks with anyone the road has wronged, and there are men still on the payroll who would
  rather you had stayed on it.</p>

  <h3 id="ix-o-scout">The Scout</h3>
  <p>You read the land like scripture, whether the country bore you or you simply spent your life learning its moods —
  a guide, a hunter, a wagon-pilot, an Army auxiliary. The newcomers need you and distrust you in turn, and you owe
  them little. <strong>Gift:</strong> +1 DEX and +1 RES. You are trained in Survival, ignore difficult ground afoot,
  and are never lost beneath an open sky. <strong>Boon:</strong> you read country at a glance — gain +2 on Notice to spot ambush, tracks, and lying-in-wait out of doors, and you are never surprised beneath the open sky. <strong>Burden:</strong> a life on the trail leaves you ill at ease behind walls; indoors and in close crowds you take &minus;1 on Notice, the roof and the press of bodies sitting on you like a held breath. <span class="note">If your Scout belongs to one of the First Peoples,
  read the guidance below before play.</span></p>

  <h3 id="ix-o-undertaker">The Undertaker</h3>
  <p>You washed and boxed the dead of three towns. You know the weight of a grown man, the smell of the fourth day, and
  which families pay. Not one of them ever frightened you, and you were proud of that, right up until the day one sat
  up. <strong>Gift:</strong> +1 STR and +1 RES. You are trained in Medicine, though what you learned it on was past
  helping. <strong>Boon:</strong> the dead are work to you and not horror: gain +2 on Medicine to read what killed a
  body and how long it has lain there, and once per scene, when a corpse or a grave or a charnel sight would cost you
  Nerve, it costs you none. <strong>Burden:</strong> you have handled too many bodies to fear one, and that is exactly
  the trouble: the first time each session a corpse proves to be something other than a corpse, you are Off-Guard for a
  round while you finish deciding that it is.</p>

  <h3 id="ix-o-veteran">The Veteran</h3>
  <p>You served — blue or gray in the late war, or a hard hitch with the cavalry and infantry in the long campaigns that
  followed it across these plains. You know drill, the chain of command, the weight of a carbine, and exactly what a volley
  does to men. Some of it you are proud of. Some of it wakes you in the small hours. <strong>Gift:</strong> +1 CON and +1 STR.
  You are trained in <strong>Athletics</strong> or <strong>Intimidate</strong> at your choice, begin play with a service carbine or sidearm, and once
  per session may steady the line — you and each ally who can hear you shrug off fear for a round. <strong>Boon:</strong> drill is in your bones — once per scene reroll a failed Reflex save to take cover or hit the dirt, and you reload and clear a jam a half-beat faster than any green hand. <strong>Burden:</strong> some of it never left; the first time each session the sudden roar of gunfire or the touch of the uncanny finds you, make a Dread Check or be Shaken a round as the old war rises behind your eyes.</p>

  <h3 id="ix-o-wrong">Came Back Wrong</h3>
  <p>You died &mdash; of fever, of lead, of cold, of something with no name &mdash; and then you did not stay dead. You remember the dark
  on the other side. It remembers you. (Begin play at Mark 1; see Chapter XII.) <strong>Gift:</strong> +1 CON and +1 RES. You no
  longer need to breathe to live and feel cold and pain dimly, but you start one step along the Mark, and the uncanny notices its own. <strong>Boon:</strong> what came back with you does not die easy &mdash; once per session, when you would drop to 0 Blood you instead stay standing at 1 until the end of the round, and you need neither food nor sleep to go on, though you may rest if you wish. <strong>Burden:</strong> the dead do not forget you; the Old Dark notices you before any other, and the living sense without knowing why that something about you is wrong (&minus;1 on first-impression checks with the breathing).</p>
  <p class="note">This Origin runs deeper than one paragraph. Choose a <strong>Shape of Return</strong>
  and read <a href="#ix-returned">The Returned</a> in Chapter XII: you carry a <strong>Hunger</strong>
  track that no other soul has, you mend by spending it, and it is the only way you heal at all.</p>

  <div class="quote">
    "My grandmother told me the land does not belong to us. We belong to it, and it has been lending
    us back to ourselves for a thousand winters. The newcomers think a paper changes that. The land
    has read no papers."
    <span class="src">— recorded by a mission teacher; the speaker asked that her name be kept</span>
  </div>

  <h2 id="firstpeoples">The First Peoples</h2>
  <p>West of the Mississippi, the country was never empty and never new. It was — and is — the home of nations
  older than any territory drawn on a map: among them the <strong>Lakota, Dakota, and Nakota</strong> of the northern
  plains; the <strong>Cheyenne, Arapaho, Crow, Pawnee,</strong> and <strong>Osage;</strong> the <strong>Comanche,
  Kiowa,</strong> and <strong>Wichita</strong> of the southern plains; the <strong>Apache</strong> peoples and the
  <strong>Diné (Navajo)</strong> of the desert southwest; the <strong>Ute, Shoshone, Paiute,</strong> and
  <strong>Bannock</strong> of the Great Basin; the <strong>Nez Perce, Cayuse,</strong> and the Plateau nations; the
  <strong>Pueblo, Hopi,</strong> and <strong>Zuni</strong> of the pueblos; and a hundred more, each with its own
  language, law, kinship, and faith. They are not one people, and never were.</p>
  <p>By 1885 these nations have endured a generation of catastrophe not of their making: the slaughter of the
  buffalo, broken treaties, forced removal, military campaigns, epidemic disease, the reservation, and the
  boarding school that took the children to unmake their tongue. This is the true horror against which the
  invented horror of this game is only a shadow. A character of the First Peoples is most likely a survivor of
  all of it — and a person, fully, before they are anything else.</p>

  <div class="box">
    <h3>Playing a Character of the First Peoples</h3>
    <p>If a player wishes to portray a character from one of these nations, the whole table owes the choice some care.
    A few plain rules of the road:</p>
    <ul class="dash">
      <li><strong>Avoid the worn lies.</strong> No noble-savage, no bloodthirsty-savage, no vanishing-race elegy. These are propaganda, not character.</li>
      <li><strong>Be specific, not generic.</strong> Choose a real nation and learn a little of its actual history, country, and circumstance in the 1880s. "Generic Indian" is a settler's invention; do not play it.</li>
      <li><strong>Honor lines and veils.</strong> Real massacres, removals, and the boarding schools are matters a table may choose to handle gravely, glancingly, or not at all. Decide together, and never for shock.</li>
      <li><strong>Sacred is not a mechanic.</strong> The Signs, the Mark, and the Old Rites of this book are the game's <em>invented</em> dark. Do not pin them to any real living religion, ceremony, or sacred object. If you want a faith-keeper, see the note in Chapter VI.</li>
      <li><strong>They are people first.</strong> Give them families, humor, grudges, hopes, and an inner life — not mystic set-dressing for someone else's story.</li>
    </ul>
    <p class="note">When in doubt, the people whose history this is should be heard before the dice are. If no one at the
    table can speak to it with care, it is honorable to leave it to the Keeper's background and play someone else.</p>
  </div>

  <p>Mechanically, a First Peoples character chooses any Origin that fits their life — most often the <strong>Scout</strong>
  or <strong>Homesteader</strong>, but any may apply — and any Calling. Their nation, language, and history are written into
  the four Questions, not bought with a stat. The country they know best is, after all, the one being taken.</p>

  <h2 id="mexicanpeoples">The Mexican Frontier</h2>
  <p>The border did not cross these families; the border crossed them. Long before the territories were drawn, the land
  from Texas to California was <strong>Mexico</strong>, and before that New Spain — and the <strong>Tejano, Californio,</strong>
  and <strong>Nuevomexicano</strong> families who built the missions, ranchos, and towns of the Southwest did not vanish when
  the maps were redrawn in 1848. They remained: ranchers and <em>vaqueros</em> — the first cowboys, whose craft and very words
  (<em>lariat, lasso, rodeo, corral, chaps, buckaroo</em>) the Anglo cowhand later borrowed — alongside farmers, freighters,
  miners, priests, merchants, and laborers, on land their grandparents had worked for a hundred years.</p>
  <p>By 1885 many find themselves strangers in their own country: old Spanish and Mexican land grants challenged or stolen
  outright in Anglo courts, the language of law turned against them, and a hard new color line drawn through towns their
  families founded. Some hold their ranchos still; some have lost everything to lawyers and lynch-law; some ride the border
  both ways, and a few have taken up the revolver to settle what the courts would not. They are Catholic, mostly, with a
  faith that keeps its own saints and its own dead close — no small thing on a haunted frontier.</p>

  <div class="box">
    <h3>Playing a Mexican Character</h3>
    <p>The same courtesy owed any real people applies here. A few plain rules of the road:</p>
    <ul class="dash">
      <li><strong>Avoid the worn lies.</strong> No bandit-buffoon, no sleeping peon, no hot-blooded caricature. These are dime-novel propaganda, not character.</li>
      <li><strong>Be specific.</strong> A Tejano ranching family near San Antonio, a Californio whose grant was swallowed after statehood, a Nuevomexicano from a village older than the United States — these are different lives. Choose one and learn a little of it.</li>
      <li><strong>Faith is a strength, not set-dressing.</strong> Catholic devotion, the saints, the Day of the Dead, the village <em>curandera</em> — these can anchor a character against the dark without being reduced to mysticism.</li>
      <li><strong>Not a costume or an accent.</strong> Give them family, faith, pride, and an inner life. Spanish belongs in their mouth naturally, never as comic seasoning.</li>
      <li><strong>The injustice is real history.</strong> Stolen land grants, the lynchings, the slur "greaser," the color line — these happened. Use them with weight, by agreement, never for flavor.</li>
    </ul>
    <p class="note">As with the First Peoples, lines and veils are the table's to set together. When the history is someone's own, let them be heard before the dice are.</p>
  </div>

  <p>Mechanically, a Mexican character chooses any Origin and Calling that fits — the <em>vaquero</em> is a Drifter, Gunhand,
  or Marshal as readily as any Anglo, and the old ranching families field Homesteaders and Fallen Gentry alike. Their
  language, faith, and the grant the family is fighting to keep are written into the four Questions, not bought with a stat.</p>

  <h2 id="blackwesterners">Black Westerners</h2>
  <p>The West was worked by Black hands from the first drive to the last spike, and the record is plainer than the
  dime novels ever admitted. Roughly <strong>one trail hand in four</strong> on the great cattle drives is Black or
  Mexican; the best bronc-riders and ropers in the business are known by name across three territories. Black men and
  women are freighters, blacksmiths, cooks, barbers, laundresses who own the building, homesteaders, mail carriers,
  and lawmen — a deputy marshal riding out of Fort Smith into Indian Territory has brought in more wanted men than any
  other deputy in the Territory — thousands of them over his career — and every outlaw between the Arkansas
  and the Red knows his name. Four regiments of the regular
  Army — the <strong>Ninth and Tenth Cavalry, the Twenty-Fourth and Twenty-Fifth Infantry</strong> — are Black
  soldiers under mostly white officers, and the Plains nations who fought them named them the
  <strong>Buffalo Soldiers</strong>, which was meant as respect and was taken as such.</p>
  <p>Most came under their own power and for their own reasons. When Reconstruction was abandoned in '77 and the old
  order came back wearing a sheet, tens of thousands left the South in the <strong>Exodus of 1879</strong>, the migrants remembered as <strong>Exodusters</strong> — walking,
  riding, and taking deck passage up the Mississippi for Kansas, which they had heard was free ground. They founded
  whole towns of their own: <strong>Nicodemus</strong> on the Kansas grass, and after it a string of Black towns
  across Kansas, Indian Territory, and Texas, each with its church and its school built before its saloon. What they
  found was freer, and it was not free: the color line came west on the same trains they did, sundown towns turned
  them out at dusk, and the law was a coin-flip. By 1885 the door is closing again — and they are still here, still
  building, and no longer asking anyone's leave.</p>

  <div class="box">
    <h3>Playing a Black Character</h3>
    <p>The same courtesy owed any real people applies here. A few plain rules of the road:</p>
    <ul class="dash">
      <li><strong>Avoid the worn lies.</strong> No faithful retainer, no comic relief, no saintly sufferer, no character who exists to be endured against. These are minstrel-show inventions, not character.</li>
      <li><strong>Be specific.</strong> An Exoduster homesteader proving up (working a claim the years the law required to earn its title) outside Nicodemus, a sergeant of the Tenth out of Fort Davis with fifteen years in, a trail hand on his sixth drive who is the best horseman in the outfit, a widow who owns the laundry and half the block — these are different lives. Choose one and learn a little of it.</li>
      <li><strong>Competence is the historical record.</strong> Where a Black character is the best hand, the best shot, or the best doctor in the scene, that is the ordinary case, and the table should play it as ordinary.</li>
      <li><strong>Community is the strength.</strong> The church, the lodge, the school built first, the town that holds together — these anchor a character against the dark, and they are somewhere to come back to.</li>
      <li><strong>The injustice is real history.</strong> Slavery, the Exodus, the color line, and the violence that enforced it all happened. Use them with weight, by agreement, and never for flavor or shock.</li>
    </ul>
    <p class="note">As with the First Peoples and the Mexican frontier, lines and veils are the table's to set together. When the history is someone's own, let them be heard before the dice are.</p>
  </div>

  <p>Mechanically, a Black character chooses any Origin and Calling. <strong>The Freed</strong> and <strong>The
  Veteran</strong> are the obvious roads and by no means the only ones — a great many were born free, and the
  frontier's Black Gunhands, Sawbones, Marshals, Preachers, and Prospectors are all a matter of record. Where they
  came from, who they left, and what they are proving up on go into the four Questions, not into a stat.</p>

  <h2 id="chinesefrontier">The Chinese on the Frontier</h2>
  <p>The hardest miles of the transcontinental railroad were built by Chinese labor, and the Central Pacific's own
  officers said so. At the peak of the work, <strong>nine men in ten</strong> on that grade were Chinese — better
  than ten thousand of them — cutting the Sierra tunnels by hand through granite at eight inches a day, hanging in
  baskets off the Cape Horn cliffs, setting nitroglycerin, and wintering under forty feet of snow in the sheds while
  avalanches took whole camps. When the rails met in '69 and the photograph was taken, not one of them was asked to
  stand in it. Afterward they went where the work was: the quartz mines and the placer bars, the levees that made
  the delta farmland, the fisheries, the cigar benches, the laundries and restaurants and market gardens of every
  town on the coast and half the towns inland — and the cook tent of any cattle outfit shrewd enough to hire one,
  where the man feeding twelve hands is often the best-paid and least-replaceable soul in the crew. The herbalist
  with a shop full of drawers is a trained physician in a tradition two thousand years older than the one the Army
  surgeon studied, and the town generally works this out the first time somebody is dying.</p>
  <p>The country's answer to all this was the law. The Page Act of '75 shut out the women; the
  <strong>Exclusion Act of 1882</strong> — three years back — shut the door outright, barred naturalization, and
  stranded a generation of men on the wrong side of an ocean from wives and children they send money to and may
  never see again. Where the law would not do it, mobs did: Los Angeles in '71, and this very year the coal camp at
  <strong>Rock Springs</strong>, where a wage dispute ended with the Chinese quarter burned and twenty-eight men
  dead. Against all of it they built their own civil order — the <strong>district associations</strong> that
  settle disputes, lend money, run the schools, bury the dead, and ship the bones home to be buried properly in the
  village. They are not guests here. They built the hardest miles of the road west, and they are owed for it.</p>

  <div class="box">
    <h3>Playing a Chinese Character</h3>
    <p>The same courtesy owed any real people applies here. A few plain rules of the road:</p>
    <ul class="dash">
      <li><strong>Avoid the worn lies.</strong> No inscrutable mystic, no comic laundryman, no dispenser of ancient wisdom, no fortune-cookie speech, and no dialect played for laughs. These are stage inventions of the exclusion years, and they were built to justify it.</li>
      <li><strong>Be specific.</strong> Nearly all came from a handful of districts in <strong>Guangdong</strong> — most from Toisan and the Sze Yup counties — and speak Cantonese, not "Chinese." They have a village, a family, a surname that means something, and a remittance going home every quarter. Choose the particulars.</li>
      <li><strong>Skill is a trade, not magic.</strong> The herbalist's medicine is medicine; the railroad man's blasting is engineering; the merchant's ledger is capital. Do not turn any of it into mysticism, and do not hang the game's invented dark on Buddhist or Taoist practice — the same rule the First Peoples' section sets, for the same reason.</li>
      <li><strong>The associations are civil society.</strong> The <em>huiguan</em> is a bank, a court, a hiring hall, and a burial society at once. A character with standing in one has resources; a character who has crossed one has a problem that a gun will not solve.</li>
      <li><strong>The injustice is real history.</strong> The tax, the queue ordinances, the Exclusion Act, and the burnings all happened, and 1885 is the year of Rock Springs. Use them with weight, by agreement, never for flavor.</li>
    </ul>
    <p class="note">Lines and veils are the table's to set together. When the history is someone's own, let them be heard before the dice are.</p>
  </div>

  <p>Mechanically, a Chinese character chooses any Origin and Calling. <strong>The Laborer</strong> is the road most
  walked and is far from the only one — the <strong>Sawbones</strong> fits the herbalist tradition exactly, and the
  frontier's Chinese Prospectors, Gamblers, Drifters, and Bounty Hunters are all a matter of record. Their district,
  their family across the water, and what the remittance is for go into the four Questions, not into a stat.</p>

  <div class="pageno">9</div>
</section>

<!-- ===================== V. CALLINGS ===================== -->
<section class="page" id="callings">
  <div class="runhead"><span class="l">V. Worldly Callings</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">V. Worldly Callings</h1>
  <p class="chapter-sub">The trades of the desperate, from first blood to last stand.</p>
  <div class="divider"></div>
  <p class="dropcap lead">A Calling is what your character does when the talking stops — the trade by which they earn
  coin, enemies, and an early grave. Each advances over ten levels, the highest a mortal is likely to reach before the
  country collects its due. Your Calling sets your Hit Die (the dice you roll for Blood), your war-progression (Base
  Attack Bonus), your strong saves, and the features that make you dangerous.</p>
  <p id="ix-perks">Each Calling also carries one <strong>Perk</strong>, printed above its table. A Perk is the single
  thing that Calling alone does, true from 1st level and true forever after. It costs nothing, spends nothing, and is
  never rolled for. Some are worth a great deal at the right moment and nothing at all for weeks; a few are as much
  reputation as ability, and one or two are frankly a liability, which is rather the point of them. Read the nineteen
  Perks together and you have the shortest honest answer to what each Calling is for.</p>
  <p id="ix-ledger">Under the Perk sits a second band, in two halves: <strong>In a fight</strong> and
  <strong>You pay</strong>. The Perk is what a Calling is worth at the table over a long campaign. The ledger is
  narrower and more brutal: what that Calling actually does in a round of shooting, and what it gives up to be
  the thing that does it. Both halves are true. The Marshal will not out-damage anybody in this book and the
  ledger says so plainly, because the Marshal spends its Calling on everyone else's turn and a player who
  wanted to top a tally should be told before they roll, not after. Read the nineteen ledgers together and the
  shape of a posse falls out of them: somebody has to end things, somebody has to keep the ending from
  happening to you, and the good tables work out early which of them they are short of.</p>
  <p>This book groups the Callings by the well they draw from, across three chapters. The <strong>worldly Callings</strong>
  in this chapter — Gunhand, Drifter, Sawbones (the frontier's word for a doctor), Marshal, Prospector, Mountain Man,
  Bounty Hunter, Engineer, and Gambler — live by
  iron, instinct, learning, law, luck, a hard eye for the unnatural, a quick hand on the wrong side of the law, a head for powder and machinery, and a cooler hand at the card table. Those who draw on <strong>faith</strong> —
  Padre, Preacher, Shaman, Medicine Man, and the Witch Hunter — are gathered in Chapter VI. And those who walk with
  the <strong>Old Dark</strong> by pact, by craft, by deceit, or by devotion — Hexer, Witch, False Prophet, and Dark Cultist —
  are given Chapter VII, for such roads ask a toll the others do not.</p>
  <p class="note">Read each table thus: <strong>Attack</strong> is your Calling's attack proficiency by level, read straight
  from its table, added to Strikes along with your keyed ability; <strong>Fort/Ref/Will</strong> are
  your save proficiencies by level, added to saves along with the keyed ability; <strong>Features</strong> are gained at the
  listed level. The number beside <strong>Trained Skills</strong> in the statline, plus your WIT modifier, is how many skills
  you begin trained in; you gain a skill increase at 3rd, 5th, 7th, and 9th level.</p>
  <div class="pageno">10</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">V. Worldly Callings</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-bounty">Bounty Hunter</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Reflex, Will · Attack Practiced</p>
  <p>Some come to the frontier to take what others carried; the Bounty Hunter comes for the men who took it. Manhunter,
  paper-collector, skip-chaser — call it what you like, the trade is the same: find the soul the warrant names, be where he
  does not expect you, and bring him in before his friends or his nerve can turn the odds. Bounty men are not duelists and
  seldom heroes, but one who has lived past his third warrant has learned the only lessons that keep a man breathing — pick
  the moment, take your mark unready, and always, always know the way out with him in tow.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Paper on Him.</span> Give you a night in any town with a jail, a telegraph office, or a saloon, and you will come back knowing who wants a man, what for, how much, and whether the paper is still good. You will also come back knowing who wants you, which is worth finding out early.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The hardest single hit in the book, when you set it up. Bushwhack turns a foe who has not seen you yet into four extra dice by 10th level.</div>
    <div class="pays"><span class="k">You pay</span>A d8, and dice that only come when you have the drop. A fight you walk into face-first is a fight you have with a gun and nothing else.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+2</td><td>Edge, Bushwhack 1d6, Quick Hands</td></tr>
      <tr><td>2</td><td class="c">+2</td><td class="c">+0</td><td class="c">+3</td><td class="c">+3</td><td>Road Sense</td></tr>
      <tr><td>3</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td class="c">+3</td><td>Edge, Trade</td></tr>
      <tr><td>4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>The Drop</td></tr>
      <tr><td>5</td><td class="c">+5</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Edge, Bushwhack 2d6, Getaway</td></tr>
      <tr><td>6</td><td class="c">+6</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+7</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>Edge, Hard Ride</td></tr>
      <tr><td>8</td><td class="c">+8</td><td class="c">+2</td><td class="c">+6</td><td class="c">+6</td><td>Bushwhack 3d6</td></tr>
      <tr><td>9</td><td class="c">+9</td><td class="c">+3</td><td class="c">+6</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+10</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>Dead or Alive, Bushwhack 4d6, Trade Mastery</td></tr>
      <tr><td>11</td><td class="c">+11</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>Cold Trail</td></tr>
      <tr><td>12</td><td class="c">+12</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+13</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Bushwhack 5d6, Nowhere to Run</td></tr>
      <tr><td>14</td><td class="c">+14</td><td class="c">+4</td><td class="c">+9</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+15</td><td class="c">+5</td><td class="c">+9</td><td class="c">+9</td><td>The Warrant</td></tr>
    </tbody>
  </table>
  <h4>Bushwhack</h4>
  <p>Bringing a man in is not a fair fight, and you do not pretend otherwise. Once per turn, when you Strike a quarry who is
  unaware of you, who has not yet acted in the fight, or whom an ally threatens, deal the listed extra damage. The ambush is
  the whole of the art — a bounty man forced to trade blows in the open with a cornered killer has already made his mistake.</p>
  <h4>Quick Hands</h4>
  <p>Years of needing your iron — or your irons, the manacle kind — a half-second sooner than the other man. You draw,
  holster, reload, or snap on a cuff as part of another action rather than spending a Beat on it, and add +2 to the roll that
  decides who acts first. Lockpicks, knots, and a fugitive's hidden pockets answer to these hands as readily as a trigger does.</p>
  <h4>Road Sense</h4>
  <p>You have laid enough ambushes to know when you are walking into one. Gain +2 on Notice against traps, tails, and
  lying-in-wait, and you are never caught flat — you act in the first round of a fight even when surprise is called against
  you. The hunted set snares too.</p>
  <h4>The Drop</h4>
  <p>With a quarry dead to rights — your iron drawn, his not — you may Demoralize as a single Beat, and a man who yields
  comes along quiet, hands where you can see them. Against one who calls the bluff, your first Strike counts him as unaware.
  Dead or alive is his choosing; you are paid the same either way.</p>
  <h4>Getaway</h4>
  <p>The catch is only half done until you and your man are clear of his friends. Immediately after you Strike, take a
  prisoner, or break free, you may Step and then Stride for free; mounted, you may instead vault to the saddle and ride,
  prisoner and all.</p>
  <h4>Hard Ride</h4>
  <p>You and your horse have run down more men — and outrun more of their kin — than you can count. Your mounted Speed
  increases by 10 feet, you cross rough country a fleeing man must slow for, and once per scene you may close on a single quarry who
  thought he had lost you, or shake a pursuit of your own, given a moment's lead and a place to turn.</p>
  <h4>Dead or Alive</h4>
  <p>At 10th level your name is worth nearly as much as the paper you carry. Once per scene, a Bushwhack you land against an
  unready quarry is an automatic critical hit. And you are never truly cornered: declare a bolt-hole — a relay horse, a
  confederate, a lawman who owes you, a back trail only you know — and the Keeper will honor it, once, when all seems lost.
  A great many men have been promised to the rope, and you are the one who delivers them.</p>
  <h4>Cold Trail</h4>
  <p>A trail stops going cold on you. Given a name and one thing that belonged to the man — a hat, a letter, a horse he
  rode — you may sit an hour with it at dusk and learn the direction he lies in and roughly how far, once each day. It
  tells you nothing of what stands between. Many a bounty man has ridden four hundred miles on a true bearing and
  arrived a week after the funeral.</p>
  <h4>Nowhere to Run</h4>
  <p>You have closed too many doors to leave one open now. A quarry you have Struck this scene cannot Disengage from you
  without first beating your Notice with an Athletics or Stealth check, and any cover he takes is cover you have already
  used yourself. When he runs anyway, your first shot after him counts him unaware.</p>
  <h4>The Warrant</h4>
  <p>Your name has become a kind of law. Once per session you may write a warrant of your own — on the back of a bill, on
  a barn door, on nothing at all — naming one creature or one man. Until the session ends, or the warrant is served, you
  always know the direction of the named and how far off it lies, your Bushwhack against it is an automatic critical
  hit, and any lawman, hand or honest citizen who hears the name will help you against it or stand out of your way.
  Serve it, and the country pays: the Keeper grants one lasting boon out of what the warrant was worth, and the paper
  goes on the wall of some office where men will read the name for fifty years. Write the wrong name and you will find
  that out the same way.</p>

  <div class="quote">"Folks ask how I bring them in when faster men could not. I do not bring them in fast. I bring them in
    tired — a week of no fire, no sleep, no notion of where they are, until the open country has done my work for me and the
    iron is only the receipt."
    <span class="src">— attributed to the bounty man called Cole Renner, who always collected</span></div>

  <div class="box">
    <h4>Trades of the Bounty Hunter</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Stalker.</strong> You read a quarry's trail and habits and strike from where he never looks; your Bushwhack deals extra dice against a foe who has not yet acted. <em>Mastery (10th):</em> once per scene, a perfect ambush against an unready quarry is an automatic critical that may end the chase before it starts.</li>
      <li><strong>The Posse Boss.</strong> You ride at the head of a hunting party, swear in hands to the chase, and may Demoralize a whole group at once. <em>Mastery (10th):</em> once per scene, your name alone breaks lesser fugitives who know it — they scatter, surrender, or freeze.</li>
      <li><strong>The Trailsman.</strong> You handle and run down mounts with ease, and ride harder than any man you hunt. <em>Mastery (10th):</em> once per scene, you run a quarry to ground that no horse and no head start could have saved.</li>
    </ul>
  </div>
  <div class="pageno">11</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>V. Worldly Callings</span></div>
  <h2 id="ix-c-drifter">Drifter</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Save Reflex · Attack Steady</p>
  <p>The Drifter belongs to no town and answers to no brand. Scout, tracker, horse-thief, bounty-man, or simply a soul
  who cannot stop moving — the Drifter survives by seeing first, striking once, and being elsewhere by dawn. They are the
  party's eyes on the trail and its knife in the dark.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">No Name Sticks.</span> You have used a dozen names and answered to all of them. What you did in one town follows you to the next only if a living soul carries it there on purpose, and every description of you is wrong in at least one particular that matters.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Position. Sudden Strike pays whenever somebody else has the foe&rsquo;s attention, and Evasion means the blast that catches the posse often does not catch you.</div>
    <div class="pays"><span class="k">You pay</span>Steady attack, a d8, and no answer at all to a thing that has already seen you and is walking straight at you.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td>Edge, Sudden Strike +1d6, Pathfinder</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+0</td><td class="c">+3</td><td class="c">+0</td><td>Ghost</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+1</td><td>Edge, Evasion, Trail</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+1</td><td class="c">+4</td><td class="c">+1</td><td>—</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td class="c">+1</td><td>Edge, Sudden Strike +2d6</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td class="c">+2</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+5</td><td class="c">+2</td><td>Edge, Uncanny Step</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+2</td><td class="c">+6</td><td class="c">+2</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+3</td><td class="c">+6</td><td class="c">+3</td><td>Edge, Sudden Strike +3d6</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+3</td><td class="c">+7</td><td class="c">+3</td><td>Vanish, Trail Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+3</td><td class="c">+7</td><td class="c">+3</td><td>Never Was Here</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+4</td><td class="c">+8</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+4</td><td class="c">+8</td><td class="c">+4</td><td>Sudden Strike +4d6, The Long Odds</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+4</td><td class="c">+9</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+5</td><td class="c">+9</td><td class="c">+5</td><td>Gone</td></tr>
    </tbody>
  </table>
  <h4>Sudden Strike</h4>
  <p>When you strike a foe who is unaware of you, or whom an ally is engaging (an Off-Guard target; see Conditions), you
  deal extra damage as shown — the patient violence of the ambush. The dice rise as you advance.</p>
  <h4>Pathfinder</h4>
  <p>You move at full speed through wilderness others must crawl through, leave a trail only the gifted can follow, and add
  your level to checks to track, forage, or find the way.</p>
  <h4>Ghost / Uncanny Step / Vanish</h4>
  <p>You learn to disappear. <em>Ghost</em> lets you hide even while briefly observed. <em>Uncanny Step</em> leaves no track
  on any surface. <em>Vanish</em> lets you drop from sight once per scene, as if the land itself closed over you — out here,
  perhaps it has.</p>
  <h4>Evasion</h4>
  <p>Your reflexes are inhuman. On a successful Reflex save against an effect that would harm an area — a blast, a cave-in,
  a sweep of fire — you take no harm at all rather than half. On a <em>critical</em> success, you also end your move in any
  open square adjacent to the danger.</p>
  <h4>Never Was Here</h4>
  <p>You have got so good at leaving that the leaving takes the arriving with it. After a night in a place you may spend an
  hour undoing your own presence in it: the ledger entry, the stall in the livery, the face behind the bar. Anyone
  questioned about you afterward remembers a man, remembers nothing useful, and grows less certain the harder they are
  pressed. Dogs and children are unaffected, and neither are the dead.</p>
  <h4>The Long Odds</h4>
  <p>Evasion becomes something worse for whatever is throwing at you. On a failed save against an effect Evasion would have
  halved, you take half instead of full; on a success you take none and may Step for free. The blast that catches the
  posse has caught you three hundred times, and you have gone under it three hundred times.</p>
  <h4>Gone</h4>
  <p>There is no situation you cannot walk out of. Once per session, as a free action at any moment including one in which
  you are held, bound, buried, grappled, surrounded, unconscious or falling, you are simply elsewhere: any place you
  could plausibly have reached on foot within the last hour, unharmed, with whatever you were carrying and one thing or
  one willing soul you had a hand on. Nothing that was watching can say how. The cost is that you leave: whatever you
  were in the middle of goes on without you, and the country between you and it is a day's ride wide by the time you
  think better of it.</p>

  
  <div class="box">
    <h4>Trails of the Drifter</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Ghost Trail.</strong> Gain a bonus to Sneak and Hide, and you may Hide in cover even while observed. <em>Mastery (10th):</em> once per scene, become wholly unseen for a round, striking from nowhere.</li>
      <li><strong>The Hard Trail.</strong> Ignore the toll of harsh country, weather, and want; +2 Fortitude against the elements. <em>Mastery (10th):</em> once per scene, shrug off the first wound or affliction that would lay you low.</li>
      <li><strong>The Hunter's Trail.</strong> You never lose a trail and gain +2 against ambush and to read a quarry. <em>Mastery (10th):</em> once per scene, study a foe a moment and learn the weakness that undoes it.</li>
    </ul>
  </div>
  <div class="pageno">12</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>V. Worldly Callings</span></div>
  <h2 id="ix-c-engineer">Engineer</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Reflex, Will · Attack Steady</p>
  <p>Everyone else out here is trying to survive the country. You are trying to make it hold still long enough to build
  something on. You came west with a transit or a powder licence or an apprenticeship you never finished, and what you
  have since learned is that the frontier is not short of brave men and is desperately short of anyone who can make a
  thing work twice. You are not a scholar. You are a tradesman with theory, which is worse for everybody who has to
  argue with you.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Every Machine Answers.</span> A quarter hour with any built thing and you can say what it does, what is wrong with it, and what putting it right would take: a lock, a pump, a press, a rifle action, a stamp mill, a clock. Whether you can fix it today depends on what is in the wagon. Whether you understand it depends on nothing at all.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Whatever the posse is short of. A frame is a gun, a wall, a hook or a wrench, and every one of them works in somebody else&rsquo;s hands as well as it works in yours.</div>
    <div class="pays"><span class="k">You pay</span>Steady attack, a d8, and a Beat and a point of Ingenuity each time. Your best round is the one that makes three other people&rsquo;s rounds better, which is a hard thing to feel proud of while it is happening.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td class="c">+2</td><td>Edge, The Contraption, Powder & Fuse</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+0</td><td class="c">+3</td><td class="c">+3</td><td>Jury-Rig</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+3</td><td>Edge, Discipline</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Cut the Charge</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Edge, The Contraption (second), Field Expedient</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>Edge, Overbuilt</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+2</td><td class="c">+6</td><td class="c">+6</td><td>The Contraption (third)</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+3</td><td class="c">+6</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>The Machine Age, The Contraption (fourth), Discipline Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>The Contraption (fifth), Proving Ground</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>The Standing Work</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+4</td><td class="c">+9</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+5</td><td class="c">+9</td><td class="c">+9</td><td>The Century Coming</td></tr>
    </tbody>
  </table>
  <h4>Ingenuity</h4>
  <p>You have a pool of <strong>Ingenuity</strong> equal to your WIT modifier + half your level (minimum 1), refreshed
  after a full rest and a chance to sit with your tools. It is the measure of how much of your attention your devices
  are still owed.</p>
  <h4>The Contraption</h4>
  <p>You have built one thing that exists nowhere else. Choose a frame from the list below; you build another at 5th, 8th, 10th and 11th level, and you may rebuild any of them over a night with your tools. Working a frame costs 1 Ingenuity and a Beat, and here is the part that matters: anybody you have shown it to may work it instead of you. On a natural 1, or any time the Keeper rules you have asked too much of it, it breaks; mending it takes an hour and your hands, and it is never quite the same afterward. You have stopped expecting it to be.</p>
  <div class="box">
    <h4>A Contraption&rsquo;s Frames</h4>
    <ul class="dash">
      <li><strong>The Repeater.</strong> A gun fed by a clock spring and a drum. It Strikes at your attack for 1d10 and never wants reloading. Wind it for a Beat and it fires once on its own at the end of each of your turns until the spring runs down, which takes three rounds.</li>
      <li><strong>The Bulwark.</strong> A folding plate on a tripod that sets in a Beat and gives hard cover to two souls behind it. It weighs what you would expect. Dragging it forward costs somebody a Beat, and somebody always volunteers once the shooting starts.</li>
      <li><strong>The Winch.</strong> A hooked line on a geared drum. Spend a Beat to take hold of one creature within 30 feet: Fortitude (DC 10 + half your level + WIT) or be dragged 10 feet toward you and left Prone. Things with claws in the ground resist it. Things in the air do not.</li>
      <li><strong>The Governor.</strong> A brass regulator that clamps onto any working mechanism and persuades it to stop: a lock, a pump, a rifle action, a jaw that opens on a hinge. It seizes for a round. Against a made thing that fights, a round is a great deal.</li>
      <li><strong>The Alarum.</strong> Wire, a bell and a spring, set across the approaches. Nothing crosses your camp unannounced, and you sleep like a man who has been paid.</li>
      <li><strong>The Listening Horn.</strong> A wall stops being a wall. Set the bell against it and hear what is said on the other side, at a distance the speaker would never credit.</li>
      <li><strong>The Diving Lamp.</strong> Burns wet, burns under, burns in the bad air at the bottom of a shaft, and does not go out because something in the dark would prefer it did.</li>
      <li><strong>The Heliograph.</strong> Mirrors and a shutter on a folding stand. In daylight you can hold a conversation with somebody a mile off, and so can anybody who knows the code, which is the part worth thinking about.</li>
    </ul>
  </div>
  <h4>Powder &amp; Fuse</h4>
  <p>Blasting is a trade and you served it. You cut, time and place a charge without the Keeper calling for a check, and you know to the yard how far back is far enough. Each dawn you prepare two charges of your own, and any prepared explosive you set yourself deals an extra die of its damage.</p>
  <h4>Jury-Rig</h4>
  <p>Once per scene, put something back into service with wire, a strap, and language nobody should hear. A broken tool, a jammed action, a snapped trace, a door off its hinge: it works for the rest of the scene, and afterward it is broken again and rather worse.</p>
  <h4>Cut the Charge</h4>
  <p>You know what a blast wants to do and where it will go. You take half damage from any explosion, and so does any ally you had a moment to shout at. The shout is required. More of this trade is shouting than the recruiting posters admit.</p>
  <h4>Field Expedient</h4>
  <p>Given ten minutes, a few hands and whatever the ground offers, you throw up a work: a barricade, a footbridge, a sluice, a firing step, a hoist. It is ugly, it holds for the scene, and it changes what the ground is worth.</p>
  <h4>Overbuilt</h4>
  <p>You have stopped building things that fail when it matters. Your contraptions and field works no longer break on a natural 1, and break at all only when the Keeper rules something genuinely beyond their design was asked of them.</p>
  <h4>The Machine Age</h4>
  <p>At 10th level the things you make outlast the making of them. Choose one of your contraptions: it costs no Ingenuity to work, it does not break, and it can be handed to somebody else and will work for them. You have crossed the line between a trick and a tool, and the century coming will be built out of what is on your side of it.</p>
  <h4>Proving Ground</h4>
  <p>You have finally got somewhere to test things before they are needed. Given a day and a place to work, you may rebuild
  any contraption into any other frame, and once per scene you may declare that a contraption you are working has been
  tuned for exactly this: it does not break on a natural 1, and its save DC rises by 2 against the specific thing you
  built the tuning for. You were up all night. It shows in the work and it shows in your face.</p>
  <h4>The Standing Work</h4>
  <p>Given four hours, a place and hands to help, you raise something that does not travel: a redoubt, a sluice, a spanned
  gap, a wall with a gate in it. It gives cover the Keeper rates as greater, holds against anything you can still shoot
  for a scene, and can be worked by anyone you have shown it to. It stays where you built it after you have gone, which
  is more than most men manage.</p>
  <h4>The Century Coming</h4>
  <p>Once per session, you build a thing that does not exist yet. Name the problem in front of the posse and describe the
  machine that answers it; if the Keeper can imagine it built out of what this century has — iron, steam, powder, wire,
  glass, water and time — then you have built it, over an hour and whatever it costs, and it works once, fully, at the
  scale the problem needs. A rail car that outruns a thing on the track behind it. A cage that will hold what nothing
  holds. A light that reaches the far side of the valley. Afterward it is scrap, and you are the only one who knows how
  it went together, which is a heavy thing to be.</p>

  <div class="quote">
    "He would not tell us what the thing in the crate was for. He said it was for one job and one
    job only and that we would know the job when we saw it. Then the bridge went and he opened the
    crate, and I will say this: he did know the job when he saw it."
    <span class="src">— deposition of a Central Pacific gang boss, Humboldt division</span>
  </div>

  <div class="box">
    <h4>Disciplines of the Engineer</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Powderman.</strong> Charges answer to you. Any explosive you prepare may be shaped: choose which side of it is dangerous, and allies outside that arc take nothing at all. <em>Mastery (10th):</em> once per scene, bring down a structure, a span or a shaft exactly as you intend, in the direction you intend.</li>
      <li><strong>The Machinist.</strong> Given a day and a workshop you permanently improve one weapon or tool: an extra shot before reloading, one step less Kickback, a jam that clears itself. Only one item at a time carries your work. <em>Mastery (10th):</em> once per scene, one of your contraptions acts on its own for a round, taking a Beat's action you name.</li>
      <li><strong>The Bridgewright.</strong> Spans, shafts and crossings. You and anyone following you ignore difficult ground and broken country, and a gap that stops a party stops you for ten minutes. <em>Mastery (10th):</em> once per session, build in a day what should have taken a crew a week, and it stands.</li>
    </ul>
  </div>
  <h2 id="ix-c-gambler">Gambler</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Reflex, Will · Attack Steady</p>
  <p>Every town past the railhead has a green-felt table and a soul who lives by it. The Gambler reads people the way the
  Prospector reads rock — the tell, the bluff, the breaking nerve — and has made a working peace with chance that most folk
  only pray for. They are charming, watchful, and very hard to rattle, for anyone who has seen a year's wages turn on a
  single card has learned that the trick was never the card. The trick is knowing the odds — and knowing when to break them. Where the <strong>Gambler background</strong> of Chapter IV grants but a single knack of the green table, this Calling is the whole craft — a life given wholly over to chance, and to the bending of it.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Never a Stranger at the Table.</span> Any game running in any town has a chair for you and credit enough to sit down with. By the time it breaks up you know what the table knows: who is flush, who is lying, who is leaving in the morning, and who owes money to the wrong man.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The dice themselves. Favor reaches into any roll at the table, yours or a foe&rsquo;s, and there is no round it cannot touch.</div>
    <div class="pays"><span class="k">You pay</span>The thinnest Blood of any Worldly Calling, and a pool that empties whether the gamble paid or not. That is rather the point of it.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td class="c">+2</td><td>Edge, Fortune's Favor, Cardsharp</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+0</td><td class="c">+3</td><td class="c">+3</td><td>Hedge Your Bets</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+3</td><td>Edge, Game</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Cold Deck</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Edge, Ace in the Hole</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>Edge, Press Your Luck</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+2</td><td class="c">+6</td><td class="c">+6</td><td>Stack the Odds</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+3</td><td class="c">+6</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>The House Always Wins, Game Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>Marked Deck</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Table Stakes</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+4</td><td class="c">+9</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+5</td><td class="c">+9</td><td class="c">+9</td><td>All In</td></tr>
    </tbody>
  </table>
  <h4>Fortune's Favor</h4>
  <p>Chance leans your way, and you have learned to lean back. Keep a pool of <strong>Favor</strong> equal to your PRE
  modifier + half your level (minimum 1), refreshed each dawn; you also recover 1 point whenever you stake something real on
  a genuine risk and let the dice fly. Spend a point to <strong>reroll any one d20 you just rolled</strong> and keep the
  better result, to add 1d6 to a check, or to force a foe to reroll a hit or a save made against you. Favor spent is gone
  whether the gamble pays or not — that is rather the point of it.</p>
  <h4>Cardsharp</h4>
  <p>You are trained in games of chance and the arts that bend them — palming, marking, dealing seconds, and reading a face
  for the truth it is trying to hide. Gain +2 on Deceive, sleight of hand, and Insight at any table, and you know at a
  glance whether a game is honest. In a crowd, your hands move quicker than a witness's eye.</p>
  <h4>Hedge Your Bets</h4>
  <p>You rarely lose it all at once. When you fail a check, you may spend a point of Favor to treat it as a success instead —
  but the Keeper names the price: a complication, a debt, a watching eye, a worse spot down the road. You win the hand. The
  game goes on.</p>
  <h4>Cold Deck</h4>
  <p>Once per scene, free of any cost, force a single reroll — your own, or that of a foe whose luck has run too good. And
  when you spend Favor to reroll, you may instead simply <strong>take the dealt card</strong>: treat the die as though it had
  come up an 11, no better and no worse, for the moments when steady is worth more than lucky.</p>
  <h4>Ace in the Hole</h4>
  <p>You are never quite as cornered as you look. Once per scene, produce something you "had ready all along" — a hideout
  derringer, a palmed knife, a marked card, a bribed dealer, a second key. And when you are reduced to 0 Blood, you may spend
  3 Favor to come up at 1 instead and take an immediate action. The Gambler's oldest trick is not being dead when everyone
  else has folded.</p>
  <h4>Press Your Luck</h4>
  <p>Before you roll, you may <strong>ante</strong>: wager a point of Nerve or of Blood on the outcome. Succeed, and you win
  big — a critical success on a hit, an extra Beat on a skill, a boon the Keeper honors. Fail, and you lose the ante and the
  failure cuts deeper. The bolder the bet, the richer the pot the Keeper may allow.</p>
  <h4>Stack the Odds</h4>
  <p>Your luck spills onto those who stand with you. Once per round, free, grant an ally who can see you +1 to
  a roll; and you may spend your own Favor on their behalf, letting a companion reroll as though the luck were theirs.</p>
  <h4>The House Always Wins</h4>
  <p>At 10th level you have made chance a silent partner. Your Favor refreshes at the start of every scene rather than each
  dawn. And once per session you may <strong>call the turn</strong>: declare, before it is cast, that a single die — yours, or
  one thrown against you — comes up its best or its worst, a natural 20 or a natural 1, as though fate had dealt it from the
  bottom of the deck for you. The bill for such certainty always comes due. It simply does not come due tonight.</p>
  <h4>Marked Deck</h4>
  <p>You have stopped needing to see the cards. Once per scene you may spend 2 Favor to know one true thing about a person
  in front of you that they are actively hiding — what they are carrying, what they mean to do next, or who they answer
  to — as though you had caught the flicker of it in their hands. It is never the whole hand. It is enough to bet on.</p>
  <h4>Table Stakes</h4>
  <p>You can put something on the table that is not money. Once per scene, name a stake — an hour of your life, a memory,
  the use of your gun hand, a favour owed to somebody frightening — and gain 1d6 Favor at once. The Keeper decides what
  the stake costs and when it is collected, and the Keeper will collect it. Nobody who plays this long plays for chips.</p>
  <h4>All In</h4>
  <p>Once per session you may go all in. Declare it before any roll that matters, spend every point of Favor you have, and
  take the following for the rest of the scene: every d20 you roll is rolled twice and you keep the better, you cannot
  be reduced below 1 Blood, and any single die anyone throws in that scene may be rerolled by you once, whoever threw
  it. When the scene ends, the house takes its cut. You lose all Favor until the next dawn, you take a lasting mark of
  the Keeper's choosing — a debt, a name, a limp, a face you now owe — and everyone who watched it happen knows they
  watched something they will not see twice.</p>

  <div class="quote">"I have lost more money than most men will ever see, and I will give you the secret of it free, since you
    won't believe me anyhow: the cards do not care. The cards never cared. You play the man, and the odds, and your own cold
    nerve — and you leave the praying to folks who like to lose."
    <span class="src">— Eulalie &ldquo;Lucky&rdquo; Devereaux, who was not, in the end, lucky</span></div>
  
  <div class="box">
    <h4>Games of the Gambler</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Charmer.</strong> Spend Favor on Deceive, Persuade, and reading a room, and gain a bonus at any table. <em>Mastery (10th):</em> once per scene, bend a crowd or a single mark wholly to your play.</li>
      <li><strong>The Duelist.</strong> Spend Favor to add luck to your Strikes and to turn a blow aside. <em>Mastery (10th):</em> once per scene in a duel, turn a foe's hit into a miss, or your miss into a killing crit.</li>
      <li><strong>The Mechanic.</strong> Your Favor pool grows, and once per scene you may set a die to any face you please. <em>Mastery (10th):</em> once per scene, stack fate entirely — take the better result on every roll for a round.</li>
    </ul>
  </div>
  <div class="pageno">13</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">V. Worldly Callings</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-gunhand">Gunhand</h2>
  <p class="statline">Hit Die d10 · Trained Skills 2 + WIT · Strong Saves Fortitude, Reflex · Attack Practiced</p>
  <p>Some folk are simply faster than the rest, and have made their peace with what that means. The Gunhand is the
  gunfighter, the shootist, the hired iron — a person who has reduced the question of survival to who clears leather
  first. They are not brave so much as quick, and they know the difference even if no one else does. The Gunhand is built
  for the gun rules of Chapter XI; learn the Iron Code well.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Let Him Draw First.</span> Against a foe who has already drawn on you, you act first. No roll, no argument. There are men out here who have built an entire career on standing very still and waiting to be threatened.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Iron, and the choice of how to spend it. Deadly Aim trades accuracy for damage at a rate that improves as you climb, and No Quarter turns a killing shot into another shot.</div>
    <div class="pays"><span class="k">You pay</span>Nothing but the gun. No working, no blessing, no trick that reaches a thing lead cannot, and the day you meet one you are the man reloading.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+1</td><td class="c">+2</td><td class="c">+2</td><td class="c">+0</td><td>Edge, Deadly Aim, Gunhand's Edge</td></tr>
      <tr><td>2</td><td class="c">+2</td><td class="c">+3</td><td class="c">+3</td><td class="c">+0</td><td>Trick Shot</td></tr>
      <tr><td>3</td><td class="c">+3</td><td class="c">+3</td><td class="c">+3</td><td class="c">+1</td><td>Edge, School</td></tr>
      <tr><td>4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td>—</td></tr>
      <tr><td>5</td><td class="c">+5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td>Edge, Lightning Hand</td></tr>
      <tr><td>6</td><td class="c">+6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+7</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td>Edge</td></tr>
      <tr><td>8</td><td class="c">+8</td><td class="c">+6</td><td class="c">+6</td><td class="c">+2</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+9</td><td class="c">+6</td><td class="c">+6</td><td class="c">+3</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+10</td><td class="c">+7</td><td class="c">+7</td><td class="c">+3</td><td>No Quarter, School Mastery</td></tr>
      <tr><td>11</td><td class="c">+11</td><td class="c">+7</td><td class="c">+7</td><td class="c">+3</td><td>Second Nature</td></tr>
      <tr><td>12</td><td class="c">+12</td><td class="c">+8</td><td class="c">+8</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+13</td><td class="c">+8</td><td class="c">+8</td><td class="c">+4</td><td>Six Living Men</td></tr>
      <tr><td>14</td><td class="c">+14</td><td class="c">+9</td><td class="c">+9</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+15</td><td class="c">+9</td><td class="c">+9</td><td class="c">+5</td><td>The Fastest Alive</td></tr>
    </tbody>
  </table>
  <h4>Deadly Aim</h4>
  <p>You may take a –2 penalty on a firearm attack to add +4 to its damage. The penalty and bonus both increase at 5th
  level (–3 / +6) and 9th (–4 / +8).</p>
  <h4>Gunhand's Edge</h4>
  <p>You gain a pool of <strong>Edges</strong> — sharp little tricks. Choose one combat Edge from Chapter IX at 1st level
  and at every odd level after. These are in addition to the Edges every character earns.</p>
  <h4>Trick Shot</h4>
  <p>Once per round, before rolling, you may declare a called shot — to disarm, to wound a limb, to shatter a lantern or
  a rope, to ring a skull with a barrel or a butt and leave the man <strong>Stunned</strong> a round. Take –4 to the
  attack; on a hit, the Keeper grants the effect in place of, or alongside, reduced damage. Under
  the Iron Code (Chapter XI), a <em>critical</em> hit on a called shot grants the effect <em>and</em> full damage.</p>
  <h4>Lightning Hand</h4>
  <p>Your reflexes outrun thought. Drawing a holstered weapon costs no action (a free Interact), and you act before
  anyone you have not yet met in a fight unless they, too, have this knack. Once per fight you may take an extra Strike
  as a reaction the instant initiative is rolled.</p>
  <h4>No Quarter</h4>
  <p>When you drop a foe to 0 Blood or below with a firearm, you may immediately make one more attack against a different
  target within range, free of the Multiple Attack Penalty. There is no limit to how many times this may chain in a single
  round but your own luck.</p>
  <h4>Second Nature</h4>
  <p>The gun has stopped being a thing you use. You reload, clear a jam, change hands and take cover without spending a
  Beat on any of it, you never suffer a penalty for shooting from horseback or in the dark at a shape you have already
  hit once, and a called shot costs you 2 less on the roll. It has been years since you had to think about the part in
  the middle.</p>
  <h4>Six Living Men</h4>
  <p>You have cleared a room before and you can do it again. Once per scene, spend your whole turn and name up to your PRE
  modifier in targets you can see, minimum two: make one Strike against each at your full attack. Missing one ends it
  there. Men who have seen it done stop being brave in the order they were standing.</p>
  <h4>The Fastest Alive</h4>
  <p>There is nothing left to be faster than. Once per session, declare it at any point in any scene: you act first,
  before every creature present regardless of what any die said, and for that one turn every Strike you make hits
  without a roll and counts as a critical against anything you can still shoot. Then it is over, and you are a man
  standing in the smoke with an empty gun and a full second of nothing to do. You are Slowed for the following round,
  and every soul who lived through it will carry the story, which is how the next one finds you.</p>

  <div class="quote">
    "A pistol is an argument that ends the conversation. Most arguments out here
    were never worth starting, which is the one thing a fast man learns too late."
    <span class="src">— Marshal T. Coyle, retired in both senses of the word</span>
  </div>
  
  <div class="box">
    <h4>Schools of the Gun</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Fanning Hand.</strong> With a single-action revolver you may fan a second Strike each round at the Multiple Attack Penalty without spending an extra Beat. <em>Mastery (10th):</em> once each round, dropping a foe lets you immediately Strike another in range at no penalty.</li>
      <li><strong>The Fast Draw.</strong> You always act first in a one-on-one draw, and your first Strike of a fight gains +1. <em>Mastery (10th):</em> the first shot you fire in a scene is a critical hit if it lands.</li>
      <li><strong>The Long Rifle.</strong> Ignore the penalty at the first range increment, and Aim as a single Beat. <em>Mastery (10th):</em> a braced, aimed shot ignores cover and concealment and is an automatic critical against a foe who has not yet acted.</li>
    </ul>
  </div>
  <div class="pageno">14</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>V. Worldly Callings</span></div>
  <h2 id="ix-c-marshal">Marshal</h2>
  <p class="statline">Hit Die d10 · Trained Skills 4 + WIT · Strong Saves Fortitude, Will · Attack Practiced</p>
  <p>Lawman, cavalry sergeant, wagon-boss, or self-appointed keeper of a town that never asked — the Marshal leads. Their
  gift is not the fast draw but the steady one, the voice that keeps frightened people pointed the right way when everything
  in them wants to run. A Marshal rarely dies alone.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Your Word Is the Record.</span> What you write down becomes the official account of it. A wire sent over your name is believed at the other end, a man you name as wanted is wanted, and a killing you rule justified stays ruled, in every town that recognizes any law at all. Being wrong on paper is a slower kind of trouble than being wrong in the street, and it takes longer to catch you.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Other people&rsquo;s turns. Command hands an ally a whole action out of turn, which is worth more damage than you will ever deal yourself.</div>
    <div class="pays"><span class="k">You pay</span>You will not top a damage table and you should stop reading them. Your Calling is spent on the posse, and it shows up in the ledger as somebody else&rsquo;s good round.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+1</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Command, Reputation</td></tr>
      <tr><td>2</td><td class="c">+2</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Hold the Line</td></tr>
      <tr><td>3</td><td class="c">+3</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Oath</td></tr>
      <tr><td>4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>—</td></tr>
      <tr><td>5</td><td class="c">+5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Unflinching</td></tr>
      <tr><td>6</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge</td></tr>
      <tr><td>8</td><td class="c">+8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+9</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Last Stand, Oath Mastery</td></tr>
      <tr><td>11</td><td class="c">+11</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Deputize</td></tr>
      <tr><td>12</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+13</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>The Long Arm</td></tr>
      <tr><td>14</td><td class="c">+14</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+15</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>This Is My Town</td></tr>
    </tbody>
  </table>
  <h4>Command</h4>
  <p>As an action, bark an order. One ally within earshot may immediately take a single action — a shot, a move, a check —
  out of turn, gaining your PRE modifier as a bonus. Usable a number of times per scene equal to your PRE modifier (minimum 1).</p>
  <h4>Reputation</h4>
  <p>Your name carries. Add your level to checks to rally, deputize, requisition, or overawe, and choose at 1st level whether
  folk mostly fear you or trust you. Either opens doors; each closes others.</p>
  <h4>Hold the Line / Unflinching</h4>
  <p>Allies within sight of you gain +1 on saves against fear and the uncanny, rising to +2 at 5th level, when you yourself
  become immune to being Frightened. Courage, it turns out, is contagious — the only blessing in this book that is.</p>
  <h4>Last Stand</h4>
  <p>Once per session, when an ally within sight would drop to 0 Blood, you may shout them upright: they remain conscious and
  acting until the end of the fight or until struck again. Some Marshals have held a doorway with five dead men still standing
  at their word.</p>
  <h4>Deputize</h4>
  <p>You can make a lawman out of a shopkeep. Over ten minutes, swear in up to your PRE modifier in willing souls, minimum
  two: for the next day they gain +2 on saves against fear, count as trained in one skill you name, and may take the
  Ready action on your word without spending a Beat. Sworn hands who die under your badge are on your account, and the
  town will keep that account whether you do or not.</p>
  <h4>The Long Arm</h4>
  <p>Word of you travels faster than you do. In any settlement inside a week's ride, you may send ahead: when you arrive, a
  thing you asked for has been done — a man held, a road watched, a room kept, a wire sent on. Once per session, and
  never a thing that takes courage from somebody who has none.</p>
  <h4>This Is My Town</h4>
  <p>Once per session, plant yourself and say it. Name a place you can see the whole of — a street, a church, a bridge, a
  camp — and for the rest of the scene nothing hostile crosses into it without beating your Will save, every ally inside
  it is immune to fear and heals 1d8 Blood the first time they drop below half, and you may Command any ally within it
  as a free action once per round instead of once per scene. You may not leave the ground you named while it stands.
  Whatever wanted in will still be out there at dawn, and it will know your face now, and where you sleep.</p>

  <div class="quote">
    "I never asked to be followed. I only stood where the road forked and would not move,
    and after a while there were people standing behind me. That is the whole of leadership.
    That, and never letting them see you reckon the odds."
    <span class="src">— from the deposition of a wagon-boss, Fort Reliance</span>
  </div>
  
  <div class="box">
    <h4>Oaths of Office</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Lawman.</strong> Your commands carry weight — a bonus to Demoralize and to rally — and you may deputize allies for a scene. <em>Mastery (10th):</em> once per scene, your word stays a hand: a foe must lay down arms or stand frozen a round.</li>
      <li><strong>The Manhunter.</strong> Name a quarry; gain bonuses to track, read, and strike them. <em>Mastery (10th):</em> your mark cannot shake you, and once per scene you land a decisive, fight-ending blow or capture against them.</li>
      <li><strong>The Shield.</strong> You may intercept a blow meant for an ally at your side. <em>Mastery (10th):</em> once per scene, become the only target the enemy may strike, or turn aside a killing blow aimed at another.</li>
    </ul>
  </div>
  <div class="pageno">15</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">V. Worldly Callings</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-mountain">Mountain Man</h2>
  <p class="statline">Hit Die d10 · Trained Skills 6 + WIT · Strong Saves Fortitude, Will · Attack Practiced</p>
  <p>Some men went up into the high country to trap beaver and never entirely came back down. The Mountain Man lives where
  the maps give out — the peaks, the deep timber, the snowbound passes — trapping, hunting, and reading a wilderness that
  kills the unready in an afternoon. He is hard as a hickory axe-handle, easy with a long rifle, and short on conversation,
  and he has seen things in the deep snow that he does not, as a rule, talk about. When something out of the dark comes down
  out of the hills, he is often the only soul who already knows its name.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Half a Wild Thing.</span> Horses stand for you. Dogs stop barking. Game looks at you a long moment before it bolts, and now and then it does not bolt. Men cross the street, and the ones who do not cross the street are generally the sort you would rather had.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Reach. The Hawken and Dead Aim between them put more on one distant shot than anything else a Worldly soul carries.</div>
    <div class="pays"><span class="k">You pay</span>A slow gun and slower ground. Everything you are good at wants range, patience and open country, and a room takes all three away at once.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+1</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Hawken Rifle, Dead Aim 1d6, Hard Country</td></tr>
      <tr><td>2</td><td class="c">+2</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Read Sign</td></tr>
      <tr><td>3</td><td class="c">+3</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Range</td></tr>
      <tr><td>4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Skinner</td></tr>
      <tr><td>5</td><td class="c">+5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Dead Aim 2d6</td></tr>
      <tr><td>6</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Iron Constitution</td></tr>
      <tr><td>7</td><td class="c">+7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Mountain Sense</td></tr>
      <tr><td>8</td><td class="c">+8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>Unbroken</td></tr>
      <tr><td>9</td><td class="c">+9</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>King of the High Country, Dead Aim 3d6, Range Mastery</td></tr>
      <tr><td>11</td><td class="c">+11</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Dead Aim 4d6, Winter Count</td></tr>
      <tr><td>12</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+13</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>The Far Shot</td></tr>
      <tr><td>14</td><td class="c">+14</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+15</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Mountain Knows You</td></tr>
    </tbody>
  </table>
  <h4>Hawken Rifle</h4>
  <p>The heavy plains rifle is your right arm. With a two-handed rifle you ignore the penalty at the first range increment,
  and the first reload each round costs no extra Beat. You keep your piece clean, charged, and to hand, and you do not miss
  the shots a lesser hand calls lucky.</p>
  <h4>Dead Aim</h4>
  <p>Spend a Beat to steady your rifle — this is the <em>Aim</em> action — and your next shot this turn deals the extra
  damage shown on a hit: <strong>1d6</strong> at 1st level, <strong>2d6</strong> at 5th, <strong>3d6</strong> once you are King of the High Country, and <strong>4d6</strong> at 11th. Patience, a good rest, and a held breath are worth more than any luck.</p>
  <h4>Hard Country</h4>
  <p>The wilderness is your parlor. You are never lost in wild country, you ignore natural difficult terrain — scree,
  deadfall, brush, snow — and a day's hunting or foraging feeds you and up to four others. Cold, altitude, thirst, and hunger
  that would break other men, you simply endure.</p>
  <h4>Read Sign</h4>
  <p>Gain +2 to Survival and Notice to track and to read what passed — how many, how long ago, and whether it walked on two
  legs or something else. You leave little trail of your own: the DC to track <em>you</em> rises by 2, and you know when you
  are being followed.</p>
  <h4>Skinner</h4>
  <p>Spend a Beat to study a beast or an unnatural thing (Survival or Lore: Occult) and learn one weakness or trait the
  Keeper will honor. Against animals and the wild things of the dark you deal <strong>+1 damage</strong>, and you may harvest
  a kill — hide, fat, claw, tooth, gland — for coin, for trade, or for the makings of a remedy or a ward.</p>
  <h4>Iron Constitution</h4>
  <p>The mountains have been trying to kill you for years and have not managed it. Gain a bonus against cold, heat, thirst,
  hunger, poison, and disease, and once per scene you may reroll a failed Fortitude save. You heal a little faster than you
  have any right to.</p>
  <h4>Mountain Sense</h4>
  <p>You cannot be caught flat in the wild. You are never surprised out of doors, you act first in the opening round of any
  ambush you spring or spot, and predators give you a wide berth — they know a bigger one when they smell it.</p>
  <h4>Unbroken</h4>
  <p>You have seen what the high country hides in the deep snow, and naming it did not break you. Gain a bonus on Dread
  Checks in the wilderness, and you may spend a Beat to steady a companion who can see you, lending them your nerve to face
  what is coming down out of the hills.</p>
  <h4>King of the High Country</h4>
  <p>At 10th level the wilderness is yours, and everything in it knows your step. Your Dead Aim rises to 3d6; while out of
  doors you gain a standing +1 to Defense and to all saves; and once per scene a single steadied rifle shot is an automatic
  critical against a living or unnatural quarry you have studied with Skinner. The mountain does not give up its king easily,
  and neither, in the end, do you.</p>
  <h4>Winter Count</h4>
  <p>You have kept a count of your winters the old way, and the years are worth something. Once per session, name any
  wilderness, weather, beast, trail or man you have plausibly met before, and you have: you know one true and useful
  thing about it that nobody in the posse could have known, and you gain +4 on your next check concerning it. The Keeper
  decides what the year was.</p>
  <h4>The Far Shot</h4>
  <p>Distance has stopped being a penalty and started being an advantage. You suffer no penalty for range with a long gun
  at any distance you can see, and a steadied shot taken from beyond the reach of anything shooting back ignores cover
  that is not solid stone. The rifle was always the argument. Standing far enough away was the rest of it.</p>
  <h4>The Mountain Knows You</h4>
  <p>The high country has decided you belong to it. Once per session, out of doors and away from a town, call on it: for
  the rest of the scene the ground, the weather and the beasts of that place are on your side. Terrain hinders your
  enemies and never you, wind and snow and dark obscure them and never you, and one beast of the country arrives to
  fight beside you until the scene ends. Every Dead Aim shot you take that scene is an automatic critical against
  anything living. The mountain asks in return that you never bring the thing you are hunting into a town, and it will
  know.</p>

  <div class="quote">"Folks down in the settlements think the wild is empty. I have wintered alone above the timberline with
    the wind screaming for three months, and I will tell you it is the most crowded place I know. Something up there counts
    every man who comes. I just learned to count back."
    <span class="src">— Eli Six-Bears, trapper, who came down out of the Bitterroots one spring and would not say why</span></div>

  <div class="box">
    <h4>Ranges of the Mountain Man</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Hermit.</strong> You have gone native in the deep country and made a peace of sorts with what lives there: beasts will not harm you unbidden, you find shelter and forage anywhere, and you read the land's moods. <em>Mastery (10th):</em> once per scene, call on the wild — a beast comes to your aid, a sudden storm covers your retreat, or the country itself turns a pursuer aside.</li>
      <li><strong>The Hunter.</strong> Name a quarry as the Marshal marks a man, but for the beasts and monsters of the wild: gain bonuses to track, read, and damage it. <em>Mastery (10th):</em> once per scene, a Dead Aim shot against your quarry strikes a killing blow that fells even a great beast.</li>
      <li><strong>The Trapper.</strong> You set deadfalls, snares, and pit-traps swiftly and well; a trap on ground you have readied forces the unwary to save or be caught — Grabbed, Slowed, or wounded as the trap allows. <em>Mastery (10th):</em> once per scene, a sprung trap is ruinous — the quarry, beast or man, is caught fast and badly hurt.</li>
    </ul>
  </div>
  <div class="pageno">16</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>V. Worldly Callings</span></div>
  <h2 id="ix-c-prospector">Prospector</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Fortitude, Reflex · Attack Steady</p>
  <p>The Prospector came west for the one honest promise the country ever made: that what lies in the ground belongs to
  whoever is fool enough to dig it out. Part surveyor, part gambler, part blasting-man, they read rock and water and luck
  the way others read scripture — and they have learned, the hard way, that some seams were sealed for a reason, and that
  the deepest shafts open onto more than ore.</p>
  <div class="quote">&ldquo;We followed the vein down past where the air goes wrong, and there he sat in his rusted Spanish iron, four hundred years dead and still holding the box like he meant to keep it. We took the gold. I have wished, every night since, that we had not.&rdquo;
    <span class="src">&mdash; J. Halloran, testimony given at the Widow&rsquo;s Comfort inquest</span></div>

  <p class="perk"><span class="lbl">Perk</span><span class="nm">Filed and Recorded.</span> Any ground nobody has claimed, you can claim, and you know exactly how to make it stick: the stakes, the posted notice, the recorder's fee, the wording that survives a challenge in a territorial court. Whether it is worth anything is a separate question. Being yours has started more shooting out here than gold ever did.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Everything at once. Charges climb from 2d6 to 5d6, Demolitionist doubles the dice against the unliving, and a burst does not much care how many of them there are.</div>
    <div class="pays"><span class="k">You pay</span>A count. Charges are prepared at dawn and they run out, and the fight that goes long finds you standing there holding a pick.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+2</td><td class="c">+0</td><td>Edge, Pay Dirt, Powderman</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+3</td><td class="c">+0</td><td>Grubstake</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+3</td><td class="c">+1</td><td>Edge, Claim</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td>Dowse, Field Inventions</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td>Edge, Assayer's Eye</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td>Demolitionist</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td>Edge, Sapper</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+6</td><td class="c">+2</td><td>Overcharge</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+6</td><td class="c">+3</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+7</td><td class="c">+3</td><td>The Mother Lode, Claim Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+7</td><td class="c">+3</td><td>The Deep Vein</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+8</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+8</td><td class="c">+4</td><td>Bring It Down</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+9</td><td class="c">+4</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+9</td><td class="c">+5</td><td>What the Ground Owes</td></tr>
    </tbody>
  </table>
  <h4>Pay Dirt</h4>
  <p>Luck is a muscle, and yours is overdeveloped. You have a pool of <strong>Pay Dirt</strong> equal to your WIT modifier
  + half your level (minimum 1), refreshed each dawn. Spend a point to add 1d6 to any check tied to searching, surviving,
  digging, or scrounging — or to declare a small fortunate find: a length of fuse, a sound timber for cover, a trickle of
  water, a glint of something useful in the dirt. The Keeper says how much it amounts to; you only ever guarantee that
  there is <em>something</em>.</p>
  <h4>Powderman</h4>
  <p>You handle blasting powder, dynamite, and raw nitro as easily as another handles a fork. Each dawn you prepare a number of <strong>field charges</strong> equal to your WIT modifier + half your level (minimum 2) — sticks, bottles, and the specialty devices you have learned to build. A stick of dynamite deals <strong>2d6 fire</strong> in a 10-foot burst (basic Reflex, DC 10 + half your level + WIT), rising to 3d6 at 4th level, 4d6 at 7th, and 5d6 at 10th. You may shape or time any charge — shorten or stretch a fuse, narrow the burst to a line, or widen it by 5 feet at the cost of a die. Best of all, your explosives never mishap on your account: a natural 1 merely fizzles rather than going off in your hand. Most powdermen learn that last rule posthumously.</p>
  <h4>Grubstake</h4>
  <p>You are never quite empty-handed. You always carry working prospecting and mining tools, and once per session you may
  produce one mundane but useful item you "had all along" — a spare pick, a coil of wire, a candle-stub, a creased claim-map
  of the very ground you stand on. You also know the outfitters; in any town of size you may secure a fair price and a line
  of credit no questions asked, so long as your luck holds.</p>
  <h4>Dowse</h4>
  <p>With a forked rod, a pan, or a pendulum and a minute's concentration, make a Survival check to sense the nearest
  <strong>water, ore, or worked metal</strong> within a quarter-mile, and its rough direction and depth. The same gift,
  pushed, finds darker things — buried bodies, salted graves, and the <em>bad veins</em> where the Old Dark runs close to
  the surface. The rod always tells the truth. It simply does not always tell you what you hoped to hear.</p>
  <h4>Field Inventions</h4>
  <p>You are forever modifying your kit by lamplight. Choose <strong>two Devices</strong> from the list below at 4th level, and one more at 6th and at 8th; you may rebuild your loadout each dawn. Unless noted, readying a Device spends one prepared charge.</p>
  <div class="box">
    <h4>A Powderman&rsquo;s Devices</h4>
    <ul class="dash">
      <li><strong>Concussion Charge.</strong> A muffled blast of nonlethal force that deafens; gentle on walls, hard on men.</li>
      <li><strong>Flash Powder.</strong> A blinding crack in a 10-foot burst; Fortitude or be dazzled a round, <strong>Blinded</strong> for the scene on a critical failure.</li>
      <li><strong>Grapnel &amp; Line.</strong> A launched hook and rope to scale a height, swing a gap, or drag an object — or a man — off his feet.</li>
      <li><strong>Repeating Fuse.</strong> Throw or place a charge as a single Beat rather than two, and add +2 to land it where you mean to.</li>
      <li><strong>Scattergun Charge.</strong> Packed shrapnel fires in a 20-foot cone instead of a burst, dealing piercing for fire.</li>
      <li><strong>Smoke Pot.</strong> A 15-foot bank of concealing smoke that drifts and lingers a minute or more.</li>
      <li><strong>String of Cats.</strong> A rattling chain of bangers that apes a firefight — fine for a distraction, or a Demoralize against the green.</li>
      <li><strong>Thunderboot Auger.</strong> A shaped breaching charge that opens a barred door, a safe, or a mine-wall in seconds.</li>
    </ul>
  </div>
  <h4>Assayer's Eye</h4>
  <p>You appraise the worth and the honesty of a thing at a glance: the value of goods and gems, the salted claim, the
  counterfeit coin, the true content of a vein. You instantly recognize <strong>silver</strong> and <strong>cold iron</strong>
  by their gleam and heft — knowledge worth more than money against the things that fear them.</p>
  <h4>Demolitionist</h4>
  <p>Your understanding of powder has passed from craft into art. Your bursts gain +5 feet of radius, and against structures, wagons, and the unliving your charges deal <strong>double dice</strong>. Once per scene you may daisy-chain several prepared charges into a single catastrophic blast, combining their dice and their burst — the kind of thing that reshapes a canyon wall, or the course of a battle.</p>
  <h4>Sapper</h4>
  <p>You dig, tunnel, and undermine at twice the speed of honest men. In a fight, spend two Beats and a point of Pay Dirt to
  throw up hard cover from the ground itself — a trench, a rubble-pile, a collapsed timber — or, with a charge set, to bring
  a wall, a bridge, or a mine-roof down on whatever stands beneath it.</p>
  <h4>Overcharge</h4>
  <p>Once per scene, as a single Beat, you overload a Device or your own iron: until the end of your next turn your charges and gunshots deal <strong>+2 dice</strong> and ignore the first step of a target&rsquo;s resistance, and one Device fires without spending a charge. Push your luck and overcharge a second time in the same scene, and you risk a backfire — a flat check, or the thing goes off early, and on you.</p>
  <h4>The Mother Lode</h4>
  <p>Once per session you strike it rich. Either refill your Pay Dirt pool entirely and take a genuine windfall the Keeper
  honors — a fat vein, a lost cache, a buried strongbox — or, in a tight place, declare that <em>everything goes your way</em>
  for one round: treat every check you make that round as one degree of success better. The deep digging has changed you,
  too: you feel it in your fillings when the Old Dark stirs underground, and the Keeper gives you a moment's warning before
  it surfaces. You have learned what sleeps in the deep. You keep digging anyway.</p>
  <h4>The Deep Vein</h4>
  <p>You have learned to read a country the way another man reads a page. Once per day, sink a shaft with your mind rather
  than a pick: name a thing that could be under the ground within a mile — water, ore, a worked passage, a buried body,
  a cavity — and learn whether it is there, how deep, and what lies between you and it. Your Pay Dirt pool refreshes at
  the start of every scene rather than each dawn.</p>
  <h4>Bring It Down</h4>
  <p>You have stopped blasting rock and started blasting structures. Given ten minutes to place charges and a thing that
  stands — a wall, a bridge, a trestle, a mine mouth, a house — you drop it, whole, when you choose to. Anything inside
  or under takes 8d6 and is buried; anything the size of a barn or larger takes half. There is no save to be somewhere
  else once the charges are set, only to be somewhere else before.</p>
  <h4>What the Ground Owes</h4>
  <p>You have taken enough out of the earth that it has started paying without being asked. Once per session, in any place
  with ground under it, call in the debt: the earth gives you exactly one thing the posse needs and could conceivably be
  down there. A seam of silver to buy a town's cooperation. A spring in a dry country. A worked tunnel running under the
  wall you cannot get through. A vein of something that burns. It is real, it is yours, and it is enough. What comes up
  with it is the Keeper's to decide, and something is always down there with the good stuff.</p>

  <div class="quote">
    "Folks say I struck it lucky. I struck it <em>deep</em>, is what I did, and lucky was getting back up the shaft.
    There's a sound down there, past the silver — patient, like water that learned to wait. I do not dig at night now.
    I have all the money a man could want, and I sleep with the lamp lit."
    <span class="src">— J. Halloran, late of the Widow's Comfort claim, now of no fixed address</span>
  </div>
  
  <div class="box">
    <h4>Claims of the Prospector</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Deep Claim.</strong> You see in the dark underground and sense ore, water, and the Old Dark near at hand. <em>Mastery (10th):</em> once per scene the deep answers — unearth a useful relic, or turn the Old Dark's notice aside for a round.</li>
      <li><strong>The Lucky Claim.</strong> Your Pay Dirt pool grows, and once per scene you may reroll a search, survival, or save for free. <em>Mastery (10th):</em> once per scene, declare the dice fall your way — treat any one roll as a natural 20.</li>
      <li><strong>The Powder Claim.</strong> Prepare extra charges, and your bursts gain +5 feet of radius. <em>Mastery (10th):</em> once per scene, set off a single ruinous blast that can level a building, or a monster.</li>
    </ul>
  </div>
  <div class="pageno">17</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">V. Worldly Callings</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-sawbones">Sawbones</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p><em>Sawbones</em> is what the West called a doctor, after the saw in the bag, and the trade was as rough as the name.
  Surgeon, alienist, horse-doctor, or barber with a bone-saw — the Sawbones is the one who digs the bullet out by
  lamplight and decides who is worth the laudanum. They know the body too well to romanticize it, and the mind too well to
  trust it. In a country this lethal, they are worth their weight in silver.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Not On My Table.</span> A soul whose wounds you have dressed since the last full rest will not bleed out while you are conscious and in the same fight. They fall, they hold one point short of dead, and they wait for you. Whether you reach them in time is the only question. It is always the only question.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The posse still standing. Field Surgery puts Blood back in the middle of a round, and Precise Strike says you are not harmless while you do it.</div>
    <div class="pays"><span class="k">You pay</span>Steady attack, a d8, and a blade&rsquo;s reach. Your damage wants you close to a thing you would much rather be operating on afterward.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Field Surgery, Anatomist</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Tonics</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Practice</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Precise Strike 1d6</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Alienist</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Precise Strike 2d6</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Precise Strike 3d6, Miracle Worker, Practice Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Precise Strike 4d6, The Waking Draught</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Read the Body</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Hour After</td></tr>
    </tbody>
  </table>
  <h4>Field Surgery</h4>
  <p>With a kit and a few minutes, you restore 1d8 + your level in Blood to a patient, once per wound. Without a kit you may
  still stop bleeding and stabilize the dying on a Medicine check.</p>
  <h4>Anatomist / Precise Strike</h4>
  <p>You know exactly where things come apart. Against any living foe whose anatomy you understand, you may add the listed
  extra damage with a precise attack — a scalpel, a derringer pressed to the ribs, a well-placed blade.</p>
  <h4>Tonics</h4>
  <p>You brew and carry remedies: stimulants, sedatives, laudanum, antitoxins. Each dawn you may prepare a number of doses
  equal to your WIT modifier + half your level. Their use, and abuse, is detailed in Chapter X.</p>
  <h4 id="ix-alienist">Alienist</h4>
  <p>You can doctor the mind as well as the body. By talking a sufferer through their terror for ten quiet minutes, you
  restore Nerve equal to 1d6 + your WIT modifier — reason held up like a lamp against the dark. It does not work twice on
  the same fright.</p>
  <h4>Miracle Worker</h4>
  <p>At 10th level your hands have become something the country whispers about. Once per session you may attempt the
  impossible at the operating table: a Beyond (DC 30) Medicine check, taken over an hour of desperate work, can
  pull a character back from death itself so long as the body is whole and no more than a minute has passed — or can lift a
  single Lasting Injury or bodily Affliction entirely. Whether the patient is grateful for what you have done is between
  them and their god.</p>
  <h4>The Waking Draught</h4>
  <p>You have mixed something that argues with unconsciousness. Once per scene, a dose brings a dying or senseless patient
  to their feet with 1d8 + your level in Blood and a clear head for ten minutes, whatever put them down. When the ten
  minutes are up they drop where they stand and cannot be raised this way again until they have slept. Used on the
  Marked or the uncanny it does nothing at all, and they will know you tried.</p>
  <h4>Read the Body</h4>
  <p>A living thing in front of you is a document you can read. Spend a Beat studying any creature: learn its remaining
  Blood, its lowest save, whether it is diseased, poisoned, possessed, expectant, healing or already dead, and the
  single most fragile thing about it. Your Precise Strike against that creature ignores any damage reduction for the
  rest of the scene.</p>
  <h4>The Hour After</h4>
  <p>Once per session, given a body no more than an hour dead and whole enough to work on, you bring it back. Not a Beyond
  check and not a prayer: an hour of surgery, both hands, everything you have, and at the end of it the patient
  breathes. They return at 1 Blood with a Lasting Injury of the Keeper's choosing and no memory of the interval, and
  they are not quite the same about the dark afterward. You may not do this twice for the same soul, and the second time
  you do it for anybody at all in a season, something notices that a doctor out here is undoing its work.</p>
  
  <div class="box">
    <h4>Practices of the Sawbones</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Chemist.</strong> Prepare extra tonics each day and name any poison or drug at a glance. <em>Mastery (10th):</em> brew a signature serum that grants a mighty boon for a scene, or lays a foe insensible.</li>
      <li><strong>The Field Medic.</strong> Tend wounds in the thick of a fight without provoking, and reach the downed faster. <em>Mastery (10th):</em> once per scene, a barked field-treatment heals every ally who can hear you.</li>
      <li><strong>The Surgeon.</strong> Your Treat Wounds restores an extra die, and you stabilize the dying as a single Beat. <em>Mastery (10th):</em> once per scene, drag a freshly-fallen ally back to their feet and fighting.</li>
    </ul>
  </div>
  <div class="pageno">18</div>
</section>

<!-- ===================== VI. CALLINGS OF FAITH ===================== -->
<section class="page" id="faith">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VI. Callings of Faith</span></div>
  <h1 class="chapter">VI. Callings of Faith</h1>
  <p class="chapter-sub">For those who answer the dark with a louder Word.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Not every power in this country is bought from the Old Dark beneath it. Some is asked for, on
  the knees, of a higher and quieter thing — and sometimes the asking is answered, though never plainly. The Callings of
  Faith draw their strength from conviction: the certainty, against all evidence, that the world has a maker and the maker
  has not entirely turned away. Whether that certainty is true matters less, mechanically, than that it is <em>held</em>.
  Faith made countable is the rarest currency in the Territories, and it spends.</p>
  <p>This chapter holds six Callings of Faith, each answering the dark in a different tongue.
  <strong>Padre</strong> meets it with sacrament, Latin rite, and the long authority of the Church.
  <strong>Preacher</strong> meets it with the open Word and sheer conviction. <strong>Shaman</strong>
  meets it by walking with the spirits of the living country itself. <strong>Medicine Man</strong> meets it with the
  oldest answer of all — by keeping the wounded alive in spite of it. And the <strong>Witch Hunter</strong> meets it with
  fire, silver, and a zealot's certainty, hunting the dark's servants back to their dens.</p>
  <p>All five work <strong>Miracles</strong> — a chosen, ranked repertoire of graces, each paid from its own
  pool of faith made countable. The Callings are laid out first; the Miracles they draw on, and the rules that govern
  them, are gathered with the Signs in Chapter XIII, under <em>The Work of Faith</em>.</p>

  <div class="box gold">
    <h4>A Note on Faiths Not Your Own</h4>
    <p>The faith-keepers of the First Peoples are <strong>not</strong> a Calling in this book and should never be reduced
    to one. Their ceremonies are living religion, not game mechanics, and they are not the "Old Rites" of Chapter XIII. The
    <strong>Shaman</strong> presented here is a deliberately fictional, syncretic spirit-talker — drawn from the broad
    frontier well of animist and folk belief, and likewise <em>not</em> a stand-in for any real nation's sacred practice. If
    a table wishes to portray such a figure, do so as a person of faith — with the care urged in Chapter IV — and leave the
    sacred specifics of any living tradition off the character sheet entirely.</p>
  </div>
  <div class="pageno">19</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VI. Callings of Faith</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-medicine">Medicine Man</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p>In a country that deals exclusively in wounds, the rarest soul of all is the one who closes them. The Medicine Man is
  that soul: healer, herb-doctor, prayer-mender, bonesetter — keeper of the only craft the frontier truly cannot do without.
  Where other Callings of Faith answer the dark with fire or rite, this one answers it with the simple, stubborn insistence
  that the people in its care are going to <em>live</em>. No Calling keeps a party breathing like this one.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">One Look and You Know.</span> Look at any living thing and name what is wrong with it: the wound, the sickness, the poison, the hunger, the curse, or nothing at all, which is now and then the worse answer. Curing it is a longer conversation, and it starts here.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Blood back, and the sickness out with it. More ways to put a soul right than any other Calling in the book.</div>
    <div class="pays"><span class="k">You pay</span>Almost nothing that ends a fight. You keep the posse alive long enough for somebody else to end it, and you will watch them get the credit.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Healing Hands, Herb-Lore</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Mend the Body</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Way</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Draw Out the Sickness</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Call Back the Breath</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Soothe the Spirit</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Hands of Life, Way Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Long Song</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Turn the Sickness Back</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>Call Back the Name</td></tr>
    </tbody>
  </table>
  <h4>Healing Hands</h4>
  <p>You possess the deepest healing well of any Calling: a pool of <strong>Vital Breath</strong> equal to your RES modifier
  + your full level (not half), refreshed each dawn. Every gift below draws on it. Where another healer counts pennies, you
  carry a purse.</p>
  <h4>Miracles</h4>
  <p>You know and work <strong>Miracles</strong> (see <em>The Work of Faith</em>, in Chapter XIII), drawing on the <strong>Common Blessings</strong> and on <strong>the Mending</strong> — the quiet, stubborn craft of keeping the wounded alive, paid from your Vital Breath.
  You begin knowing two and learn another as each new Rank opens to you: at 3rd, 5th, 7th, and 9th level.</p>
  <h4>Herb-Lore</h4>
  <p>You gather and prepare remedies from the living country — poultices, teas, tinctures, splints. Gain +2 on
  Medicine and Survival, and treat your prepared remedies as a Sawbones' Tonics. Between fights, your herb-work stabilizes
  the dying and tends the hurt <em>without</em> spending Vital Breath, so that your well is full when the shooting starts.</p>
  <h4>Mend the Body</h4>
  <p>By touch, spend 1 Vital Breath to heal <strong>2d8 Blood</strong> — more per point than any other Calling can manage —
  or to instantly stabilize a dying soul and bring them back to their senses. Pour in more points to mend more — each further point of Vital Breath heals another 2d8.</p>
  <h4>Draw Out the Sickness</h4>
  <p>Spend Vital Breath to grant an immediate save against a poison, disease, or Affliction at +4 — or, for
  3 Vital Breath, end one outright. You may also ease the penalty of a Lasting Injury for a day, buying a wounded
  companion the time the country would otherwise deny them.</p>
  <h4>Call Back the Breath</h4>
  <p>Within a minute of a death, you may spend half your maximum Vital Breath (rounded up) and a long, exhausting effort to call a soul
  back into a body still whole enough to hold it. It is never certain and never cheap, and the country sometimes takes
  notice when you cheat it of a meal. But you can do the one thing nearly nothing else in this book can: undo a death.</p>
  <h4>Soothe the Spirit</h4>
  <p>Your gift mends more than meat. Restore Nerve as readily as Blood, lift fear from the frightened, and — uniquely —
  suppress the <em>symptoms</em> of the Mark for a scene, granting a Hexer, a Dark Cultist, or any haunted soul a few hours of
  true peace. You cannot lift the Mark itself. But you can give the Marked a night's sleep, which they will remember as a
  kindness long after they have forgotten your name.</p>
  <h4>Hands of Life</h4>
  <p>Once per session, a great mercy pours out of you to every soul you can reach: all your companions restored, afflictions
  lifted, the freshly dying raised, fear washed clean away. For one moment you are the thing this country refuses to be. The
  cost is borne in your own body — you take on a measure of what you healed, a share of the wounds and the dread — and you
  cannot do it again until you have rested and grieved what it cost you.</p>
  <h4>The Long Song</h4>
  <p>You have learned to sing a thing all the way through rather than in pieces. Over an hour of singing, spend any amount
  of Vital Breath: everything it would heal, it heals, and it will also lift one disease, poison, or Affliction from
  every soul in the circle. It cannot be hurried and it cannot be sung twice in a day. A camp that has heard it sleeps
  without dreaming.</p>
  <h4>Turn the Sickness Back</h4>
  <p>What was put into a body can be sent back to whoever put it there. When you draw out a disease, poison, curse or
  Affliction, you may hold it in your hands rather than let it go: for the rest of the scene you may place it on any
  creature you touch or point at within thirty feet, which suffers it with no save if it is the one that dealt it, or
  with a Fortitude save otherwise. Carrying it costs you 1 Vital Breath a round and it is unpleasant to hold.</p>
  <h4>Call Back the Name</h4>
  <p>Once per session, over a night and a fire, you may call a soul back that has been gone as much as a day. Speak the
  name until the name answers. The body must be present and need not be whole; what returns is whole, at half Blood,
  with everything it was. The price is fixed and is not paid by them: you give up a year of your own life, every point
  of Vital Breath until the next dawn, and one thing you loved about the world, which the Keeper names and which does
  not come back. Do it four times and you will be very old and very quiet.</p>

  <div class="box gold">
    <h4>A Note on the Name</h4>
    <p>"Medicine Man" carries real and specific meaning in Native American traditions. This Calling is <strong>not</strong> a
    portrait of any nation's sacred healer or ceremony — those, as Chapters IV and VI insist, stay off the character sheet.
    It is a deliberately fictional, syncretic frontier healer, blending the herb-doctor, the granny-woman, the faith-healer,
    and the bonesetter of many trail traditions. Tables are warmly encouraged to rename it to taste — the Healer, the Granny,
    the Bonesetter, the Yarb-Doctor — and to play the mercy and the craft while leaving real ceremony alone.</p>
  </div>
  
  <div class="box">
    <h4>Ways of the Medicine Man</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Dreaming Way.</strong> You walk in visions and read omens for guidance. <em>Mastery (10th):</em> once per scene, walk the dream to foresee a danger, or to find what is hidden or lost.</li>
      <li><strong>The Mending Way.</strong> Your remedies are potent and may lift a lingering affliction. <em>Mastery (10th):</em> once per scene, a healing rite mends every ally near you.</li>
      <li><strong>The Warding Way.</strong> Craft charms that turn aside the dark and its lesser servants. <em>Mastery (10th):</em> once per scene, draw a circle of protection no uncanny thing may enter.</li>
    </ul>
  </div>
  <div class="pageno">20</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VI. Callings of Faith</span></div>
  <h2 id="ix-c-padre">Padre</h2>
  <p class="statline">Hit Die d8 · Trained Skills 4 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p>Where the Preacher improvises, the Padre inherits. Behind one tired man at a crumbling mission stands eighteen
  centuries of liturgy, an unbroken chain of ordination, and a Church that has been writing down what it learned about the
  dark since long before the dark followed the settlers west. The Padre's power is the power of the Rite, performed exactly,
  whether or not the celebrant's own faith is steady. The words work. That is rather the point of them.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">The Church Owes You a Bed.</span> Every mission, chapel, rectory, and lay house that keeps the faith will take you in and yours with you: a roof, a meal, a horse if they can spare one, and the name of who to ask for in the next town. The Church has a long memory and longer ledgers, and one day somebody will present yours.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The rite. Exorcism, holy water and the Church Militant reach what lead cannot, and the blessing list arms whoever among you is best with a gun.</div>
    <div class="pays"><span class="k">You pay</span>Steady attack, a d8, and a pool that answers slowly. Against a man with a rifle you are a man with a book.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Sacraments, Rite of Exorcism</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Holy Water & Relic</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Order</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Sanctuary</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Viaticum</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, The Greater Rite</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Church Militant, Order Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Greater Rite (second), Cure of Souls</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Anathema</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Word Made Binding</td></tr>
    </tbody>
  </table>
  <h4>Sacraments</h4>
  <p>You have a pool of <strong>Grace</strong> equal to your PRE modifier + half your level (minimum 1), refreshed at the
  dawn Mass (or its private equivalent). Grace fuels every rite below. A Padre who has missed his offices too long begins
  the day with the pool halved — the Church is exacting about its bookkeeping.</p>
  <h4>Miracles</h4>
  <p>You know and work <strong>Miracles</strong> (see <em>The Work of Faith</em>, in Chapter XIII), drawing on the <strong>Common Blessings</strong> and on <strong>the Liturgy</strong> — the sacramental Latin the Church has kept against the dark for eighteen centuries, paid from your Grace.
  You begin knowing two and learn another as each new Rank opens to you: at 3rd, 5th, 7th, and 9th level.</p>
  <h4>Rite of Exorcism</h4>
  <p>Your signature work. Against a possessing spirit, a controlling influence, or the Mark working in a living soul, spend
  Grace and intone the Rite — a contest of your <strong>Sacrament DC</strong> (10 + half level + PRE) against the thing's
  Will, repeated each round you persist. Win the contest and you suppress it for the scene; win it twice running and you
  cast it out entirely. It is slow, it is loud, and it makes you the only thing in the room the dark wants dead.</p>
  <h4>Holy Water &amp; Relic</h4>
  <p>You may bless water by the vial; a thrown vial deals 1d6 holy damage (Scatter 5 ft) to the uncanny and burns the
  Marked. You also carry a true <strong>relic</strong> — a saint's bone, a splinter, a medal worn smooth — which grants one
  reroll each day on a save against the unnatural, and which the restless dead are loath to approach.</p>
  <h4>Sanctuary</h4>
  <p>Spend Grace and a minute to consecrate a space. Uncanny things must make a Will save against your Sacrament DC to enter
  or to strike those within; allies inside recover Nerve each round and gain +2 on Will saves. The ground holds until dawn,
  until deconsecrated, or until you are carried out of it.</p>
  <h4>Viaticum</h4>
  <p>The last rites are also the kindest medicine. Spend Grace to heal 2d8 Blood and halt the dying by touch. Should the
  patient die regardless, you shrive them: their soul departs in peace, beyond the dark's reach — they cannot rise as
  restless dead — and the quiet of a good death restores you 1d6 Nerve.</p>
  <h4>The Greater Rite</h4>
  <p>You learn one major liturgical working: <em>Bell, Book, and Candle</em> (a ten-minute rite that banishes a lesser
  uncanny outright, or a greater one for a day and a night), or the <em>Consecration of a Haunt</em> (which lays a binding
  on the very stones of a haunted place). Choose at 7th and a second at 11th; the Keeper may permit more in play.</p>
  <h4>The Church Militant</h4>
  <p>Once per session, draw on the whole weight of the Church behind you. As an action, name the unclean in Latin and
  command it: it makes a Will save against your Sacrament DC or is destroyed if a lesser thing, banished if a greater, and
  in any case driven Frightened and Slowed. Every ally who can hear the Rite is immune to fear until the scene ends. Two
  thousand years of the dead speak the words with you, and for one moment, the dark remembers that it has lost this argument before.</p>
  <h4>Cure of Souls</h4>
  <p>You have a parish now, whether or not it has a building. Any soul you have shriven, married, buried kin for, or sat
  with through a bad night counts as yours: they gain +2 on saves against the uncanny while you live, you always know if
  one of them has died, and once per session one of them turns up where you need them, doing what little they can. It is
  never much. It is never nothing, either.</p>
  <h4>Anathema</h4>
  <p>You may pronounce a thing cut off. Name an uncanny creature you have seen and speak the sentence over an hour with
  bell, book and candle: for the next day it cannot enter consecrated ground, cannot be healed by any means, cannot be
  aided by another of its kind, and takes 2d8 holy damage each time it touches you. It will know who did it and it will
  know where the church is.</p>
  <h4>The Word Made Binding</h4>
  <p>Once per session you may speak once with the whole authority of the office behind you, and the world is obliged.
  Command a single thing of one creature that can hear you, in plain language, in one sentence: leave, kneel, release
  her, tell the truth, be still, go back. Anything you can still shoot obeys outright. Anything past that must beat your
  Will save or obey for one round, which is often the round that mattered. Then you are hollowed out — no Grace, no
  Miracles, and no second word until the next dawn — and you will spend a long time wondering whether it was your
  authority or Someone Else's, and whether the difference is any of your business.</p>

  <div class="quote">
    "The boy's father asked me did I believe, truly, that the words would hold the thing in his son.
    I told him belief was his department. The Rite was mine, and the Rite does not require my opinion.
    Then I opened the book, and we found out together which of us was right."
    <span class="src">— Fr. Ignacio Reyes, Mission San Crisanto</span>
  </div>
  
  <div class="box">
    <h4>Orders of the Padre</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Exorcist.</strong> Rebuke the uncanny and loosen its grip upon the possessed. <em>Mastery (10th):</em> once per scene, cast out a possessing or lesser horror entirely.</li>
      <li><strong>The Martyr.</strong> Take a wound meant for another, and endure where others fall. <em>Mastery (10th):</em> once per scene, interpose against a killing blow, or fall and rise once more, unbroken.</li>
      <li><strong>The Shepherd.</strong> Bless allies who can hear you and ward them against fear. <em>Mastery (10th):</em> once per scene, raise a sanctuary that shields all nearby from harm for a round.</li>
    </ul>
  </div>
  <div class="pageno">21</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VI. Callings of Faith</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-preacher">Preacher</h2>
  <p class="statline">Hit Die d8 · Trained Skills 4 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p>Whether ordained, defrocked, or self-anointed, the Preacher carries the Word into a country that has plainly been
  abandoned by whatever wrote it — and keeps preaching anyway. Their faith is a weapon and a wall. Whether any god hears them
  is a question the Preacher has stopped asking aloud.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">A Crowd Where You Stand.</span> Anywhere with a dozen souls in it, you can raise a congregation in the time it takes to climb up on something. They will listen. What they do about it afterward is between them and God, and it has gone both ways in living memory.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Brimstone, which is Faith&rsquo;s own damage and wants no gun at all, and a Sermon that moves a room before the shooting starts.</div>
    <div class="pays"><span class="k">You pay</span>Conviction, spent. Brimstone is its own action rather than a rider on a shot, so the round you preach is a round you do not fire.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Conviction, Sermon</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Ward</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Testament</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Brimstone 1d6</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Lay On Hands</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Brimstone 2d6</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Brimstone 3d6, Revelation, Testament Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Brimstone 4d6, The Camp Meeting</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Testify</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Great Awakening</td></tr>
    </tbody>
  </table>
  <h4>Conviction</h4>
  <p>You have a pool of <strong>Conviction</strong> equal to your PRE modifier + half your level (minimum 1), refreshed each
  dawn. Conviction fuels your sermons and miracles. It is faith made countable — and it runs dry exactly when you need it most.</p>
  <h4>Miracles</h4>
  <p>You know and work <strong>Miracles</strong> (see <em>The Work of Faith</em>, in Chapter XIII), drawing on the <strong>Common Blessings</strong> and on <strong>the Revival</strong> — the mourner&rsquo;s bench, the camp meeting, and the fire that falls when the Word is loud enough, paid from your Conviction.
  You begin knowing two and learn another as each new Rank opens to you: at 3rd, 5th, 7th, and 9th level.</p>
  <h4>Sermon</h4>
  <p>Spend 1 Conviction and speak for a round. Allies who hear you regain Nerve equal to your PRE modifier and gain +1 on
  Will saves until the scene ends. The unfaithful may mock; they steady all the same.</p>
  <h4>Ward</h4>
  <p>Spend 1 Conviction to inscribe or invoke a ward against the uncanny. Marked and unnatural things must make a Will save
  to cross it or strike those within. A ward holds until dawn or until you fall.</p>
  <h4>Brimstone</h4>
  <p>Your invective becomes a smiting. As an attack, point and condemn a single creature within sight; spend 1 Conviction to
  deal the listed holy damage (doubled against the Marked and the uncanny), Will save for half. It is loud, and it draws notice.</p>
  <h4>Lay On Hands</h4>
  <p>By touch and prayer, spend Conviction to heal 1d8 Blood per point spent, or to halt bleeding and stabilize the dying. The
  same gift, turned on the unnatural, deals that much instead.</p>
  <h4>Revelation</h4>
  <p>At 10th level, faith burns through the veil. Once per session, as an action, you may spend 3 Conviction to lay the truth
  of a place or a creature bare before all who can hear you: the uncanny within sight is named aloud — its nature, its hunger,
  and the one thing it fears — and is struck Frightened 1 for the scene, while your companions ignore the next Dread Check they would
  face. The Word, spoken once with perfect certainty, still moves something. You simply never learn what, or whether it was
  listening, or merely could not bear to be seen.</p>
  <h4>The Camp Meeting</h4>
  <p>Give you a night, a fire and a crowd, and you will change the temper of a place. Everyone who stays to the end of the
  meeting recovers all Nerve, gains +2 on their next save against fear or the uncanny, and will tell you what they came
  there to confess. What they confess is the useful part. A town has never yet been converted, but it has often been
  talked into helping.</p>
  <h4>Testify</h4>
  <p>You have stopped preaching at the dark and started giving evidence about it. Once per scene, spend 2 Conviction and
  name what an uncanny thing did: it takes 4d6 damage that nothing reduces, and every ally who heard you may immediately
  reroll one save they failed this scene. The truth spoken plainly about a thing that lives on not being spoken of costs
  it.</p>
  <h4>The Great Awakening</h4>
  <p>Once per session, you preach the sermon you have been carrying your whole life. Everything within earshot that can
  hear you and is not uncanny recovers all Blood and all Nerve and is immune to fear for the scene. Everything within
  earshot that is uncanny takes 10d6 and must beat your Will save or be Frightened and unable to approach you for the
  rest of the scene, and the lesser sort of uncanny that fails is simply undone where it stands. When you finish you
  have nothing left: no Conviction, no voice for a day, and the certain knowledge that you have spent something you will
  not get back and cannot count.</p>

  <div class="quote">
    "I have buried ninety souls and christened thirty, and I keep the arithmetic in the same book.
    If the Lord reads it of an evening, He has not yet seen fit to remark upon the difference."
    <span class="src">— Rev. Amos Teague, his own ledger, water-stained</span>
  </div>
  
  <div class="box">
    <h4>Testaments of the Preacher</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Hellfire Testament.</strong> Your Brimstone strikes an additional foe within reach of the first. <em>Mastery (10th):</em> once per scene, call down a pillar of fire upon the unclean.</li>
      <li><strong>The Revival Testament.</strong> Your sermons mend the faithful and steady their nerve. <em>Mastery (10th):</em> once per scene, a great revival heals and emboldens every ally who can hear you, and lifts the freshly fallen.</li>
      <li><strong>The Wrathful Testament.</strong> Gain a bonus against the uncanny and those who serve it. <em>Mastery (10th):</em> once per scene, your smite banishes a lesser horror outright.</li>
    </ul>
  </div>
  <div class="pageno">22</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VI. Callings of Faith</span></div>
  <h2 id="ix-c-shaman">Shaman</h2>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p>The Shaman of this book is a spirit-talker: one who has learned that the country is not empty but <em>crowded</em> —
  with the spirits of beasts and weather, river and rock, and the long-departed dead — and who keeps a working peace with
  them through respect, offering, and the long apprenticeship of listening. Theirs is not the borrowed power of the Hexer
  but a relationship, maintained the way any relationship is: with patience, gifts, and a healthy fear of giving offense.</p>
  <p class="note">See the box opposite (Chapter VI's note, and Chapter IV): this Shaman is a fictional, syncretic frontier
  archetype, not a portrait of any living nation's sacred role. Play the relationship and the respect; leave real ceremony off the sheet.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">You Dream It First.</span> Every night you sleep on open ground, the Keeper owes you one true thing: an image, a warning, a name, a direction. It is never clear enough to act on cleanly and it has never once been wrong.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The spirits, and the pack with them. Become the Mask changes what you are for the length of a fight.</div>
    <div class="pays"><span class="k">You pay</span>The thinnest hand in a stand-up fight of any Calling of Faith. What you are best at happens before the shooting and after it.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Spirit-Sight, The Helping Spirits</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Mending Hands</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Spirit-Pact</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Spirit-Walk</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Don the Aspect</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Commune</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Become the Mask, Spirit-Pact Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Wide Circle</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Two Worlds at Once</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Land Answers</td></tr>
    </tbody>
  </table>
  <h4>Spirit-Sight</h4>
  <p>You perceive the spirits of the living world and the unquiet dead, the thin places, and the moods of the country
  itself. You may address a spirit of place and, with courtesy, be answered — though the spirits keep their own counsel and
  their own grudges.</p>
  <h4>The Helping Spirits</h4>
  <p>One or more spirits walk with you — choose an <strong>Aspect</strong>, such as the Wolf (the hunt and the pack), the
  Raven (cunning and the dead), the River (mending and endurance), or the Elder (memory and counsel). The Aspect grants a
  standing boon and a called-upon boon fueled by your pool of <strong>Breath</strong> (RES modifier + half level, refreshed
  each dawn). You may make peace with a second Aspect at 6th level.</p>
  <h4>Miracles</h4>
  <p>You know and work <strong>Miracles</strong> (see <em>The Work of Faith</em>, in Chapter XIII), drawing on the <strong>Common Blessings</strong> and on <strong>the Spirits</strong> — courtesies asked of the crowded country and its neighbors, paid from your Breath.
  You begin knowing two and learn another as each new Rank opens to you: at 3rd, 5th, 7th, and 9th level.</p>
  <h4>Mending Hands</h4>
  <p>Spend Breath to heal 1d8 Blood per point by touch and song, or to ease a frightened soul — granting back Nerve or a
  fresh save against an Affliction. The spirits mend what they are asked to, in their own time and to their own ends.</p>
  <h4>Spirit-Walk</h4>
  <p>Send your spirit out from your body to scout unseen, or step a short way through the spirit-world to cross ground you
  could not otherwise reach. Your body lies senseless while you wander, and the longer you stay out, the harder the road
  back; tarry too long and you risk a Dread Check to find your way home.</p>
  <h4>Don the Aspect</h4>
  <p>For a scene, take on the gifts of a Helping Spirit: the Wolf's claws and speed, the Raven's wings and sight, the
  River's tirelessness, the Elder's uncanny insight. The change is partial and temporary, and it asks a little of you each
  time — the spirits lend, they do not give.</p>
  <h4>Commune</h4>
  <p>Sit with the land, the weather, or the recently dead and learn what they know: the way through, the coming storm, the
  game and the water, the name of what walks at night. With proper respect you may also lay a restless spirit to rest, which
  is the truest service a Shaman renders, and the one the dead remember.</p>
  <h4>Become the Mask</h4>
  <p>Once per session you may give yourself wholly over to a great spirit for a scene, embodying its full power — a storm,
  a beast-king, an ancestor of terrible weight. While the spirit rides, you wield gifts far beyond a mortal's. But when it
  departs, make a Will save (DC the Keeper sets) or a little of it stays, and a little of you does not return. Wear the mask
  too often and the question stops being whether it comes off, and starts being who is wearing whom.</p>
  <h4>The Wide Circle</h4>
  <p>The spirits that answer you have started bringing others. Your Helping Spirits may be sent to any ally you can see
  rather than only to yourself, and once per scene you may ask the spirits of a place one question about what has
  happened there, which they answer honestly and rudely. Places where something bad was done answer loudest.</p>
  <h4>Two Worlds at Once</h4>
  <p>You have stopped having to cross over. You see and may act upon the spirit world and this one together: you always
  know what is present and unseen, you may Strike an incorporeal thing with a bare hand as though it were solid, and you
  may Spirit-Walk without leaving your body behind for anything to find. Holding both open is tiring, and you dream
  badly.</p>
  <h4>The Land Answers</h4>
  <p>Once per session, ask the country itself for help, and it helps. The spirits of the place take a side for the rest of
  the scene: name a single thing you want from it, and the land does that thing. The river rises. The rock closes. The
  herd turns. The fog comes down and lifts only for your people. The dead of that ground stand up and remember whose
  they were. It is not a spell and there is no save; it is a place deciding, and places decide slowly and completely.
  Afterward you owe it, and the Keeper will name what it wants, and it will want something you would rather keep.</p>

  <div class="quote">
    "My grandmother told me the spirits are not servants and not enemies. They are neighbors,
    and a neighbor remembers everything — the borrowed cup, the kind word, the slight at the well.
    Treat them as you would the people whose land you cross. You are, after all, doing both at once."
    <span class="src">— recorded from a spirit-talker who asked to be named only as a friend of the river</span>
  </div>
  
  <div class="box">
    <h4>Spirit-Pacts of the Shaman</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Ancestor Pact.</strong> The honored dead counsel you; gain rerolls on lore and warning of danger. <em>Mastery (10th):</em> once per scene, call an ancestral host to stand and fight beside you a round.</li>
      <li><strong>The Beast Pact.</strong> A spirit-beast walks with you, lending its senses and its aid. <em>Mastery (10th):</em> once per scene, take on the great beast's shape, or call it forth in full.</li>
      <li><strong>The Land Pact.</strong> Command small workings of wind, water, ember, and stone. <em>Mastery (10th):</em> once per scene, loose a great elemental working — a sudden storm, a swallowing earth.</li>
    </ul>
  </div>
  <div class="pageno">23</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VI. Callings of Faith</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-sister">Sister</h2>
  <p class="statline">Hit Die d8 · Trained Skills 4 + WIT · Strong Saves Fortitude, Will · Attack Steady</p>
  <p>Not every soul who serves does it from a pulpit. Your order sent you where the diocese would not go: the fever camp,
  the mining town with no doctor, the mission school at the end of a road nobody maintains. The Padre has authority and
  the Preacher has conviction. What you have is a habit of staying in the room, and the country has learned that this is
  the harder of the three to get rid of.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Nobody Turns Away a Sister.</span> The sick house, the jail, the barracks, the deathbed, the room upstairs where a girl is in trouble. Doors open for you that open for nobody else in the posse, and they open at once. Men who fully intend to shoot you will let you in first.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The Least of These, Hold the Lamp, and a doorway nobody gets through. You are what stands between the posse and the dark while they do the killing.</div>
    <div class="pays"><span class="k">You pay</span>The vigil was not written to win a fight and it does not. Three workings reach a round and none of them is damage.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, The Vigil, Nurse</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Hold the Lamp</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Order</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Not One Step</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, The Cool Cloth</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, The Long Watch</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>—</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Least of These, Order Mastery</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Longer Watch</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Between You and It</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Lamp Does Not Go Out</td></tr>
    </tbody>
  </table>
  <h4>Mercy</h4>
  <p>You have a pool of <strong>Mercy</strong> equal to your RES modifier + half your level (minimum 1), refreshed by a
  full rest and the morning office, said aloud or not. It is not a measure of how much you care. It is a measure of how
  much you have left.</p>
  <h4>The Vigil</h4>
  <p>You were not called to preach and never wanted to be. What you took were vows of work: to go where the sick are, to stay when others leave, and to keep watch over what should not be left alone. You work Miracles from the blessing and vigil lists, spending Mercy, and your Miracle DC is 10 + half your level + your RES modifier. Your order taught you that a thing watched is a thing that cannot get on with what it was doing.</p>
  <h4>Miracles</h4>
  <p>You know and work <strong>Miracles</strong> (see <em>The Work of Faith</em>, in Chapter XIII), drawing
  on the <strong>Common Blessings</strong> and on <strong>the Vigil</strong> — the warding, watching work of an
  order that has always been sent to sit up with things nobody else will — paid from your Mercy. You begin knowing
  two and learn another as each new Rank opens to you: at 3rd, 5th, 7th, and 9th level.</p>
  <h4>Nurse</h4>
  <p>Bandaging, broth, a hand on a forehead, a window opened at the right hour. A soul you tend through a full rest recovers 1d6 additional Nerve along with its usual Blood, and you may stabilize a dying soul with a touch and no check at all. Nothing about this is uncanny. You have simply done it four hundred times and know what the fourth hundred looks like.</p>
  <h4>Hold the Lamp</h4>
  <p>Set your lamp down and stand over it. For as long as you hold the spot and strike at nothing, every soul who can see the light takes +2 on Dread Checks, and any Nerve they do lose is reduced by 1. Step away and it is a lamp again.</p>
  <h4>Not One Step</h4>
  <p>You cannot be made to run. You are immune to the Frightened condition and to any effect that would compel you to flee, leave, or turn away, and a soul you have physical hold of shares that while you keep hold. This has killed Sisters. It has also saved most of the people they were standing in front of.</p>
  <h4>The Cool Cloth</h4>
  <p>Once per scene, spend 1 Mercy and take one lasting hurt off a soul you can touch: a condition, an affliction in its early stage, or the whole of one Dread Check's Nerve loss suffered this scene. You cannot do it twice for the same soul in a scene, and it does not work on yourself.</p>
  <h4>The Long Watch</h4>
  <p>You have not slept a whole night since you took the veil, and it has stopped costing you. Two hours' rest gives you a full rest's benefit, a night spent watching costs you no penalty, and while you are awake and on watch nothing surprises the camp.</p>
  <h4>The Least of These</h4>
  <p>At 10th level you have spent so long standing between other people and the dark that the dark has learned your face. Once per session, when a soul within your reach would die or be taken, dragged off, possessed, unmade or called away, you may refuse it. They are not. The cost is yours: you drop to 1 Blood, lose all remaining Mercy, and cannot do it again until the next session. Whatever wanted them now knows exactly who you are.</p>
  <h4>The Longer Watch</h4>
  <p>You have sat up with worse than this. You need no sleep on a night you have chosen to keep watch, and every soul
  resting under your watch recovers Nerve fully and wakes with +2 on their first save of the day. You may keep three
  such nights in a row before it starts to tell, and it does tell.</p>
  <h4>Between You and It</h4>
  <p>Standing in front of somebody has become a thing you are good at rather than a thing you are brave about. As a
  reaction, take any single attack, effect or grab aimed at an ally within ten feet upon yourself instead, and reduce it
  by your level. You may do this as many times a round as you have reactions, which is once, and there has never yet
  been a round in which you did not use it.</p>
  <h4>The Lamp Does Not Go Out</h4>
  <p>Once per session, set your lamp down and refuse the dark on behalf of everyone inside its light. For the rest of the
  scene, no ally within thirty feet of you can die, be taken, be possessed, be unmade or be reduced below 1 Blood; every
  one of them is immune to fear; and any uncanny thing that enters the light must beat your Will save each round or be
  unable to act at all. You may not move from where you set it down and you may not attack. Every point of damage the
  light refuses is dealt to you instead, and it will be more than you have. Sisters who do this are usually doing it for
  the last time, and they know that when they set the lamp down.</p>

  <div class="quote">
    "We asked her to come away from the door. She said she would, directly, and did not.
    I have thought about that answer for eleven years. She was not being brave at us.
    She simply had not finished."
    <span class="src">— Hollis Vane, on the night at the Calvary Crossing pest-house</span>
  </div>

  <div class="box">
    <h4>Orders of the Sister</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Hospitaller.</strong> The fever ward and the cholera camp are your ground. Disease and contagion have no hold on you, and a soul under your care through a full rest recovers as though it had rested twice. <em>Mastery (10th):</em> once per scene, a soul who dies within your reach does not, and has until the end of the next round to be saved properly.</li>
      <li><strong>The Teacher.</strong> You ran a mission school and learned what a frightened child needs to hear. Any soul you have spoken with for a full scene gains +2 on its next Will save, and you may teach a skill you are trained in to anyone willing, given a week. <em>Mastery (10th):</em> once per scene, every ally who can hear you uses your Will save in place of their own.</li>
      <li><strong>The Missioner.</strong> Your order sent you to the far stations and forgot to send anyone after you. Hard country, hard weather and hard travel cost you and any company you lead nothing, and you are never lost on a road anyone has walked before. <em>Mastery (10th):</em> once per session, name a place you have heard of; you know the way, and the way is shorter than it should be.</li>
    </ul>
  </div>
  <h2 id="ix-c-witchhunter">Witch Hunter</h2>
  <p class="statline">Hit Die d10 · Trained Skills 4 + WIT · Strong Saves Fortitude, Will · Attack Practiced</p>
  <p>Where the Marshal hunts men, the Witch Hunter hunts the things that wear them. Inquisitor, monster-killer, burned-out
  zealot — they are the grim specialists who ride toward the thing the town is fleeing, with silver in the cylinder and a
  litany of weaknesses by heart. In a country where the uncanny is plainly real, they are a mercy. The trouble is that a
  man who has spent twenty years finding the Mark on the guilty eventually begins to see it on the innocent, too.</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">The Guilty Flinch.</span> You never have to accuse anybody. Stand where the room can see you, say plainly what you are, and watch: somebody always looks at the door. You are right often enough to keep doing it and wrong often enough that it ought to trouble you more than it does.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The best of both halves: a Practiced attack, a d10, Judgment&rsquo;s three dice on the quarry, and Sanctified Iron for what the quarry turns out to be.</div>
    <div class="pays"><span class="k">You pay</span>One quarry. Judgment names a single thing, and the second thing in the room gets a plain Strike from a man who has already spent his Zeal.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+1</td><td class="c">+2</td><td class="c">+0</td><td class="c">+2</td><td>Edge, The Hunt, Sanctified Iron, Zeal</td></tr>
      <tr><td>2</td><td class="c">+2</td><td class="c">+3</td><td class="c">+0</td><td class="c">+3</td><td>Steeled Nerve</td></tr>
      <tr><td>3</td><td class="c">+3</td><td class="c">+3</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Creed</td></tr>
      <tr><td>4</td><td class="c">+4</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Recognize the Unclean</td></tr>
      <tr><td>5</td><td class="c">+5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Judgment 1d8</td></tr>
      <tr><td>6</td><td class="c">+6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>—</td></tr>
      <tr><td>7</td><td class="c">+7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Relentless</td></tr>
      <tr><td>8</td><td class="c">+8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+6</td><td>Judgment 2d8</td></tr>
      <tr><td>9</td><td class="c">+9</td><td class="c">+6</td><td class="c">+3</td><td class="c">+6</td><td>Edge</td></tr>
      <tr><td>10</td><td class="c">+10</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>The Pyre, Judgment 3d8, Creed Mastery</td></tr>
      <tr><td>11</td><td class="c">+11</td><td class="c">+7</td><td class="c">+3</td><td class="c">+7</td><td>Judgment 4d8, The Name Written Down</td></tr>
      <tr><td>12</td><td class="c">+12</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+13</td><td class="c">+8</td><td class="c">+4</td><td class="c">+8</td><td>No Sanctuary</td></tr>
      <tr><td>14</td><td class="c">+14</td><td class="c">+9</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+15</td><td class="c">+9</td><td class="c">+5</td><td class="c">+9</td><td>The Last Fire</td></tr>
    </tbody>
  </table>
  <h4>The Hunt</h4>
  <p>As a single Beat, name one creature you can see as your <strong>quarry</strong>. Against that quarry you gain +1 to
  hit and to all checks to find, track, and study it; you ignore any supernatural concealment it enjoys; and you may not be
  forced to flee it by fear. You may have one quarry at a time and may shift it with another Beat. The Hunt is the whole of
  the art: choose your prey, and never lose the trail.</p>
  <h4>Sanctified Iron</h4>
  <p>Each dawn, anoint your weapons with salt, silver-wash, oil, and a muttered rite. Until next dawn they count as
  <strong>silver, cold iron, and blessed</strong> for the purpose of overcoming the uncanny's resistances, and deal +1
  damage to the Marked and the unnatural. At 6th level, all three at once; before that, choose one each morning and guess
  well.</p>
  <h4>Zeal &amp; the Consecrations</h4>
  <p>You carry a cold and countable certainty: a pool of <strong>Zeal</strong> equal to your WIT modifier + half
  your level (minimum 1), refreshed each dawn when you anoint your irons. Zeal fuels your <strong>Miracles</strong>
  (see <em>The Work of Faith</em>, in Chapter XIII), drawn from the <strong>Common Blessings</strong>
  and from <strong>the Consecrations</strong> — salt, silver, fire, ward, and the litany of weaknesses that turns
  a hunt into an execution. You begin knowing two and learn another as each new Rank opens: at 3rd, 5th, 7th, and
  9th level. The Witch Hunter is no healer, and it shows in the list; grace, in these hands, is a weapon like any other.</p>
  <h4>Steeled Nerve</h4>
  <p>You have stared into too many open graves to flinch at one more. Gain +2 on all Dread Checks and saves against fear,
  and halve the Nerve you lose to your current quarry's kind. The horror is still there. You have simply made a profession
  of not looking away.</p>
  <h4>Recognize the Unclean</h4>
  <p>Study a creature or a person for a round and make a Lore: Occult check: learn whether they bear the Mark or are
  unnatural, what manner of thing they are, and one weakness the Keeper will honor — silver, fire, running water, true
  names, the dawn. The gift is exact, and it is the most dangerous thing you own, for it tempts you to trust it absolutely.</p>
  <h4>Judgment</h4>
  <p>Once per quarry, declare <strong>Judgment</strong> before a Strike. On a hit, deal the listed extra holy-and-silver
  damage; on a critical hit, the quarry must save (DC 10 + half level + WIT) or be Frightened and Slowed, losing a Beat.
  Judgment refreshes when you name a new quarry.</p>
  <h4>Relentless</h4>
  <p>When your quarry drops or flees, you do not relent: immediately Stride toward it for free, and your first Strike in
  pursuit ignores the Multiple Attack Penalty. A wounded thing that runs from a Witch Hunter is merely choosing where it dies.</p>
  <h4>The Pyre</h4>
  <p>At 10th level you are the bane of unclean things. Your Judgment recharges at the start of every scene, no longer only with
  each new quarry. And once per session, when you reduce an uncanny quarry to 0 Blood, you may perform the rites of ending —
  salt, fire, the severed name — and ensure it <strong>stays dead</strong>: it does not rise, reform, or return. Nothing the
  Keeper has prepared survives the Pyre. The cost is the man you have become to wield it.</p>
  <h4>The Name Written Down</h4>
  <p>You keep a book, and what goes in the book does not come out. Enter a creature's name and one true fact about it, and
  thereafter you always know whether it lives, you gain +2 on every roll against it, and it cannot conceal its nature
  from you by any means. You may carry as many names as your WIT modifier. Crossing one out is the only way to make
  room, and there are two ways to cross one out.</p>
  <h4>No Sanctuary</h4>
  <p>A thing you are hunting has nowhere to be. It cannot heal, regenerate, reform or be aided while you are within a
  hundred feet of it, and any ward, threshold, holy ground or bound place that shelters it opens for you and closes
  behind you. What you have hunted onto consecrated ground stays on it.</p>
  <h4>The Last Fire</h4>
  <p>Once per session, light the fire you have been carrying since the beginning. For the rest of the scene you are
  wreathed in a cold white burning: you take no damage from any uncanny source, every Strike you land deals an
  additional 6d8 to unclean things, and anything reduced to 0 Blood in that light is ended outright — no rising, no
  reforming, no return, nothing left to salt. When it goes out you are at 1 Blood, all Zeal spent, and Fatigued until
  you have slept a full night somewhere with a roof. It is understood among your order that a man only gets so many of
  these, and that nobody has ever counted his own correctly.</p>

  <div class="box">
    <h3>On Hunting, and on Zealotry</h3>
    <p>In this country the monsters are real, and the Witch Hunter is sometimes the only thing between a town and the dark.
    But history's witch hunters mostly burned the frightened, the strange, and the inconvenient — and a long-serving Hunter
    in this game should feel that pull. Keepers may ask for a Will save or a touch of the Mark when a Hunter condemns on too
    little proof. The most frightening question this Calling can ask is not <em>what is that thing</em>. It is <em>how
    certain are you</em> — and whether certainty is the same as being right.</p>
  </div>
  
  <div class="box">
    <h4>Creeds of the Witch Hunter</h4>
    <p>At 3rd level, choose one. It grants a boon at once and blooms into its greater ability — its <strong>Mastery</strong> — at 10th level, the height of a frontier life.</p>
    <ul class="dash">
      <li><strong>The Inquisitor.</strong> You sense lies and the Mark upon a soul, and you resist the uncanny's influence. <em>Mastery (10th):</em> once per scene, speak a binding word that holds a lesser uncanny thing helpless a round.</li>
      <li><strong>The Slayer.</strong> Deal extra damage against your quarry's kind. <em>Mastery (10th):</em> your Judgment can fell even a great horror, and a killing blow against the uncanny cannot be shrugged off.</li>
      <li><strong>The Warden.</strong> Scribe wards that bar the uncanny and shield others from the Old Dark. <em>Mastery (10th):</em> once per scene, sanctify the ground around you, which no uncanny thing may cross.</li>
    </ul>
  </div>
  <div class="pageno">24</div>
</section>

<!-- ===================== VII. THE HEXER ===================== -->
<section class="page" id="hexer">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VII. Callings of the Old Dark</span></div>
  <h1 class="chapter">VII. Callings of the Old Dark</h1>
  <p class="chapter-sub">Four roads into the Old Dark — by pact, by craft, by deceit, and by devotion.</p>
  <div class="divider"></div>
  <div class="narr">You have come a fair way into this almanac, reader — through the honest chapters, the
  wages and the weather and the workaday iron. Notice, if you would, how naturally you turned this page.
  That is how it happens out there, too: one door at a time, each opening easily off the last, until a
  soul looks up from its reading and finds the light has changed. The pages from here forward concern
  the things the handbills do not mention. It is not too late to close the book. It has never yet been
  too late for anyone, at this particular page.</div>
  <p class="dropcap lead">Not all power is preached from a pulpit. Beneath this country lies an older one — the <strong>Old Dark</strong>: the deep strata of buried gods, drowned hungers, and patient things that were ancient when the first peoples were young. It does not love you and it does not hate you; it lends, and is inherited, and is worshipped, and it always collects. Four Callings in this chapter reach down into the Old Dark, each by a different road, and it is an old and fatal error to mistake one road for another. The <strong>Hexer</strong> takes power on loan from the Old Dark, and the lender never forgets a debt. The <strong>Witch</strong> inherits an older, steadier craft, bound to a familiar and worked in curses and brews. The <strong>False Prophet</strong> neither borrows nor inherits, but runs a confidence game on the Old Dark&rsquo;s behalf — and arranges for a deceived flock to pay the bill. And the <strong>Dark Cultist</strong> has simply fallen in love with one of the things below, and serves it gladly, body and soul.</p>
  <p class="note">All four work <strong>Signs</strong> and <strong>Old Rites</strong> from Chapter XIII, paying the Old Dark in Nerve (and sometimes Blood, or worse). Every Sign carries a <strong>Rank</strong> from one to five, and you reach a new Rank at 1st, 3rd, 5th, 7th and 9th level; every Sign also sits on one of three lists. Three of these Callings draw on the Common Signs and <strong>the Bargain</strong>; the Witch alone draws on <strong>the Craft</strong>, which is older than the thing the others deal with. Each chooses a <strong>Bargain</strong> at 3rd level that grants a boon now and a greater boon at 9th — the shape of the bargain, the craft, the lie, or the devotion. Hexer and Dark Cultist begin Marked and walk the track quickly — the Hexer dragged, the Dark Cultist glad of it; the Witch does not begin Marked at all; and the False Prophet, cleverest and worst, sees to it that someone <em>else</em> bears the Mark in their stead.</p>
  <div class="quote">&ldquo;We put six torches and a deal of lead into the thing that used to be Abner Cole, and ran it clear to Diablo Canyon before it went down. What we buried was not a wolf, and it was not Abner. Salt the grave. Do not mark it.&rdquo;
    <span class="src">&mdash; Marshal T. Coyle, on a matter he would not enter in the ledger</span></div>

  <div class="pageno">25</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VII. Callings of the Old Dark</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-cultist">Dark Cultist</h2>
  <p>Where the Hexer <em>uses</em> the dark and the False Prophet <em>cheats</em> it, the Dark Cultist <strong>loves</strong> it.
  They have looked upon one of the old things beneath the country, understood exactly what it is, and chosen it — gladly,
  fully, with both hands. Their power is the gift of a true believer to a patron that answers, and they pay its price not in
  dread but in joy. The Hexer flinches at the Mark. The Dark Cultist counts each step of it as a sacrament, and asks the dark for one more.</p>
  <p class="statline">Hit Die d8 · Trained Skills 4 + WIT · Strong Save Will · Attack Slight</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">There Is Always a Brother.</span> In any settlement of any size at least one soul keeps the faith, and the signs the two of you share will turn them up by the second night. They will help you. What they want in exchange is a separate conversation, and it is never nothing.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>Nine workings that reach a fight by 10th level, and a Vessel that will not stay down when it ought to.</div>
    <div class="pays"><span class="k">You pay</span>A Slight attack, Backlash on every Sign, and a Mark you start the game already carrying. What you spend to be useful is written on you where the town can read it.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Devotion, Dark Communion, The Glad Mark</td></tr>
      <tr><td>2</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+3</td><td>Sign learned</td></tr>
      <tr><td>3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Sacrifice, Devotion</td></tr>
      <tr><td>4</td><td class="c">+2</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Sign learned</td></tr>
      <tr><td>5</td><td class="c">+3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Gifts of the Patron</td></tr>
      <tr><td>6</td><td class="c">+4</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Sign learned</td></tr>
      <tr><td>7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Edge, Rapture</td></tr>
      <tr><td>8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+2</td><td class="c">+6</td><td>Sign learned</td></tr>
      <tr><td>9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+3</td><td class="c">+6</td><td>Edge, Devotion (Greater)</td></tr>
      <tr><td>10</td><td class="c">+8</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Vessel</td></tr>
      <tr><td>11</td><td class="c">+9</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Sign learned, The Patron's Ear</td></tr>
      <tr><td>12</td><td class="c">+10</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+11</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Sign learned, What Is Owed</td></tr>
      <tr><td>14</td><td class="c">+12</td><td class="c">+4</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+13</td><td class="c">+5</td><td class="c">+5</td><td class="c">+9</td><td>The Patron Comes</td></tr>
    </tbody>
  </table>
  <h4>Devotion</h4>
  <p>You have a pool of <strong>Devotion</strong> — your patron's favor — equal to your RES modifier + half your level,
  refreshed through observance: the kept fast, the night vigil, the rite performed at the proper hour. It fuels your Dark
  Communion. A Dark Cultist who lets devotion lapse finds the favor cold exactly when it is needed.</p>
  <h4>Dark Communion</h4>
  <p>You draw on the <strong>Common Signs</strong> and <strong>the Bargain</strong> (Chapter XIII), up to the highest Rank your level allows, paid in Devotion (or, when that runs dry,
  in Nerve and Blood), and you receive them as what they are to you: genuine gifts from the thing you serve. You begin knowing
  two Signs and learn another at each <em>Sign learned</em>.</p>
  <h4>The Glad Mark</h4>
  <p>You begin already touched (Mark 1), as a Hexer does — but where the Hexer is dragged along the track, you <em>walk</em>
  it, willingly, eyes open. Reckless workings advance your Mark as theirs do; the difference is that you do not mourn the
  steps. And unlike any other Calling, a rising Mark <strong>repays</strong> you (see Gifts of the Patron). You are becoming
  something else on purpose, and calling it grace.</p>
  <h4>Sacrifice</h4>
  <p>Devotion is best shown in blood. Spend your own Blood to empower a working at the Blood-Price rate, or offer a worthier
  sacrifice — a beast, a treasure, a life — to petition your patron for a boon beyond your level, which the Keeper
  adjudicates. Great gifts demand great offerings, and the patron always knows the difference between a sacrifice that costs
  you and one that does not.</p>
  <h4>Gifts of the Patron</h4>
  <p>As the Mark claims you, the patron remakes you in its image. At Mark 2, 3, and 4, choose a <strong>Gift</strong>:
  unnatural resilience (DR), a malformed weapon-limb, sight that pierces any dark, a voice that staggers the faithful, the
  cold strength of the deep places. Each is a true power and a true disfigurement. The more monstrous you become, the more
  the dark can pour through you.</p>
  <h4>Rapture</h4>
  <p>Once per scene, give yourself over to ecstatic communion: become immune to fear and pain (ignore Frightened,
  gain DR) and let your workings surge in power. While raptured you cannot retreat, and you cannot act against your patron's
  interest — for in that moment you have no interest of your own.</p>
  <h4>Vessel</h4>
  <p>Once per session you may invite your patron to descend fully into you for a scene. You become its herald upon the
  earth, wielding power no mortal should hold — and the Keeper plays you while it lasts, for it is no longer entirely your
  body. When the scene ends, make a Will save against a DC the Keeper sets. Fail, and a little more of you stays behind the
  veil; fail at high Mark, and you do not come back at all, but step willingly into the dark a finished thing. The most
  devoted Dark Cultist's last prayer is always answered, exactly as it was asked.</p>
  <h4>The Patron's Ear</h4>
  <p>It listens now without being called. Once per scene, ask a question of your Patron in your own head and receive an
  answer: one word, one image, or one direction, honest in the way a thing that does not care about you is honest. Each
  answer moves you one step further toward its manner of seeing, and the Keeper keeps that count.</p>
  <h4>What Is Owed</h4>
  <p>You have learned the shape of the ledger you are in. Once per scene, name a price and pay it — Blood, Nerve, a memory,
  a year, a companion's luck — and take back exactly what it was worth: damage undone, a save passed, a Sign worked for
  free, a door open. The Keeper sets the exchange and the Keeper is not generous, but the Keeper is exact, and that is
  more than most bargains offer.</p>
  <h4>The Patron Comes</h4>
  <p>Once per session, you may open the way and let something through. It comes. For one scene the Patron is present in
  the world where you are standing — not summoned, not bound, not yours — and it does what it came to do, which will
  include the thing you wanted, and will not stop there. Say what you asked for and the Keeper says what arrives; the
  thing you asked for happens completely. Everything else that happens is the Keeper's. Your Mark rises by 1 permanently
  and cannot be reduced, every soul who witnessed it must save against fear at your Devotion DC or be Frightened for a
  day, and the place it stood in is never quite right again. You will do this more than once. That is the part they
  never believe when they are told.</p>

  <div class="box">
    <h3>On Playing a Dark Cultist</h3>
    <p>This is, more often than not, the Calling of the people the others ride out to stop — the membership of the cults the
    country breeds in its lonely places. It can be played, and played well: as a fallen soul seeking redemption, a true
    believer the party does not yet suspect, a double agent, or a tragedy walking knowingly into the fire. But its arc bends
    toward the monstrous by design. Talk it through with your table first. Some doors are written to be walked through; this
    Calling is the hinge.</p>
  </div>
    <div class="box">
    <h4>Dark Cultist&rsquo;s Devotions</h4>
    <p>At 3rd level, name the Patron you serve — one of the Patrons of the Old Dark on the following page. Your Devotion grants a boon at once and a greater boon at 9th level, as the thing below sinks its hooks the deeper.</p>
    <ul class="dash">
      <li><strong>The Cold Deep.</strong> Spend Devotion to drain warmth (Slowed, Drained, cold damage) and steady yourself against your end (reroll a failed Fortitude save to stop your bleeding; ignore fear). <em>Greater (9th):</em> once per session, open a sphere of annihilating cold that withers all within and shows each witness the indifferent end.</li>
      <li><strong>The Devourer.</strong> Slaying or sacrificing heals you and grants Devotion; your Gifts favor claws and toughness; you regenerate while fed. <em>Greater (9th):</em> once per scene, swell into a thing of teeth — large, swift, regenerating — devouring what you bring down.</li>
      <li><strong>The Long Trail.</strong> Spend Devotion to lay a withering death-touch (necrotic cold) and to sense the dying — you know who in your sight is marked to die soon, and may bid a freshly-slain foe rise and serve you a round. Your Gifts favor a deathless calm, an unerring eye for a mortal wound, and a body slow to quit. <em>Greater (9th):</em> once per session, pronounce a death sentence on one you can name — short of a true miracle the Long Trail comes for them before the arc is out — or, when you yourself fall, rise once at the next dusk, a little further down the trail than you were.</li>
      <li><strong>The Red Sermon.</strong> Spend Devotion to borrow a face and a honeyed voice — charm or compel those who hear you, pass for someone trusted, and feed on a crowd's devotion to refill your pool. You gather a small flock that believes, and their belief is meat. Your Gifts favor a stolen face, a compelling word, and a hunger worn as warmth. <em>Greater (9th):</em> once per session, hollow a gathering — every soul who can hear you is gripped by compulsion or terror, and a little of each is fed to the thing you serve, leaving you flush with power and them diminished and yours.</li>
      <li><strong>The Thing Beneath the Mountain.</strong> Spend Devotion to call on the deep stone — a crushing grip, a hide of grinding rock (DR and resistance), and tremor-sense through earth and floorboard. You see in the lightless dark, never lose your way underground, and the buried answers when you knock. Your Gifts favor stone flesh, a crushing strength, and the secrets of ore and vein. <em>Greater (9th):</em> once per session, wake the mountain a little — bring down a ceiling, split the ground, or clad yourself in living rock, huge and all but unkillable, for a few rounds.</li>
      <li><strong>The Whisperer.</strong> Spend Devotion to pluck a secret from a mind or the air, and to whisper madness — confusion, fear, or a Dread Check. <em>Greater (9th):</em> once per session, speak the Unspeakable Word — unmake a mind, or wring one true and terrible answer from your Patron.</li>
    </ul>
  </div>
  <div class="pageno">26</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VII. Callings of the Old Dark</span></div>
  <h2 id="ix-c-prophet">False Prophet</h2>
  <p>A False Prophet did not sign for power as a Hexer does, nor inherit it as a Witch does. They stumbled instead on a
  meaner trick: the dark will pay, and pay handsomely, for <strong>worship</strong> — and it does not greatly care where
  the worship is aimed. So the False Prophet raises a congregation that believes it prays to Heaven, skims the devotion off
  the top, and lets something out past the firelight drink the rest. The miracles are real. The gospel is a lie. And the
  bill, when at last it falls due, is mailed to the flock.</p>
  <p class="statline">Hit Die d8 · Trained Skills 6 + WIT · Strong Saves Reflex, Will · Attack Steady</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Whatever You Say You Are.</span> You arrive with papers, a history, and two or three people willing to swear to it: a bishop's letter, a discharge, a widow who remembers you fondly from somewhere she cannot quite place. It holds until somebody with a real reason to check actually checks, and most people go their whole lives without a real reason.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The same nine workings, and a mouth that can stop a fight before it becomes one.</div>
    <div class="pays"><span class="k">You pay</span>Steady attack, a d8, Backlash, and a Tribute that somebody else pays. Your power is borrowed from people who trust you.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td class="c">+2</td><td>Edge, False Gospel, The Conduit</td></tr>
      <tr><td>2</td><td class="c">+1</td><td class="c">+0</td><td class="c">+3</td><td class="c">+3</td><td>Stolen Wonder</td></tr>
      <tr><td>3</td><td class="c">+2</td><td class="c">+1</td><td class="c">+3</td><td class="c">+3</td><td>Edge, Gospel</td></tr>
      <tr><td>4</td><td class="c">+3</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Honeyed Word</td></tr>
      <tr><td>5</td><td class="c">+4</td><td class="c">+1</td><td class="c">+4</td><td class="c">+4</td><td>Edge, Visit the Cost</td></tr>
      <tr><td>6</td><td class="c">+5</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>Stolen Wonder</td></tr>
      <tr><td>7</td><td class="c">+6</td><td class="c">+2</td><td class="c">+5</td><td class="c">+5</td><td>Edge, Feed the Dark</td></tr>
      <tr><td>8</td><td class="c">+7</td><td class="c">+2</td><td class="c">+6</td><td class="c">+6</td><td>Stolen Wonder</td></tr>
      <tr><td>9</td><td class="c">+8</td><td class="c">+3</td><td class="c">+6</td><td class="c">+6</td><td>Edge, Gospel (Greater)</td></tr>
      <tr><td>10</td><td class="c">+9</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>The Hollow Crown</td></tr>
      <tr><td>11</td><td class="c">+10</td><td class="c">+3</td><td class="c">+7</td><td class="c">+7</td><td>Stolen Wonder (fourth), The Bigger Lie</td></tr>
      <tr><td>12</td><td class="c">+11</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+12</td><td class="c">+4</td><td class="c">+8</td><td class="c">+8</td><td>Stolen Wonder (fifth), Believers</td></tr>
      <tr><td>14</td><td class="c">+13</td><td class="c">+4</td><td class="c">+9</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+14</td><td class="c">+5</td><td class="c">+9</td><td class="c">+9</td><td>The Word Made Flesh</td></tr>
    </tbody>
  </table>
  <h4>The Conduit</h4>
  <p>Your power is stolen worship, and your pool of it is called <strong>Tribute</strong>. It equals your PRE modifier +
  half your level, but its maximum <em>swells</em> with the size and fervor of the flock you have deceived — a packed revival
  tent raises the ceiling high; a doubting crowd or a night alone drops it to nothing. Tribute refills when you preach the
  false gospel to believers. Cut off from a congregation to fleece, you are merely a liar with empty hands and a dangerous patron.</p>
  <h4>False Gospel</h4>
  <p>You may work a small repertoire drawn from the <strong>Common Signs</strong> and <strong>the Bargain</strong> (Chapter XIII), up to the Rank your level allows — but in your hands they wear the mask of holy
  wonders: light where there should be shadow, a dove where there should be a worm. None but the witch-sighted perceive the
  dark beneath. You pay for these workings in <strong>Tribute</strong>, never your own Nerve. You begin knowing two such
  wonders and learn another with each <em>Stolen Wonder</em> feature.</p>
  <h4>Honeyed Word</h4>
  <p>Few resist a prophet. Gain +3 on Persuade and Deceive against crowds and the faithful, and once per scene
  issue a Command the devout obey as scripture (Will save to resist, at disadvantage for true believers).</p>
  <h4>Visit the Cost</h4>
  <p>This is the black heart of the Calling, and the thing that sets you apart from every other soul in this chapter. When a
  working would make <em>you</em> pay — a Backlash, a Blood price, an advance of the Mark — you may instead lay that cost upon
  a member of your flock: a believer takes the wound, the ruin, the creeping Mark, while you walk away clean and haloed. The
  dark does not care who bleeds, only that someone does. But each time you do it, the thing behind your gospel sinks its
  hooks a little deeper into the congregation — and into you.</p>
  <h4>Feed the Dark</h4>
  <p>Once per session, offer the massed devotion of a gathering up to your unseen patron. Refill your Tribute and gain a
  surge besides — and the dark grows fat, while your flock comes away hollowed, hungrier for you, and a little less themselves
  than they were. They will not know why. They will only know they need another sermon.</p>
  <h4>The Hollow Crown</h4>
  <p>Once per session, for a single scene, you throw the doors wide and let the dark wear your gospel openly through you:
  tremendous power flows — great smitings, healings, terrors, commands — and the crowd will die at your asking, and some may.
  But you are no longer entirely the one preaching; the Keeper may put a word in your mouth and turn your hand, as the thing
  behind the curtain stretches into the room it has rented all this time. When the scene ends the Mark advances, and you
  understand the shape of the trick at last: you did not gather a flock for yourself. You baited a hook. You were the worm.</p>
  <h4>The Bigger Lie</h4>
  <p>The small ones stopped working on you years ago; the enormous ones have never failed. Once per session, tell a lie so
  large that checking it is somebody else's job — an army behind you, a pardon in your pocket, a dead man alive, the
  whole town in on it — and until it is disproved by direct evidence, everyone who heard it acts as though it were so.
  The disproving is a scene of its own, and you should be elsewhere by then.</p>
  <h4>Believers</h4>
  <p>You have gathered enough of them that they have become a resource rather than an audience. You command a congregation
  of your PRE modifier × 5 souls, which travels with you or is left where it is useful. They will lie for you, work for
  you, take a beating for you and give you what they have. They will not knowingly die for you. Once per session, they
  turn out to be exactly where you needed somebody. What you spend them on is on your account.</p>
  <h4>The Word Made Flesh</h4>
  <p>Once per session, a lie of yours becomes true. Name any single thing you have publicly claimed this session — a
  healing you faked, an authority you invented, a prophecy you made up on the spot, a power you do not have — and it is
  now the case, fully and in the world, for as long as the scene runs. The healed stand up. The prophecy occurs. The
  power is yours and works. Something made it so, and it was not you, and it did not do it as a favour. Your Mark rises
  by 1 and cannot be reduced, and from then on the thing that answered will occasionally make your lies true without
  being asked, at the moment least convenient to you, in front of the people you most needed to keep fooled.</p>

  <div class="box gold">
    <h4 id="ix-three-debts">Three Debts: Hexer, Witch, False Prophet</h4>
    <p>The <strong>Hexer</strong> borrows from the dark directly and is Marked from the first hour. The <strong>Witch</strong>
    inherits an older craft and pays in her own Nerve. The <strong>False Prophet</strong> does neither — they run a confidence
    game on the dark's behalf and arrange for the deceived to settle the account. The Hexer dreads the bill. The Witch budgets
    for it. The False Prophet mails it to a parishioner and passes the collection plate again.</p>
  </div>

  <div class="quote">
    "He laid hands on my boy and the fever broke, and I thanked God on my knees in the mud.
    My boy has not slept right since. Says a man with my preacher's face stands at the foot of the bed
    and takes something small out of him, each night, with great tenderness. I have stopped going to the tent.
    I find I am the only one in town who has."
    <span class="src">— testimony of a mother, recorded and sealed at Calvary Wells</span>
  </div>
    <div class="box">
    <h4>False Prophet&rsquo;s Gospels</h4>
    <p>At 3rd level, choose one. It grants a boon at once and a greater boon at 9th level — the deepening of the gospel.</p>
    <ul class="dash">
      <li><strong>The Borrowed Saint.</strong> Healing and blessing wonders cost 1 less Tribute and run deeper; you read as genuinely holy to Witch-Sight and any test of faith. <em>Greater (9th):</em> once per session, stage a public miracle that binds every witness to you as devoted and floods your Tribute.</li>
      <li><strong>The Doomsayer.</strong> Fear and smiting wonders surge; once per scene pronounce a small judgment — a blight, a swarm, a sickness, a curse of ill luck. <em>Greater (9th):</em> once per session, prophesy and unleash a scene-wide calamity, its cost paid by the deceived flock.</li>
      <li><strong>The Golden Calf.</strong> You and your faithful prosper — conjure good fortune and draw a sourceless income wherever you preach. <em>Greater (9th):</em> once per session, seal a covenant of plenty over a town for the arc, while the dark quietly mortgages the deceived.</li>
    </ul>
  </div>
  <div class="pageno">27</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VII. Callings of the Old Dark</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-c-hexer">Hexer</h2>
  <p>Some did not wait for the dark to come to them. The Hexer — conjure-doctor, hedge-sorcerer,
  pact-sworn — has reached into the old country beneath the country and pulled something back. Their power is real and it
  is borrowed, and the lender always collects. Every Hexer begins already touched (Mark 1), and every Hexer travels the
  Mark faster than the rest of the living. This is not a Calling for a soul that wishes to stay one.</p>
  <p class="statline">Hit Die d6 · Trained Skills 4 + WIT · Strong Save Will · Attack Slight</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">Your Debts Are Public.</span> What you pay for the dark shows on the world around you. Lamps gutter. Milk turns. The dog will not come into the room, and the priest's eye keeps coming back to you all through the sermon. Everyone in town knows what you are inside a week and not one of them can prove a word of it. You agreed to this.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The whole Old Dark ladder, earliest and deepest of anyone. Blood Price buys a working when the Nerve is gone.</div>
    <div class="pays"><span class="k">You pay</span>The worst body in the book. A d6, a Slight attack, Backlash on everything, a Mark from the first day, and a price paid in your own Blood when the pool runs dry.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td>Edge, Witch-Sight, Signs, Marked</td></tr>
      <tr><td>2</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+3</td><td>Sign learned</td></tr>
      <tr><td>3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Bargain</td></tr>
      <tr><td>4</td><td class="c">+2</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Sign learned</td></tr>
      <tr><td>5</td><td class="c">+3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Blood Price</td></tr>
      <tr><td>6</td><td class="c">+4</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Sign learned</td></tr>
      <tr><td>7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Edge</td></tr>
      <tr><td>8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+2</td><td class="c">+6</td><td>Sign learned</td></tr>
      <tr><td>9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+3</td><td class="c">+6</td><td>Edge, Bargain (Greater)</td></tr>
      <tr><td>10</td><td class="c">+8</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Sign learned, Adept</td></tr>
      <tr><td>11</td><td class="c">+9</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Sign learned, The Deeper Bargain</td></tr>
      <tr><td>12</td><td class="c">+10</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+11</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Sign learned, Adept (Second)</td></tr>
      <tr><td>14</td><td class="c">+12</td><td class="c">+4</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+13</td><td class="c">+5</td><td class="c">+5</td><td class="c">+9</td><td>The Long Debt</td></tr>
    </tbody>
  </table>
  <h4>Signs</h4>
  <p>You know and may work <strong>Signs</strong> — the rites of the Old Dark (Chapter XIII) — drawing on
  the <strong>Common Signs</strong> and on <strong>the Bargain</strong>, the list of those who reached out and took. You
  begin knowing two and learn another at each even level, choosing freely from any Rank your level has opened
  to you. Working a Sign costs Nerve, and sometimes Blood, and always risks <strong>Backlash</strong>.</p>
  <h4>Witch-Sight</h4>
  <p>You see what is truly there: the residue of violence, the Mark upon a soul, the thin places where the world wears
  through. This sight cannot be unlearned, and some nights you wish it could.</p>
  <h4>Marked</h4>
  <p>You begin at Mark 1 and advance the Mark faster than others — reckless use of Signs, and the knowledge they bring,
  pushes you along the track toward the thing you are slowly becoming. Power and ruin are the same road.</p>
  <h4>Blood Price</h4>
  <p>From 5th level you may pay for a Sign in Blood (Hit Points) when your Nerve runs short, at a rate of 2 Blood per point
  of Nerve. The Old Dark does not care which red ledger you draw from.</p>
  <h4>Adept</h4>
  <p>At 10th level, choose one Sign you know. You may work it without spending Nerve once per scene — though never without
  consequence.</p>
  <h4>The Deeper Bargain</h4>
  <p>You may borrow against yourself. Once per scene, work any Sign you know without spending Nerve by instead taking its
  Nerve cost as damage that cannot be healed until you have slept. A Hexer who has learned this generally learns it in
  one particular night, and remembers that night for good.</p>
  <h4>Adept (Second)</h4>
  <p>Choose a second Sign you know. It too may be worked once per scene without spending Nerve. The consequence attached to
  it does not stop attaching.</p>
  <h4>The Long Debt</h4>
  <p>Once per session, work any Sign of any rank you have ever read, whether or not you know it, whether or not you have
  the Nerve, at any scale the fiction can hold — a Sign laid on a town, on a river, on a bloodline, on a night. It
  works, completely, the first time and without a roll. Then the debt comes due, and it does not come due to you: the
  Keeper takes something from the world you were standing in. A person. A place. A year of somebody's life who never
  asked. You will be told what it cost afterward, in detail, and you will do it again, because you always know exactly
  what it is worth and you are never the one paying.</p>

  <div class="box gold">
    <h4>Working a Sign — the Short of It</h4>
    <p>Declare the Sign and pay its Nerve (or Blood). If it forces a save, the target rolls against your <strong>Sign DC</strong>
    = 10 + half your level + your RES modifier. Backlash strikes on the listed trigger — most often a natural 1 on any roll the
    working requires, or a failed working. The deep truths a Sign reveals may also demand a Dread Check of their own. Knowing is
    never free; for a Hexer, it is merely cheaper at first.</p>
  </div>
    <div class="box">
    <h4>Hexer&rsquo;s Bargains</h4>
    <p>At 3rd level, choose one. It grants a boon at once and a greater boon at 9th level — the deepening of the bargain.</p>
    <ul class="dash">
      <li><strong>The Conjurer.</strong> Bind a Sign or Rite into a charm anyone may trigger without Nerve (keep WIT-mod charms); +2 and half-time on Old Rites. <em>Greater (9th):</em> once per session, craft a great charm that wards a whole scene — allies gain a Ward, the uncanny recoil — paid for with something dear.</li>
      <li><strong>The Hollow-Born.</strong> Feel pain and fear dimly — DR 2 vs nonmagical harm, ignore the first Nerve lost each scene — but advance the Mark faster. <em>Greater (9th):</em> at Mark 4+, once per scene work any Sign without Nerve, paying in Blood instead — each working a step nearer the sixth Mark.</li>
      <li><strong>The Pact-Sworn.</strong> Once per scene, turn a failed Sign or Will save into a success by taking a Debt; on your third Debt the Patron calls it in — a demand, and +1 Mark. <em>Greater (9th):</em> once per session, when you would die, the Patron stays death's hand — stabilize at 1 Blood and rise, at the cost of +1 Mark.</li>
      <li><strong>The Spiritist.</strong> See and briefly question the recently dead; set a willing spirit to watch and warn (+5 Notice). <em>Greater (9th):</em> once per session, invite a willing spirit to act through you for a round, borrowing a skill or memory; the unwilling risks possession.</li>
    </ul>
  </div>
  <div class="pageno">28</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>VII. Callings of the Old Dark</span></div>
  <h2 id="ix-c-witch">Witch</h2>
  <p>Where the Hexer signs for borrowed power, the Witch was born to hers, or had it handed down a crooked family line, or
  learned it slow from an old woman at the edge of a town that no longer exists. The Craft is older than the dark the Hexer
  bargains with, and steadier; a Witch does not begin Marked, and need not end that way. But the Craft keeps its own
  accounts — in curses that linger, in a familiar's small life bound to hers, and in the quiet certainty that the village
  will turn on her the day a child takes sick.</p>
  <p class="statline">Hit Die d6 · Trained Skills 4 + WIT · Strong Save Will · Attack Slight</p>
  <p class="perk"><span class="lbl">Perk</span><span class="nm">They Come to You at Night.</span> Whatever the town says about you in daylight, somebody knocks after dark: a girl in trouble, a man with a debt, a mother with a child that will not wake. You always have something worth trading, and there is always somebody in that town who cannot afford to watch you hang.</p>
  <div class="fight">
    <div class="brings"><span class="k">In a fight</span>The Craft, which no other Calling may learn, a familiar out on the field with you, and the Evil Eye.</div>
    <div class="pays"><span class="k">You pay</span>A d6 and the weakest Strike in the book. You will not shoot your way out of anything. The Craft is the whole of your answer and it is prepared work, so a fight you did not see coming is a fight you begin behind.</div>
  </div>
  <table class="lvl">
    <thead><tr><th class="c">Lvl</th><th class="c">Attack</th><th class="c">Fort</th><th class="c">Ref</th><th class="c">Will</th><th>Class Features</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+2</td><td>Edge, The Craft, Familiar, The Evil Eye</td></tr>
      <tr><td>2</td><td class="c">+0</td><td class="c">+0</td><td class="c">+0</td><td class="c">+3</td><td>Sign learned</td></tr>
      <tr><td>3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+1</td><td class="c">+3</td><td>Edge, Craft</td></tr>
      <tr><td>4</td><td class="c">+2</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Sign learned, Brew</td></tr>
      <tr><td>5</td><td class="c">+3</td><td class="c">+1</td><td class="c">+1</td><td class="c">+4</td><td>Edge, Hex</td></tr>
      <tr><td>6</td><td class="c">+4</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Sign learned</td></tr>
      <tr><td>7</td><td class="c">+5</td><td class="c">+2</td><td class="c">+2</td><td class="c">+5</td><td>Edge</td></tr>
      <tr><td>8</td><td class="c">+6</td><td class="c">+2</td><td class="c">+2</td><td class="c">+6</td><td>Sign learned</td></tr>
      <tr><td>9</td><td class="c">+7</td><td class="c">+3</td><td class="c">+3</td><td class="c">+6</td><td>Edge, Craft (Greater)</td></tr>
      <tr><td>10</td><td class="c">+8</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Sign learned, The Old Witch</td></tr>
      <tr><td>11</td><td class="c">+9</td><td class="c">+3</td><td class="c">+3</td><td class="c">+7</td><td>Sign learned, The Second Familiar</td></tr>
      <tr><td>12</td><td class="c">+10</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Edge</td></tr>
      <tr><td>13</td><td class="c">+11</td><td class="c">+4</td><td class="c">+4</td><td class="c">+8</td><td>Sign learned, The Deep Craft</td></tr>
      <tr><td>14</td><td class="c">+12</td><td class="c">+4</td><td class="c">+4</td><td class="c">+9</td><td>Edge</td></tr>
      <tr><td>15</td><td class="c">+13</td><td class="c">+5</td><td class="c">+5</td><td class="c">+9</td><td>What the Old Ones Knew</td></tr>
    </tbody>
  </table>
  <h4>The Craft</h4>
  <p>You know and work <strong>Signs</strong> (Chapter XIII), beginning with two and learning another at each even level,
  paid in Nerve and risking Backlash as the Hexer's are, and choosing freely from any Rank your level has opened.
  Where you differ is the list. You draw on the <strong>Common Signs</strong> and on <strong>the Craft</strong>, and the Craft is
  closed to every other Calling in this book — no Hexer learns the Poppet, and no cultist will ever ward a house.
  The Craft is inherited, not borrowed: you do <strong>not</strong> begin Marked, and you advance the Mark only through
  genuine recklessness, never automatically. The dark did not hand you this. Your line did.</p>
  <h4 id="ix-familiar">Familiar</h4>
  <p>A small beast is bound to you — a cat, a crow, a hare, a toad, a black snake. It is cannier than any animal, scouts and
  spies at your bidding, can deliver a touch-range Sign for you, and grants a standing boon while near (a +2 to one sense or
  skill befitting its nature). You share its senses at will. Should it die, you are Sickened until you can bind another over
  a long night's rite — and you will feel the loss far longer than the penalty lasts.</p>
  <h4>The Evil Eye</h4>
  <p>With a look and a muttered word, lay a minor bane on a creature you can see (Will save vs your Sign DC): –1 to its rolls
  and a run of small misfortunes for a round per two levels. It costs no Nerve, but everyone who sees you do it remembers
  your face.</p>
  <h4>Brew</h4>
  <p>This is the kitchen craft, not the Rank 3 Sign of the same family — <em>The Brewing</em> bottles a
  working, while this bottles medicine. Given a kitchen, a fire, and time, you brew the work of the Goods chapter and more — healing poultices, sleeping
  draughts, truth-loosening teas, and poisons that no assayer can name. Treat your brews as a Sawbones' Tonics, with effects
  you and the Keeper devise; the dose is in the making, and the making is in your hands.</p>
  <h4>Hex</h4>
  <p>Your maledictions grow teeth. As an action and 1 Nerve, lay a true <strong>Hex</strong> on a foe (Will save vs Sign DC):
  Frightened, Clumsy, Sickened, or cursed with ruinous luck (foes' crits against allies, your crits against the cursed) for a
  scene. A Hexed soul knows it is Hexed, and knows who did it, which is sometimes the worst of it.</p>
  <h4>The Old Witch</h4>
  <p>At 10th level your curses set like winter ground: a target who fails a Hex carries it until it is lifted by rite,
  apology, or your death. Once per session you may speak a <em>true curse</em> of dire and lasting effect, the kind that
  follows a bloodline. You have outlived everyone who feared you young. The ones who fear you now are right to.</p>
  <h4>The Second Familiar</h4>
  <p>A second beast comes to you and stays. Bind it as you bound the first, from the table of familiars: you gain its boon
  as well, both may be abroad at once, and either may carry the Evil Eye for you at a distance you can walk in an hour.
  Two of them will not stay in the same room, and you will spend a surprising amount of your life managing that.</p>
  <h4>The Deep Craft</h4>
  <p>Your brews and hexes have stopped being small. A Brew you make lasts a season rather than a day and may be given away
  without weakening, and a Hex you lay may name a condition for its lifting rather than a duration — a spoken apology, a
  returned thing, a river crossed, a name said three times. Most who carry one never learn the condition, which is
  generally the point.</p>
  <h4>What the Old Ones Knew</h4>
  <p>Once per session, do the thing the old women in the stories do. Change one thing that has already happened this
  session, as though it had gone otherwise: the shot missed, the door was locked, the letter never came, she was
  somewhere else that night. It is not an illusion and nobody remembers it the old way except you and anything older
  than you. The world simply is as you have said. What it costs is fixed: you age a year, the nearest living thing that
  trusts you dies quietly within the week, and one of your own memories goes into the gap to hold it open. You will not
  know which one is missing. You will only notice, sometimes, that there is a space where a name used to be.</p>

  <div class="box gold">
    <h4>Witch and Hexer — the Difference</h4>
    <p>Both work Signs and pay in Nerve, but the Hexer's power is a <em>loan</em> (begins Marked, races the Mark) while the
    Witch's is <em>inheritance</em> (no starting Mark, advances it only through abuse). A Hexer can become a Witch's cautionary
    tale; a Witch can become a Hexer the day she reaches for something her line never taught her. Keep the distinction at the
    table — it is the whole tragedy of the chapter.</p>
  </div>
    <div class="box">
    <h4>Witch&rsquo;s Crafts</h4>
    <p>At 3rd level, choose one. It grants a boon at once and a greater boon at 9th level — the deepening of the craft.</p>
    <ul class="dash">
      <li><strong>The Cursewife.</strong> Your Hexes and Evil Eye strike harder and cling tighter; Hex two targets at once; lifting your curse costs dearly. <em>Greater (9th):</em> once per session, lay a curse of escalating ruin on a wrongdoer until they amend, fall, or flee the country.</li>
      <li><strong>The Familiar-Bound.</strong> Your familiar grows clever and hardy, delivers your Signs, and lets you see and hear through it at any distance. <em>Greater (9th):</em> swap places with it once per scene and share wounds or Blood; should you fall, it carries your spirit to a new dawn — once.</li>
      <li><strong>The Greenwitch.</strong> Brews never spoil and take half the time; keep a free healing or warding brew; +2 Survival and Medicine; beasts will not harm you unbidden. <em>Greater (9th):</em> once per scene, call the wild — walling thorns, a healing green circle, or a trail the land hides until dawn.</li>
      <li><strong>The Moon-Daughter.</strong> See in the dark; once a night take to the air until dawn; slip into a sleeper's dreams to glean or leave a secret. <em>Greater (9th):</em> once per session, ride the night sky to any place you have been, carrying your coven, and walk the dreams of the distant sleeping.</li>
    </ul>
  </div>
  <div class="pageno">29</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">VII. Callings of the Old Dark</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-patrons">The Patrons of the Old Dark</h2>
  <p>The Old Dark is a depth rather than a god, and things move in that depth. Certain of them are old enough and
  particular enough to be worth a name, and those are the <strong>Patrons</strong>: the powers a Hexer borrows from on
  his Bargain, a Dark Cultist serves in her Devotion, and a False Prophet feeds through his Gospel without ever quite
  learning whose plate he is filling. A Witch seldom deals with them at all. Her Craft is older and quieter and does not
  need them.</p>
  <p>Nobody has written any of this down honestly. What follows is what the country says, which is a different thing:
  six sets of stories, collected off men who were drunk, frightened, or lying, and set out here in the order they are
  usually told. Your Keeper knows which parts are true. You are not going to find out by asking.</p>

  <h3>The Devourer</h3>
  <p>They tell it about the winter of the Ellender party, snowed in above the tree line with eleven souls and four days
  of flour. Nine came down in the spring, fat and glossy and walking easy, and would not say what they ate. The story
  has been told in a dozen counties with a dozen different names on it, which is either evidence that it never happened
  or evidence that it keeps happening. Every telling agrees on the same two details: nobody ever went hungry again, and
  nobody ever stopped eating.</p>

  <h3>The Whisperer</h3>
  <p>There is a version of this one in every town and it is always about somebody's uncle. The uncle woke one morning
  knowing a thing he had no way to know, and it was right, and he made money off it. Then he woke knowing another. In
  the tellings where the uncle is a figure of fun, he ends up in the territorial asylum shouting corrections at the
  walls. In the tellings where he is a warning, he ends up perfectly calm and perfectly correct and no longer anybody's
  uncle. The tellings where he is a figure of fun are considerably more common, and considerably newer.</p>

  <h3>The Cold Deep</h3>
  <p>Nobody tells a story about the Cold Deep. They tell you about a person. A widow who stopped wearing black and
  stopped wearing anything else either; a man who buried a child in March and was seen in June and had nothing at all
  behind his eyes; a deputy who walked into a burning house and out again and never once mentioned it. The country
  notices this kind of quiet, and it does not have a word for it, so it borrows one from the weather.</p>

  <h3>The Long Trail</h3>
  <p>Every road out here has a rider on it one ridge behind you, and every teamster who has ever been asked about him
  says the same thing: he is not gaining. The stories divide sharply on what happens when he does. Half of them say
  the dead come back and the other half say the dead come back <em>wrong</em>, and both halves are told by people who
  claim to have seen it. There is a third kind of story, less often told, in which somebody who ought to have died
  simply did not, and afterward could always tell you exactly when anybody in the room was going to.</p>

  <h3>The Thing Beneath the Mountain</h3>
  <p>The Cornish miners will not work a bad vein and will not tell an American why. The Mexican crews have a different
  set of names for the same thing and the same refusal. Ask any of them and you get a shrug and a change of subject;
  ask a company man and you get a lecture about superstition and productivity. Two facts are not in dispute anywhere in
  the Territories. Some seams pay better than they have any business paying. And the men who work them stop coming up
  for air.</p>

  <h3>The Red Sermon</h3>
  <p>This is the newest of the six and the one people are least willing to tell in front of a preacher. A revival comes
  through, and it is a good one, and the drunks dry out and the fighting stops and the collection plate goes around
  twice. Six months later the town is quieter than it was before the tent came. Not worse. Quieter. The story is always
  told by somebody from the next county over, and it is never their own town, and if you ride to the town they name you
  will find a perfectly ordinary place where nobody remembers a revival.</p>

  <div class="box">
    <h4>The Mad Spaniard</h4>
    <p>He is not a Patron and every story about him is attached to one. A gentleman in a good coat, forty years out of
    date, met on a road at an hour when no one should be on it. He is unfailingly polite. He knows your business. He
    asks after people you have not thought about in years, by name, and gets the details right, and one of the details
    is always wrong in a way you do not notice until later.</p>
    <p>The stories cannot agree on what he wants and are unanimous that he wants something. In the mining camps he
    warns men off the bad veins and is thanked for it. On the Llano he is said to have ridden with the comancheros and
    to have been the reason they stopped. In the Rockies they say he is going from cult to cult with a proposal. He has
    been described the same way for a hundred and forty years by people with no reason to have compared notes, and the
    description includes a scar he did not have in the earliest tellings.</p>
    <p>Every soul who works the Old Dark hears of him eventually. A good many claim to have met him. A few have.</p>
  </div>
</section>

<!-- ===================== VIII. SKILLS ===================== -->
<section class="page" id="skills">
  <div class="runhead"><span class="l">VIII. Skills</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">VIII. Skills</h1>
  <p class="chapter-sub">The hundred small competencies between you and the grave.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Skills are the things you have learned to do on purpose. Each is tied to an ability and to a
  <strong>proficiency rank</strong> — untrained, trained, expert, or master. Once you are trained, your check is a d20 +
  your proficiency (your level, plus +2 trained, +4 expert, or +6 master) + the keyed ability's modifier, against a
  Difficulty Class; while untrained, you roll ability alone. At creation you become trained in a number of skills set by
  your Calling and your Wits, and you raise one skill a rank with each <strong>skill increase</strong> at 3rd, 5th, 7th,
  and 9th level, as your level allows — for out here, a thing you cannot do is a way you can die.</p>
  <table>
    <thead><tr><th>Skill</th><th>Ability</th><th>What It Covers</th></tr></thead>
    <tbody>
      <tr><td>Acrobatics</td><td>DEX</td><td>Balance, tumbling, slipping a grapple or a fall</td></tr>
      <tr><td>Animal Handling</td><td>PRE</td><td>Calming, driving, training beasts; reading them</td></tr>
      <tr><td>Athletics</td><td>STR</td><td>Climbing, swimming, jumping, raw feats of body</td></tr>
      <tr><td>Deceive</td><td>PRE</td><td>Lies, disguise, the confidence and the con</td></tr>
      <tr><td>Gamble</td><td>PRE</td><td>Cards, dice, odds, and the reading of opponents</td></tr>
      <tr><td>Insight</td><td>RES</td><td>Reading truth, motive, and madness in a face</td></tr>
      <tr><td>Intimidate</td><td>PRE</td><td>Threats, menace, the cold promise of violence</td></tr>
      <tr><td>Lore: Frontier</td><td>WIT</td><td>Towns, trails, peoples, law, history, rumor</td></tr>
      <tr><td>Lore: Occult</td><td>WIT</td><td>The Old Dark, its signs, its rites, its appetites</td></tr>
      <tr><td>Medicine</td><td>WIT</td><td>First aid, surgery, disease, poison, the dying</td></tr>
      <tr><td>Notice</td><td>RES</td><td>Spotting the ambush, the tell, the wrong shadow</td></tr>
      <tr><td>Persuade</td><td>PRE</td><td>Reason, charm, negotiation, the honest plea</td></tr>
      <tr><td>Repair</td><td>WIT</td><td>Mending guns, tack, wagons, machinery, traps; clearing a misfire</td></tr>
      <tr><td>Ride</td><td>DEX</td><td>Horsemanship, mounted fighting, hard country at speed</td></tr>
      <tr><td>Sleight</td><td>DEX</td><td>Palming, pickpocketing, marking cards, hidden draws</td></tr>
      <tr><td>Stealth</td><td>DEX</td><td>Moving unseen and unheard; hiding self and goods</td></tr>
      <tr><td>Survival</td><td>RES</td><td>Tracking, foraging, weather, wayfinding, shelter</td></tr>
    </tbody>
  </table>

  <h2 id="ix-using-skills">Using a Skill</h2>
  <p>Most of the time, the Keeper sets a DC from the table in Chapter II and you roll. Some uses deserve a word:</p>
  <ul class="dash">
    <li id="ix-demoralize"><strong>Demoralize.</strong> A combat use of Intimidate: spend a Beat and roll Intimidate against a foe's Will save (DC 10 + half their level + their PRE modifier). On a success the target is <strong>Frightened 1</strong>; on a critical success, Frightened 2. Several Callings sharpen this — letting you Demoralize a whole group at once, or strike harder at the cowed.</li>
    <li id="ix-aid"><strong>Helping (Aid).</strong> Declare you are helping before the action; on your turn, make a DC 10 check of a relevant skill. Success grants your ally +2 (a critical success, +3); a critical failure may hinder them by –1. Many hands make light a heavy door.</li>
    <li><strong>Lore as a lifeline.</strong> A successful Lore (Occult) check may tell you what a thing is, what it wants, and what it fears — but every such check on the deep dark risks a Dread Check (Chapter XII). A <em>critical</em> success tells you all three and spares the Dread Check; a <em>critical</em> failure plants a confident lie. Knowing is never free.</li>
    <li><strong>Opposed work.</strong> Stealth opposes Notice; Deceive opposes Insight; Sleight opposes Notice. Read these as opposed rolls, not flat DCs, when a living mind stands against you.</li>
    <li id="ix-spoor"><strong>Reading the country.</strong> A Survival check forewarns of weather, finds water, and reads how long ago something passed. <em>Spoor</em> is the physical trace a thing leaves &mdash; track, scat, hair on wire, blood, a scrape on a tree at a height you would rather not measure; <em>sign</em> is everything wider, the kill, the silence, the stock that will not go back in the barn. Against the spoor of the uncanny the DC rises and the answer chills, and some things you will only ever meet this way: the Keeper is not obliged to put every horror in front of you in the flesh, and the ones two Tiers above your posse arrive as tracks and a survivor's account. Read them well. It is the difference between a thread and a funeral.</li>
    <li id="ix-untrained"><strong>Untrained.</strong> You may attempt most skills while untrained, rolling ability alone — save for Medicine (surgery), Repair (machinery), and the two Lores, which need at least Trained proficiency to attempt the hard work. The untrained do not perform amputations by guesswork. Often they perform them anyway.</li>
  </ul>

  <div class="box">
    <h4 id="ix-green-table">At the Green Table &mdash; Each Trade Its Own Tell</h4>
    <p>Anyone may sit down to cards, and most do. Beyond the <strong>Gamble</strong> skill itself, every worldly Calling &mdash; and every Calling of the Old Dark &mdash; brings a small standing edge to the table, in the manner of the Gift an Origin grants. (Men and women of faith are pointedly absent from this list; the Padre would rather you came to the rail than the rake.) Each edge below is a minor knack, not a class feature.</p>
    <ul class="dash">
      <li><strong>Bounty Hunter &mdash; Reading the Room.</strong> Gain +1 on Notice and Gamble checks to take the measure of a table, and you know at a glance which player is carrying the most iron &mdash; and which face matches the paper in your pocket.</li>
      <li><strong>Drifter &mdash; Stranger&rsquo;s Seat.</strong> No one here has played you before. Gain +1 on Gamble checks at any table where you are not known, and a foe gets no read on your tells the first hand.</li>
      <li><strong>Gambler &mdash; The Whole Craft.</strong> The table is your trade and it shows. Treat your proficiency rank in Gamble as one rank higher, and you may spend <strong>Favor</strong> on Gamble checks as on any other roll. The others bring a knack; you brought your life&rsquo;s work.</li>
      <li><strong>Gunhand &mdash; Nobody Calls a Loaded Hand.</strong> Gain +1 on Gamble checks to bluff or hold a pot while you are openly armed. Few men call a shootist&rsquo;s raise on a thin hand.</li>
      <li><strong>Marshal &mdash; House Rules.</strong> Gain +1 on Gamble checks at a table where your authority is known, and +2 to catch a cheat (Notice against their Sleight). Crooked dealers fold early when a badge sits down.</li>
      <li><strong>Mountain Man &mdash; Granite Face.</strong> Your weathered stillness gives nothing away: foes take &minus;1 to read your tells, and you ignore the first measure of drink or fatigue that would shake another&rsquo;s hand.</li>
      <li><strong>Prospector &mdash; Reads the Odds Like Ore.</strong> Gain +1 on Gamble checks in games of pure chance &mdash; faro, dice, chuck-a-luck &mdash; which you reckon as coldly as an assay.</li>
      <li><strong>Sawbones &mdash; The Body Doesn&rsquo;t Lie.</strong> Gain +1 on Gamble checks to read an opponent. You mark the racing pulse, the dry mouth, the sweat at the collar &mdash; the tells a man cannot will away.</li>
      <li><strong>Dark Cultist &mdash; The Patron Smiles.</strong> Once per session, when you stake something real, your patron tilts a single card your way: roll one Gamble check twice and keep the better. A small grace, and never a free one.</li>
      <li><strong>False Prophet &mdash; The Long Con.</strong> Gain +1 on Gamble checks to deceive at the table; you run a crooked game as smoothly as a crooked gospel, and the marks thank you for the fleecing.</li>
      <li><strong>Hexer &mdash; Borrowed Luck.</strong> Once per session, whisper to the Old Dark and reroll one Gamble check. The unpaid luck comes due later &mdash; a point of Nerve, or worse, at the Keeper&rsquo;s choosing.</li>
      <li><strong>Witch &mdash; A Charm in the Sleeve.</strong> Keep a small luck-charm worked beforehand; once per session it turns one losing hand into a winning one &mdash; until someone notices the brew on your breath.</li>
    </ul>
  </div>

  <div class="quote">
    "There is no such thing as a useless skill out here. There is only the skill you did not have
    on the one night it would have mattered, and the small wooden marker they put up after."
    <span class="src">— from a primer for greenhorns, sold for a dollar, worth more</span>
  </div>
  <div class="pageno">31</div>
</section>

<!-- ===================== IX. EDGES ===================== -->
<section class="page" id="edges">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>IX. Edges</span></div>
  <h1 class="chapter">IX. Edges</h1>
  <p class="chapter-sub">The hard-won knacks that set the quick apart from the dead.</p>
  <div class="divider"></div>
  <div class="quote">
    &ldquo;The greenhorn asks what a man's good at. The old hand asks what he's lived through.
    Same question, and only one of them knows it.&rdquo;
    <span class="src">&mdash; Marshal T. Coyle</span>
  </div>
  <p class="dropcap lead">Every character gains an Edge at 1st level and at each odd level after — 1st, 3rd, 5th, 7th, and 9th —
  and then again at 12th and 14th, and may also raise one ability score by a point at 5th, 10th and 15th. Edges are the
  deliberate choices that shape what your character is good at. Some have requirements, noted in parentheses. A selection
  follows, grouped by the part of you they sharpen; your Keeper may allow others.</p>
  <p class="note">An Edge marked <strong>(11th)</strong> cannot be taken before eleventh level, whatever else you meet. Those
  are what the two late Edges are for, and a Calling's own late Edge builds on the feature it names, so the pair of them are
  usually taken together.</p>

  <h2 id="ix-eg">Edges of the Gun</h2>
  <p class="note">These knacks come alive under the Iron Code (Chapter XI). Where one speaks of <em>Strikes</em>, <em>Beats</em>,
  the <em>Multiple Attack Penalty</em>, or <em>misfires</em>, see that chapter.</p>
  <ul class="dash">
    <li id="ix-e-cylinder"><strong>Cylinder &amp; Sky.</strong> (Quick Draw) Once per round, when you reduce a foe to 0 Blood, you may immediately spend a Beat you have not yet used to reload — a habit that has outlived a great many faster men.</li>
    <li id="ix-e-dead-eye"><strong>Dead Eye.</strong> (DEX 15) Once per scene, before rolling a single Strike, declare it a hit short of the impossible; it cannot be a failure, and you roll its damage twice, keeping the higher. It cannot, however, become a critical on its own.</li>
    <li id="ix-e-fan"><strong>Fan the Hammer.</strong> (Quick Draw) With a single-action revolver, spend two Beats to make up to three Strikes, applying the Multiple Attack Penalty as normal but at half the usual step (–2/–4 rather than –5/–10). Loud, wasteful, final.</li>
    <li id="ix-e-calm"><strong>Gunfighter's Calm.</strong> Once per scene, ignore the Multiple Attack Penalty on a single Strike — the noise falls away and the world seems to slow to let you aim.</li>
    <li id="ix-e-reload"><strong>Practiced Reload.</strong> Reduce the Beats to reload any one weapon you favor by 1 (minimum 0). You clear your own misfires as a single Interact rather than an action plus a check.</li>
    <li id="ix-e-quick-draw"><strong>Quick Draw.</strong> You may draw and Strike in one motion, and add +2 to the roll deciding who shoots first.</li>
    <li id="ix-e-steady"><strong>Steady Shot.</strong> If you do not move on your turn, ignore the first range increment penalty and gain +1 to hit. With a Kickback weapon you also ignore the recoil penalty.</li>
    <li id="ix-e-throw"><strong>Throw the Stick.</strong> If you carry powder, you may hurl a lit charge in place of a Strike, lobbing it a fair distance to burst where it lands.</li>
    <li id="ix-e-two-gun"><strong>Two-Gun.</strong> Fight with a pistol in each hand. Your off-hand Strike does not increase your Multiple Attack Penalty for that round, though it is still made at the current penalty.</li>
    <li id="ix-e-two-guns-speaking"><strong>Two Guns Speaking.</strong> (Two-Gun, 11th) Both irons at once count as one Strike: roll once, and on a
      hit apply the damage of both weapons. Your Multiple Attack Penalty does not rise for it. Reloading two guns still takes reloading two guns.</li>
    <li id="ix-e-through-and-through"><strong>Through and Through.</strong> (11th) A shot that drops a foe carries on. When a Strike reduces a
      creature to 0 Blood, make one free Strike at the same attack against a second creature standing behind or beside it.</li>
    <li id="ix-e-the-last-round"><strong>The Last Round.</strong> (11th) You are never out at the moment it matters. Once per scene, declare that the
      chamber you thought was empty is not, and take one Strike with it at +2. Nobody has ever caught you counting.</li>
</ul>

  <h2 id="ix-ebd">Edges of the Body</h2>
  <ul class="dash">
    <li id="ix-e-fleet"><strong>Fleet.</strong> Your Speed afoot increases by 10 feet.</li>
    <li id="ix-e-hard-to-kill"><strong>Hard to Kill.</strong> Once per session, when you would drop to 0 Blood, drop to 1 instead and stay on your feet. The frontier is not done with you yet.</li>
    <li id="ix-e-iron-gut"><strong>Iron Gut.</strong> +2 on Fortitude saves against poison, disease, drink, and spoiled provisions — and you can hold your liquor past any reasonable man.</li>
    <li id="ix-e-saddle-born"><strong>Saddle-Born.</strong> You and your horse act as one; never fall from the saddle by mishap, and fight mounted without penalty.</li>
    <li id="ix-e-rawhide"><strong>Tough as Rawhide.</strong> Gain +1 Blood per level, now and as you advance.</li>
    <li id="ix-e-old-bones-old-habits"><strong>Old Bones, Old Habits.</strong> (11th) You do not get Fatigued, by weather, wounds, want of sleep, hard
      travel or the uncanny. You still feel all of it. You have simply stopped letting it decide anything.</li>
    <li id="ix-e-get-up"><strong>Get Up.</strong> (Hard to Kill, 11th) Once per scene, on your own turn while Dying, stand at half your Blood with
      everything you were holding. Whatever put you down is entitled to be surprised.</li>
</ul>

  <h2 id="ix-emn">Edges of Mind and Nerve</h2>
  <ul class="dash">
    <li id="ix-e-born-lucky"><strong>Born Lucky.</strong> Once per session, reroll any single roll you have just made — yours, and no one else's — and keep the kinder result.</li>
    <li id="ix-e-cold-read"><strong>Cold Read.</strong> +3 on Insight, and you may spend a moment to learn one true thing a person is trying to hide.</li>
    <li id="ix-e-gallows"><strong>Gallows Humor.</strong> Once per scene, crack wise in the face of the awful and recover 1d6 Nerve — yours, or a companion's who laughs.</li>
    <li id="ix-e-iron-will"><strong>Iron Will.</strong> Once per scene, reroll a failed save against fear, charm, or compulsion and keep the better result.</li>
    <li id="ix-e-stone"><strong>Stone Nerve.</strong> Gain +2 maximum Nerve per level, and +1 on Dread Checks. The horrors find you harder ground.</li>
    <li id="ix-e-unshakable"><strong>Unshakable.</strong> (RES 13) The first time each scene you would lose Nerve, lose none instead. You have seen worse, or tell yourself so.</li>
    <li id="ix-e-nothing-new-under-the-"><strong>Nothing New Under the Sun.</strong> (11th) You have seen a version of this before. Gain +4 on any
      check to identify a creature, a working, a poison, a mechanism or a scheme, and the Keeper will tell you one true thing about it whether you
      rolled well or not.</li>
    <li id="ix-e-the-long-view"><strong>The Long View.</strong> (11th) Once per session, ask the Keeper what the worst likely consequence of the plan
      on the table is, and get a straight answer. It is not prophecy. It is thirty years of watching plans.</li>
    <li id="ix-e-known-far-off"><strong>Known Far Off.</strong> (11th) Your name has travelled ahead of you. In any settlement, somebody already knows
      it and one of the following is true, your choice: they are glad, they are afraid, or they owe you. The Keeper says who.</li>
</ul>

  <h2 id="ix-efr">Edges of the Frontier</h2>
  <ul class="dash">
    <li id="ix-e-provider"><strong>Dead Shot Provider.</strong> You never want for food or fresh horses where game or ranches exist, and your camp is always well-sited.</li>
    <li id="ix-e-frontier-med"><strong>Frontier Medicine.</strong> (Trained in Medicine) Your field care heals an extra 1d6, and you can improvise a remedy from what the land offers.</li>
    <li id="ix-e-pathfinder"><strong>Pathfinder.</strong> You are never truly lost; gain +2 on overland travel and always find water, forage, and safe ground where others find none.</li>
    <li id="ix-e-powder"><strong>Powder Sense.</strong> +2 to set, spot, or disarm charges and traps, and your own blasts never catch a friend you can plainly see.</li>
    <li id="ix-e-tracker"><strong>Tracker.</strong> +3 on Survival to track, and you may track across stone, shallow water, and the spoor of unnatural things.</li>
    <li id="ix-e-the-country-knows-you"><strong>The Country Knows You.</strong> (11th) You are never lost, never without water, and never without a
      place to sleep out of the weather, in any country you have crossed once before. Nothing hostile finds your camp by accident.</li>
    <li id="ix-e-winter-proof"><strong>Winter-Proof.</strong> (Iron Gut, 11th) Cold, heat, thin air, thirst, bad water and foul air do you no harm at
      all, and you may carry one soul through the same for a day.</li>
</ul>

  <h2 id="ix-eod">Edges of the Old Dark</h2>
  <ul class="dash">
    <li id="ix-e-hedge"><strong>Hedge Magic.</strong> You learn a single Sign (Chapter XIII) and gain a small Nerve pool to fuel it, though you are not a Hexer. Knowledge has a way in.</li>
    <li id="ix-e-salt-wise"><strong>Salt-Wise.</strong> +2 on Lore (Occult), and the Old Rites (Chapter XIII) take you half the usual time and materials.</li>
    <li id="ix-e-touched"><strong>Touched.</strong> (RES 13) You have brushed the uncanny and lived. Gain Witch-Sight, +1 Mark, and an unsettling certainty about where the dark is thickest.</li>
    <li id="ix-e-warded"><strong>Warded.</strong> (Salt-Wise) Scribe a ward at a threshold that the uncanny cannot cross uninvited for a night; the crossing costs such a thing dearly.</li>
    <li id="ix-e-bearing-it"><strong>Bearing It.</strong> (11th) Your Mark does not show. No creature, holy ground, ward or gift of sight registers
      it, and it costs you none of its usual penalties in front of the living. It has all the same effects on what you are becoming.</li>
    <li id="ix-e-the-second-voice"><strong>The Second Voice.</strong> (11th) Once per scene, work a Sign you know as a reaction rather than on your
      turn. Something in your throat does the speaking and it is not quite your accent.</li>
</ul>
  <div class="pageno">32</div>
</section>

<section class="page" id="calling-edges">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>IX. Edges</span></div>
  <h2>Edges of the Callings</h2>
  <p>The edges that follow belong to a single Calling. You may choose one only if it names a Calling you hold and you meet
  what it asks. These are the signatures of the trade — the moves that make a Gunhand a Gunhand, and more than a soul with
  a pistol and bad luck.</p>

  <h3>Worldly Callings</h3>
  <ul class="dash">
    <li><strong>Bounty Hunter — Run It Down.</strong> (Getaway) After a Bushwhack lands, immediately Step and Stride for free; your quarry must spend an action to break away, or you stay on him through the dust.</li>
    <li><strong>Bounty Hunter — The Trail Warms.</strong> (Cold Trail, 11th) Cold Trail may be worked twice a day, and a bearing you take once holds
      for a week without repeating it.</li>
    <li><strong>Drifter — Long Gone.</strong> Once per scene, when no enemy is looking your way, you may slip from sight even while observed and take a free Stride into cover.</li>
    <li><strong>Drifter — No Such Person.</strong> (Never Was Here, 11th) Never Was Here reaches a whole county rather than a place, and paper about
      you goes missing along with the rest.</li>
    <li><strong>Engineer — Charge Already Set.</strong> Once per fight, declare that you prepared this ground before the shooting started. One explosive of yours is already placed where you now say it is, and goes off on your Beat.</li>
    <li><strong>Engineer — Bench-Tested.</strong> (Proving Ground, 11th) Two contraptions may be tuned at once rather than one, and a tuned
      contraption may be handed to somebody else already tuned.</li>
    <li><strong>Gambler — Double or Nothing.</strong> Once per scene, before you roll, name the stake: on a success the result is one degree better; on a failure, one degree worse. The house is always watching.</li>
    <li><strong>Gambler — The Whole Deck.</strong> (Marked Deck, 11th) Marked Deck reads a whole room rather than one person: one true hidden thing
      about each of up to four people you can see.</li>
    <li><strong>Gunhand — Pistolero's Tally.</strong> When you drop a foe with a Strike, your next Strike this round ignores the Multiple Attack Penalty.</li>
    <li><strong>Gunhand — The Middle Part.</strong> (Second Nature, 11th) Called shots cost you nothing at all, and you may change your grip, your
      weapon and your cover in the same Beat.</li>
    <li><strong>Marshal — The Long Arm.</strong> When you Demoralize a foe or invoke the law against it, allies who can hear you gain +1 on their next Strike against that foe.</li>
    <li><strong>Marshal — Sworn and Standing.</strong> (Deputize, 11th) Deputized hands keep their oath for a week rather than a day, and one of them
      may take a hit meant for you.</li>
    <li><strong>Mountain Man — One Shot, One Kill.</strong> (Dead Aim) Once per scene, a steadied shot against a foe unaware of you deals <strong>maximum</strong> Dead Aim dice and ignores any Damage Reduction from hide or armor — the shot you spend an hour in the cold to earn.</li>
    <li><strong>Mountain Man — Kept Count.</strong> (Winter Count, 11th) Winter Count may be called twice a session, and the second telling gives the
      posse the bonus as well as you.</li>
    <li><strong>Prospector — Hang Fire.</strong> (Powderman) Set a charge to blow on a trigger you name — a tripwire, a gunshot, a spoken word — and it waits, patient as the deep, until that moment comes.</li>
    <li><strong>Prospector — Read the Whole Seam.</strong> (The Deep Vein, 11th) The Deep Vein reaches five miles rather than one, and names what is
      down there without your having to guess it first.</li>
    <li><strong>Prospector — Highball Charge.</strong> (Powderman) Once per scene, overpack a single charge: it deals <strong>maximum dice</strong> and doubles its burst radius. Stand well back, and count your friends first.</li>
    <li><strong>Prospector — Laid By.</strong> Once per session, declare that you laid by a useful mundane item, a cached supply, or a contact in this place — within reason, you did.</li>
    <li><strong>Sawbones — Battlefield Surgeon.</strong> Your field care in the thick of a fight provokes no reaction and restores an extra die of Blood.</li>
    <li><strong>Sawbones — Two Doses.</strong> (The Waking Draught, 11th) You carry a second dose, and a patient raised by either may act for twenty
      minutes rather than ten.</li>
  </ul>

  <h3>Callings of Faith</h3>
  <ul class="dash">
    <li><strong>Medicine Man — Mending Hands.</strong> Your remedies lift one lingering affliction — Sickened, Drained, the first grip of a curse — along with the Blood they restore.</li>
    <li><strong>Medicine Man — The Song Carries.</strong> (The Long Song, 11th) The Long Song may be sung over a whole camp of any size, and those who
      hear it are proof against fear until the next dusk.</li>
    <li><strong>Padre — Shepherd's Word.</strong> Spend a Beat to grant an ally who can hear you an immediate save, with your bonus, against a fear already gripping them.</li>
    <li><strong>Padre — The Parish Wide.</strong> (Cure of Souls, 11th) Your parish includes anyone who has ever taken shelter under your roof, and
      two of them turn up each session rather than one.</li>
    <li><strong>Preacher — Hellfire Sermon.</strong> Your invocations against the unclean reach every foe who can hear your voice, not one alone.</li>
    <li><strong>Preacher — The Fire Catches.</strong> (The Camp Meeting, 11th) A camp meeting leaves behind a standing congregation: that town will
      answer a call from you once, later, however far away you are.</li>
    <li><strong>Shaman — Spirit-Spoken.</strong> Once per scene, put one yes-or-no question to the spirits about this land, its dead, or what passed here, and be answered true.</li>
    <li><strong>Shaman — The Circle Holds.</strong> (The Wide Circle, 11th) The Helping Spirits may be sent to every ally at once, and the spirits of
      a place will answer two questions rather than one.</li>
    <li><strong>Sister — Between Them and It.</strong> When a foe would Strike an ally adjacent to you, you may take the Strike yourself instead. You are Off-Guard until your next turn, and the ally may not refuse.</li>
    <li><strong>Sister — The Third Night.</strong> (The Longer Watch, 11th) You may keep watch for a week rather than three nights before it tells,
      and one soul under your watch heals a Lasting Injury over it.</li>
    <li><strong>Witch Hunter — Bane-Sharpened.</strong> When you exploit your quarry's known weakness, deal an extra die of damage; you also name the kind of any uncanny thing on sight.</li>
    <li><strong>Witch Hunter — The Longer Book.</strong> (The Name Written Down, 11th) Your book holds twice as many names, and a name in it cannot
      lie to you in any tongue, at any distance.</li>
  </ul>

  <h3>Callings of the Old Dark</h3>
  <ul class="dash">
    <li><strong>Dark Cultist — Devoted Unto Death.</strong> You are immune to fear of the power you serve, and once per scene may shrug off a wound's effect for a round — the Mark keeps the tally.</li>
    <li><strong>Dark Cultist — It Volunteers.</strong> (The Patron's Ear, 11th) Once per session the Patron answers a question you did not ask, at the
      moment it becomes relevant, whether or not you wanted it.</li>
    <li><strong>False Prophet — Golden Tongue.</strong> You may work a single Deceive against an entire crowd at once, as readily as against one trusting soul.</li>
    <li><strong>False Prophet — Told Twice.</strong> (The Bigger Lie, 11th) A lie of yours that is disproved may be told again, once, to a different
      audience, as though it never had been.</li>
    <li><strong>Hexer — Hard Bargain.</strong> Once per scene, work a Sign for one less Nerve than it asks; the unpaid cost comes due later, at a time of the Keeper's choosing.</li>
    <li><strong>Hexer — Interest Deferred.</strong> (The Deeper Bargain, 11th) Damage taken through The Deeper Bargain may be pushed onto a willing
      soul who has agreed to it, once per scene.</li>
    <li><strong>Witch — Bitter Brew.</strong> Keep one extra charm or poison prepared, and your brews hold their potency a full day longer than another's would.</li>
    <li><strong>Witch — The Third Beast.</strong> (The Second Familiar, 11th) A third familiar comes to you and binds. The three of them will not be
      in the same county, and you will manage.</li>
  </ul>
  <div class="pageno">33</div>
</section>

<!-- ===================== X. GOODS ===================== -->
<section class="page" id="goods">
  <div class="runhead"><span class="l">X. Goods &amp; Provisions</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">X. Goods &amp; Provisions</h1>
  <p class="chapter-sub">Iron, leather, powder, and the price of everything.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Coin in the Territories is reckoned in dollars and bits — a bit being one eighth of a dollar, twelve
  and a half cents, the width of a hard day's wage. What follows are fair prices in a fair town; a remote post or a desperate
  hour will charge what it likes. Your starting wealth depends on your Calling, rolled below and spent before play.</p>
  <table>
    <thead><tr><th>Calling</th><th>Starting Coin</th></tr></thead>
    <tbody>
      <tr><td>Bounty Hunter</td><td>3d6 × $10 (in collected bounties)</td></tr>
      <tr><td>Dark Cultist</td><td>2d6 × $5, plus the favor of the patron</td></tr>
      <tr><td>Drifter</td><td>2d6 × $10</td></tr>
      <tr><td>False Prophet</td><td>3d6 × $10 (collected, never earned)</td></tr>
      <tr><td>Gambler</td><td>3d6 × $10 (as the cards fell)</td></tr>
      <tr><td>Gunhand</td><td>3d6 × $10</td></tr>
      <tr><td>Hexer</td><td>2d6 × $5</td></tr>
      <tr><td>Marshal</td><td>3d6 × $10, plus a badge or its like</td></tr>
      <tr><td>Medicine Man</td><td>2d6 × $10, plus a healer's kit &amp; herbs</td></tr>
      <tr><td>Mountain Man</td><td>2d6 × $10 in pelts, plus a rifle, traps, and a good knife</td></tr>
      <tr><td>Padre</td><td>2d6 × $10, plus vestments &amp; a relic</td></tr>
      <tr><td>Preacher</td><td>2d6 × $10, plus a holy book</td></tr>
      <tr><td>Prospector</td><td>3d6 × $10, plus prospecting tools</td></tr>
      <tr><td>Sawbones</td><td>3d6 × $10, plus a surgeon's kit</td></tr>
      <tr><td>Shaman</td><td>2d6 × $5, plus the regard of the spirits</td></tr>
      <tr><td>Witch</td><td>2d6 × $5, plus a familiar</td></tr>
      <tr><td>Witch Hunter</td><td>3d6 × $10, plus silver for a few rounds</td></tr>
    </tbody>
  </table>

  <div class="quote">&ldquo;Everything&rsquo;s for sale and nothing&rsquo;s cheap. A man comes down out of the high country once a season, trades his pelts, and rides out with half what he meant to carry and twice what he&rsquo;ll need to bury him. That&rsquo;s commerce.&rdquo;
    <span class="src">&mdash; Eb Tuttle, outfitter, Calvary Wells mercantile</span></div>

  <div class="box gold">
    <h4 id="ix-rarity">Of Rarity — Common, Uncommon &amp; Rare</h4>
    <p>Goods in this country come in three grades. <strong>Common</strong> items fill any general store and carry the listed
    price; unless a thing is marked otherwise, treat everything in the tables of this chapter as Common. <strong>Uncommon</strong>
    items are scarce, specialized, or controlled — found only in a city, a fort, or by special order, and dearer for the trouble
    (the Keeper may add a surcharge of half again or more, and a roll to locate one at all). <strong>Rare</strong> items are
    another matter entirely. They are seldom for sale at any honest price, and the truest of them are not mundane goods but
    <strong>relics and artifacts</strong> — objects with a real and uncanny power, the haunted frontier's answer to the
    enchanted swords and holy relics of older tales. A Rare item is found, won, inherited, or stolen; it is the Keeper's to
    place, never the player's to purchase; and it nearly always carries a history, a hunger, or a price folded inside the gift.</p>
  </div>

  <h2 id="ix-firearms">Firearms</h2>
  <p>Damage is rolled on a hit. <strong>Range</strong> is the increment in feet; each full increment beyond the first is a
  cumulative –2 to hit. <strong>Cap.</strong> is how many shots before reloading. <strong>Reload</strong> is the Beats (actions)
  it takes to make the weapon ready again, per the Iron Code (Chapter XI). <strong>Traits</strong> are explained below. Black
  powder fouls, misfires in the wet, and gives away your position with smoke — the Keeper may make much of this.</p>
  <table>
    <thead><tr><th>Weapon</th><th class="c">Damage</th><th class="c">Range</th><th class="c">Cap.</th><th class="c">Reload</th><th>Traits</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Buffalo Rifle</td><td class="c">1d12</td><td class="c">250</td><td class="c">1</td><td class="c">1</td><td>Kickback, Volley 30 ft, Fatal d12</td><td class="c">$55</td></tr>
      <tr><td>Cap-and-Ball Revolver</td><td class="c">1d8</td><td class="c">40</td><td class="c">6</td><td class="c">slow</td><td>Fatal d10, Misfire 2</td><td class="c">$12</td></tr>
      <tr><td>Derringer</td><td class="c">1d6</td><td class="c">20</td><td class="c">2</td><td class="c">1</td><td>Concealable, Fatal d8, Misfire 1</td><td class="c">$8</td></tr>
      <tr><td>Double-Barrel Shotgun</td><td class="c">2d8</td><td class="c">30</td><td class="c">2</td><td class="c">1</td><td>Scatter 10 ft, Kickback, Fatal d12</td><td class="c">$25</td></tr>
      <tr><td>Lever-Action Repeater</td><td class="c">1d10</td><td class="c">120</td><td class="c">12</td><td class="c">1/shot</td><td>Repeating, Fatal d12</td><td class="c">$40</td></tr>
      <tr><td>Single-Action Revolver</td><td class="c">1d8</td><td class="c">50</td><td class="c">6</td><td class="c">1/shot</td><td>Fatal d10, Misfire 1</td><td class="c">$20</td></tr>
    </tbody>
  </table>

  <h3 id="ix-weapon-traits">Weapon Traits</h3>
  <ul class="dash">
    <li><strong>Concealable.</strong> +2 to hide it on your person, and it may be drawn as part of the Strike rather than a separate Beat.</li>
    <li><strong>Fatal dX.</strong> On a critical hit, this weapon's damage dice all become dX, and you add one extra die of that size. A gun is at its most honest in the half-second it kills you.</li>
    <li><strong>Kickback.</strong> The recoil is brutal. Take –2 to the Strike unless your STR is 12 or higher, or you spend a Beat to brace (Aim). Firing a Kickback weapon without bracing leaves you Off-Guard until your next turn.</li>
    <li><strong>Misfire X.</strong> On a critical failure to hit (or any natural 1), the weapon jams. Clearing it costs an Interact action and a Repair check (DC 10 + X). In wet weather, increase X by 1 for black-powder arms.</li>
    <li><strong>Reach.</strong> The weapon strikes at a step's distance — a lance, spear, pike, or fixed bayonet. It can hit a foe (or a rider) one rank back, and lets a footman set against a charge (see <em>Fighting from the Saddle</em>).</li>
    <li><strong>Repeating.</strong> Holds many rounds. Loading a single round is one Interact; a full reload follows the rule below.</li>
    <li><strong>Scatter X.</strong> On a hit, deal 1d6 splash damage to every creature within X feet of the target. On a miss within the first range increment, the target still takes the splash.</li>
    <li><strong>Two-Handed.</strong> The weapon needs both hands to wield. You cannot also manage a shield, the reins, or a second gun, and using it from a moving horse is doubly awkward.</li>
    <li><strong>Volley X.</strong> This long iron is made for distance; Strikes against targets within X feet take –2.</li>
  </ul>
  <h3>Reloading</h3>
  <p>"Reload 1/shot" means each shot can be chambered with one Beat, firing and feeding in rhythm. "Reload 1" single-shot arms
  spend one Beat to load the next round. A <strong>slow</strong> reload (the cap-and-ball revolver) means fully recharging the
  cylinder takes three rounds of dedicated work — which is why a wise gunhand carries a second loaded cylinder, or a second gun.
  Topping a capacity or repeating weapon back to full takes Beats equal to half its capacity, rounded up.</p>
  <div class="pageno">34</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>X. Goods &amp; Provisions</span></div>
  <h2 id="ix-blades">Blades &amp; Bludgeons</h2>
  <table>
    <thead><tr><th>Weapon</th><th class="c">Damage</th><th>Notes</th></tr></thead>
    <tbody>
      <tr><td>Club / Rifle-Butt</td><td class="c">1d6</td><td>Common; nonlethal by choice</td></tr>
      <tr><td>Fists / Boots</td><td class="c">1d3</td><td>Nonlethal unless you mean it; Agile</td></tr>
      <tr><td>Hatchet</td><td class="c">1d6</td><td>Throwable to 20 ft</td></tr>
      <tr><td>Knife / Bowie</td><td class="c">1d4</td><td>Concealable; Agile; +1 on a Sudden Strike</td></tr>
      <tr><td>Saber / Cavalry Sword</td><td class="c">1d8</td><td>Reach and heft; favored mounted</td></tr>
    </tbody>
  </table>
  <p class="note"><strong>Agile</strong> weapons reduce the Multiple Attack Penalty (–4 / –8 instead of –5 / –10). A blade
  with the Fatal trait is rare and dear; most simply cut.</p>

  <h2 id="ix-armor">On Armor</h2>
  <p>There is precious little armor in this country, and less that helps. A heavy duster or buffalo coat turns a knife and the
  cold; boiler-plate and scavenged iron will stop a pistol ball at the cost of speed and sweat. Note the hard truth plainly:
  <strong>most firearms ignore most armor.</strong> Worn armor grants Damage Reduction against blades and small shot only; cover
  and not being shot remain your best defense.</p>
  <p><strong>Small shot</strong> means birdshot and buckshot, a spent ricochet, or a pocket pistol's ball fired from
  across a room — anything that reaches you with less than a full charge behind it. A rifle ball is not small shot,
  and neither is a revolver at conversational range. The table below will not save you from either one.</p>
  <table>
    <thead><tr><th>Protection</th><th class="c">vs Blades</th><th class="c">vs Small Shot</th><th>What it costs you</th><th class="c">Price</th></tr></thead>
    <tbody>
      <tr><td>Heavy Duster / Coat</td><td class="c">DR 1</td><td class="c">DR 1</td><td>Nothing, and it keeps the cold out</td><td class="c">$6</td></tr>
      <tr><td>Boiled Leather</td><td class="c">DR 2</td><td class="c">DR 1</td><td>–1 Defense; stiff in the heat</td><td class="c">$15</td></tr>
      <tr><td>Scavenged Iron Plate</td><td class="c">DR 3</td><td class="c">DR 3</td><td>–2 Speed, and loud with it</td><td class="c">$60</td></tr>
    </tbody>
  </table>
  <p>The iron is the exception worth the money. Alone among the three it applies its DR against a pistol ball as well,
  which is why a soul who expects to be shot at close quarters will sweat under sixty dollars of stove plate and call it
  a bargain. Long irons still punch through it. Nothing here stacks: wear the coat over the leather if you like, but
  count only the better of the two.</p>
  <p>Read the leather for what it is: a <strong>blade answer</strong>, and only that. Against shot it carries the same
  DR the duster does and takes a point of Defense for the privilege, so a soul who expects lead rather than knives is
  better off in the coat and nine dollars richer. Buy the leather when you know what is coming and it has hands.</p>
  <p>One more honest thing about all three. Armor is a flat subtraction and the country is not flat. A duster turns
  aside about a fifth of what a lesser thing hits you for and about a twentieth of what a great one does, and the iron
  falls the same way, from better than half down to a seventh. The coat is doing its work the whole time. The work is
  simply small next to the thing standing in front of you, which is the same lesson Chapter XI teaches about shooting
  at it.</p>

  <h2 id="ix-gear">Provisions, Gear &amp; Sundries</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>50 ft hemp rope</td><td class="c">75¢</td><td>Bandages, per use</td><td class="c">10¢</td></tr>
      <tr><td>Bedroll &amp; tarp</td><td class="c">$2</td><td>Bottle of whiskey</td><td class="c">50¢</td></tr>
      <tr><td>Box of cartridges (50)</td><td class="c">$1</td><td>Graveyard salt, lb.</td><td class="c">$1</td></tr>
      <tr><td>Holy book</td><td class="c">$3</td><td>Lantern &amp; oil</td><td class="c">$1</td></tr>
      <tr><td>Laudanum, per dose</td><td class="c">25¢</td><td>Shovel / tools</td><td class="c">$2</td></tr>
      <tr><td>Silver ball, each</td><td class="c">$5</td><td>Spyglass</td><td class="c">$8</td></tr>
      <tr><td>Stick of dynamite</td><td class="c">$2</td><td>Surgeon's kit</td><td class="c">$10</td></tr>
      <tr><td>Talisman or charm</td><td class="c">$2–$20</td><td>Week's rations</td><td class="c">$3</td></tr>
    </tbody>
  </table>

  <h2 id="ix-tonics">Tonics &amp; the Sawbones' Trade</h2>
  <p>Prepared doses (a Sawbones' Tonics, or bought dear) take a Beat to administer. Their use, and their abuse, ride together:</p>
  <ul class="dash">
    <li><strong>Antitoxin.</strong> +5 on the next save against a poison or disease, or a fresh save against one already taking hold.</li>
    <li><strong>Laudanum.</strong> Restores 1d6 Nerve and quiets pain (ignore the penalty of one Lasting Injury for an hour). Lean on it and court the vice — repeated use demands rising Fortitude saves against Drained.</li>
    <li><strong>Sedative.</strong> Calms a panicking patient: ends one fright and grants a new save against an Affliction, but renders them Clumsy and slow for ten minutes.</li>
    <li><strong>Stimulant.</strong> Removes Fatigued and suppresses Frightened for one scene; afterward, a DC 13 Fortitude save or take Fatigued.</li>
  </ul>

  <h3 id="ix-special-ammo">Special Ammunition</h3>
  <p>The uncanny does not always heed lead. The wise carry alternatives, dear as they are: <strong>silver</strong> balls bite
  the lycanthrope and the restless dead; <strong>rock-salt</strong> loads scatter the spectral and drive off the merely living
  without killing (treat as nonlethal, Scatter 5 ft); <strong>blessed or cold-iron</strong> rounds wound things that shrug off
  ordinary fire. Against a thing that should not be, the right ammunition is the difference between a fight and a funeral — yours.</p>

  <h2 id="ix-mounts">Mounts &amp; Tack</h2>
  <p>A horse is the line between a journey and a death. A man out here will go hungry a day before his
  horse does, and he is right to. The mount you ride decides how far you go
  in a day, what you can carry, and whether you outrun trouble or are run down by it.</p>
  <table>
    <thead><tr><th>Mount</th><th class="c">Speed</th><th class="c">Blood</th><th class="c">Def</th><th class="c">Carry</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Burro / Donkey</td><td class="c">40 ft</td><td class="c">16</td><td class="c">11</td><td class="c">130 lb</td><td class="c">$12</td></tr>
      <tr><td>Cow Pony / Mustang</td><td class="c">55 ft</td><td class="c">20</td><td class="c">12</td><td class="c">200 lb</td><td class="c">$25</td></tr>
      <tr><td>Draft Horse</td><td class="c">45 ft</td><td class="c">30</td><td class="c">11</td><td class="c">400 lb</td><td class="c">$60</td></tr>
      <tr><td>Fine Saddle Horse</td><td class="c">65 ft</td><td class="c">24</td><td class="c">13</td><td class="c">230 lb</td><td class="c">$90+</td></tr>
      <tr><td>Mule</td><td class="c">50 ft</td><td class="c">26</td><td class="c">11</td><td class="c">260 lb</td><td class="c">$30</td></tr>
      <tr><td>Ox (per yoke)</td><td class="c">30 ft</td><td class="c">34</td><td class="c">10</td><td class="c">pulls</td><td class="c">$35</td></tr>
      <tr><td>Riding Horse</td><td class="c">60 ft</td><td class="c">22</td><td class="c">12</td><td class="c">230 lb</td><td class="c">$40</td></tr>
      <tr><td>Trained Warhorse</td><td class="c">60 ft</td><td class="c">28</td><td class="c">13</td><td class="c">250 lb</td><td class="c">$150+</td></tr>
    </tbody>
  </table>
  <p>A horse kicks for 1d6 and bites for 1d4; a warhorse is trained to do both in a fight and to hold its ground against the
  uncanny. A mule is slower and stubborn but tougher of gut, surer on bad ground, and far harder to spook — which in this
  country is often worth more than speed. Saddle, bridle, and blanket run about $15 the set.</p>

  <h4>Tack &amp; Trappings</h4>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bedroll &amp; tarp</td><td class="c">$2</td><td>Feedbag &amp; a week's grain</td><td class="c">$2</td></tr>
      <tr><td>Hobbles / picket line</td><td class="c">50¢</td><td>Lariat / lasso (60 ft)</td><td class="c">$1</td></tr>
      <tr><td>Packsaddle (mule)</td><td class="c">$6</td><td>Saddle scabbard (long gun)</td><td class="c">$4</td></tr>
      <tr><td>Saddle, bridle &amp; blanket (set)</td><td class="c">$15</td><td>Saddlebags</td><td class="c">$3</td></tr>
      <tr><td>Shoeing (set of four)</td><td class="c">$1</td><td>Spurs</td><td class="c">$2</td></tr>
    </tbody>
  </table>

  <h4>On the Trail</h4>
  <p>At a steady <strong>walk</strong> a mount covers about <strong>30 miles a day</strong> over good ground — half that in
  mountains, mud, or snow. A <strong>trot</strong> doubles the distance but wears on animal and rider alike; a
  <strong>gallop</strong> is for emergencies only, good for a mile or two before the horse must be walked or be ruined. Push a
  mount past its wind and the rider makes a Ride check each hour; on a failure the animal falters, founders, or —
  driven long enough — dies under you. Grain, water, and rest are not optional out here.</p>

  <h4 id="ix-horse-nerve">A Horse's Nerve</h4>
  <p>Animals know the dark before their riders do. The first time a mount faces a monster, an explosion, or a soul gone deep
  into the Mark, the rider rolls <strong>Ride</strong> against the thing's Dread DC; on a failure the
  animal bolts, bucks, rears, or flatly refuses, and may throw its rider (see <em>Fighting from the Saddle</em>, Chapter XI).
  A mule rolls this with a bonus; a trained warhorse ignores ordinary frights altogether.</p>
  <div class="pageno">35</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">X. Goods &amp; Provisions</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-more-arms">More Arms &amp; Powder</h2>
  <p>The five irons of the foregoing table are the common run; a person with coin and a particular need has further choices.
  Traits are explained on the previous pages and apply as written.</p>
  <table>
    <thead><tr><th>Weapon</th><th class="c">Damage</th><th class="c">Range</th><th class="c">Cap.</th><th class="c">Reload</th><th>Traits</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bolt / Trapdoor Rifle</td><td class="c">1d12</td><td class="c">200</td><td class="c">1</td><td class="c">1</td><td>Volley 30 ft, Fatal d12</td><td class="c">$30</td></tr>
      <tr><td>Bow / Crossbow</td><td class="c">1d8</td><td class="c">60</td><td class="c">1</td><td class="c">1</td><td>Silent; Volley 20 ft (bow)</td><td class="c">$6</td></tr>
      <tr><td>Carbine (lever)</td><td class="c">1d10</td><td class="c">90</td><td class="c">8</td><td class="c">1/shot</td><td>Repeating, Fatal d12</td><td class="c">$34</td></tr>
      <tr><td>Coach Gun (sawed-off)</td><td class="c">2d8</td><td class="c">15</td><td class="c">2</td><td class="c">1</td><td>Scatter 15 ft, Concealable, Kickback</td><td class="c">$22</td></tr>
      <tr><td>Coal-Oil Bomb</td><td class="c">1d6 fire</td><td class="c">15*</td><td class="c">—</td><td class="c">—</td><td>Thrown; Scatter 5 ft, persists 1 round</td><td class="c">50¢</td></tr>
      <tr><td>Heavy "Walker" Revolver</td><td class="c">1d10</td><td class="c">50</td><td class="c">6</td><td class="c">slow</td><td>Kickback, Fatal d12, Misfire 1</td><td class="c">$22</td></tr>
      <tr><td>Pepperbox Pistol</td><td class="c">1d6</td><td class="c">25</td><td class="c">5</td><td class="c">slow</td><td>Concealable, Misfire 2</td><td class="c">$10</td></tr>
      <tr><td>Pocket Revolver</td><td class="c">1d6</td><td class="c">30</td><td class="c">5</td><td class="c">1/shot</td><td>Concealable, Fatal d8, Misfire 1</td><td class="c">$14</td></tr>
      <tr><td>Stick of Dynamite</td><td class="c">2d6</td><td class="c">10*</td><td class="c">—</td><td class="c">—</td><td>Thrown; 10-ft burst, Reflex DC 15 half</td><td class="c">$2</td></tr>
      <tr><td>Throwing Knife / Tomahawk</td><td class="c">1d4 / 1d6</td><td class="c">20</td><td class="c">—</td><td class="c">—</td><td>Thrown, Agile (knife)</td><td class="c">$1</td></tr>
      <tr><td>Wall / Punt Gun</td><td class="c">3d10</td><td class="c">80</td><td class="c">1</td><td class="c">slow</td><td>Scatter 20 ft, Kickback, Volley 20 ft</td><td class="c">$70</td></tr>
    </tbody>
  </table>
  <p class="note">*Thrown explosives use the range as a throwing increment, not a shooting one. A Prospector ignores the
  scatter against themselves and may shape the burst (Chapter V).</p>

  <h2 id="ix-spec-rounds">Ammunition &amp; Specialty Rounds</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Blessed round, each</td><td class="c">$4</td><td>Cold-iron round, each</td><td class="c">$3</td></tr>
      <tr><td>Incendiary / phosphor round</td><td class="c">$2</td><td>Metallic cartridges, box of 50</td><td class="c">$1.25</td></tr>
      <tr><td>Paper cartridges, per 50</td><td class="c">$1</td><td>Percussion caps, tin of 100</td><td class="c">50¢</td></tr>
      <tr><td>Powder &amp; ball, per 50</td><td class="c">75¢</td><td>Powder horn / flask</td><td class="c">75¢</td></tr>
      <tr><td>Rock-salt load, each</td><td class="c">25¢</td><td>Shotgun shells, box of 25</td><td class="c">$1</td></tr>
      <tr><td>Silver ball / round, each</td><td class="c">$5</td><td>Soft-lead (hollow) round</td><td class="c">15¢</td></tr>
    </tbody>
  </table>
  <p class="note"><strong>Soft-lead</strong> rounds add +1 damage against the unarmored living but lose a die against anything
  with Damage Reduction. <strong>Incendiary</strong> rounds set the dry and the oily alight; the Keeper adjudicates the blaze.</p>

  <h2 id="ix-furniture">Weapon Furniture</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bandolier / cartridge belt</td><td class="c">$2</td><td>Bayonet / knife mount</td><td class="c">$2</td></tr>
      <tr><td>Cleaning kit &amp; gun oil</td><td class="c">$1.50</td><td>Holster, plain</td><td class="c">$1</td></tr>
      <tr><td>Quick-draw / cross-draw rig</td><td class="c">$4</td><td>Saddle scabbard</td><td class="c">$4</td></tr>
      <tr><td>Shoulder rig (concealed)</td><td class="c">$3</td><td>Spare loaded cylinder</td><td class="c">$6</td></tr>
      <tr><td>Speed-loader (rare)</td><td class="c">$8</td><td>Telescopic sight</td><td class="c">$25</td></tr>
    </tbody>
  </table>
  <p class="note">A <strong>spare loaded cylinder</strong> turns a slow cap-and-ball reload into a single Interact — the
  difference, often, between a story told and a stone carved.</p>
  <div class="pageno">36</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>X. Goods &amp; Provisions</span></div>
  <h2 id="ix-clothing">Clothing &amp; the Cold</h2>
  <p>The country kills more travelers with weather than with lead. Dress for the one and you may live to worry about the other.</p>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bandana / kerchief</td><td class="c">15¢</td><td>Buffalo / fur coat</td><td class="c">$14</td></tr>
      <tr><td>Fine Stetson</td><td class="c">$10</td><td>Hat (felt or straw)</td><td class="c">$2</td></tr>
      <tr><td>Leather gloves / gauntlets</td><td class="c">$1</td><td>Oilskin slicker</td><td class="c">$3</td></tr>
      <tr><td>Snowshoes</td><td class="c">$3</td><td>Spectacles</td><td class="c">$4</td></tr>
      <tr><td>Spurs &amp; chaps</td><td class="c">$4</td><td>Sunday best</td><td class="c">$12</td></tr>
      <tr><td>Tinted "glare" glasses</td><td class="c">$2</td><td>Working clothes &amp; boots</td><td class="c">$5</td></tr>
    </tbody>
  </table>

  <h2 id="ix-tools">Tools of Many Trades</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Apothecary / brewing kit</td><td class="c">$8</td><td>Blacksmith's tools</td><td class="c">$12</td></tr>
      <tr><td>Branding iron</td><td class="c">$2</td><td>Carpenter's / general tools</td><td class="c">$4</td></tr>
      <tr><td>Climbing kit &amp; pitons</td><td class="c">$5</td><td>Field camera &amp; plates</td><td class="c">$30</td></tr>
      <tr><td>Lockpicks / skeleton keys</td><td class="c">$8</td><td>Manacles &amp; key</td><td class="c">$3</td></tr>
      <tr><td>Prospecting kit (pan, pick, rod)</td><td class="c">$6</td><td>Sewing / tailoring kit</td><td class="c">$1</td></tr>
      <tr><td>Surgeon's kit (refill)</td><td class="c">$10</td><td>Telegraph key (portable)</td><td class="c">$15</td></tr>
    </tbody>
  </table>

  <h2 id="ix-camp">The Camp &amp; the Trail</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bullseye / dark lantern</td><td class="c">$3</td><td>Candles, dozen</td><td class="c">20¢</td></tr>
      <tr><td>Canteen / water-skin</td><td class="c">75¢</td><td>Canvas tent (two-soul)</td><td class="c">$5</td></tr>
      <tr><td>Compass</td><td class="c">$2</td><td>Cook pot, pan &amp; tin</td><td class="c">$1.50</td></tr>
      <tr><td>Fishing line &amp; hooks</td><td class="c">25¢</td><td>Matches, tin of 100</td><td class="c">10¢</td></tr>
      <tr><td>Panniers (pair)</td><td class="c">$4</td><td>Sextant</td><td class="c">$20</td></tr>
      <tr><td>Steel traps, each</td><td class="c">$1</td><td>Territory map (fair)</td><td class="c">$3</td></tr>
      <tr><td>Tinderbox &amp; flint</td><td class="c">25¢</td><td>Wool blanket</td><td class="c">$2</td></tr>
    </tbody>
  </table>

  <h2 id="ix-vittles">Vittles &amp; Comforts</h2>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Airtights (canned goods), each</td><td class="c">25¢</td><td>Bottle of fine brandy</td><td class="c">$3</td></tr>
      <tr><td>Bottle of whiskey</td><td class="c">50¢</td><td>Cigars, each</td><td class="c">10¢</td></tr>
      <tr><td>Coffee, lb.</td><td class="c">35¢</td><td>Flour / beans, lb.</td><td class="c">5¢</td></tr>
      <tr><td>Hardtack &amp; jerky, lb.</td><td class="c">20¢</td><td>Hot meal, saloon</td><td class="c">25¢</td></tr>
      <tr><td>Patent "cure-all" tonic</td><td class="c">50¢</td><td>Sugar, lb.</td><td class="c">12¢</td></tr>
      <tr><td>Tobacco &amp; papers</td><td class="c">25¢</td><td>Week's trail rations</td><td class="c">$3</td></tr>
    </tbody>
  </table>
  <div class="pageno">37</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">X. Goods &amp; Provisions</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-prov-dark">Provisions Against the Dark</h2>
  <p>A wise soul lays in more than powder. These are dear, often hard to find, and worth every cent the night you need them.
  Several are the working stock of the Callings of Faith and of the Old Dark — a Padre's vial, a
  Witch's herb, a Hexer's chalk.</p>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Beeswax candles &amp; incense</td><td class="c">$1</td><td>Blessed oil, vial</td><td class="c">$1.50</td></tr>
      <tr><td>Church bell, hand</td><td class="c">$4</td><td>Cornmeal &amp; chalk (sigils)</td><td class="c">20¢</td></tr>
      <tr><td>Divining rod / pendulum</td><td class="c">$1</td><td>Graveyard salt, lb.</td><td class="c">$1</td></tr>
      <tr><td>Hand mirror</td><td class="c">$1</td><td>Holy water, vial</td><td class="c">$1</td></tr>
      <tr><td>Horseshoe / iron nails</td><td class="c">25¢</td><td>Iron filings, lb.</td><td class="c">75¢</td></tr>
      <tr><td>Mojo bag / charm</td><td class="c">$2–$20</td><td>Sage, wolfsbane, herbs, bundle</td><td class="c">75¢</td></tr>
      <tr><td>Saint's relic (true)</td><td class="c">rare</td><td>Silver crucifix / medal</td><td class="c">$6</td></tr>
      <tr><td>Spirit-board</td><td class="c">$2</td><td>Warding chalk &amp; tallow</td><td class="c">50¢</td></tr>
    </tbody>
  </table>
  <p class="note">Most of these do nothing in untrained hands but reassure. In trained hands — a Padre's, a Witch's, a Hexer's — they are the difference between a rite that holds and one that lets the dark in behind it.</p>

  <h2 id="ix-services">Services &amp; Lodging</h2>
  <table>
    <thead><tr><th>Service</th><th class="c">Cost</th><th>Service</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Bath &amp; shave</td><td class="c">25¢</td><td>Coffin &amp; burial</td><td class="c">$15</td></tr>
      <tr><td>Doctor's visit</td><td class="c">$2</td><td>Laundry, the load</td><td class="c">20¢</td></tr>
      <tr><td>Lawyer, per matter</td><td class="c">$10+</td><td>Letter &amp; postage</td><td class="c">3¢</td></tr>
      <tr><td>Posting a bounty</td><td class="c">$5+</td><td>Rail ticket, per mile</td><td class="c">3¢</td></tr>
      <tr><td>Room, per night</td><td class="c">25–75¢</td><td>Stabling a horse, night</td><td class="c">25¢</td></tr>
      <tr><td>Stagecoach, per mile</td><td class="c">10¢</td><td>Telegram, per word</td><td class="c">2¢</td></tr>
    </tbody>
  </table>
  <h2 id="ix-livestock">Livestock &amp; Conveyances</h2>
  <table>
    <thead><tr><th>Animal / Vehicle</th><th class="c">Cost</th><th>Notes</th></tr></thead>
    <tbody>
      <tr><td>Buckboard wagon</td><td class="c">$45</td><td>Light haul; needs a team</td></tr>
      <tr><td>Buggy / surrey</td><td class="c">$60</td><td>Town conveyance for those with airs</td></tr>
      <tr><td>Canoe / flatboat</td><td class="c">$8 / $25</td><td>For the rivers, where the roads give out</td></tr>
      <tr><td>Cattle dog</td><td class="c">$3</td><td>Loyal, loud, and the first to smell the dark</td></tr>
      <tr><td>Conestoga / freight wagon</td><td class="c">$120</td><td>The home you drag west</td></tr>
      <tr><td>Draft horse / ox</td><td class="c">$60 / $35</td><td>For plow and wagon; oxen tireless, slow</td></tr>
      <tr><td>Fine saddle horse</td><td class="c">$90+</td><td>Faster, braver, far more spirited</td></tr>
      <tr><td>Mule</td><td class="c">$30</td><td>Slow, stubborn, sure on bad ground; hard to spook</td></tr>
      <tr><td>Mustang (green-broke)</td><td class="c">$18</td><td>Cheap, hardy, may yet throw you</td></tr>
      <tr><td>Pack mule / burro</td><td class="c">$15</td><td>Carries the camp so you needn't</td></tr>
      <tr><td>Riding horse (sound)</td><td class="c">$40</td><td>Blood 22, Def 12, Speed 60 ft, kick 1d6</td></tr>
    </tbody>
  </table>

  <div class="quote">
    "I have buried men who skimped on the horse and men who skimped on the salt, and I will tell you
    the salt funerals were the worse to look upon. Spend on both. You can always sell a good horse.
    You cannot un-see what comes for the one who saved a dollar on the salt."
    <span class="src">— Eb Tuttle, outfitter, Calvary Wells mercantile</span>
  </div>
  <div class="pageno">38</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">X. Goods &amp; Provisions</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-uncommon">Uncommon Goods</h2>
  <p>The following are <strong>Uncommon</strong>: scarce, specialized, or controlled. A general store will not stock them.
  Expect to find them only in a city, a fort, a railhead, or by special order — and to pay a surcharge of half again or more
  for the privilege, after a roll to turn one up at all.</p>
  <table>
    <thead><tr><th>Item</th><th class="c">Cost</th><th>Item</th><th class="c">Cost</th></tr></thead>
    <tbody>
      <tr><td>Astronomer's telescope</td><td class="c">$30</td><td>Book of true occult lore</td><td class="c">$25</td></tr>
      <tr><td>Carrier pigeons, trained pair</td><td class="c">$8</td><td>Chemist's / forensic kit</td><td class="c">$20</td></tr>
      <tr><td>Crude diving apparatus</td><td class="c">$40</td><td>Disguise &amp; theatrical kit</td><td class="c">$12</td></tr>
      <tr><td>Dynamite, case of ten</td><td class="c">$18</td><td>Ether, anesthetic bottle</td><td class="c">$4</td></tr>
      <tr><td>Forged papers, the set</td><td class="c">$10+</td><td>Good strongbox / safe</td><td class="c">$30</td></tr>
      <tr><td>Hand printing press</td><td class="c">$60</td><td>Iron vest (turns pistol ball)</td><td class="c">$50</td></tr>
      <tr><td>Jointed prosthetic limb</td><td class="c">$25–$60</td><td>Lever-action shotgun</td><td class="c">$45</td></tr>
      <tr><td>Master lockbreaker's tools</td><td class="c">$20</td><td>Matched scope &amp; target rifle</td><td class="c">$80</td></tr>
      <tr><td>Morphine &amp; syringe kit</td><td class="c">$12</td><td>Mountaineering rig</td><td class="c">$12</td></tr>
      <tr><td>Nitroglycerin, vial (volatile)</td><td class="c">$10</td><td>Repeating crossbow</td><td class="c">$20</td></tr>
      <tr><td>Superior doctor's bag</td><td class="c">$30</td><td>Trained bloodhound</td><td class="c">$15</td></tr>
      <tr><td>Camera &amp; wet-plate kit</td><td class="c">$35</td><td>Blasting machine &amp; wire</td><td class="c">$25</td></tr>
      <tr><td>Coffin, lead-lined</td><td class="c">$30</td><td>Galvanic battery, medical</td><td class="c">$15</td></tr>
      <tr><td>Pinkerton file on a name</td><td class="c">$15+</td><td>Surveyor's transit &amp; chains</td><td class="c">$25</td></tr>
    </tbody>
  </table>
  <p class="note"><strong>Superior doctor's bag.</strong> Grants +2 to Medicine and lets a Sawbones or Medicine Man treat one
  extra patient between rests. <strong>Iron vest.</strong> The tailored cousin of the scavenged plate in
  Chapter X — chest and back only, but cut to fit and bought rather than hammered out of a boiler. Same DR 3
  against blades, small shot and pistol balls, same –2 Speed, same racket. Most long irons still punch clean
  through it. <strong>Book of true occult lore.</strong> A month's careful study grants +2 to
  Lore: Occult, or — at the Keeper's discretion, and at the usual risk — the working of a single Sign.
  <strong>Camera &amp; wet-plate kit.</strong> A long exposure and a steady hand make a portrait — and now and again the
  plate holds what the eye refused: a figure at the window, a face in the smoke. The camera does not lie, which is exactly
  the trouble with it. <strong>Coffin, lead-lined.</strong> A body sealed in lead and buried proper does not rise. Usually.
  <strong>Pinkerton file on a name.</strong> Bought quiet from an agency man: aliases, known associates, last verified
  whereabouts. The Keeper answers three plain questions about the name; the fourth costs more than money.</p>
  <div class="pageno">39</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>X. Goods &amp; Provisions</span></div>
  <h2 id="ix-charms">Rare — Charms &amp; Lesser Relics</h2>
  <p>Here the goods stop being merely goods. Each of the following is <strong>Rare</strong> and carries a small but true
  uncanny power. None is reliably for sale; each is found, won, or inherited, and placed by the Keeper. The lesser relics
  below are potent without being world-shaking — a good first taste of the magic of the haunted frontier.</p>

  <h4 id="ix-rel-coin">Hangman's Coin <span class="note">(Rare · cursed)</span></h4>
  <p>A coin taken from a hanged man's eyes. Once, spend it to turn a failed save against death into a success — but the dead
  man wants it back, and from that night he walks a step behind you in dreams, holding out his hand.</p>

  <h4 id="ix-rel-compass">Dead Man's Compass <span class="note">(Rare)</span></h4>
  <p>Its needle points not north, but toward the nearest restless dead within a mile — or, when there are none, toward the
  thing you most fear. It is never wrong about either, which is the trouble with it.</p>

  <h4 id="ix-rel-bottle">Witch-Bottle <span class="note">(Rare · one use)</span></h4>
  <p>A stoppered bottle of pins, nails, and worse, buried at a threshold. It catches the next curse or Hex laid upon the
  household and turns it back, entire, upon the one who cast it. Then it shatters, its work done.</p>

  <h4 id="ix-rel-bone">Saint's Finger-Bone <span class="note">(Rare · true relic)</span></h4>
  <p>A genuine relic in a silver reliquary. Once per day, add a die to one healing or warding you perform, and the lesser
  uncanny will not lay hands on the bearer without first making a Will save. Faith, made into an object you can lose.</p>

  <h4 id="ix-rel-deck">Gambler's Marked Deck <span class="note">(Rare · cursed)</span></h4>
  <p>Once per session, force a single roll to be rerolled — yours or another's — as the cards decide. But the deck always
  collects in the end: the Keeper holds one reroll in reserve to use against you, at the worst possible hour, and you will
  know it is the deck by the cold that comes with it.</p>

  <h4 id="ix-rel-spurs">Ghost-Iron Spurs <span class="note">(Rare)</span></h4>
  <p>Forged from a graveyard's fence. Your mount cannot be panicked by the uncanny, and once per scene may outrun anything
  dead that pursues it, however fast that dead thing flies.</p>

  <h4 id="ix-rel-salt">Salt of the Forty Martyrs <span class="note">(Rare · consumable, a few uses)</span></h4>
  <p>Blessed graveyard salt of terrible potency. A pinch makes any single ward you lay so strong that the uncanny save
  against it at a steep penalty. A small tin holds perhaps three pinches, and there is no more being made.</p>

  <h4 id="ix-rel-tooth">Coyote's Tooth <span class="note">(Rare · cursed)</span></h4>
  <p>A yellowed canine on a leather cord, taken — so the story goes — from the Trickster's own jaw while he slept. Once
  per session, slip free of any one thing that holds you: a knot, a manacle, a grapple, a cell. But the tooth loves a
  liar, and while you wear it small falsehoods come easier than truths, until the people who know you best begin to
  hear it.</p>

  <h4 id="ix-rel-locket">Widow's Locket <span class="note">(Rare)</span></h4>
  <p>A mourning locket holding a faded portrait of someone else's beloved dead. The dead one keeps watch: once per
  session the locket grows cold a moment before an ambush, a betrayal, or a bullet with your name on it. But grief
  clings to the bearer like woodsmoke, and the locket's price is that the dead beloved must be mourned as your own —
  skip the graveside visit too long and the warnings stop.</p>

  <h4 id="ix-rel-nail">Church-Door Nail <span class="note">(Rare · one use)</span></h4>
  <p>A hand-forged nail drawn from the door of a church that stood a hundred years and never burned. Driven into a
  threshold, a gatepost, or a wagon-board at dusk, no uncanny thing may cross that doorway until sunrise. In the
  morning the nail is only iron, its century spent in a single night.</p>
  <div class="pageno">40</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">X. Goods &amp; Provisions</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-artifacts">Rare — Artifacts &amp; Relics of Power</h2>
  <p>And here are the great ones: <strong>Rare</strong> artifacts of real power, each unique, each the heart of a story.
  Treat these as you would the legendary relics of older tales — won at cost, never bought, and never without a history
  folded inside. Most carry a price, a curse, or a hunger. A campaign need hold only one or two.</p>

  <h4 id="ix-rel-round">The Peacemaker's Last Round <span class="note">(Rare · artifact, one use)</span></h4>
  <p>A single cartridge of blessed silver, its casing scribed with a dying prayer. Fired at any Marked or uncanny thing, it
  cannot miss and strikes as a critical hit, Fatal die and all. Then it is spent forever — and the gun that fired it never
  shoots quite true again, having known perfection once.</p>

  <h4 id="ix-rel-vial">Vial from the Weeping Spring <span class="note">(Rare · artifact)</span></h4>
  <p>Water from a spring that should not weep. A single swallow cures any affliction, mends grievous wounds, and within a
  minute of death will call a willing soul back into its body. There is only ever a little — three sips, perhaps — and it
  refills for no one, save at the spring itself, wherever in the world that has wandered to now.</p>

  <h4 id="ix-rel-bell">Saint Dymphna's Bell <span class="note">(Rare · artifact · true relic)</span></h4>
  <p>A small hand-bell of cracked bronze. Rung, it ends a possession or calms every maddened and Frightened mind within
  earshot, and bars the uncanny from crossing its sound. The bell cracks a little further with each ringing; no one knows
  how many peals remain in it, and the bearer dares not waste one finding out.</p>

  <h4 id="ix-rel-cartographer">The Cartographer's Eye <span class="note">(Rare · artifact · cursed)</span></h4>
  <p>A glass eye that sees what the living one cannot: through illusion and disguise, into the thin places, and across the
  true and dreadful shape of haunted ground. It showed its first owner the hour and manner of his own death, exactly once,
  and it will show you yours the day you first put it in. It has never yet been wrong.</p>

  <h4 id="ix-rel-rope">The Hanged Man's Rope <span class="note">(Rare · artifact · cursed)</span></h4>
  <p>A noose that never frays and never breaks, and binds even the uncanny fast where chain and iron fail. But it is heavy
  with the despair of all it has held; carry it long, and that weight settles into the bearer, draining hope and Nerve until
  the rope begins to seem less a tool than a suggestion.</p>

  <h4 id="ix-rel-cuirass">The Conquistador's Cuirass <span class="note">(Rare · artifact · cursed)</span></h4>
  <p>A blackened Spanish breastplate three centuries old. It turns even rifle balls (DR against firearms), an unheard-of
  protection — but it remembers the will of the man who died in it, and whispers in old Castilian, and covets the wearer.
  Wear it through enough battles and the cuirass begins, quietly, to decide which of you is in command.</p>

  <h4 id="ix-rel-star">The Iron Star <span class="note">(Rare · artifact · true relic)</span></h4>
  <p>The badge of a sheriff who never once broke his word or abandoned the helpless. Shown to a liar, it compels the truth;
  worn, it steadies the bearer's Nerve against any terror. But it holds its wearer to the old lawman's code as surely as a
  geas: turn your back on the innocent while you wear the Star, and it will burn cold against your chest until you cannot
  bear it — or until you become someone who can, which is the worse outcome by far.</p>

  <h4 id="ix-rel-lantern">The Padre's Lantern <span class="note">(Rare · artifact · true relic)</span></h4>
  <p>A dented tin lantern carried on the mission trails by a padre who walked the worst of this country and was never
  once touched. Lit, its circle of light is honest ground: nothing within it may wear a false face, hold an illusion,
  or hide its true shape — and the uncanny must save even to step into the glow. But the light is honest about the
  bearer too. Within the circle you cannot lie, cannot conceal, cannot be hidden from what hunts you; the lantern
  makes its carrier the brightest thing on the plain, and it has outlived every soul who carried it.</p>

  <h4 id="ix-rel-fiddle">The Bone Fiddle <span class="note">(Rare · artifact · cursed)</span></h4>
  <p>Strung with gut and pegged in yellowed bone, its maker unknown and better left so. Played, it commands the dead:
  every restless thing in earshot — the Risen, the walkers, the things half-through the door — stops to listen for as
  long as the tune holds, and a masterful player can walk them a slow measure back toward their graves. But the tunes
  it plays are not learned from the living, and each performance is a conversation: the dead hear where the fiddle is,
  they remember the fiddler kindly, and one night, when the playing is done, they will want a tune of their own choosing.</p>

  <h4 id="ix-rel-chain">The Meridian Chain <span class="note">(Rare · artifact)</span></h4>
  <p>A surveyor's chain of sixty-six iron feet, struck — the story runs — from the first true meridian stake driven in
  the Territories. Ground enclosed by the chain between dusk and dawn is <em>surveyed</em>: it belongs, for that night,
  to the living, and the uncanny must save at a steep penalty to cross the line. One acre, no more, and the chain must
  be taken up and laid fresh each evening by the same hands. Homesteads have stood forty years behind it. Every one of
  them fell the year its keeper grew too old to walk the line, and forgot a single corner.</p>

  <h4 id="ix-rel-dollar">The Ferryman's Dollar <span class="note">(Rare · artifact · cursed)</span></h4>
  <p>A worn silver dollar, minted no year a living man can find in a ledger. Held under the tongue, it lets the bearer
  walk unseen among the dead for a scene — the restless take you for one of their own, and let you pass, and answer
  what you ask them in their fashion. But the coin is fare, not disguise: each crossing, make a Will save or leave a
  little of yourself on the far bank. Those who use it often are known by their gray eyes and their quiet, and by how
  the dogs no longer bark at them.</p>

  <div class="box gold">
    <h4>A Note on What Is Not Here</h4>
    <p>You will find no nation's nor any living faith's sacred objects laid out as loot in these pages — no medicine
    bundles, no stolen ceremonial regalia, no holy thing of a people still praying with it. Such items are not treasure, and
    a table reaching for that well should reach instead for the care urged in Chapter IV. There is no shortage of invented
    relics in a haunted country. Make your own; the dark is generous with them.</p>
  </div>

  <div class="quote">
    "Every one of these cursed marvels was somebody's salvation once, and every one of them is for sale now,
    which tells you exactly how that salvation went. Buy the rope if you must. Just don't be surprised
    when you start to feel how many necks it has known, and how patient it is, and how well it fits."
    <span class="src">— Eb Tuttle, outfitter, declining to set a price</span>
  </div>
  <div class="pageno">41</div>
</section>
<section class="page" id="conflict">
  <div class="runhead"><span class="l">XI. Conflict &amp; the Iron Code</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">XI. Conflict &amp; the Iron Code</h1>
  <p class="chapter-sub">How violence is reckoned, and how quickly it ends a life.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Violence in <em>Blood and Grit</em> is fast, ugly, and rarely fair. A gunfight lasts a
  handful of seconds, and someone dies inside them. Fight only when you must, from cover when you can, and never in the belief
  that your numbers make you safe. They do not. The rules of the gun are called the <strong>Iron Code</strong>, though no
  marshal enforces them — they are the plain arithmetic of powder and flesh, which the country enforces for itself.</p>
  <h2 id="ix-beats">Rounds, Turns, and the Three Beats</h2>
  <p>When blood is in the offing, time breaks into <strong>rounds</strong> of roughly six seconds. Everyone rolls
  <strong>initiative</strong> — a Notice check (or another skill the Keeper calls for, after the manner of Pathfinder 2E) — and acts from highest to lowest. On your turn you have three
  <strong>Beats</strong> — the small, equal measures of what a person can do in those six seconds. Spend them in any
  order, and on any mix of the actions below. A second Strike in a turn is harder than the first; a third, harder still.
  That is the whole of the Code, and the whole of why patient people outlive quick ones.</p>

  <table>
    <thead><tr><th>Action</th><th class="c">Beats</th><th>What It Does</th></tr></thead>
    <tbody>
      <tr><td>Aim / Brace</td><td class="c">1</td><td>+2 on your next Strike before your turn ends; braces a Kickback weapon.</td></tr>
      <tr><td>Interact</td><td class="c">1</td><td>Draw or stow a weapon, clear a jam, work a lever, open a door, fetch a tonic.</td></tr>
      <tr><td>Reload</td><td class="c">varies</td><td>Make a spent weapon ready; see Reloading below.</td></tr>
      <tr><td>Steady a Soul</td><td class="c">1</td><td>A shout, a hand, a Command — many Calling features cost a Beat. The feature says so.</td></tr>
      <tr><td>Stride</td><td class="c">1</td><td>Move up to your Speed. Mounted, move your horse's Speed.</td></tr>
      <tr><td>Strike</td><td class="c">1</td><td>One attack with a readied weapon. Subject to the Multiple Attack Penalty.</td></tr>
      <tr><td>Take Cover</td><td class="c">1</td><td>Press to available cover, improving its bonus by one step until you leave it.</td></tr>
    </tbody>
  </table>
  <p class="note" id="ix-reactions"><strong>Free of charge.</strong> A single short phrase, dropping prone, and letting go of what you hold cost
  no Beat. <strong>Reactions.</strong> Once between your turns you may take one reaction. The common one is
  <em>Dive for Cover</em>: when you can see the shot coming — a leveled gun, a lit fuse — drop prone and gain the benefit
  of cover against that one attack, at the cost of being Prone when you rise.</p>

  <h2 id="ix-map">The Strike, and the Multiple Attack Penalty</h2>
  <p>To make a Strike, roll d20 + your attack (your level, adjusted by your Calling's rank — Chapter XIV) + the keyed ability — DEX for guns and thrown, STR for blades and
  fists — against the target's <strong>Defense</strong>. Your first Strike in a turn is clean. Your second takes a
  <strong>Multiple Attack Penalty (MAP)</strong> of –5; your third, –10. An <strong>Agile</strong> weapon (a knife, a
  light blade) softens this to –4 and –8. The penalty resets at the start of each of your turns. The Code rewards the
  one good shot over the three wild ones — as the dead could tell you, if the dead said much.</p>

  <h2 id="ix-four-degrees">The Four Degrees of Success</h2>
  <p>Every Strike, and many a desperate skill check besides, has not two outcomes but four. Compare your total to the
  Defense (or DC):</p>
  <table>
    <thead><tr><th>Result</th><th>How It Lands</th></tr></thead>
    <tbody>
      <tr><td><strong>Critical Success</strong></td><td>Beat the number by 10 or more, <em>or</em> roll a natural 20 that also hits. Deal double damage and apply the weapon's <strong>Fatal</strong> die. A wound to be buried with.</td></tr>
      <tr><td><strong>Success</strong></td><td>Meet or beat the number. Roll damage and subtract it from their Blood.</td></tr>
      <tr><td><strong>Failure</strong></td><td>Fall short. No harm done — this time.</td></tr>
      <tr><td><strong>Critical Failure</strong></td><td>Miss by 10 or more, <em>or</em> roll a natural 1. The shot is wasted, and a weapon with the <strong>Misfire</strong> trait jams (see Chapter X).</td></tr>
    </tbody>
  </table>
  <p>This is the spine of the Iron Code: the same roll that decides whether you hit also decides whether you hit
  <em>well</em>, and whether your own iron betrays you. A natural 20 shifts the result one step better as it does on any
  roll (Chapter II), and in a Strike it always <em>at least</em> hits; a natural 1 shifts one step worse, and always at
  least misses. The country humbles the sure.</p>
  <div class="pageno">42</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>XI. Conflict &amp; the Iron Code</span></div>
  <h2 id="ix-circumstance">Circumstance</h2>
  <p>Few shots are taken on a fair field. The Keeper applies what the moment warrants:</p>
  <table>
    <thead><tr><th>Circumstance</th><th>Effect on the Strike</th></tr></thead>
    <tbody>
      <tr><td>Beyond first range increment</td><td>–2 per full increment past the first</td></tr>
      <tr><td>Firing into melee</td><td>–4, or a miss may strike a friend at the Keeper's call</td></tr>
      <tr><td>Point-blank (adjacent)</td><td>No range penalty; a long gun is unwieldy this close (–2 unless braced)</td></tr>
      <tr><td>Target behind cover (light / heavy)</td><td>–2 / –4 to hit; <em>Take Cover</em> improves the target's by one step</td></tr>
      <tr><td>Target fully concealed</td><td>Cannot be targeted directly; fire blind at –8 and guess the square</td></tr>
      <tr><td>Target Off-Guard</td><td>+2 to hit; a Drifter adds Sudden Strike damage</td></tr>
      <tr><td>You Aimed and did not move</td><td>+2 on the Strike (does not stack with itself)</td></tr>
    </tbody>
  </table>
  <p class="note" id="ix-offguard"><strong>Off-Guard</strong> is the Code's word for a target who cannot properly defend — unaware of you,
  flanked between two foes, caught unready at the first instant of a fight, or knocked sprawling. An Off-Guard creature is
  easier to hit and easier to hit <em>well</em>.</p>

  <h2 id="ix-aiming">Aiming and Bracing</h2>
  <p>Patience is a weapon. Spend a Beat to <strong>Aim</strong> and your next Strike before your turn ends gains +2.
  A Kickback weapon — a shotgun, a buffalo rifle — punishes the hasty: fire it without bracing and you take –2 and stand
  Off-Guard until your next turn, unless your STR is 12 or better. Spending a Beat to <strong>brace</strong> (the same
  action as Aim) plants your feet and lifts both penalties. A long gun fired from a galloping horse is a prayer, not a plan.</p>

  <div class="box gold">
    <h4 id="ix-aim-two">Two shots, or three?</h4>
    <p>A Beat spent aiming is a Beat not spent shooting, and every table argues about it sooner or later. The argument
    has an answer, and it is not close. Every fight in this book has been played out on the engine the Keeper's app
    runs on, at every level, hundreds of times a case. A soul who spends the first Beat aiming and then takes
    <strong>two</strong> Strikes lands close to <strong>45%</strong> of them. A soul who skips the Aim and takes
    <strong>three</strong> at the rising Multiple Attack Penalty lands close to <strong>30%</strong>. That is about
    three hits for every two, and the aimed posse came out ahead at every level measured, on hits and on whether they
    lived.</p>
    <p>Pour it on anyway when the shot has to happen now: a thing one stride from somebody, a last round before it
    reaches cover, a target you only need to graze. The rest of the time, breathe first. The patient shootist is not
    a style of play in this game. It is the arithmetic.</p>
  </div>

  <h2 id="ix-reloading">Reloading</h2>
  <p>An empty gun is an expensive club. How long it takes to feed it depends on the iron:</p>
  <ul class="dash">
    <li><strong>1 / shot.</strong> A single-action revolver or lever repeater takes one Interact to chamber or thumb in one round between Strikes — or a full reload to top off (below).</li>
    <li><strong>Full reload.</strong> Topping a capacity or repeating weapon all the way back to full takes Beats equal to half its capacity, rounded up — a six-gun, three Beats; a twelve-shot repeater, six. The <em>Practiced Reload</em> Edge shaves one Beat from a weapon you favor.</li>
    <li><strong>Single (1).</strong> A break-action — derringer, double shotgun, single-shot rifle — is one Interact to reload fully.</li>
    <li><strong>Slow (cap-and-ball).</strong> Powder, ball, and cap by hand: a cap-and-ball revolver takes <strong>three rounds</strong> of dedicated work to make ready, and cannot be partially loaded in a hurry. This is the price of the cheapest gun in the book.</li>
  </ul>
  <p class="note">A wet day fouls black powder: increase a black-powder weapon's Misfire value by 1 (Chapter X), and clearing
  the jam is the more anxious for the rain running down your collar.</p>

  <div class="box gold">
    <h4 id="ix-answering">Answering a Working</h4>
    <p>Two workings in this book let you stop another one before it lands: the Sign called <em>Foul the Working</em>
    and the Miracle called <em>Not While I Stand</em>. They are answered the same way, and it is the same roll you
    already know.</p>
    <p>Spend the Reaction and the price. Then roll <strong>d20 + half your level + the ability your working uses</strong>
    against <strong>the other worker's DC</strong>. Beat it and the working comes apart: the price is spent, and
    nothing happens. Miss and it lands exactly as it meant to, and you have paid anyway. Neither of you may answer the
    answer.</p>
    <p>The difference between them is the difference between the two kinds of power. A Sign fouls
    <strong>anything</strong> worked, because the dark does not care whose hands are on the wire, and the price of
    reaching for a line already pulled taut is that on a natural 1 the working lands on you instead. A Miracle refuses
    <strong>only the dark</strong> and never another Miracle, because what is asked for in good faith is not yours to
    deny; in exchange it is safe, and you may do it as often as you can pay.</p>
    <p>A creature's own working is answerable by either. Most of what walks out here has never once been told no, and
    a great many of them do not have a second idea.</p>
  </div>

  <h2 id="ix-not-shooting">Some Things You Do Not Shoot</h2>
  <p>Most of what walks out here can be killed with what you are carrying. Some of it cannot, and the game means that
  literally rather than as a warning about difficulty. A thing far enough above you has more Blood than your posse can
  spend a night putting holes in, and the arithmetic does not care how well you play. Everyone at the table works this
  out at about the same moment, usually two rounds in.</p>
  <p>What such a thing has instead is an <strong>answer</strong>: fire, silver, running water, the grave it came out
  of, its true name, the man who called it, the thing it was promised and never got. Every one of them has one and the
  Keeper knows what it is. The shooting is still worth doing, because it buys the minutes somebody else needs to find
  the answer and reach it, and because a thing that is bleeding pays less attention to the person walking behind it.
  But the shooting is not how it ends.</p>
  <p>So when a fight is going badly in a way that feels arithmetical rather than unlucky, stop trying to win it. Ask
  what the thing wants, what it will not cross, what it was before, and who in this county already knows. That is not
  the Keeper being merciful. It is the game working as designed.</p>
  <p id="ix-still-shoot">A few rules later in this book say <strong>a thing you can still shoot</strong>, and that is
  the line they mean: everything on the near side of it, which is most of what you will ever meet, and which lead and
  powder and a good position will eventually finish. The far side has an answer instead. Your Keeper knows which side
  of the line anything is on and will tell you, usually by the second round, usually by how the arithmetic feels.</p>

  <h2 id="ix-wounds">Wounds, Bleeding, and Death</h2>
  <p>Your <strong>Blood</strong> is your hit points; it is also, plainly, your blood. At <strong>0 Blood</strong> you fall,
  <strong>Dying</strong> and bleeding — losing 1 Blood each round — until someone stabilizes you or you reach
  <strong>–CON</strong>, at which point you are dead, and out here dead is dead. A Fortitude save (DC 15) or a Medicine
  check (DC 15) can stop the bleeding; a point of Grit can keep you upright and acting one round more (Chapter II).</p>
  <p id="ix-dr"><strong>Damage Reduction (DR)</strong> and <strong>resistance.</strong> Some armor, hides, and unnatural toughness grant <strong>Damage Reduction</strong>: subtract that number from the Blood lost to each qualifying hit, so <em>DR 2 vs blades</em> turns a six-Blood knife wound into four. DR never lowers a hit below zero, and a noted limit (<em>vs blades</em>, <em>vs nonmagical</em>) means it helps only against that source. A creature with <strong>resistance</strong> to a kind of harm — fire, lead, the merely mortal — treats it as steep DR against that source and may shrug such blows off almost wholly; overcoming a resistance, with silver or fire or a blessed weapon, is often the whole of the problem.</p>
  <div class="pageno">43</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">XI. Conflict &amp; the Iron Code</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-saddle">Fighting from the Saddle</h2>
  <p>A horse turns a gunfight into a moving thing. The rules below cover a rider and mount in a fight; the mount's own
  statistics and temperament are in Chapter X (<em>Mounts &amp; Tack</em>).</p>

  <h4>The Mount&rsquo;s Movement</h4>
  <p>You and your mount act on your turn, sharing your three Beats. Spend a Beat to have a trained horse Stride its full
  Speed; you may move before and after a Strike as your Beats allow. Controlling a calm, trained mount is free. Controlling a
  green, wounded, or frightened one costs a Beat and a <strong>Ride</strong> check — fail, and the animal does as it pleases.
  A galloping mount that Strides at least 30 feet in a straight line lets you ride a foe down or break clean past a line.</p>

  <h4>Shooting from Horseback</h4>
  <p>From a <strong>standing or walking</strong> horse you fire as normal. From a <strong>trotting or galloping</strong> horse,
  every ranged attack takes <strong>–2</strong> for the moving platform, you cannot <em>Aim</em> or <em>Brace</em>, and a
  two-handed long gun (rifle, carbine, shotgun) takes a further <strong>–2</strong> and cannot be reloaded until you slow to a
  walk. The pistol is the horseman's weapon for good reason: fired one-handed, it leaves a hand for the reins.</p>

  <h4>Striking from Horseback</h4>
  <p>Mounted, you strike <strong>down</strong> at a foe on foot: gain <strong>+1</strong> to melee Strikes against the
  unmounted, and a footman needs reach — a spear, a polearm, a bayonet — or an Acrobatics check to strike back at you rather
  than at the horse. A two-handed melee weapon swung from the saddle is awkward (<strong>–2</strong>); the cavalry carries a
  saber and a lance for a reason.</p>

  <h4 id="ix-charge">The Charge</h4>
  <p>If your mount Strides at least <strong>20 feet</strong> in a straight line into a foe and you Strike with a
  <strong>lance, spear, or saber</strong>, the blow deals <strong>+1 die</strong> of damage — a couched lance deals
  <strong>double dice</strong> on a hit. You are committed and off-balance after: <strong>–2</strong> Defense until your next
  turn. A foe who sets a braced polearm or bayonet against your charge lands their blow on your mount first.</p>

  <h4>Keeping the Saddle</h4>
  <p>You may be thrown when the horse takes a critical hit, when it bolts or rears, or when you yourself take a critical melee
  blow. Make a <strong>Ride</strong> save (DC 15, or the attacker's result); on a failure you are unhorsed — fall prone, take
  <strong>1d6</strong> damage, and land a few feet from the animal. Mounting or vaulting up on purpose costs a Beat (a Drifter
  or a Veteran may do it free). A rider who has lost his horse is, all at once, just a person standing in the open.</p>

  <div class="box">
    <h4>From the Saddle, by Weapon</h4>
    <ul class="dash">
      <li><strong>Carbine / rifle / shotgun.</strong> –2 at a gallop and again for being two-handed (–4 in all); no reload above a walk. A saddle scabbard keeps it to hand.</li>
      <li><strong>Knife, hatchet, fists.</strong> Usable but graceless from the saddle, and they earn no charge bonus.</li>
      <li><strong>Pistol / revolver.</strong> No penalty at a walk; –2 at a gallop. The ideal horseback arm — one-handed and quick to holster.</li>
      <li><strong>Saber / lance / spear.</strong> The charge weapons: +1 die on a charge, double dice for a couched lance. A saber also serves at a stand, the mounted –2 waived.</li>
      <li><strong>Thrown (dynamite, knife, bottle).</strong> –2 from a moving horse — and pray the fuse and the gallop agree.</li>
    </ul>
  </div>
  <div class="pageno">44</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">XI. Conflict &amp; the Iron Code</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-grievous">Grievous Wounds</h2>
  <p>Guns are made to maim. When a single blow deals damage equal to half your maximum Blood or more, or on any
  <strong>critical hit</strong>, you must make a Fortitude save (DC 15, or higher for terrible weapons) or suffer a
  <strong>Lasting Injury</strong> — roll on the table below. These do not heal with rest alone; they require a Sawbones,
  time, and sometimes a graveyard.</p>
  <table>
    <thead><tr><th class="c">d6</th><th>Lasting Injury</th></tr></thead>
    <tbody>
      <tr><td class="c">1</td><td>Bloody Gash — bleed 1 extra until doctored; a scar to remember it by</td></tr>
      <tr><td class="c">2</td><td>Cracked Ribs — –2 on STR and DEX actions until healed</td></tr>
      <tr><td class="c">3</td><td>Maimed Hand — drop what you hold; –4 on tasks needing two good hands</td></tr>
      <tr><td class="c">4</td><td>Lamed Leg — Speed halved until set and rested a week</td></tr>
      <tr><td class="c">5</td><td>Ruined Eye or Ear — –4 on Notice and ranged Strikes; permanent</td></tr>
      <tr><td class="c">6</td><td>Gut-Shot — Dying at once; survival buys a lifelong frailty</td></tr>
    </tbody>
  </table>

  <h2 id="ix-nonlethal">Two Kinds of Fighting</h2>
  <p>Not every quarrel ends in a grave. A barroom scuffle, a wrestling-down, a pistol-whipping meant to subdue — declare
  before you roll that you strike <strong>nonlethally</strong>. Fists and a club do so by default; most other arms take –2
  to pull the blow. A foe brought to 0 Blood this way is knocked senseless, not killed. The same mercy is rarely offered
  to the things that hunt at night, and is never offered to a Hexer who has gone Lost.</p>

  <div class="box gold">
    <h4>The Mercy of Lethality</h4>
    <p>A game where bullets are deadly is a game where players think before they draw. That is the point. Telegraph
    danger, let foes be talked down or fled, and make the rare gunfight matter. When a character does die, give the death
    its weight — a last word, a turn of silence — and let the table feel it before the next scene rides in.</p>
  </div>

  <div class="quote">
    "I have seen a man empty all six and hit nothing but the night, and I have seen a woman fire once
    and end a war. The difference was never the gun. It was the half-second she took that he did not."
    <span class="src">— Marshal T. Coyle, on the only lesson worth teaching</span>
  </div>
  <div class="pageno">45</div>
</section>

<section class="page" id="nerve">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>XII. Nerve &amp; the Uncanny</span></div>
  <h1 class="chapter">XII. Nerve &amp; the Uncanny</h1>
  <p class="chapter-sub">The mind's slow accounting, and the long road of the Mark.</p>
  <div class="divider"></div>
  <div class="narr">Set down, for a moment, what you were told in the first chapter, and hear the rest of
  it. Something kept these plains before the buffalo, before the first peoples, before the word for
  hunger had a mouth to say it. The settlers call the silence peace. It is not peace. It is patience —
  and this chapter is the accounting of what that patience does to the souls who finally hear it.</div>
  <p class="dropcap lead">This is the heart of the game. A body can be doctored; a mind, once it has seen too far past the
  edge of the ordinary world, does not mend so cleanly. <strong>Nerve</strong> measures how much horror your character can
  carry before something in them gives way. The <strong>Mark</strong> measures how much of them the dark has already
  claimed. Watch both. They are the truest hit points you have.</p>
  <div class="quote">&ldquo;It stood over her the way weather stands over a valley &mdash; without face, without name, without any need of either. Elara screamed until she had no voice, and then she smiled, and that was worse. I have not slept a whole night since.&rdquo;
    <span class="src">&mdash; from the sealed testimony concerning Mrs. Elara, Calvary Wells</span></div>


  <h2 id="ix-nerve-pool">The Nerve Pool</h2>
  <p>Your maximum Nerve equals your <strong>RES score + your level</strong> (Edges and Callings may raise it). You begin
  each session at your maximum. When you witness or endure the uncanny, the Keeper calls a <strong>Dread Check</strong>:
  a Will save against the Dread DC of what you face. Fail, and you lose Nerve; succeed, and you steel yourself, losing none
  or only a little.</p>
  <table>
    <thead><tr><th>The Sight</th><th class="c">Dread DC</th><th>Nerve Lost on a Failed Save</th></tr></thead>
    <tbody>
      <tr><td>A fresh corpse, plainly murdered</td><td class="c">10</td><td>1</td></tr>
      <tr><td>A mutilation, a thing half-eaten</td><td class="c">13</td><td>1d4</td></tr>
      <tr><td>The walking dead; a true haunting</td><td class="c">16</td><td>1d6</td></tr>
      <tr><td>A thing from outside; the deep dark</td><td class="c">20</td><td>1d10</td></tr>
      <tr><td>A truth that unmakes your world</td><td class="c">25</td><td>1d10 + a lasting Affliction</td></tr>
    </tbody>
  </table>
  <p class="note">A <strong>critical success</strong> on a Dread Check (beating the DC by 10, or a natural 20) costs no Nerve
  and steadies you against the same horror for the rest of the scene. A <strong>critical failure</strong> (missing by 10,
  or a natural 1) loses the listed Nerve <em>and</em> imposes Frightened 1 at once.</p>

  <h2 id="ix-breaking">Breaking</h2>
  <p>Lose Nerve and you fray. At low Nerve the Keeper may impose the <strong>Frightened</strong> condition — a status penalty to all your rolls equal to its value —
  until you steady. Reach <strong>0 Nerve</strong> and you <strong>break</strong>: roll at once on the table below for a
  short, uncontrolled response, and take a lasting Affliction that rides you until it is treated. A broken character stays in play, and
  becomes dangerous to themselves and to those beside them.</p>
  <table>
    <thead><tr><th class="c">d6</th><th>In the Moment of Breaking</th></tr></thead>
    <tbody>
      <tr><td class="c">1</td><td>You freeze — lose your next turn, then act Frightened</td></tr>
      <tr><td class="c">2</td><td>You flee, heedless, toward the nearest dark or door</td></tr>
      <tr><td class="c">3</td><td>You fire wild at the threat — and at whatever is near it</td></tr>
      <tr><td class="c">4</td><td>You go to your knees, useless, until shaken hard or slapped</td></tr>
      <tr><td class="c">5</td><td>Hysterical laughter or weeping; others nearby test Nerve too</td></tr>
      <tr><td class="c">6</td><td>A moment of terrible clarity — you understand, and gain +1 Mark</td></tr>
    </tbody>
  </table>
  <p id="ix-afflictions"><strong>Lasting Afflictions</strong> are the scars of the mind: a phobia of the dark or the open plain, a compulsion
  to count or to pray, a palsy of the hands, or the <em>Thousand-Yard Stare</em> — a flatness that costs –2 on Presence and
  Insight until lifted. They are treated by an Alienist, a Confession, or long safe rest among people who love you, which
  in this country is the rarest medicine of all. (The Keeper's Book carries a full table of them.)</p>
  <div class="pageno">46</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">XII. Nerve &amp; the Uncanny</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-mark">The Mark</h2>
  <p>Some knowledge cannot be unlearned, and some contact cannot be washed off. The <strong>Mark</strong> is a track of six
  steps. You advance it when you break utterly, when you reach for power the world was not meant to hold, or when you touch
  the deep dark and survive changed. The Mark does not heal on its own. It only ever waits.</p>
  <table>
    <thead><tr><th class="c">Mark</th><th>What It Means</th></tr></thead>
    <tbody>
      <tr><td class="c">1</td><td>A chill others feel near you; dogs will not meet your eye</td></tr>
      <tr><td class="c">2</td><td>Dreams that are not yours; you wake knowing things</td></tr>
      <tr><td class="c">3</td><td>A visible sign — pale eyes, a cold touch, a wound that won't close</td></tr>
      <tr><td class="c">4</td><td>The uncanny treats you as kin; Dread DCs against you ease</td></tr>
      <tr><td class="c">5</td><td>You hunger for something you cannot name; Will saves to resist it</td></tr>
      <tr><td class="c">6</td><td>You are <strong>Lost</strong> — the dark finishes its work; the character becomes the Keeper's</td></tr>
    </tbody>
  </table>

  <h2 id="ix-returned">The Returned</h2>
  <p>Most who die stay dead. This is for the ones who did not, and for what it costs to be one of them
  at a fire where everybody else still breathes. A soul who <a href="#ix-o-wrong">Came Back Wrong</a>
  is not a horror out of the Bestiary. You answer to your own name, you ride in the order, and your
  friends know you. What sets you apart is that the ordinary mercies have stopped reaching you. Sleep
  mends nothing. A Sawbones lays hands on you and finds no pulse to work against. Whiskey goes down
  cold. You mend by <em>wanting</em>, and the wanting is the whole of the problem.</p>

  <h3 id="ix-hunger">Hunger</h3>
  <p>A track of six steps that is yours alone. Nobody else at the table carries one. It is not the
  Mark and it does not move with the Mark, though a soul unlucky enough to walk both at once will
  find they rhyme.</p>
  <table>
    <thead><tr><th class="c">Hunger</th><th>What It Means</th></tr></thead>
    <tbody>
      <tr><td class="c">0</td><td>Quiet. In a dim room, at a distance, you pass for living</td></tr>
      <tr><td class="c">1</td><td>The want has a shape now, and you know its name</td></tr>
      <tr><td class="c">2</td><td>Cold to the touch; you stop bothering to pretend at meals</td></tr>
      <tr><td class="c">3</td><td>Your Shape's tell shows plainly, and will not be explained away twice</td></tr>
      <tr><td class="c">4</td><td>Dogs will not abide you; the living find reasons to sit elsewhere</td></tr>
      <tr><td class="c">5</td><td>You are mostly want. Will save to refuse what is put in front of you</td></tr>
      <tr><td class="c">6</td><td>You are <strong>Consumed</strong>; the character passes into the Keeper's hands</td></tr>
    </tbody>
  </table>

  <p><strong>Mending.</strong> Spend a Beat and take <strong>one Hunger</strong> to knit what has been
  opened: recover <strong>1d6 Blood for every two levels you have</strong>, and never less than 1d6.
  This is the only way you heal. Not rest, not medicine, not a Miracle worked over you by somebody who
  loves you. The arithmetic is worth saying plainly, because it is the whole of what this Origin is:
  the thing that keeps you standing is the same thing that is taking you away.</p>

  <p><strong>Feeding.</strong> Feeding takes your Hunger <strong>down by one</strong>. What feeds you
  is decided by your Shape, below, and it is never an action you take on your turn. It is a scene. It
  costs somebody something, it happens where the table can see it, and the Keeper is the one who says
  whether what you did was enough. A Hunger bought back cheaply teaches everyone that the track does
  not mean anything.</p>

  <h3 id="ix-returned-worth">What the grave gave you</h3>
  <ul class="dash">
    <li><strong>You have already seen it.</strong> +2 on Dread Checks. Very little out here is new to
    somebody who has been on the other side of it.</li>
    <li><strong>The body's business is finished.</strong> Food, water, sleep and air are habits now, not
    needs. Poison and disease find nothing in you to work on.</li>
    <li><strong>At Hunger 3 and above you stop losing Nerve to Dread Checks altogether.</strong> Read
    that twice before you decide it is a gift. Nerve is the measure of a soul still able to be
    horrified, and a thing that cannot be horrified has lost its last honest warning system.</li>
  </ul>

  <h3 id="ix-returned-cost">What it takes</h3>
  <ul class="dash">
    <li><strong>Grace does not settle on you.</strong> Any Miracle that harms the Marked or the uncanny
    harms you the same, and a blessing meant to mend simply will not take. Your Preacher will work this
    out, and the evening they work it out is worth playing.</li>
    <li><strong>The Old Dark knows its own.</strong> It notices you before it notices anybody standing
    next to you, which is a thing a posse can use exactly once.</li>
    <li><strong>The living can tell.</strong> Not what, only that. &minus;1 on first impressions with
    the breathing, and it gets no better as the Hunger climbs.</li>
  </ul>

  <h3 id="ix-shapes">The Shapes of Return</h3>
  <p>Choose one when you make the character. It says what came back, what it wants, and the one thing
  it can do that the living cannot.</p>
  <ul class="dash">
    <li><strong>The Risen.</strong> Put back together by a hand that should have known better, or
    simply refused by ground that would not take you. <em>You hunger for</em> warmth, company, a reason
    to be upright. <em>Feeding:</em> a night of being treated as a person by somebody who knows what you
    are. <em>Gift:</em> you are hard to put down. Your death threshold is twice your CON, and the blow
    that drops you leaves you on your feet until the end of the round it lands.</li>
    <li><strong>The Sanguine.</strong> What runs in the living is the thing you no longer make. <em>You
    hunger for</em> blood, given or taken. <em>Feeding:</em> you drink, and somebody is less afterward.
    <em>Gift:</em> what you take, you keep. When you feed, recover Blood as though you had mended, and
    pay no Hunger for it.</li>
    <li><strong>The Hollow.</strong> You came back with a piece missing and you cannot name which piece.
    <em>You hunger for</em> the memory, and failing that, anyone else's. <em>Feeding:</em> you take a
    true memory from somebody willing to give it, and they do not get it back. <em>Gift:</em> you are
    not entirely here. Once a scene, pass through a closed thing or let a blow pass through you.</li>
    <li><strong>The Tolled.</strong> Something paid to have you back and it is holding the note.
    <em>You hunger for</em> whatever the lender is asking this month. <em>Feeding:</em> you do the
    errand, and you do not get to know why. <em>Gift:</em> the lender answers. Once a session ask for
    one thing within its reach and receive it, and take a Hunger for the asking.</li>
  </ul>

  <div class="box">
    <h3 id="ix-returned-safety">A Word Before Anybody Plays One</h3>
    <p>This Origin seats a predator at the table, and three of the four Shapes feed on people who did not
    volunteer. Settle at the start what that looks like in your game, the same way you settled everything
    else. A Keeper may rule any Shape's feeding bloodless, or off-screen, or both, and the rules lose
    nothing by it. The horror in Blood &amp; Grit has always been the price a soul agrees to pay. It has
    never been the details of the meal.</p>
  </div>

  <h2 id="ix-recover-nerve">Recovering Nerve</h2>
  <p>Nerve is dear, and the ways to restore it are few:</p>
  <ul class="dash">
    <li><strong>Confession.</strong> Speaking the horror plainly to someone who listens — a Preacher, a friend, a downtime scene — restores 1d6 and may ease an Affliction.</li>
    <li><strong>Safe rest.</strong> A full night unmolested in genuine safety restores 1d6 Nerve; a week of true peace, all of it.</li>
    <li><strong>The gifts of others.</strong> A Preacher's sermon, a Sawbones' reason, a comrade's grim joke, or a point of Grit can each buy back a measure of steadiness.</li>
    <li><strong>Whiskey and worse.</strong> A stiff drink steadies the hand now — recover 1d4 Nerve — but lean on it and court a vice, and the Fortitude saves that come with it.</li>
  </ul>

  <div class="box">
    <h3 id="ix-safety">A Second Word on Safety</h3>
    <p>The horror in this game lives most in the mind — in dread, helplessness, and the dark turns a frightened character
    may take. Keep checking in with your table, honor every line and veil, and remember that no one's real unease is the
    price of a good scare. The Mark is a story tool, not a trap; a player should always know roughly where their character
    stands on it, and have a fighting chance to step back.</p>
  </div>

  <div class="quote">
    "Folk ask me what the dark wants. It don't want. Wanting is a thing the living do.
    The dark only keeps — patient as a ledger, and twice as honest about what you owe."
    <span class="src">— attributed to the conjure-woman of Calvary Wells</span>
  </div>
  <div class="pageno">47</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">XII. Nerve &amp; the Uncanny</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-taint">The Taint of the Land</h2>
  <p>Some country has drunk too deep. Where a Patron of the Old Dark has been fed — a massacre left unburied, a cult's
  ground worked for a generation, a mine that broke into the deep dark, a thin place where the veil has worn through —
  the land itself takes a stain. Crops come up the wrong color. Water runs cold and tastes of iron. The dark does not
  haunt such places so much as <em>own</em> them, and it asks a toll of every living soul that lingers, whether they
  ever lay eyes on a ghost or not.</p>
  <p>A character of any calling <strong>save those of the Old Dark</strong> who remains on tainted ground gathers its
  <strong>Taint</strong> — a stain measured in four steps that deepens the longer they stay. The Old Dark callings
  (Chapter VII) feel no such toll; the blight is kin to them, and a few grow stronger in it. For everyone else the land
  is patient, and the ledger runs one way only, until the ground is cleansed or the soul is claimed.</p>

  <h3>The Reckoning</h3>
  <p>For every <strong>three days</strong> a soul spends on tainted ground — waking or sleeping, it makes no difference —
  the Keeper calls a <strong>Taint save</strong> against the ground's DC. The save is <strong>Fortitude</strong> while the
  stain is still in the body and <strong>Will</strong> once it has reached the mind; the Keeper names which. Hold your
  save and you are no worse than you were. Fail, and your Taint deepens by one step. A <strong>critical failure</strong>
  deepens it by two; a <strong>critical success</strong> sheds a step you had already taken.</p>
  <table>
    <thead><tr><th>The Ground</th><th class="c">Taint DC</th></tr></thead>
    <tbody>
      <tr><td>Soured — a hanging-tree, a salted field, blood spilled in the dark's name</td><td class="c">13</td></tr>
      <tr><td>Blighted — a cult's seat, a haunted claim, a true thin place</td><td class="c">16</td></tr>
      <tr><td>Unhallowed — a Patron's own ground, the deep dark risen into the land</td><td class="c">20</td></tr>
    </tbody>
  </table>
  <p class="note">A ward, a charm, or the right Provision Against the Dark (Chapter X) eases the DC by 2. Ground that is
  blessed, salted, and watched may be held off for a while; ground that is properly <strong>sanctified</strong> sheds its
  taint for good — though the doing of it is its own long night's work.</p>

  <h3>The Four Steps of the Stain</h3>
  <table>
    <thead><tr><th class="c">Taint</th><th>What the Land Does to You</th></tr></thead>
    <tbody>
      <tr><td class="c">1 — The Sickening</td><td>The body sours first. You are <strong>Sickened 1</strong> and <strong>Fatigued</strong>; food will not sit and wounds knit slow. The illness lifts a day after you quit the ground.</td></tr>
      <tr><td class="c">2 — The Whisper</td><td>It finds a voice. Whenever you would plainly cross the dark — break its work, leave its ground, warn another soul — the Keeper calls a <strong>Will save</strong>; fail, and you hesitate, &ldquo;forget,&rdquo; or talk yourself onto its errand instead.</td></tr>
      <tr><td class="c">3 — The Stain</td><td>It is in you now. The penalties harden, the place reads your wants, and your dreams turn to its purpose; while you remain, Dread DCs ease for the dark and worsen for you.</td></tr>
      <tr><td class="c">4 — The Claiming</td><td>Exposed this long, you are all but owned. At <strong>each further Reckoning</strong> you make a Will save or take <strong>+1 Mark</strong> (Chapter XII) — and the Mark, once taken, does not wash off when you ride away.</td></tr>
    </tbody>
  </table>

  <h3 id="ix-shed-taint">Shedding the Taint</h3>
  <ul class="dash">
    <li><strong>Distance.</strong> Leave the ground and the stain eases one step for every three days clear of it — but a Taint that reached the Claiming leaves its Marks behind regardless.</li>
    <li><strong>Sanctuary and rite.</strong> A Padre's blessing, a Confession, true holy ground, or the Old Rites (Chapter XIII) can each lift a step, and full sanctification on the Compass (Chapter III) clears the whole of it.</li>
    <li><strong>The Marked ride easier.</strong> A soul already bearing the Mark eases its own Taint DC by 2 — the dark is slow to spoil what it half-owns — yet pays for that kinship in every other quarter.</li>
  </ul>

  <div class="box">
    <h3>For the Keeper</h3>
    <p>Taint is a clock, not a coin-toss. Name the ground, set the DC, and let the players feel the days pressing on them.
    Tell them plainly when a place is tainted and roughly how deep their stain has run; the dread lives in the choice to
    stay, never in a hidden number. Use it to give cursed country real weight — and always leave a road back out: a church,
    a rite, a reason to ride for clean air before the land collects what it is owed.</p>
  </div>
  <div class="pageno">48</div>
</section>
<section class="page" id="signs">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>XIII. Signs, Miracles &amp; Old Rites</span></div>
  <h1 class="chapter">XIII. Signs, Miracles &amp; Old Rites</h1>

  <p class="chapter-sub">The borrowed words of the dark, the words asked for on the knees, and the folk-craft that holds both off.</p>
  <div class="divider"></div>
  <p class="dropcap lead">There is power in the old country beneath the country, and it can be reached — by the Hexer freely,
  by the Touched a little, by the desperate at ruinous cost. <strong>Signs</strong> are worked acts of will and word. Each one lists its
  <strong>Rank</strong>, its casting time, its price in Nerve or Blood, the save it forces where it forces one, what it
  does, and its <strong>Backlash</strong> — what the dark exacts when the working slips. There are fifty-five of them here,
  across three lists, and no single soul will ever hold more than a handful.</p>
  <p>The <strong>Miracles</strong> are in this chapter too, beginning at <em>The Work of Faith</em>. They are the other
  half of the same subject and the book kept them eighty pages apart for years, which helped nobody: a Sign is taken and
  a Miracle is asked for, and the difference between those two sentences is most of what this chapter is about. The
  <strong>Old Rites</strong> close it out, and belong to neither.</p>
  <h2 id="ix-sign-rank">Rank and Reach</h2>
  <p>Every Sign carries a <strong>Rank</strong> from one to eight. The Rank measures the reach: how far into
  the old country you have to go to fetch the words, and how much of you comes back with them. A Rank Eight
  Sign is no harder to pronounce than a Rank One. It simply costs more to mean it. You may
  learn and work any Sign of a Rank your level allows, and no other. There is no arguing the point with a Sign
  of a Rank above you: the words are there, the meaning is not, and nothing happens at all.</p>
  <table>
    <thead><tr><th class="c">Rank</th><th class="c">You may work it at</th><th>What it is</th></tr></thead>
    <tbody>
      <tr><td class="c">1</td><td class="c">1st level</td><td>Small workings — sight, salt, a sour word, a light</td></tr>
      <tr><td class="c">2</td><td class="c">3rd level</td><td>The first real reaching — holding, hiding, stepping</td></tr>
      <tr><td class="c">3</td><td class="c">5th level</td><td>Working harm, working mercy, working across distance</td></tr>
      <tr><td class="c">4</td><td class="c">7th level</td><td>Binding and unbinding: wards, contracts, curses that hold</td></tr>
      <tr><td class="c">5</td><td class="c">9th level</td><td>The deep reach. Every one of these costs something permanent</td></tr>
      <tr><td class="c">6</td><td class="c">11th level</td><td>Past what the books hold. You are working from memory and nerve</td></tr>
      <tr><td class="c">7</td><td class="c">13th level</td><td>Weather, ground, sleep, luck — the conditions other people live inside</td></tr>
      <tr><td class="c">8</td><td class="c">15th level</td><td>One rank, three Signs, and each is the last thing a worker learns</td></tr>
    </tbody>
  </table>
  <p class="note">You do not gain new Signs merely for reaching a Rank. Your Calling's table says how many Signs you
  know; the Rank says which ones you are allowed to choose from. A tenth-level Hexer knows fewer Signs than there are
  Signs in this chapter, and will go to her grave never having learned most of them. That is the intended shape of it.</p>
  <p class="note">Ranks Six and Seven hold four Signs apiece and Rank Eight holds three, which is not an oversight.
  Nobody was ever meant to have a menu at that reach. A worker who gets there has three or four of them at most, has
  paid for every one, and knows exactly which of them she will not use again.</p>

  <h2 id="ix-sign-price">The Price</h2>
  <p>Signs are paid for in three coins, and the difference between them is the difference between a bad night and a
  ruined life.</p>
  <ul class="dash">
    <li><strong>Nerve</strong> is the standing coin. Every Sign lists its cost, which is generally its Rank. Nerve comes
    back with rest, confession, whiskey, and the company of people who love you — see Chapter XII.</li>
    <li><strong>Blood</strong> is the desperate coin. Where a Sign offers the trade you may pay <strong>two Blood for
    each Nerve</strong> instead, and some Signs take Blood and nothing else. Blood spent on a working does not come back
    until you have rested properly; it is not a wound a Sawbones can close.</li>
    <li><strong>Mark</strong> is the coin you cannot earn back. Rank 5 Signs cost it, some of the Bargain's Signs cost it
    at any Rank, and nothing in this book gives it back. Six Marks and the character is the Keeper's (Chapter XII).</li>
  </ul>
  <p class="note" id="ix-sign-dc">Where a Sign forces a save, the DC is the worker's <strong>Sign DC = 10 + half their
  level + RES modifier</strong>. A casting time given in Beats follows the Iron Code (Chapter XI); a Sign that takes an
  <em>Action</em> costs one Beat. Working a Sign is plainly visible: there is a word, there is a gesture, and everyone
  in the room can see who did it.</p>

  <h2 id="ix-sign-lists">The Three Lists</h2>
  <p>Not every worker reaches the same place, and the places do not hold the same things. There are three lists in this
  chapter. Your Calling says which you may draw from, and no Calling draws from all three.</p>
  <ul class="dash">
    <li><strong>The Common Signs</strong> are open to anyone who works Signs at all.</li>
    <li><strong>The Bargain</strong> belongs to the Hexer, the Dark Cultist, and the False Prophet — the ones who
    reached out and took, and who are still being invoiced.</li>
    <li><strong>The Craft</strong> is the Witch's alone. It is older than the thing the Hexer bargains with, it was
    handed down rather than sought, and it concerns itself with houses and weather and grudges more than with the
    deep dark.</li>
  </ul>
  <p>A Hexer and a Witch sitting at the same table are not two of the same thing. She can ward the house he is standing
  in and he cannot; he can open the ground under a thing she could only curse. Neither list is stronger. They want
  different nights.</p>
  <h2 id="ix-signs-common">The Common Signs</h2>
  <p>Worked by anyone who works Signs at all — the plain grammar of the thing, learned first and leaned on longest.</p>
  <h3 id="ix-s-witchsight">Witch-Sight</h3>
  <p><em>Rank 1 · Free · 1 Nerve.</em> For a scene you see the unnatural plainly: the Marked, the haunted, the places where the world has worn thin. Distance does not help it and neither does daylight. <strong>Backlash:</strong> What you are looking at may notice that you are looking.</p>
  <h3 id="ix-s-salt">Salt &amp; Iron</h3>
  <p><em>Rank 1 · 1 Beat · 1 Nerve · Will save.</em> A handful of blessed salt or cold-iron filings thrown wide. Uncanny things within ten feet save or recoil, and the Marked feel its sting whether they meant to stand in it or not. The salt is thrown and it is done. <strong>Backlash:</strong> None. This is the kindest Sign in the book, and the weakest.</p>
  <h3 id="ix-s-listening">The Listening</h3>
  <p><em>Rank 1 · One minute · 1 Nerve.</em> Lay your palm flat on a wall, a table, a floorboard, and hear what was spoken in that room within the past day. You get the words. Tone, and who was lying, you must judge yourself. <strong>Backlash:</strong> You also hear whatever else has been speaking in that room, which is not always a person.</p>
  <h3 id="ix-s-coldlamp">Cold Lamp</h3>
  <p><em>Rank 1 · 1 Beat · 1 Nerve.</em> A light rises off your hand that sheds no warmth and throws no shadow, bright as a good lantern, lasting an hour. It cannot be blown out, drowned, or hidden. <strong>Backlash:</strong> It cannot be hidden. Everything in that dark now knows exactly where you are standing.</p>
  <h3 id="ix-s-stilling">The Stilling</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve · Will save.</em> A word and a gesture. One living creature within sight saves or is held fast, unable to act, for one round per two levels you hold. <strong>Backlash:</strong> On a failed working you are stilled instead, for the same count.</p>
  <h3 id="ix-s-foul">Foul the Working</h3>
  <p><em>Rank 2 · Reaction · 2 Nerve.</em> Someone within sight has begun to work something, and you are on the same wires they are. Grab the line and cross it. Roll d20 + half your level + your Sign ability against their working DC; on a success the working comes apart at once, its price already spent, and nothing happens at all. This answers anything worked, a Sign or a Miracle or the thing a creature does with its mouth, because the dark does not care whose hands are on it. Backlash: on a natural 1 the working lands on you instead, at full strength, and you may foul nothing else this scene.</p>
  <h3 id="ix-s-hollow">Hollow Step</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve.</em> Step into one shadow and out of another within sight, as far as a stone's throw. You arrive whole, which is not guaranteed and is worth remarking on. The step is taken and it is done. <strong>Backlash:</strong> Some part of you arrives late: Frightened 1 until your next turn.</p>
  <h3 id="ix-s-tally">The Tally</h3>
  <p><em>Rank 2 · Ten minutes · 2 Nerve.</em> Ask the dark one question and receive an answer that is true, partial, and unwelcome. It does not lie. It simply declines to be helpful. The answer given, the working is done. <strong>Backlash:</strong> The answer costs a Dread Check, and a deep enough truth gains a Mark.</p>
  <h3 id="ix-s-deadmans">Deadman's Coat</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve.</em> For a scene the eye slides off you the way it slides off a fencepost. You are not invisible; you are uninteresting, which in a crowded room works better. <strong>Backlash:</strong> Speak, strike, or draw and it breaks at once, and whoever was nearest is startled into looking straight at you.</p>
  <h3 id="ix-s-breath">Borrowed Breath</h3>
  <p><em>Rank 3 · 1 Beat · 3 Nerve.</em> Lend a dying companion a measure of your own life. Heal them 2d8 and take half that number in Blood yourself, which does not come back until you rest. <strong>Backlash:</strong> If they die anyway, you gain +1 Mark. The dark keeps the loan regardless.</p>
  <h3 id="ix-s-longwhisper">The Long Whisper</h3>
  <p><em>Rank 3 · 1 Beat · 3 Nerve.</em> Speak a sentence into the ear of someone you have met, wherever they are, as though you stood behind them. They may answer once. Most do not, the first time. The way stays open for the scene. <strong>Backlash:</strong> Anything between you that can hear the dark hears it too, and now has both your names.</p>
  <h3 id="ix-s-nailshadow">Nail the Shadow</h3>
  <p><em>Rank 3 · 1 Beat · 3 Nerve · Reflex save.</em> Drive an iron nail through a creature's shadow. It saves or cannot move from that spot until the nail is pulled, though it may still fight, and will. <strong>Backlash:</strong> Pull the nail carelessly and the shadow comes with it, attached to you until dawn.</p>
  <h3 id="ix-s-unburden">The Unburdening</h3>
  <p><em>Rank 3 · One minute · 3 Nerve.</em> Take another soul's terror onto yourself. Clear their Frightened condition and restore 1d6 of their Nerve; you lose that much of your own. <strong>Backlash:</strong> You take their memory of the thing along with the fear, and it does not fade on the ordinary schedule.</p>
  <h3 id="ix-s-threshold">Ward of the Threshold</h3>
  <p><em>Rank 4 · Ten minutes · 4 Nerve.</em> Chalk, salt, and a spoken name across a doorway. Until dawn nothing uncanny crosses it uninvited, and an invitation once given cannot be taken back that night. <strong>Backlash:</strong> The ward holds both ways. What is already inside stays inside with you.</p>
  <h3 id="ix-s-reckoning">The Reckoning Hour</h3>
  <p><em>Rank 4 · One minute · 4 Nerve.</em> Look at a creature and learn the one thing that will kill it: silver, fire, its own name spoken backward, a blessed round, the fourth cut and not the third. <strong>Backlash:</strong> It learns the same about you, in the same moment, and it does not have to work a Sign to use what it learns.</p>
  <h3 id="ix-s-unmake">Unmake the Working</h3>
  <p><em>Rank 4 · 1 Beat · 4 Nerve.</em> End another's Sign as it is spoken or after it has settled. Roll your Sign DC against theirs; the higher unmakes the lower, and a tie leaves both standing. The unmaking is resolved at once. <strong>Backlash:</strong> Fail and you have paid the Nerve and announced yourself to a worker who now knows your range.</p>
  <h3 id="ix-s-longnight">The Long Night</h3>
  <p><em>Rank 5 · One minute · 5 Nerve and 1 Mark.</em> Hold a soul at the very edge of death until dawn. They do not worsen, do not wake, and cannot be killed by anything short of fire or the deliberate hand of something old. <strong>Backlash:</strong> Whatever was coming for them waits at the foot of the bed until sunrise, and it is patient, and it can be seen.</p>
  <h3 id="ix-s-debt">The Debt Called In</h3>
  <p><em>Rank 5 · 1 Beat · 5 Nerve and 1 Mark.</em> Everything out here owes something to something. Name a creature you can see and call in what it owes, whether or not you are the one it owes it to. It takes 6d6 at once and is Frightened of you until the end of its next turn, and there is no save, because a debt is not an opinion. Backlash: you take a point of Mark for having reached that far into a ledger that was never yours, and that is the whole of the price.</p>
  <h3 id="ix-s-unwrittenhou">The Unwritten Hour</h3>
  <p><em>Rank 6 · 1 Beat · 6 Nerve and 1 Mark.</em> Say that the last round did not happen, and it did not. Everything
  since your own last turn comes undone: the shot, the fall, the word spoken, the door opened. Everyone acts again from
  where they stood, knowing nothing. Backlash: you remember both hours, and for a day you cannot reliably tell which of
  the two you are living in. Roll a flat check the first time it matters, and the Keeper will not tell you why.</p>
  <h3 id="ix-s-nothinganswe">Nothing Answers Here</h3>
  <p><em>Rank 6 · One minute · 6 Nerve.</em> Draw the line and close it. For an hour, inside a hundred feet of where you
  drew it, no Sign works, no Miracle is granted, no uncanny thing does the thing it does, and nothing may be summoned,
  banished, healed by grace or harmed by a working. It is quiet in there in a way that frightens people who have never
  heard it. Backlash: you are inside it too, and you cannot lift it early.</p>
  <h3 id="ix-s-groundgives">The Ground Gives</h3>
  <p><em>Rank 7 · 1 Beat · 7 Nerve and 1 Mark.</em> The country stops holding still. For the scene, within sight, you move
  the ground: a road becomes a ravine, a river runs the other way, a wall is somewhere else, a floor opens, a hill
  stands where there was flat. One change a round, each of them real and each of them permanent unless something changes
  it back. Backlash: the ground remembers who moved it, and every working you attempt on that land afterward costs one
  more Nerve, for good.</p>
  <h3 id="ix-s-noonesleepst">No One Sleeps Tonight</h3>
  <p><em>Rank 7 · One minute · 7 Nerve and 1 Mark.</em> Take the night off a place. For a full night, nobody inside a mile
  sleeps, rests, recovers Blood or Nerve, regains a pool, or heals by any means short of a Miracle. The uncanny do not
  restore themselves either, which is generally the point, and the living get to dawn with nothing left. Backlash: you
  do not sleep for three nights afterward, and the third one is bad.</p>
  <h3 id="ix-s-wordunderwor">The Word Under the Word</h3>
  <p><em>Rank 8 · One minute · your whole pool of Nerve and 1 Mark, permanently.</em> Every working has a word under it
  that nobody says. Say it. One working of any kind, anywhere you have ever been — a curse, a ward, a binding, a
  Miracle, a Sign, a thing a creature was made to do — comes apart and has never worked. It may be one that finished a
  hundred years ago, and the hundred years rearrange themselves around its absence. Backlash: your Mark rises by one and
  does not come down, and one working of your own, chosen by the Keeper, comes apart at the same moment.</p>
  <h2 id="ix-signs-bargain">The Bargain</h2>
  <p>For those who reached out and took: the Hexer, the Dark Cultist, the False Prophet. These Signs are stronger than the Common ones and priced accordingly, most often in Mark.</p>
  <h3 id="ix-s-debt">Debt Collected</h3>
  <p><em>Rank 1 · Free · 1 Nerve.</em> Name a creature you can see and mark it as owing. Your next blow against it, by hand or gun or Sign, deals an extra 1d6. <strong>Backlash:</strong> If the mark goes uncollected before the scene ends, you take that 1d6 yourself.</p>
  <h3 id="ix-s-lender">The Lender's Ear</h3>
  <p><em>Rank 1 · One minute · 1 Nerve.</em> Put a question to whatever it is you deal with, framed so that yes or no will answer it. You get the one word. It is accurate. The one word given, the working is done. <strong>Backlash:</strong> It remembers that you asked, and asking is a thing that accrues.</p>
  <h3 id="ix-s-rot">Rot the Wound</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve · Fortitude save.</em> A wound you dealt this scene will not close. The creature saves or takes 1d6 each round until it is doctored, bound, or dead. <strong>Backlash:</strong> The next wound dealt to you behaves the same way, and you cannot doctor your own.</p>
  <h3 id="ix-s-grasping">The Grasping Dark</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve · Reflex save.</em> Shadows within twenty feet take hold. Creatures there save or are held fast until they break loose with a Strength check against your Sign DC. <strong>Backlash:</strong> The dark does not distinguish. Your companions are standing in it too.</p>
  <h3 id="ix-s-coinpain">Coin of Pain</h3>
  <p><em>Rank 2 · 1 Beat · 2 Blood.</em> The trade run backward: open your own arm and buy 1d6 Nerve with the Blood. Some nights this is the only bank still open. <strong>Backlash:</strong> Work it twice in a session and the second working costs a Mark as well.</p>
  <h3 id="ix-s-crimson">The Crimson Word</h3>
  <p><em>Rank 3 · 1 Beat · 3 Nerve or 6 Blood.</em> You speak a syllable that was not shaped for a human mouth, and a creature you can see takes 3d6 as its own blood turns against it. <strong>Backlash:</strong> On a natural 1, or a critical failure to overcome its resistance, you take the damage.</p>
  <h3 id="ix-s-borrowedface">The Borrowed Face</h3>
  <p><em>Rank 3 · One minute · 3 Nerve.</em> Wear the face of someone the dark has already taken. For an hour you are them to any eye, any voice, any old friend who ought to know better. <strong>Backlash:</strong> For that hour you also remember being them, and some of it stays after the face goes.</p>
  <h3 id="ix-s-hungering">The Hungering Hand</h3>
  <p><em>Rank 3 · 1 Beat · 3 Nerve · Fortitude save.</em> Your touch takes 2d6 Blood from a living creature and gives half of it to you. It saves for half, and it feels exactly what it is. <strong>Backlash:</strong> Take Blood this way three times in a day and you must save or begin to prefer it.</p>
  <h3 id="ix-s-ledger">Feed the Ledger</h3>
  <p><em>Rank 4 · 1 Beat · 1 Mark.</em> Pay in the only coin that never runs short. The next Sign you work this scene costs no Nerve and no Blood, and its dice are maximized. <strong>Backlash:</strong> None, and that is the trouble with it. The bill is already paid and it is never refunded.</p>
  <h3 id="ix-s-contract">The Black Contract</h3>
  <p><em>Rank 4 · Ten minutes · 4 Nerve and 1 Mark · Will save.</em> Bind a creature that can understand you to a single promise. It saves; on a failure it cannot break the promise, and both of you know the terms exactly. It holds until the promise is kept, or the creature is destroyed. <strong>Backlash:</strong> You are bound to your half of it on the same terms, and it read the wording more carefully than you did.</p>
  <h3 id="ix-s-vein">Open the Vein of the World</h3>
  <p><em>Rank 5 · 1 Beat · 5 Nerve and 1 Mark · Reflex save.</em> The ground splits along something that was never a fault line. Every creature within thirty feet takes 6d8 and saves for half. The crack does not close. <strong>Backlash:</strong> The ground remembers. That country gains a step of Taint, permanently.</p>
  <h3 id="ix-s-calling">The Calling</h3>
  <p><em>Rank 5 · One minute · 5 Nerve and 1 Mark.</em> You call something out of the dark to bargain or to serve, and it comes. What it is, what it wants, and whether it consents to leave are the Keeper's to decide. It stays until it is sent back, or until it has what it came for. <strong>Backlash:</strong> The most dangerous Sign in this book. Work it last, or never.</p>
  <h3 id="ix-s-whatwaspromi">What Was Promised</h3>
  <p><em>Rank 6 · 1 Beat · 6 Nerve and 1 Mark.</em> Something out there owes you, and you have decided to say so out loud. Name the debt, and you take payment instantly: any single effect of a Sign of Rank 5 or under, worked instantly and without its
  own cost, whether or not you know it. Backlash: the ledger is not yours to read. Whatever you took is added to what
  you owe at twice the value, and the Keeper decides when that is collected and from whom.</p>
  <h3 id="ix-s-sellnight">Sell the Night</h3>
  <p><em>Rank 7 · One minute · 7 Nerve and 2 Mark.</em> Offer up a night that has not happened yet. Name a night in the
  coming year and hand it over; until then you work every Sign at one Rank higher than you have earned, pay one less
  Nerve for each, and cannot be reduced below 1 Blood by anything uncanny. Backlash: on the night you sold, you are not
  yours. Where you went and what was done with you is the Keeper's, and you will hear about some of it later.</p>
  <h3 id="ix-s-nameyouwereg">The Name You Were Given</h3>
  <p><em>Rank 8 · One minute · your whole pool of Nerve and 2 Mark, permanently.</em> Everything that was made was named
  when it was made, and the name is still true. Speak the true name of one creature you can see, however old and however
  great, and it must do one thing you say, in one sentence, at once and completely, whatever it is. It cannot refuse and there is no
  save. Backlash: it now knows that you know, it knows yours, and it has as long as it likes to do something about that.
  Very few workers have used this twice, and the ones who did were not around to be asked why.</p>
  <h2 id="ix-signs-craft">The Craft</h2>
  <p>The Witch's alone. Older than the dark the Hexer bargains with, handed down a crooked family line, and largely concerned with houses, weather, kin, and grudges.</p>
  <h3 id="ix-s-sourmilk">Sour the Milk</h3>
  <p><em>Rank 1 · Free · 1 Nerve.</em> The small malice the Craft is famous for. A creature you can see takes a &minus;2 on its very next roll, and the milk goes off, and the bread will not rise. The malice holds until that roll is made. <strong>Backlash:</strong> None worth the name, which is why every witch in the territories knows it.</p>
  <h3 id="ix-s-knotwind">Knot the Wind</h3>
  <p><em>Rank 1 · Ten minutes · 1 Nerve.</em> Tie the weather into a length of cord: three knots, three winds. Loose one later for a gust, a squall, or a good hour of driving rain. <strong>Backlash:</strong> Loose all three at once and the weather comes as it pleases, over country you had not intended to include.</p>
  <h3 id="ix-s-greenhand">The Green Hand</h3>
  <p><em>Rank 1 · Ten minutes · 1 Nerve.</em> Coax what grows into doing you a kindness. Treat a wound for 1d8, or bring a field, a poultice, or a half-dead horse back from the edge of ruin. <strong>Backlash:</strong> Whatever you healed it with dies, and the ground it stood in stays bare for a season.</p>
  <h3 id="ix-s-poppet">The Poppet</h3>
  <p><em>Rank 2 · Ten minutes · 2 Nerve · Will save.</em> Bind a doll to a person whose hair, blood, or name you hold. What you do to the doll, they feel, up to 2d6 and a save to halve it, at any distance you can imagine. <strong>Backlash:</strong> Whoever holds the poppet holds the working, and dolls are small and easily pocketed.</p>
  <h3 id="ix-s-nail">The Nail and the Name</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve · Will save.</em> You have had the name, or the hair, or a drop of them, since long before tonight. Drive the nail into anything wooden and say it. The creature saves at once or takes 2d6 and is Slowed for a round; on a success it takes half and keeps its feet. You need its true name, something of its body, or a thing it touched and left, and hearing a name shouted across a room in the middle of a fight counts. This is the Craft doing in one Beat what it spent a week getting ready to do. Backlash: the nail is spent whether or not the working lands, and so is whatever you had of them.</p>
  <h3 id="ix-s-crossing">Crossing the Threshold</h3>
  <p><em>Rank 2 · One hour · 2 Nerve.</em> Make a house yours. Nothing uncanny may enter it uninvited while you sleep under its roof, and it will know it is being kept out, and it will mind. The ward holds until dawn, and must be laid again each night you want it. <strong>Backlash:</strong> You must sleep there. A witch who wards a house and rides away has built a very good box for someone else.</p>
  <h3 id="ix-s-catserrand">Cat's Errand</h3>
  <p><em>Rank 2 · 1 Beat · 2 Nerve.</em> Send your familiar out and ride behind its eyes at any distance, for as long as you sit still and let it work. It can carry a Sign of Rank 1 in its mouth and deliver it. It holds until you rise or are struck, and then you are back behind your own eyes. <strong>Backlash:</strong> What happens to the familiar out there happens while you are looking through its eyes.</p>
  <h3 id="ix-s-brewing">The Brewing</h3>
  <p><em>Rank 3 · One hour · 3 Nerve.</em> Cook a Sign of Rank 2 or lower down into a draught and cork it. It keeps a month and works for whoever drinks it, which need not be you. <strong>Backlash:</strong> It works for whoever drinks it. Label the bottle.</p>
  <h3 id="ix-s-ninefold">The Ninefold Knot</h3>
  <p><em>Rank 3 · Ten minutes · 3 Nerve · Will save.</em> Nine knots in a red cord and a name said over each. A creature saves or cannot work its own uncanny power for nine days, though it may fight, flee, and remember you fine. <strong>Backlash:</strong> Cut the cord early and the nine days come back all at once, on you.</p>
  <h3 id="ix-s-widow">The Widow's Curse</h3>
  <p><em>Rank 4 · Ten minutes · 4 Nerve · Will save.</em> The old curse, laid properly and meant. A person saves or carries a lasting misfortune of your naming until the wrong you cursed them for is put right. <strong>Backlash:</strong> It cannot be lifted by you, or by anyone, until that wrong is actually put right. Curse carefully, and be sure of the wrong.</p>
  <h3 id="ix-s-turning">The Turning</h3>
  <p><em>Rank 4 · Reaction · 4 Nerve · Will save.</em> The evil eye put to the one use that is not spite. As a blow or a working comes at you, look at what sent it. It saves or the harm goes back the way it came at once, all of it, and the sender takes what it meant for you. On a success it lands as intended and you have spent the Nerve for a hard look. Backlash: everyone who sees you do this remembers your face, and no witch has ever had a good week afterward.</p>
  <h3 id="ix-s-askline">Ask the Line</h3>
  <p><em>Rank 4 · One hour · 4 Nerve.</em> Call up a woman of your own crooked line, dead these many years, and ask her. She answers plainly, at length, and with opinions about your choices. She stays for the scene. <strong>Backlash:</strong> She may decline to go back, and a dead grandmother in the house is a long and particular haunting.</p>
  <h3 id="ix-s-oldwomans">The Old Woman's Bargain</h3>
  <p><em>Rank 5 · One hour · 5 Nerve.</em> Trade a year of your own life for a working of any Rank you know, at no other cost, worked as though you were the greatest of your line. The year is taken from the far end. The bargain is struck at once, and what you bought is worked as any other. <strong>Backlash:</strong> None at the time. The Craft always collects at the far end, and it is never late.</p>
  <h3 id="ix-s-hearth">The Hearth Unbroken</h3>
  <p><em>Rank 5 · One hour · 5 Nerve.</em> For one night a place is genuinely safe. Nothing uncanny crosses, no Dread Check is called, and every soul under that roof wakes with full Nerve and Blood. <strong>Backlash:</strong> One night only, and the same roof will not answer twice in the same season. Choose the night with care.</p>
  <h3 id="ix-s-longwinter">The Long Winter</h3>
  <p><em>Rank 6 · One hour · 6 Nerve.</em> Lay cold on a country and let it stay. For a season, the valley or the town you
  name is colder than it should be: crops fail slowly, the sick get sicker, the roads close early, and anything that was
  buried stays buried. The old women who can do this rarely explain why they have. Backlash: you feel the cold yourself
  for the whole of it, and no fire ever quite reaches you again.</p>
  <h3 id="ix-s-turningofyea">The Turning of the Year</h3>
  <p><em>Rank 7 · One hour · 7 Nerve · Fortitude save.</em> Put years into a thing or take them out, permanently. A door rots off its hinges; a corpse is
  bones; a green field is a harvest; a wound is an old scar; a young man is old. A creature resists with a Fortitude
  save against your Sign DC, and a willing one need not. Ten years is the usual reach, and forty is the most anyone has
  managed. Backlash: the years have to go somewhere. They go into you, and they show.</p>
  <h3 id="ix-s-housethatsta">The House That Stands</h3>
  <p><em>Rank 8 · One night · your whole pool of Nerve, permanently.</em> Over a night's work you make a place yours in a
  way that outlasts you. Nothing uncanny enters it uninvited, ever. Nothing inside it can be scried, called, compelled
  or taken. It does not burn, and the weather leaves it alone, and it will be standing when the town around it is a
  scatter of foundations. Backlash: you may never have another, you may not leave it for more than a season without it
  beginning to fail, and something will spend the rest of your life on the porch waiting to be asked in.</p>
  <div class="pageno">49</div>
</section>

<section class="page" id="miracles">
  <div class="runhead"><span class="l">XIII. Signs, Miracles &amp; Old Rites</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-miracles">The Work of Faith</h2>
  <p class="chapter-sub">Miracles, their Rank, and the pool that pays for them.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Where the Old Dark works <strong>Signs</strong> (Chapter XIII), the faithful work
  <strong>Miracles</strong>, and the two run deeper apart than the tongue you pray in. A Sign is taken, and the taking
  is noticed, and the debt is entered in a ledger that never forgets. A Miracle is <em>asked for</em>, on the knees, of
  a higher and quieter thing, and now and again it is granted. It costs no Mark and draws no Backlash. It costs the
  pool, and it risks the oldest disappointment there is: a prayer that goes unanswered.</p>
  <p>Each of the six Callings of Faith works Miracles. You study and keep a handful, and lean on them, and they are
  ranked and gated exactly as the Signs are.</p>

  <h2 id="ix-m-rank">Rank and the Pool</h2>
  <p><strong>Rank.</strong> Every Miracle carries a Rank from one to eight, and you reach a new Rank at the same rungs a
  sign-worker does: <strong>1st, 3rd, 5th, 7th, and 9th level</strong>, and then 11th, 13th, and 15th. You may learn and
  work any Miracle of a Rank your level allows, and no higher; ask for more than you have earned and the grace simply
  does not come. You begin knowing <strong>two</strong> Miracles and learn another as each new Rank opens to you, to a
  repertoire of six by the height of a frontier life and nine by the end of a very long one.</p>
  <p class="note">Ranks Six and Seven hold four Miracles apiece and Rank Eight holds three. All three of the Rank Eight
  Miracles are Common Blessings, open to every Calling of Faith, which is deliberate: at that reach the difference
  between a Padre and a Shaman stops mattering, and what is left is the asking.</p>
  <p><strong>The Pool.</strong> Miracles are paid not in Nerve or Blood but from your Calling's own pool of faith made
  countable — the Padre's <em>Grace</em>, the Preacher's <em>Conviction</em>, the Shaman's <em>Breath</em>, the Medicine
  Man's <em>Vital Breath</em>, the Sister's <em>Mercy</em>, and the Witch Hunter's <em>Zeal</em>. Where a Miracle's cost reads
  &ldquo;2&nbsp;Faith,&rdquo; it means two points of that pool, whatever your Calling names it. The pool refreshes with
  the dawn (or the dawn Mass, or the morning offering), and it runs dry, as faith does, exactly when the night is longest.</p>
  <p class="note" id="ix-m-dc">Where a Miracle forces a save, the DC is your <strong>Miracle DC = 10 + half your level +
  your faith ability's modifier</strong> — Presence for the Padre and the Preacher, Resolve for the Shaman, the
  Medicine Man and the Sister, Wits for the Witch Hunter. A casting time given in Beats follows the Iron Code (Chapter XI); a Miracle
  worked as an <em>Action</em> costs one Beat, and one worked as a <em>Reaction</em> is taken on another's turn.</p>

  <h2 id="ix-m-lists">The Seven Lists</h2>
  <p>Every worker of Miracles draws on the <strong>Common Blessings</strong>, the shared grammar of grace. Beyond that,
  each Calling holds one list of its own, closed to the others: the Padre his <strong>Liturgy</strong>, the Preacher his
  <strong>Revival</strong>, the Shaman the <strong>Spirits</strong>, the Medicine Man the <strong>Mending</strong>,
  the Witch Hunter the <strong>Consecrations</strong>, and the Sister the <strong>Vigil</strong>. A Padre and a Preacher answer the same dark; they do not answer it
  with the same words, and this is where the difference is written down.</p>
  <div class="pageno">24</div>
</section>
<section class="page">
  <div class="runhead"><span class="l">XIII. Signs, Miracles &amp; Old Rites</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-m-list-blessing">The Common Blessings</h2>
  <p>Worked by any Calling of Faith — the shared grammar of grace, learned first and leaned on hardest when the deeper work runs dry.</p>
  <h3 id="ix-m-steadying">The Steadying Word</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Speak to one soul who can hear you and mean it. They shake off Frightened, or gain +2 on their next save against fear. It works on the faithless and the profane alike; steadiness is not particular about who receives it. The steadiness holds until that save is rolled.</p>
  <h3 id="ix-m-light">A Light Unfailing</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> A steady light rises at your word, warm where Cold Lamp is cold, and lasts an hour. The uncanny will not willingly step into it, and the Marked find it hard to meet.</p>
  <h3 id="ix-m-road">The Blessing of the Road</h3>
  <p><em>Rank 2 · Ten minutes · 2 Faith.</em> Bless a journey before it is begun. For the next day the party ignores the first hazard of the trail and travels at +2 on Survival to find the way, the water, and the safe camp.</p>
  <h3 id="ix-m-clasped">Hands Clasped</h3>
  <p><em>Rank 2 · 1 Beat · 2 Faith.</em> Take an ally's hand, or bid them take another's. For the scene the two of you share your saves against fear — whichever of you rolls better, both use — and neither may be made to flee while the other stands.</p>
  <h3 id="ix-m-notwhile">Not While I Stand</h3>
  <p><em>Rank 2 · Reaction · 2 Faith.</em> Something uncanny is being worked where you can see it. Say no. Roll d20 + half your level + your Miracle ability against the worker's DC; on a success it comes apart at once, its price already spent. You may answer a Sign, a curse in the moment it lands, or the working of any uncanny thing. You may not answer a Miracle: what is asked for in good faith is not yours to refuse. Nothing here can turn on you and no failure is worse than failing, so you may do it as often as you can pay for it.</p>
  <h3 id="ix-m-warding">The Warding Psalm</h3>
  <p><em>Rank 3 · Reaction · 3 Faith.</em> As an uncanny blow lands on you or a soul beside you, speak the psalm and turn it: the attack is halved, and its wielder gives ground a step. You may do this once per round, and not on ordinary lead.</p>
  <h3 id="ix-m-anoint">Anoint the Iron</h3>
  <p><em>Rank 3 · 1 Beat · 3 Faith.</em> Touch a weapon, speak over it, and give it back. For the scene it counts as blessed and as silver both, and every hit it lands on something uncanny deals an extra 1d6. It does not have to be your weapon and it does not have to stay in your hands; put it in the hands of whoever out here is best with it, which is rarely you.</p>
  <h3 id="ix-m-named">The Unclean Named</h3>
  <p><em>Rank 3 · 1 Beat · 2 Faith · Will save.</em> Point and name a thing for what it truly is. It saves or its nature stands revealed to all who can hear you, and it suffers a &minus;2 against you and yours until the scene ends. Some things have not been named aloud in a long age, and do not care for it.</p>
  <h3 id="ix-m-vigil">The Vigil</h3>
  <p><em>Rank 4 · One minute · 3 Faith.</em> Keep the watch and pray it through. Until dawn, no one in the camp may be surprised or driven by fear, and every soul but you sleeps easy under it. You take no rest, and you will feel the want of it come morning.</p>
  <h3 id="ix-m-rebuke">Rebuke the Dark</h3>
  <p><em>Rank 4 · 1 Beat · 4 Faith · Will save.</em> Raise your voice against the unclean things in sight. Each lesser uncanny saves or flees you for a round per two levels, and a greater one that fails is Frightened and gives ground. The oldest of them only smile — but the small ones run.</p>
  <h3 id="ix-m-miracle">The Miracle Plain</h3>
  <p><em>Rank 5 · 1 Beat · 0 Faith.</em> Once, and never lightly: ask for the thing that cannot be asked for, and now and again receive it. Undo one calamity of the moment just past — a death, a fire caught, a fall — as the Keeper allows. It empties your whole pool to nothing and cannot be tried again until you have rested and given thanks. Most prayers are not answered. This is about the ones that are.</p>
  <h3 id="ix-m-covenant">The Covenant</h3>
  <p><em>Rank 5 · 1 Beat · 5 Faith.</em> Spread your arms and stand for them. For the scene, no ally who can hear you may be brought below 1 Blood by uncanny harm — struck to the edge of death, and no further, while your voice holds. Ordinary lead still kills as it pleases. The dark does not get to.</p>
  <h3 id="ix-m-hour">The Hour Is Not Yours</h3>
  <p><em>Rank 5 · Reaction · 5 Faith.</em> When a soul you can see is about to die, and die rather than merely fall, say aloud that the hour is not yours to take. It is not taken. They lie Dying one point above dead and no worse, stable at once and until somebody reaches them. Whatever was coming for that soul now knows your name, knows you said it out loud, and has been given a reason to learn where you sleep.</p>
  <h3 id="ix-m-cupnotemptie">The Cup Not Emptied</h3>
  <p><em>Rank 6 · Ten minutes · 6 Faith.</em> Bless what little there is. Food, water, medicine, powder, lamp oil, bandage
  — whatever is in front of you, there is now enough of it for everyone here, for a week. It is plain and it is
  sufficient and it does not keep past the week. A great many hard winters have turned on somebody being able to do
  this.</p>
  <h3 id="ix-m-outofdepths">Out of the Depths</h3>
  <p><em>Rank 7 · One minute · 7 Faith.</em> Reach for somebody who has been taken. Name a soul who is possessed, bound,
  called away, hollowed out, sold, or being worn by something else, and pull. They come back at once, out of whatever has them, whole enough to speak and to say what happened. Whatever had them is now aware that you can do this, and where you were
  standing when you did it.</p>
  <h3 id="ix-m-answer">The Answer</h3>
  <p><em>Rank 8 · One minute · your whole pool of Faith.</em> Most prayers are not answered. Ask, once, for a single thing,
  in your own words, aloud, in front of whoever is there — and it is granted, whatever it was. The dead one back. The
  fire out. The army turned. The sickness lifted off a county. The thing that has been coming, not coming. There is no
  save, no roll and no limit but the one thing. Afterward your pool is empty until you have rested and given thanks, and
  you will spend the rest of your life being careful about what you ask for, having found out that it works.</p>
  <h3 id="ix-m-greaterlove">Greater Love</h3>
  <p><em>Rank 8 · Reaction · your whole pool of Faith.</em> Step in front of all of it. Any harm, effect, death, taking or
  unmaking about to fall on any number of souls you can see falls on you instead, entire and undivided, and they are
  untouched and unaware until it is over. You will very likely not survive it. If you do not, you cannot be raised,
  called back, or spoken to afterward by any means: you are where the people you saved are not, and that was the
  arrangement.</p>
  <h3 id="ix-m-longroadhome">The Long Road Home</h3>
  <p><em>Rank 8 · One hour · your whole pool of Faith.</em> Take everyone home. Every soul who has been with you and is
  willing, living or freshly dead or lost or held somewhere else, is brought at once to one place you name that any of you has
  ever called home, safely, together, however far it is and whatever holds them. Doors open. Distances shorten. The dead
  walk in with the rest. It costs you the road: you may not use this again, and you will never afterward be able to
  travel anywhere the ordinary way without knowing exactly how much shorter it could have been.</p>
  <h2 id="ix-m-list-liturgy">The Liturgy</h2>
  <p>The Padre's alone: Latin, sacrament, and the long authority of a Church that has been writing the dark down for eighteen centuries. The words work whether or not the celebrant believes them.</p>
  <h3 id="ix-m-asperges">Asperges Me</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith · Fortitude save.</em> Sprinkle holy water and speak the old antiphon. Each Marked or uncanny thing within reach saves or takes 1d6 and recoils, hissing at the water and the Latin both.</p>
  <h3 id="ix-m-crossing">The Sign of the Cross</h3>
  <p><em>Rank 1 · Reaction · 1 Faith.</em> The oldest gesture in the Church, made in earnest. You or an ally beside you gains +2 against the next uncanny working or fear effect — if the hand is quick enough to make it in time. The blessing holds until it is spent.</p>
  <h3 id="ix-m-litany">The Litany of the Saints</h3>
  <p><em>Rank 2 · One minute · 2 Faith.</em> Call the long roll of the faithful dead, and let the living hear how many stood before them. Every ally who listens gains one reroll against fear, kept until the scene ends or it is spent.</p>
  <h3 id="ix-m-unction">Extreme Unction</h3>
  <p><em>Rank 3 · One minute · 2 Faith.</em> Anoint the dying with oil and the last words. They are stabilized at once, wake with 1d6 Blood, and — whatever comes after — cannot rise as one of the restless dead. The rite is a mercy first and a precaution second, but it is both.</p>
  <h3 id="ix-m-interdict">The Interdict</h3>
  <p><em>Rank 4 · Ten minutes · 4 Faith.</em> Lay the Church's ban upon a place, an object, or a grave. For a day and a night no uncanny thing may enter it, use it, or draw strength from it, as though the ground itself had been forbidden to them by an authority older than their hunger.</p>
  <h3 id="ix-m-tedeum">Te Deum</h3>
  <p><em>Rank 5 · One minute · 5 Faith · Will save.</em> The great hymn of thanksgiving, sung as a weapon. A lesser uncanny thing is banished outright; a greater one saves or is Frightened and Slowed the whole scene; and every soul who kneels and sings with you is eased of the Mark's symptoms for a day. Two thousand years are in the words.</p>
  <h3 id="ix-m-requiem">The Requiem</h3>
  <p><em>Rank 6 · One hour · 6 Faith.</em> Sing the whole of it over a burying ground, a battlefield, a burned house, a
  mine. Every restless dead thing in that place is laid to rest at once and cannot be raised from it again by any means.
  Those who can be told what happened to them are told. Those who cannot are simply let go, which is most of them.</p>
  <h2 id="ix-m-list-revival">The Revival</h2>
  <p>The Preacher's alone: the open Word, the camp meeting, the mourner's bench, and conviction loud enough to be heard over the guns.</p>
  <h3 id="ix-m-mourner">Call to the Mourner's Bench</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith · Will save.</em> Round on one sinner — mortal or monstrous — and call them forward to answer for it. They save or lose their next action, rooted and named before the whole room.</p>
  <h3 id="ix-m-amen">The Amen Corner</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Work the crowd, and let them work back. Allies who can hear you and answer aloud gain +1 to hit for a round. Faith, the Preacher will tell you, is a call and a response.</p>
  <h3 id="ix-m-altarcall">The Altar Call</h3>
  <p><em>Rank 2 · 1 Beat · 2 Faith.</em> Lay hands and call a soul back to itself: heal a touched ally 2d6, and they may at once reroll one save they have just failed. Come forward, the Preacher says. It is not too late — not quite yet.</p>
  <h3 id="ix-m-testify">Testify</h3>
  <p><em>Rank 3 · 1 Beat · 3 Faith · Will save.</em> Speak a true and terrible thing into the silence. One creature saves or is Frightened 2 and made to blurt the last lie it told. The Preacher has found that the guilty fear the truth far worse than the gun. The naming is resolved at once; the fear it leaves lessens a step each turn, as fear does.</p>
  <h3 id="ix-m-campmeeting">The Camp Meeting</h3>
  <p><em>Rank 4 · sustained · 4 Faith.</em> Preach a rolling revival and do not stop. For three rounds, so long as you keep the Word going and take no other action, every ally who can hear you regains Nerve and shakes one condition at the start of each round. The tent shakes. So does the dark outside it.</p>
  <h3 id="ix-m-pentecost">Pentecost</h3>
  <p><em>Rank 5 · 1 Beat · 5 Faith.</em> Tongues of fire, and every ear hearing in its own language. For the scene your Brimstone strikes every uncanny thing you can see at once, and the Marked cannot resist it by their Mark. The fire does not fall often. When it does, it does not ask permission.</p>
  <h3 id="ix-m-wholetownris">The Whole Town Rises</h3>
  <p><em>Rank 6 · One minute · 6 Faith.</em> Preach until the place stands up. Every living soul within earshot who is not
  hostile to you recovers all Blood and Nerve, shakes every condition, and for the next hour will fight, carry, dig or
  stand where you ask them to. They will not do anything they believe is wrong, and afterward they will be very tired
  and will want to know what came over them.</p>
  <h2 id="ix-m-list-spirits">The Spirits</h2>
  <p>The Shaman's alone: not commands but courtesies, asked of the crowded country and its neighbors — beast and weather, river and rock, and the honored dead.</p>
  <h3 id="ix-m-smallword">A Word to the Small Spirits</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Ask the little spirits of a place one plain thing, courteously: where the water lies, who passed this way, what waits in the next draw. They answer plainly, if they answer, and remember that you asked kindly. The answer given, the working is done.</p>
  <h3 id="ix-m-offering">The Offering</h3>
  <p><em>Rank 1 · One minute · 1 Faith.</em> Leave tobacco, salt, or bread, and name the debt. The spirits of that ground grant safe passage, or +2 on one task done there, for as long as the gift is respected and the ground not fouled.</p>
  <h3 id="ix-m-beastgift">Borrow the Beast's Gift</h3>
  <p><em>Rank 2 · 1 Beat · 2 Faith.</em> Ask a nearby animal spirit for the loan of one gift, and wear it for a scene: an owl's eyes in the dark, a wolf's nose, a hare's speed, a bear's thick hide. The spirits lend gladly and expect the courtesy of thanks.</p>
  <h3 id="ix-m-pack">Set the Pack On</h3>
  <p><em>Rank 3 · 1 Beat · 3 Breath.</em> Call whatever hunts this country and point. For one round the creature you named is beset by things that are almost not there: it stands Off-Guard, takes 2d6 at once, and cannot take the Aim. The spirits do not stay, and they will not come twice in one night for the same asking, so choose the moment rather than the enemy.</p>
  <h3 id="ix-m-weather">Turn the Weather</h3>
  <p><em>Rank 3 · One minute · 3 Faith.</em> Coax the sky a step kinder or crueler for the hour — a fog to cover a retreat, a break in the rain, a wind at your back or in the enemy's face. The weather keeps its own counsel and grants the favor, not the command.</p>
  <h3 id="ix-m-snare">The Spirit-Snare</h3>
  <p><em>Rank 4 · 1 Beat · 4 Faith · Will save.</em> Draw the knot that holds a spirit or a restless dead thing fast. It saves or cannot leave the spot until dawn or until you loose it — able to speak, and to rage, and to bargain, but not to go.</p>
  <h3 id="ix-m-greatspirit">Call the Great Spirit</h3>
  <p><em>Rank 5 · One minute · 5 Faith.</em> Call a great spirit of storm, of beast, or of the honored dead, and it answers for a scene, lending its power to your hand without the peril of wearing its mask. It comes as a neighbor answers a knock — because you have kept faith, and because you asked.</p>
  <h3 id="ix-m-councilofdea">The Council of the Dead</h3>
  <p><em>Rank 7 · One hour · 7 Faith.</em> Call the dead of a place together and sit down with them. Every spirit within a
  mile that will come, comes, and they answer honestly for an hour: what was done here, by whom, where it is now, and
  what would settle it. They are not obliged to be kind and they are frequently not. Once in a while one of them asks
  you for something, and then you have a second problem.</p>
  <h2 id="ix-m-list-mending">The Mending</h2>
  <p>The Medicine Man's alone: the quiet, stubborn craft of keeping the wounded alive, one sure mending at a time, so the deep well is there when the worst comes.</p>
  <h3 id="ix-m-poultice">The Poultice</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Press a prepared remedy to the hurt. It heals 1d8 over the next few minutes and costs only the one point — the small, sure mending you lean on so the deep well stays full for worse.</p>
  <h3 id="ix-m-setbone">Set the Bone</h3>
  <p><em>Rank 1 · One minute · 1 Faith.</em> Splint, wrap, and set what is broken. Ease the penalty of one Lasting Injury for a day, buying a wounded soul the working hours the country would sooner deny them.</p>
  <h3 id="ix-m-fever">The Fever Broken</h3>
  <p><em>Rank 2 · One minute · 2 Faith.</em> Sit the long watch and break the fever. End the next worsening of a disease or poison and grant a fresh save against it at +4. Most of doctoring is refusing to let a thing get worse. The watch is kept and the working is done.</p>
  <h3 id="ix-m-healsleep">The Sleep of Healing</h3>
  <p><em>Rank 3 · One minute · 3 Faith.</em> Sing a hurt soul down into a true healing sleep. They recover double from tonight's rest and wake clear of fear and easy of mind, which in this country is the rarer of the two cures. The sleep holds until dawn.</p>
  <h3 id="ix-m-shared">The Life Shared</h3>
  <p><em>Rank 4 · 1 Beat · 4 Faith.</em> Open the well to more than one at once. Divide your healing among every ally you can reach — 2d8 to be shared out as you choose — the mercy spread thin across many rather than poured into one.</p>
  <h3 id="ix-m-longmercy">The Long Mercy</h3>
  <p><em>Rank 5 · 1 Beat · 5 Faith.</em> Hold a mortally hurt soul back from the door for a full day and night without the well draining further, so that a true cure, a hard ride, or a better healer may reach them in time. You cannot mend what took them. You can refuse to let it finish the work today.</p>
  <h3 id="ix-m-bodymadewhol">The Body Made Whole</h3>
  <p><em>Rank 6 · Ten minutes · 6 Faith.</em> Put a person back the way they were made. All Blood restored, every disease,
  poison and Affliction gone, every Lasting Injury undone, limbs and sight and hearing returned. Whatever was done to
  them is not done to them any more. It works once on any one soul, ever, and both of you will know afterward which day
  it was.</p>
  <h2 id="ix-m-list-consecration">The Consecrations</h2>
  <p>The Witch Hunter's alone, and fueled by Zeal rather than a healer's pool: salt, silver, fire, ward, and the litany of weaknesses that turns a hunt into an execution.</p>
  <h3 id="ix-m-saltline">Salt the Threshold</h3>
  <p><em>Rank 1 · One minute · 1 Faith · Will save.</em> Lay a line of blessed salt across a door, a window, a circle of camp. Uncanny things save or cannot cross it until dawn or until the line is broken by a living hand — theirs cannot break it.</p>
  <h3 id="ix-m-weakness">The Litany of Weakness</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Recite what you know of a thing's banes — the silver, the fire, the true name, the running water. Your next Judgment against it deals +1d8, the knowledge sharpening the blow.</p>
  <h3 id="ix-m-silverround">Silver the Round</h3>
  <p><em>Rank 2 · 1 Beat · 2 Faith.</em> Bless and silver-wash a handful of ammunition on the spot. The next three shots fired from it count as silver and blessed for overcoming the uncanny's resistances, whoever pulls the trigger. The blessing holds until those three shots are fired, or until dawn, whichever comes first.</p>
  <h3 id="ix-m-branding">The Branding</h3>
  <p><em>Rank 3 · One minute · 3 Faith · Will save.</em> Mark your quarry with the sign of the hunt. For a day you always know its direction and rough distance, it cannot hide from you by any uncanny means, and it knows, wherever it runs, that it has been marked.</p>
  <h3 id="ix-m-killground">Consecrate the Killing Ground</h3>
  <p><em>Rank 4 · Ten minutes · 4 Faith.</em> Sanctify a patch of ground and make it a trap for the unclean. Within it, uncanny things fight at &minus;2 and cannot flee by any supernatural means — no stepping through shadow, no sinking into earth. What comes onto this ground leaves it on your terms or not at all.</p>
  <h3 id="ix-m-reckoningfire">The Reckoning Fire</h3>
  <p><em>Rank 5 · 1 Beat · 5 Faith · Reflex save.</em> Call a consecrated flame that burns the unclean and spares the rest. Every uncanny thing in a wide reach takes 6d6 holy fire, save for half, and what the fire kills does not rise, reform, or return. The living may stand in it unharmed. The dark has no such luck.</p>
  <h3 id="ix-m-groundmadeho">The Ground Made Holy</h3>
  <p><em>Rank 7 · One hour · 7 Faith.</em> Consecrate ground and mean it permanently. Nothing uncanny may enter, use, or
  draw strength from the bounded place ever again; the Marked feel the boundary from outside; the dead buried in it stay
  buried and quiet. It ends only if the ground is broken deliberately by a living hand, which somebody will eventually
  get around to.</p>
  <h2 id="ix-m-list-vigil">The Vigil</h2>
  <p>The Sister's alone: the work of sitting up with what should not be left alone. It wards, it watches, and it refuses to move, and there is almost nothing in it that will win a fight. That is not what it was written for.</p>
  <h3 id="ix-m-handheld">Hand Held</h3>
  <p><em>Rank 1 · 1 Beat · 1 Faith.</em> Take hold of a soul who has just failed a Dread Check and give them something to hold back. They reroll it at once, and keep the second result even if it is worse. Most take the second result gladly. The ones who do not are why you keep hold a moment longer than they want.</p>
  <h3 id="ix-m-watchkept">The Watch Kept</h3>
  <p><em>Rank 1 · Ten minutes · 1 Faith.</em> Walk the bounds of a camp, a room, a cellar stair, naming what you mean to keep out. Until you sleep or leave, every soul inside takes +2 on Dread Checks, and nothing uncanny crosses the line you walked without you knowing the moment it does. It does not stop anything. It only means you are never the last to find out.</p>
  <h3 id="ix-m-lampunquenched">The Lamp Unquenched</h3>
  <p><em>Rank 2 · 1 Beat · 2 Faith.</em> A flame you have lit cannot be put out for the rest of the scene: not by wind, water, smothering, or anything that walks. Its light does not carry further than a lamp's, and that is the whole of the comfort, but nothing that hates the light can approach within its circle without spending its whole turn to do it.</p>
  <h3 id="ix-m-nothingcomesin">Nothing Comes In</h3>
  <p><em>Rank 3 · One minute · 3 Faith · Will save.</em> Stand in a doorway, a gate, a stair-head, and refuse it. For a scene, anything uncanny that would cross must first make a Will save against your Miracle DC; on a failure it cannot cross at all this round and must spend its turn trying again. It can still reach through. It can still call. It cannot simply walk in, and a great many of them have never had to learn what to do about that.</p>
  <h3 id="ix-m-bodykeptwhole">The Body Kept Whole</h3>
  <p><em>Rank 4 · Ten minutes · 4 Faith.</em> Sit the night with a corpse and keep it. It will not rise, it cannot be raised, called, worn, or spoken through, and nothing may take from it what it carried in life. This holds until the body is buried or burned, and it holds against the thing that made it as surely as against any other. It is the oldest work your order does and the one nobody thanks you for.</p>
  <h3 id="ix-m-notbemoved">She Will Not Be Moved</h3>
  <p><em>Rank 5 · 1 Beat · 5 Faith.</em> For one scene you cannot be moved from where you stand: not shoved, dragged, teleported, banished, swallowed, possessed, charmed, or persuaded. You may still choose to walk, and choosing is the only thing that moves you. One soul you have hold of shares it while you keep hold. What this costs is that you are also standing exactly where everything can find you, for a whole scene, on purpose.</p>
  <h3 id="ix-m-untilmorning">Until Morning</h3>
  <p><em>Rank 7 · One minute · 7 Faith.</em> Sit down with them and say that this is not the night. Until dawn, no soul
  inside the room, the camp or the house may die: the dying do not go, the mortal wound waits, the sickness holds where
  it is. It does not cure any of it and morning still comes. What it buys is the hours, and the hours are usually what
  was wanted.</p>
  <div class="pageno">24</div>
</section>

<section class="page">
  <div class="runhead"><span class="l">XIII. Signs, Miracles &amp; Old Rites</span><span>Blood &amp; Grit</span></div>
  <h2 id="ix-old-rites">The Old Rites</h2>
  <p>Rites are folk-craft, not sorcery — anyone may attempt them with the right materials, time, and a skill check (usually
  Lore: Occult or Survival). They cost no Nerve, but they are slow, and failure has its own price. A <strong>critical
  success</strong> on the check doubles the protection or duration; a <strong>critical failure</strong> spoils the
  materials and may draw the very thing you meant to ward against.</p>
  <ul class="dash">
    <li id="ix-r-rain"><strong>Calling the Rain.</strong> An old song and a day's patience may, or may not, bring weather. The country keeps its own counsel. (DC 20, and the sky owes you nothing.)</li>
    <li id="ix-r-laying"><strong>Laying the Dead.</strong> A proper burial, a true name spoken, an unfinished thing set right — and a restless spirit may rest at last. (DC by the Keeper; some dead bargain hard.)</li>
    <li id="ix-r-bones"><strong>Reading the Bones.</strong> Cast and read them to glimpse one likely danger of the day ahead — vague, and never wrong in the way you hoped. (DC 15.)</li>
    <li id="ix-r-sain"><strong>The Sain.</strong> A blessing over a threshold, a grave, or a frightened soul; eases the next Dread Check by 2. (DC 12.)</li>
    <li id="ix-r-salt"><strong>Warding Salt.</strong> An hour and a pound of graveyard salt lay a line the uncanny is loath to cross until dawn. (Lore: Occult or Survival, DC 15.)</li>
  </ul>

  <div class="box">
    <h3 id="ix-who-works">Who May Work the Dark</h3>
        <p>The four Callings of the <strong>Old Dark</strong> — Hexer, Witch, False Prophet, and Dark Cultist — work
    Signs by their nature, each paying in Nerve, Blood, and the slow accrual of the Mark. A character of any Calling who
    takes the <em>Hedge Magic</em> or <em>Touched</em> Edge (Chapter IX) knows a Sign or two and a small pool to fuel
    them — a worldly soul who has already paid a little. Anyone at all may attempt the <strong>Old Rites</strong>, for they
    are tradition and patience rather than borrowed power. The First Peoples' own ceremonies are <em>not</em> represented by
    these invented Signs and Rites; see the boxes in Chapters IV and VI.</p>
    <p><strong>The Callings of Faith may never work a Sign.</strong> A Preacher, Padre, Shaman, Medicine Man, or Witch
    Hunter draws on faith, rite, and the spirits — never on the Old Dark's borrowed words, which stand opposed to their
    power at the root. A faithful soul may <em>recognize</em> a Sign, <em>resist</em> it, <em>break</em> it, or
    <em>cleanse</em> what it has wrought — much of the Witch Hunter's and the Padre's trade — but they cannot speak one.
    Should one ever truly do so, they have set down their faith entirely, and become something else by the Keeper's hand.</p>
  </div>

  <div class="box">
    <h3 id="ix-unmarked">The Unmarked at the Threshold</h3>
    <p>Now and again a Gunhand finds a dead Hexer's notebook, or a Drifter is taught one word by a thing that should not
    have spoken. A character of a <strong>worldly</strong> Calling — and only a worldly one — may attempt a Sign they have
    somehow learned, but the dark lends nothing to strangers on easy terms:</p>
    <ul class="dash">
      <li><strong>Backlash comes easy.</strong> Backlash strikes on <em>any</em> result that is not a clean success — not only on the Sign's listed trigger — and the Keeper may step its severity up.</li>
      <li><strong>It costs double.</strong> Working the Sign costs <strong>twice its Nerve</strong>; with no Nerve to spend, the shortfall is paid in <strong>Blood</strong>.</li>
      <li><strong>No proficiency.</strong> Lacking the Signs feature, their <strong>Sign DC</strong> (when a Sign forces a save) is only 10 + their RES modifier — no level added.</li>
      <li><strong>The dark remembers.</strong> On the flat check's failure, or on any Backlash, the character takes <strong>Mark 1</strong> (Chapter XII). A soul who makes a habit of this is no longer, in any way that matters, worldly — they have started down the Hexer's road, and the Mark will say so.</li>
      <li><strong>The mind must hold the shape.</strong> Before the Sign manifests, make a <strong>flat check (DC 11)</strong>. On a failure the Nerve or Blood is spent for nothing and the working rebounds anyway.</li>
    </ul>
    <p class="note">This is meant to be rare, costly, and frightening. A Keeper is right to make a player want it badly before the dark will so much as listen.</p>
  </div>

  <div class="quote">
    "Every word I know that the dark answers to, I bought. Not with coin — coin it laughs at —
    but with a piece of the morning I used to be able to stand in. Ask yourself what you have to spend
    before you ask the dark anything at all."
    <span class="src">— from a letter found unsent, signed only "your sister, what's left of her"</span>
  </div>
  <div class="pageno">50</div>
</section>
<section class="page" id="advancement">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>XIV. Advancement</span></div>
  <h1 class="chapter">XIV. Advancement</h1>
  <p class="chapter-sub">What surviving earns you, and what it does not.</p>
  <div class="divider"></div>
  <p class="dropcap lead">You advance by living through things that should have killed you. The Keeper awards experience for
  danger faced, mysteries unraveled, and scenes played true — or simply marks the passing of each hard chapter with a level.
  Either way, growth is slow, and tenth level is a long, unlikely old age for a soul in this country. Past it lies
  a stretch of five more that most tables will never see, and which the book prints anyway; see <em>Past the Tenth</em>
  below for what it is for.</p>
  <p>After the manner of Pathfinder Second Edition, advancement runs on a flat tally: <strong>every level costs 1,000
  experience</strong>. The Keeper awards experience for the dangers you survive and the mysteries you close; when your
  tally reaches 1,000 you gain a level and subtract 1,000, carrying the remainder toward the next.</p>
  <table>
    <thead><tr><th>You earn experience for&hellip;</th><th class="c">Award</th></tr></thead>
    <tbody>
      <tr><td>A trivial brush with danger</td><td class="c">10</td></tr>
      <tr><td>A low, manageable threat</td><td class="c">15</td></tr>
      <tr><td>A moderate, fair-matched danger</td><td class="c">20</td></tr>
      <tr><td>A severe, outmatched fight or horror</td><td class="c">30</td></tr>
      <tr><td>An extreme, should-not-have-survived ordeal</td><td class="c">40</td></tr>
      <tr><td>A story accomplishment or hard scene played true</td><td class="c">10&ndash;30</td></tr>
    </tbody>
  </table>
  <p class="note">A whole level is 1,000 experience however earned — a band climbs one level over many such awards, not
  many thousands. Keepers who prefer may set the tally aside entirely; see below.</p>
  <h2 id="ix-level-brings">What a Level Brings</h2>
  <ul class="dash">
    <li>One <strong>ability score</strong> raised by a point at 5th, 10th, and 15th level.</li>
    <li>Better <strong>attack and saves</strong>, as your Calling's table shows — and as <em>Attack Rank and the Saves</em>, below, lets you reckon without the book.</li>
    <li>More <strong>Blood</strong>: roll your Calling's Hit Die (or take its average) and add your CON modifier.</li>
    <li>New <strong>Calling features</strong>; an Old Dark path (Bargain, Craft, Gospel, or Devotion) deepens at 3rd and 9th; the gifted learn new <strong>Signs</strong> at the listed levels.</li>
    <li>An <strong>Edge</strong> at 1st, 3rd, 5th, 7th, and 9th level, and again at 12th and 14th.</li>
    <li>A <strong>skill increase</strong> at 3rd, 5th, 7th, and 9th level, and again at 11th and 13th, raising one skill's proficiency a step (toward Expert, then Master, as your level allows).</li>
  </ul>
  <h2 id="ix-ranks">Attack Rank and the Saves</h2>
  <p>Two of the figures on your Calling's table follow a plain rule, so you may reckon either in your
  head when the book is not to hand.</p>
  <p><strong>Attack.</strong> Every Calling holds one of three ranks, named on its statline. All three
  climb by one at every level. What the rank fixes is how far behind the gun Callings you stand — and
  that distance never grows.</p>
  <table>
    <thead><tr><th>Rank</th><th>Your attack</th><th>Callings</th></tr></thead>
    <tbody>
      <tr><td>Practiced</td><td>Equal to your level</td><td>Bounty Hunter, Gunhand, Marshal, Mountain Man, Witch Hunter</td></tr>
      <tr><td>Steady</td><td>Your level, less 1</td><td>Drifter, Gambler, Prospector, Sawbones, Medicine Man, Padre, Preacher, Shaman, False Prophet</td></tr>
      <tr><td>Slight</td><td>Your level, less 2 (never below +0)</td><td>Hexer, Witch, Dark Cultist</td></tr>
    </tbody>
  </table>
  <p><strong>Saves.</strong> Your statline names which of your three saves are strong. A <strong>strong
  save is 2 plus half your level</strong>; a <strong>weak save is a third of your level</strong>; both
  round down. Add the keyed ability on top — Fortitude (CON), Reflex (DEX), Will (RES).</p>
  <p>A Hexer will never outshoot a Gunhand, and is not meant to. But the country's teeth grow sharper as
  you climb, and no soul should arrive at a late reckoning unable to hit a barn door for the sole
  crime of having learned to read the dark.</p>

  <h2 id="ix-past-tenth">Past the Tenth</h2>
  <p>Tenth level is where a frontier life tops out. Your path Mastery lands there, your second ability point lands
  there, and the write-up of your Calling's tenth-level feature is written as an ending because for most souls it is
  one. Five more levels are printed after it, and they are a different kind of thing.</p>
  <p>Eleventh through fifteenth is what becomes of somebody who does not stop. The pattern is plain and it is the
  same for every Calling: a feature at 11th, an Edge at 12th, a feature at 13th, an Edge at 14th, and at 15th one
  named thing that only that Calling can do. Sign-workers reach Rank Six at 11th, Seven at 13th, and Eight at 15th.
  Miracle-workers reach the same ranks on the same rungs.</p>
  <p>Read the fifteenth-level entries before you promise a table this band. Every one of them is once a session, every
  one of them changes the situation rather than the arithmetic, and every one of them costs something the character
  does not get back — a year, a memory, a name, a person who trusted you, a mark that will not come off. That is
  deliberate. A soul who has gone this far past a frontier life has not been getting stronger for free, and the
  fifteenth-level entry is the book saying out loud what the bill has been.</p>
  <p class="note">Most campaigns end somewhere between 6th and 10th, and nothing is missing from one that does. Treat
  11th through 15th as the long ending you play toward once, with a table that has been together a while.</p>

  <h2 id="ix-milestones">Milestones over Tallies</h2>
  <p>Many Keepers dispense with counting experience and simply raise the whole party a level when the story turns a corner —
  a survived winter, a mystery closed, a town saved or lost. This keeps the table together and the bookkeeping light. Use
  whichever way keeps your people leaning forward.</p>

  <div class="quote">
    "They call it getting older. Out here it is only getting <em>kept</em> — by luck, by friends, by the dark
    deciding it is not done with you. Do not mistake survival for a reward. It is a stay of execution, and the
    court does not adjourn."
    <span class="src">— Rev. Amos Teague, a sermon preached to four graves and one mourner</span>
  </div>
  <div class="pageno">51</div>
</section>

<section class="page" id="play">
  <div class="runhead"><span class="l">A. Appendix: An Example of Play</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">A. Appendix: An Example of Play</h1>
  <p class="chapter-sub">How it sounds at the table on a bad night.</p>
  <div class="divider"></div>
  <div class="quote">
    &ldquo;You want to know how the game goes? It goes fine, right up until it doesn't, and then
    it goes very fast. Listen close to this next part.&rdquo;
    <span class="src">&mdash; overheard at a Leadwater table</span>
  </div>
  <p class="note">Three players sit with their Keeper. <strong>Cassidy</strong> plays Reverend Amos Teague, a Preacher;
  <strong>Lee</strong> plays the Drifter called Magpie; <strong>Sam</strong> plays Dr. Esther Vane, a Sawbones. They have
  followed a child's screaming to a sod house on the flats at dusk.</p>

  <p><strong>Keeper:</strong> The door hangs open. Inside it's black, and the screaming stopped the moment you dismounted.
  There's a smell — copper and wet wool. Magpie, you're first to the threshold. Give me a Notice check.</p>
  <p><strong>Lee:</strong> Twelve plus five — seventeen.</p>
  <p><strong>Keeper:</strong> Seventeen. The dirt floor is dark and shining all the way to the back wall, and it's running
  <em>uphill</em>, toward a shape in the corner that's too tall to be a child. Roll me a Dread Check — Will save, DC sixteen.</p>
  <p><strong>Lee:</strong> …Nine. That's a fail.</p>
  <p><strong>Keeper:</strong> You lose 1d6 Nerve — four. You're down to three, and you're Frightened. The shape turns its head
  without turning its body. What do you do?</p>
  <p><strong>Cassidy:</strong> I push past Magpie — gently — and hold up the book. I spend a Conviction and start the Sermon.
  Loud. "You are not welcome at this hearth."</p>
  <p><strong>Keeper:</strong> Good. Everyone who can hear you, take back Nerve equal to Amos's Presence — that's three.
  Magpie, you're back to six and the shake leaves your hands. The thing in the corner… flinches from the words. Esther,
  it's between you and the crying you can now hear again, under the floor.</p>
  <p><strong>Sam:</strong> Under the floor. Of course it is. I draw the derringer — that's one Beat — and I use my second to
  Aim. I tell Amos to keep talking.</p>
  <p><strong>Keeper:</strong> The derringer's a Concealable iron, so the draw and the Strike could come together if you'd
  rather — but Aiming first is the wiser play. Hold that +2. Amos, the Sermon's still going; the thing has not crossed the
  salt of the doorsill. Roll me your next round of Nerve, all of you. The floorboards are starting to lift.</p>

  <p class="note">Note how the dice escalate dread, how the Preacher spends a resource to buy the party's Nerve back, how
  the Iron Code's Beats let Esther trade speed for a steadier shot, and how the Keeper narrates mechanics as sensation —
  never "you take four psychic damage," always the head that turns the wrong way.</p>
  <div class="pageno">52</div>
</section>

<section class="page" id="conditions">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>B. Appendix: Conditions</span></div>
  <h1 class="chapter">B. Appendix: Conditions</h1>
  <p class="chapter-sub">A glossary of the ways a body and mind can fail.</p>
  <div class="divider"></div>
  <div class="quote">
    &ldquo;There's a hundred ways to come apart out here, and the country will show you every one
    if you give it the season. Best you learn their names before they learn yours.&rdquo;
    <span class="src">&mdash; Doc A. Mercer</span>
  </div>
  <table>
    <thead><tr><th>Condition</th><th>Effect</th></tr></thead>
    <tbody>
      <tr><td>Bleeding</td><td>Lose 1 Blood each round until stabilized</td></tr>
      <tr><td>Blinded</td><td>–4 Defense, –4 most actions, lose DEX to Defense, half Speed</td></tr>
      <tr><td>Clumsy</td><td>–2 on DEX-based Strikes, checks, and Defense</td></tr>
      <tr><td>Drained</td><td>–2 on Fortitude and CON checks, and lose Blood equal to your level, until recovered</td></tr>
      <tr><td>Dying</td><td>At 0 Blood; unconscious and Bleeding toward –CON and death</td></tr>
      <tr><td>Enfeebled</td><td>–2 on STR-based Strikes, damage, and checks; carry half what you could</td></tr>
      <tr><td>Fatigued</td><td>–2 on checks and saves; cannot Aim or run; rest to shed it</td></tr>
      <tr id="ix-frightened"><td>Frightened</td><td>–1 (or worse) on everything; lessens by one step each turn as you master the fear</td></tr>
      <tr><td>Grabbed</td><td>Held fast; Off-Guard; –4 DEX; a check to break free</td></tr>
      <tr><td>Lost</td><td>Mark 6; the character passes into the Keeper's hands</td></tr>
      <tr><td>Marked</td><td>Stepped along the Mark track; see Chapter XII</td></tr>
      <tr><td>Off-Guard</td><td>–2 to your Defense; you cannot properly defend (unaware, flanked, sprawled, or caught unready)</td></tr>
      <tr><td>Prone</td><td>–4 to melee; +4 to others' ranged against you; rising costs a Beat</td></tr>
      <tr><td>Sickened</td><td>–2 on Strikes, damage, checks, and saves; nausea</td></tr>
      <tr><td>Slowed 1</td><td>Lose one Beat each turn while it lasts; may still defend</td></tr>
      <tr><td>Stunned</td><td>Drop what you hold; lose all Beats this round; –2 Defense</td></tr>
    </tbody>
  </table>
  <div class="pageno">53</div>
</section>

<section class="page" id="quickref">
  <div class="runhead"><span class="l">C. Appendix: Quick Reference</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">C. Appendix: Quick Reference</h1>
  <p class="chapter-sub">The whole machine on a single page.</p>
  <div class="divider"></div>
  <div class="box gold">
    <h4>The Core Roll</h4>
    <p>d20 + ability mod + proficiency ≥ DC. Beat by 10 or a natural 20 is a critical; miss by 10 or a natural 1 is a critical failure.</p>
  </div>
  <p><strong>Difficulty.</strong> Trivial 10 · Easy 13 · Average 15 · Hard 18 · Very Hard 20 · Punishing 25 · Beyond 30.</p>
  <p><strong>Abilities.</strong> STR, DEX, CON, Wits, Resolve, Presence. Modifier = (score – 10) ÷ 2, rounded down.</p>
  <p><strong>Saves.</strong> Fortitude (CON), Reflex (DEX), Will (RES). Base from Calling + ability.</p>
  <p><strong>In a Fight (the Iron Code).</strong> Initiative: a Notice check. Each turn has <strong>three Beats</strong>: Strike,
  Stride, Aim/Brace, Interact, Reload, Take Cover. Strike = d20 + attack proficiency + DEX/STR vs Defense. Multiple Attack Penalty
  –5/–10 (Agile –4/–8). Four degrees of success; a crit applies the weapon's Fatal die.</p>
  <p><strong>Blood.</strong> 0 = Dying and Bleeding. Death at –CON. Half-max in one hit, or any crit, risks a Lasting Injury.</p>
  <p><strong>Grit (3 / session).</strong> Add 1d6 · reroll · shrug off a fright · stay up at 0 Blood · soften a critical failure.</p>
  <p><strong>Nerve.</strong> Max = RES + level. Failed Dread Check loses Nerve; 0 Nerve breaks you. The Mark has six steps;
  the sixth is Lost.</p>
  <div class="quote">
    "Keep your powder dry, your salt close, and your accounts with the dark paid up.
    The country settles every debt in the end."
    <span class="src">— the last line of the field manual, in every edition</span>
  </div>
  <div class="pageno">54</div>
</section>

<!-- ===================== D. APPENDIX: A POSSE, READY-MADE ===================== -->
<section class="page" id="posse">
  <div class="runhead"><span class="l">D. Appendix: A Posse, Ready-Made</span><span>Blood &amp; Grit</span></div>
  <h1 class="chapter">D. Appendix: A Posse, Ready-Made</h1>
  <p class="chapter-sub">Six souls built and waiting, for the table that wants to ride tonight.</p>
  <div class="divider"></div>
  <p class="lead">Character-making is a pleasure, but it is an hour's pleasure, and some nights the dark won't wait.
  Here are six finished souls &mdash; one from most walks of this book &mdash; built with the Honest Array and their
  Origin gifts, outfitted, and carrying their Four Questions already answered. Take one as written, rename it, or use
  it as a pattern. Any four of them make a sound posse; all six make a crowded and interesting one.</p>

  <div class="box">
    <h4>Ruth &ldquo;Six-Finger&rdquo; Calloway &mdash; Gunhand &middot; the Outlaw</h4>
    <p class="note">There is paper on her in two territories and a sixth finger of scar down her draw hand. She is faster than her reputation, which is saying something.</p>
    <p><strong>STR</strong> 13 (+1) &middot; <strong>DEX</strong> 16 (+3) &middot; <strong>CON</strong> 14 (+2) &middot; <strong>WIT</strong> 10 (+0) &middot; <strong>RES</strong> 12 (+1) &middot; <strong>PRE</strong> 9 (&minus;1)</p>
    <p><strong>Blood</strong> 12 &middot; <strong>Defense</strong> 13 &middot; <strong>Saves</strong> Fort +4, Ref +5, Will +1 &middot; <strong>Nerve</strong> 13 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +1 (guns +4 with DEX) &middot; single-action revolver 1d8 (Fatal d10), knife 1d4 &middot; <strong>Armor</strong> heavy duster (DR 1 vs blades &amp; small shot)</p>
    <p><strong>Trained:</strong> Notice, Intimidate. <strong>Features:</strong> Deadly Aim (&minus;2 attack / +4 damage), Gunhand's Edge. <strong>Edges:</strong> Quick Draw, Steady Shot. <strong>Perk:</strong> Let Him Draw First.</p>
    <p><strong>Gear:</strong> revolver, 40 cartridges, knife, duster, a horse she didn't pay for, $9.</p>
    <p class="note"><strong>Lost:</strong> her gang, to a job gone wrong she didn't plan. <strong>Seen:</strong> the man she shot at Careless Creek stand back up. <strong>Vice:</strong> the cards. <strong>Moving:</strong> the paper on her, and whoever's carrying it this month.</p>
  </div>

  <div class="box">
    <h4>Doc Aurelia Mercer &mdash; Sawbones &middot; the Fallen Gentry</h4>
    <p class="note">A surgeon's hands, a ruined family name, and a habit of talking to patients who have stopped listening. Politer than anyone this far west has a right to be.</p>
    <p><strong>STR</strong> 8 (&minus;1) &middot; <strong>DEX</strong> 12 (+1) &middot; <strong>CON</strong> 13 (+1) &middot; <strong>WIT</strong> 16 (+3) &middot; <strong>RES</strong> 14 (+2) &middot; <strong>PRE</strong> 11 (+0)</p>
    <p><strong>Blood</strong> 9 &middot; <strong>Defense</strong> 11 &middot; <strong>Saves</strong> Fort +3, Ref +1, Will +4 &middot; <strong>Nerve</strong> 15 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +0 &middot; knife 1d4, cap-and-ball revolver 1d8 (slow reload) &middot; <strong>Armor</strong> good coat (DR 1 vs blades &amp; small shot)</p>
    <p><strong>Trained:</strong> Medicine, Lore (Occult), Notice, Deceive, Survival, Sleight, Insight, Lore (Frontier), Persuade. <strong>Features:</strong> Field Surgery, Anatomist. <strong>Edge:</strong> Frontier Medicine. <strong>Perk:</strong> Not On My Table.</p>
    <p><strong>Gear:</strong> surgeon's kit, laudanum, good coat, worn revolver, $14 and a letter of unpaid debt.</p>
    <p class="note"><strong>Lost:</strong> the name, the house, the inheritance &mdash; a scandal she will not discuss. <strong>Seen:</strong> a body on her table open its eyes, four hours dead. <strong>Vice:</strong> laudanum. <strong>Moving:</strong> the debt, and the man back east who holds it.</p>
  </div>

  <div class="box">
    <h4>Brother Elias Crow &mdash; Preacher &middot; the Freed</h4>
    <p class="note">Took his freedom, took the Word, and walked west preaching to whoever the country hadn't killed yet. His voice can fill a canyon, and has.</p>
    <p><strong>STR</strong> 10 (+0) &middot; <strong>DEX</strong> 8 (&minus;1) &middot; <strong>CON</strong> 13 (+1) &middot; <strong>WIT</strong> 12 (+1) &middot; <strong>RES</strong> 15 (+2) &middot; <strong>PRE</strong> 16 (+3)</p>
    <p><strong>Blood</strong> 9 &middot; <strong>Defense</strong> 9 &middot; <strong>Saves</strong> Fort +3, Ref &minus;1, Will +4 &middot; <strong>Nerve</strong> 16 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +0 &middot; walking staff 1d4, double-barrel shotgun 2d8 (Scatter, kept wrapped in oilcloth and prayer) &middot; <strong>Armor</strong> none</p>
    <p><strong>Trained:</strong> Persuade, Intimidate, Lore (Occult), Notice, Insight. <strong>Features:</strong> Conviction (pool 3), Sermon. <strong>Miracles known:</strong> The Steadying Word, Call to the Mourner's Bench (both Rank 1). <strong>Miracle DC</strong> 13. <strong>Edge:</strong> Iron Will. <strong>Perk:</strong> A Crowd Where You Stand.</p>
    <p><strong>Gear:</strong> Bible, salt, camp kit, the shotgun, $11 and a congregation's last collection.</p>
    <p class="note"><strong>Lost:</strong> his congregation, to a fire that did not behave like fire. <strong>Seen:</strong> what set it &mdash; and it saw him. <strong>Vice:</strong> pride in the Word. <strong>Moving:</strong> the thing that burned his church went west, and so, therefore, did he.</p>
  </div>

  <div class="box">
    <h4>Anni Halvorsen &mdash; Mountain Man &middot; the Scout</h4>
    <p class="note">Thirty winters in the high country and a Hawken older than most towns. Speaks four languages and prefers none of them.</p>
    <p><strong>STR</strong> 15 (+2) &middot; <strong>DEX</strong> 11 (+0) &middot; <strong>CON</strong> 14 (+2) &middot; <strong>WIT</strong> 12 (+1) &middot; <strong>RES</strong> 14 (+2) &middot; <strong>PRE</strong> 8 (&minus;1)</p>
    <p><strong>Blood</strong> 12 &middot; <strong>Defense</strong> 10 &middot; <strong>Saves</strong> Fort +4, Ref +0, Will +4 &middot; <strong>Nerve</strong> 15 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +1 &middot; Hawken rifle 1d12 (Dead Aim +1d6), bowie knife 1d4 &middot; <strong>Armor</strong> buffalo coat (DR 1 vs blades &amp; small shot)</p>
    <p><strong>Trained:</strong> Survival, Notice, Athletics, Stealth, Animal Handling, Lore (Frontier), Medicine. <strong>Features:</strong> Hawken Rifle, Dead Aim 1d6, Hard Country. <strong>Edge:</strong> Tracker. <strong>Perk:</strong> Half a Wild Thing.</p>
    <p><strong>Gear:</strong> the Hawken, traps, pelts worth 2d6 &times; $10, a buffalo coat, a good knife, a better dog.</p>
    <p class="note"><strong>Lost:</strong> her trapping partner, to a winter that was not a winter. <strong>Seen:</strong> its tracks &mdash; man-shaped, and forty feet apart. <strong>Vice:</strong> solitude, and the flask that makes it bearable. <strong>Moving:</strong> she is hunting it. She does not say so.</p>
  </div>

  <div class="box">
    <h4>Addison Quill &mdash; Bounty Hunter &middot; the Veteran</h4>
    <p class="note">Rode with the cavalry, kept the carbine, and found that hunting men paid better than soldiering and asked fewer questions he couldn't answer.</p>
    <p><strong>STR</strong> 13 (+1) &middot; <strong>DEX</strong> 15 (+2) &middot; <strong>CON</strong> 11 (+0) &middot; <strong>WIT</strong> 14 (+2) &middot; <strong>RES</strong> 13 (+1) &middot; <strong>PRE</strong> 8 (&minus;1)</p>
    <p><strong>Blood</strong> 8 &middot; <strong>Defense</strong> 12 &middot; <strong>Saves</strong> Fort +0, Ref +4, Will +3 &middot; <strong>Nerve</strong> 14 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +1 (guns +3 with DEX) &middot; service carbine 1d10, revolver 1d8, rope and irons &middot; <strong>Armor</strong> none</p>
    <p><strong>Trained:</strong> Notice, Stealth, Survival, Intimidate, Insight, Lore (Frontier), Athletics, Deceive. <strong>Features:</strong> Bushwhack 1d6, Quick Hands. <strong>Edge:</strong> Cold Read. <strong>Perk:</strong> Paper on Him.</p>
    <p><strong>Gear:</strong> carbine, irons, wanted papers, field glasses, $22 of the last bounty.</p>
    <p class="note"><strong>Lost:</strong> the certainty the war promised him. <strong>Seen:</strong> a man he'd buried collect his own bounty in the next county. <strong>Vice:</strong> violence, arrived at too easily. <strong>Moving:</strong> one name left on a private list, and it keeps moving west.</p>
  </div>

  <div class="box">
    <h4>Opal Vance &mdash; Hexer &middot; the Homesteader</h4>
    <p class="note">Buried a husband and three children under sod she broke herself, and one night the country offered her a different arrangement. She took it. She is still deciding what it took back.</p>
    <p><strong>STR</strong> 8 (&minus;1) &middot; <strong>DEX</strong> 10 (+0) &middot; <strong>CON</strong> 13 (+1) &middot; <strong>WIT</strong> 14 (+2) &middot; <strong>RES</strong> 16 (+3) &middot; <strong>PRE</strong> 13 (+1)</p>
    <p><strong>Blood</strong> 7 &middot; <strong>Defense</strong> 10 &middot; <strong>Saves</strong> Fort +1, Ref +0, Will +5 &middot; <strong>Nerve</strong> 17 &middot; <strong>Grit</strong> 3</p>
    <p><strong>Attack</strong> +0 &middot; kitchen knife 1d4, and the Signs she paid for &middot; <strong>Armor</strong> none</p>
    <p><strong>Trained:</strong> Lore (Occult), Medicine, Survival, Notice, Animal Handling, Deceive. <strong>Features:</strong> Witch-Sight, Signs, Marked. <strong>Signs known:</strong> Salt &amp; Iron, The Lender's Ear (both Rank 1 — all a 1st-level soul may reach). <strong>Sign DC</strong> 13. <strong>Edge:</strong> Salt-Wise. <strong>Perk:</strong> Your Debts Are Public.</p>
    <p><strong>Gear:</strong> herb satchel, salt, iron nails, charm-makings, a crow named Deuteronomy, $6.</p>
    <p class="note"><strong>Lost:</strong> everything the sod could take, and then the man too. <strong>Seen:</strong> what answered the night she asked &mdash; she carries <strong>Mark 1</strong>, and knows it. <strong>Vice:</strong> the bargains; they keep working. <strong>Moving:</strong> paying it back before it comes to collect.</p>
  </div>

  <div class="quote"><p>&ldquo;Six strangers on one stage, and every one of them lying about why. Out here that is what we call a fair start.&rdquo;</p><p class="src">&mdash; overheard at the Wells Fargo office, Dry Season, 1885</p></div>
</section>

<!-- ===================== E. APPENDIX: PERDITION BASIN ===================== -->
<section class="page" id="basin">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>E. The Country</span></div>
  <h1 class="chapter">E. Appendix: The Country</h1>
  <p class="chapter-sub">Perdition Basin &mdash; a stretch of frontier to start your riding, drawn as a rider knows it.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Your Keeper may set you down anywhere; the country is wide. But if you want a place to begin
  &mdash; a map to point at and say <em>there, that is where we met</em> &mdash; here is one, ready-made.
  <strong>Perdition Basin</strong> is a hard, dry county in the territory: a bowl of grass and dust ringed by mesa and
  badland, its life strung along the failing Calvary River and the scattered wells that are the only sure water for a
  day's ride in any direction. This is the honest map &mdash; the country as any soul who has ridden it could scratch it
  in the dirt. What waits under it is the Keeper's business, and no concern of yours until it is.</p>

  <!--PERDITION_MAP-->

  <h2 id="ix-basin-country">What a Rider Knows</h2>
  <p>A few days' ride takes you across the whole of it. The places you will hear named:</p>
  <ul class="dash">
    <li><strong>Calvary Crossing</strong> &mdash; the county seat, where the Stage Road fords the river. A marshal, a
    bank, a doctor, a second street, and the closest thing to safe: its well still runs sweet. Where you resupply, and
    where you hear the county's talk.</li>
    <li><strong>Coffin Wells</strong> &mdash; a shrinking cattle town south and west, named for its boot-hill and its
    wells both. Hard luck lately; folks speak low of a fever out at the homesteads.</li>
    <li><strong>Saltlick Station</strong> &mdash; a lonely stage relay a hard day north and east, the last roof for
    twenty miles when the weather turns. A meal, a bed, and a bar across the door.</li>
    <li><strong>Mission San Clavo</strong> &mdash; a broken adobe church east of Coffin Wells, a ruin fifty years, and
    the oldest thing the settlers built here. The old folks still cross themselves when they pass it.</li>
    <li><strong>the Painted Mesa</strong> &mdash; red rock in the south-east, the ground of the people who were in this
    country long before the mission, and who know it better than any deed-holder. Ride there with your hat in your hand
    or not at all.</li>
    <li><strong>the Badlands</strong> &mdash; broken, waterless country to the south, where the river dies in the sand.
    People go in for shortcuts and to not be found. Some manage both.</li>
  </ul>
  <p>And everywhere between, the <strong>wells</strong>: hand-dug, ringed with stone, the whole reason a town or a
  homestead sits where it does. Water is the wealth of this country, and lately &mdash; the old-timers will tell you, if
  you stand them a drink &mdash; some of the wells have <em>gone sour</em>. The drought, they say. Most likely it is the
  drought.</p>

  <h2 id="ix-basin-talk">What Folks Say</h2>
  <p>Ride the basin a while and you will hear all of this, some of it more than once:</p>
  <ul>
    <li>&ldquo;Don't water your stock at the Coffin Wells trough. Don't matter why. Just don't.&rdquo;</li>
    <li>&ldquo;The Vane bank's buying up every homestead whose well's gone bad. Paying, too. You have to wonder what a
    man wants with dry land.&rdquo;</li>
    <li>&ldquo;Old Padre out at San Clavo never left when the mission closed. Still out there. Folks that carry him
    supplies say he's digging.&rdquo;</li>
    <li>&ldquo;Railroad's coming through. That's what the powder-noise is, up in the north country. Progress, the man
    from the survey office calls it.&rdquo;</li>
    <li>&ldquo;My granddad rode for the Mesa people one winter. Said they've got a spring that never once went dry nor
    sour, and a reason they don't share the water. He wouldn't say the reason.&rdquo;</li>
  </ul>
  <p class="note">A place to start, and no more than that. Everything here is true as far as a rider knows it &mdash; which
  in this country is never quite far enough.</p>

  <div class="narr">And that concludes the matter of the country. You came to these pages, most likely,
  for a game about the West &mdash; and you have one: the cattle and the coin are real, the winters are
  honest, and the dice fall fair. But you have read this far, and so you know now what the first chapter
  only whispered. The almanac is therefore offered &mdash; as the survey men say &mdash; for your
  consideration. Keep your fire lit. Keep your accounts square. And if some evening on the long grass you
  find that the silence has a texture to it, you will not need this book to tell you what you have found.
  You will only need to decide, as every soul in these pages once decided, how much of yourself you are
  willing to trade to be believed.</div>
</section>

<section class="page" id="ledger">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>The Ledger</span></div>
  <h1 class="chapter" style="text-align:center;">The Ledger</h1>
  <p class="chapter-sub" style="text-align:center;">A Reckoning of One Soul — Blood and Grit</p>
  <div class="divider"></div>

  <div class="sheet-row">
    <div class="field grow"><label>Name</label><div class="blank"></div></div>
    <div class="field"><label>Calling</label><div class="blank"></div></div>
    <div class="field"><label>Level</label><div class="blank"></div></div>
    <div class="field"><label>Origin</label><div class="blank"></div></div>
  </div>

  <div class="sheet-row abilities">
    <div class="abil"><label>Strength</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
    <div class="abil"><label>Dexterity</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
    <div class="abil"><label>Constitution</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
    <div class="abil"><label>Wits</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
    <div class="abil"><label>Resolve</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
    <div class="abil"><label>Presence</label><div class="ab-grid"><span>Score</span><span>Mod</span></div></div>
  </div>

  <div class="sheet-row">
    <div class="field"><label>Blood / Max</label><div class="blank"></div></div>
    <div class="field"><label>Defense</label><div class="blank"></div></div>
    <div class="field"><label>Speed</label><div class="blank"></div></div>
    <div class="field"><label>Init.</label><div class="blank"></div></div>
    <div class="field"><label>Attack</label><div class="blank"></div></div>
    <div class="field"><label>Grit</label><div class="blank"></div></div>
  </div>
  <div class="sheet-row">
    <div class="field grow"><label>Fortitude Save</label><div class="blank"></div></div>
    <div class="field grow"><label>Reflex Save</label><div class="blank"></div></div>
    <div class="field grow"><label>Will Save</label><div class="blank"></div></div>
    <div class="field grow"><label>Nerve / Max</label><div class="blank"></div></div>
  </div>

  <div class="sheet-row mark-row">
    <label class="mark-label">The Mark</label>
    <span class="mark-box">1</span><span class="mark-box">2</span><span class="mark-box">3</span>
    <span class="mark-box">4</span><span class="mark-box">5</span><span class="mark-box lost">6</span>
  </div>


  <div class="sheet-row">
    <div class="field grow">
      <label>The Four Questions</label>
      <p class="note" style="margin:.2rem 0 .4rem;">What did you lose? &middot; What keeps you moving? &middot; What is your vice? &middot; What have you seen?</p>
      <div class="bigblank" style="height:178px; margin-bottom:0;"></div>
    </div>
  </div>

  <div class="sheet-cols">
    <div class="sheet-col">
      <h4>Skills (mark proficiency)</h4>
      <ul class="skill-list">
        <li><span class="tick"></span> Acrobatics (DEX)</li>
        <li><span class="tick"></span> Animal Handling (PRE)</li>
        <li><span class="tick"></span> Athletics (STR)</li>
        <li><span class="tick"></span> Deceive (PRE)</li>
        <li><span class="tick"></span> Gamble (PRE)</li>
        <li><span class="tick"></span> Insight (RES)</li>
        <li><span class="tick"></span> Intimidate (PRE)</li>
        <li><span class="tick"></span> Lore: Frontier (WIT)</li>
        <li><span class="tick"></span> Lore: Occult (WIT)</li>
        <li><span class="tick"></span> Medicine (WIT)</li>
        <li><span class="tick"></span> Notice (RES)</li>
        <li><span class="tick"></span> Persuade (PRE)</li>
        <li><span class="tick"></span> Repair (WIT)</li>
        <li><span class="tick"></span> Ride (DEX)</li>
        <li><span class="tick"></span> Sleight (DEX)</li>
        <li><span class="tick"></span> Stealth (DEX)</li>
        <li><span class="tick"></span> Survival (RES)</li>
      </ul>
    </div>
    <div class="sheet-col">
      <h4>Edges, Calling Features &amp; Path</h4>
      <div class="bigblank" style="height:300px;"></div>
      <h4>Arms, Gear &amp; Coin</h4>
      <div class="bigblank" style="height:300px; margin-bottom:0;"></div>
    </div>
  </div>
  <div class="pageno">55</div>
</section>

<!-- ===================== INDEX ===================== -->
<section class="page" id="index">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>Index</span></div>
  <h1 class="chapter">Index</h1>
  <p class="chapter-sub">Every rule in its place, and the page where it waits.</p>
  <div class="divider"></div>
  <ul class="ix">
    <li class="ix-hd">A</li>
    <li><a href="#ix-abilities">Abilities, the six</a><span class="pg">19</span></li>
    <li><a href="#ix-level-brings">Ability boosts</a><span class="pg">208</span></li>
    <li><a href="#advancement">Advancement</a><span class="pg">207</span></li>
    <li><a href="#ix-afflictions">Afflictions, lasting</a><span class="pg">183</span></li>
    <li><a href="#ix-aid">Aid (Helping)</a><span class="pg">138</span></li>
    <li><a href="#ix-aim-two">Aim, two Strikes against three</a><span class="pg">174</span></li>
    <li><a href="#ix-aiming">Aiming &amp; bracing</a><span class="pg">174</span></li>
    <li><a href="#ix-alienist">Alienist (Sawbones)</a><span class="pg">74</span></li>
    <li><a href="#ix-m-altarcall">Altar Call, the (Miracle)</a><span class="pg">107</span></li>
    <li><a href="#ix-m-amen">Amen Corner, the (Miracle)</a><span class="pg">107</span></li>
    <li><a href="#ix-spec-rounds">Ammunition &amp; specialty rounds</a><span class="pg">158</span></li>
    <li><a href="#ix-special-ammo">Ammunition, special — silver &amp; blessed</a><span class="pg">155</span></li>
    <li><a href="#ix-m-anoint">Anoint the Iron (Miracle)</a><span class="pg">104</span></li>
    <li><a href="#ix-answering">Answering a working (counter)</a><span class="pg">175</span></li>
    <li><a href="#ix-armor">Armor</a><span class="pg">152</span></li>
    <li><a href="#ix-artifacts">Artifacts &amp; relics of power</a><span class="pg">167</span></li>
    <li><a href="#ix-s-askline">Ask the Line (Sign)</a><span class="pg">203</span></li>
    <li><a href="#ix-m-asperges">Asperges Me (Miracle)</a><span class="pg">105</span></li>
    <li class="ix-hd">B</li>
    <li><a href="#signs">Backlash</a><span class="pg">191</span></li>
    <li><a href="#ix-o-banker">Banker, the (Origin)</a><span class="pg">25</span></li>
    <li><a href="#ix-signs-bargain">Bargain, the (Sign list)</a><span class="pg">197</span></li>
    <li><a href="#ix-beats">Beats, the three</a><span class="pg">171</span></li>
    <li><a href="#ix-s-contract">Black Contract, the (Sign)</a><span class="pg">199</span></li>
    <li><a href="#ix-blades">Blades &amp; bludgeons</a><span class="pg">152</span></li>
    <li><a href="#ix-wounds">Bleeding</a><span class="pg">177</span></li>
    <li><a href="#ix-m-road">Blessing of the Road, the (Miracle)</a><span class="pg">103</span></li>
    <li><a href="#ix-wounds">Blood (hit points)</a><span class="pg">177</span></li>
    <li><a href="#ix-m-bodykeptwhole">Body Kept Whole, The (Miracle)</a><span class="pg">114</span></li>
    <li><a href="#ix-rel-fiddle">Bone Fiddle, the (artifact)</a><span class="pg">169</span></li>
    <li><a href="#ix-e-born-lucky">Born Lucky (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-m-beastgift">Borrow the Beast's Gift (Miracle)</a><span class="pg">109</span></li>
    <li><a href="#ix-s-breath">Borrowed Breath (Sign)</a><span class="pg">195</span></li>
    <li><a href="#ix-s-borrowedface">Borrowed Face, the (Sign)</a><span class="pg">199</span></li>
    <li><a href="#ix-c-bounty">Bounty Hunter (Calling)</a><span class="pg">41</span></li>
    <li><a href="#ix-m-branding">Branding, the (Miracle)</a><span class="pg">112</span></li>
    <li><a href="#ix-breaking">Breaking (0 Nerve)</a><span class="pg">182</span></li>
    <li><a href="#ix-s-brewing">Brewing, the (Sign)</a><span class="pg">202</span></li>
    <li class="ix-hd">C</li>
    <li><a href="#ix-m-greatspirit">Call the Great Spirit (Miracle)</a><span class="pg">109</span></li>
    <li><a href="#ix-m-mourner">Call to the Mourner's Bench (Miracle)</a><span class="pg">107</span></li>
    <li><a href="#ix-r-rain">Calling the Rain (Rite)</a><span class="pg">204</span></li>
    <li><a href="#ix-s-calling">Calling, the (Sign)</a><span class="pg">200</span></li>
    <li><a href="#faith">Callings of Faith</a><span class="pg">76</span></li>
    <li><a href="#hexer">Callings of the Old Dark</a><span class="pg">115</span></li>
    <li><a href="#callings">Callings, worldly</a><span class="pg">40</span></li>
    <li><a href="#ix-o-wrong">Came Back Wrong (Origin)</a><span class="pg">31</span></li>
    <li><a href="#ix-camp">Camp &amp; the trail, the</a><span class="pg">160</span></li>
    <li><a href="#ix-m-campmeeting">Camp Meeting, the (Miracle)</a><span class="pg">108</span></li>
    <li><a href="#ix-rel-cartographer">Cartographer's Eye, the (artifact)</a><span class="pg">167</span></li>
    <li><a href="#ix-s-catserrand">Cat's Errand (Sign)</a><span class="pg">202</span></li>
    <li><a href="#character">Character creation</a><span class="pg">17</span></li>
    <li><a href="#ix-charge">Charge, the (mounted)</a><span class="pg">178</span></li>
    <li><a href="#ix-charms">Charms &amp; lesser relics</a><span class="pg">164</span></li>
    <li><a href="#ix-checks">Checks, saves &amp; opposed rolls</a><span class="pg">13</span></li>
    <li><a href="#ix-rel-nail">Church-Door Nail (relic)</a><span class="pg">166</span></li>
    <li><a href="#ix-clothing">Clothing &amp; the cold</a><span class="pg">159</span></li>
    <li><a href="#ix-s-coinpain">Coin of Pain (Sign)</a><span class="pg">198</span></li>
    <li><a href="#ix-s-coldlamp">Cold Lamp (Sign)</a><span class="pg">194</span></li>
    <li><a href="#ix-e-cold-read">Cold Read (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-m-list-blessing">Common Blessings, the (Miracles)</a><span class="pg">102</span></li>
    <li><a href="#ix-signs-common">Common Signs, the</a><span class="pg">193</span></li>
    <li><a href="#ix-compass">Compass, the (alignment)</a><span class="pg">22</span></li>
    <li><a href="#conditions">Conditions, table of</a><span class="pg">212</span></li>
    <li><a href="#ix-rel-cuirass">Conquistador's Cuirass, the (artifact)</a><span class="pg">168</span></li>
    <li><a href="#ix-m-killground">Consecrate the Killing Ground (Miracle)</a><span class="pg">112</span></li>
    <li><a href="#ix-m-list-consecration">Consecrations, the (Miracle list)</a><span class="pg">111</span></li>
    <li><a href="#ix-core-roll">Core roll, the</a><span class="pg">11</span></li>
    <li><a href="#ix-m-covenant">Covenant, the (Miracle)</a><span class="pg">105</span></li>
    <li><a href="#ix-circumstance">Cover &amp; circumstance</a><span class="pg">173</span></li>
    <li><a href="#ix-rel-tooth">Coyote's Tooth (relic)</a><span class="pg">166</span></li>
    <li><a href="#ix-signs-craft">Craft, the (Sign list)</a><span class="pg">200</span></li>
    <li><a href="#ix-s-crimson">Crimson Word, the (Sign)</a><span class="pg">199</span></li>
    <li><a href="#ix-degrees">Critical success &amp; failure</a><span class="pg">12</span></li>
    <li><a href="#ix-s-crossing">Crossing the Threshold (Sign)</a><span class="pg">201</span></li>
    <li><a href="#ix-e-cylinder">Cylinder &amp; Sky (Edge)</a><span class="pg">142</span></li>
    <li class="ix-hd">D</li>
    <li><a href="#ix-dr">Damage Reduction &amp; resistance</a><span class="pg">177</span></li>
    <li><a href="#ix-c-cultist">Dark Cultist (Calling)</a><span class="pg">116</span></li>
    <li><a href="#ix-e-dead-eye">Dead Eye (Edge)</a><span class="pg">142</span></li>
    <li><a href="#ix-rel-compass">Dead Man's Compass (relic)</a><span class="pg">165</span></li>
    <li><a href="#ix-e-provider">Dead Shot Provider (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-s-deadmans">Deadman's Coat (Sign)</a><span class="pg">195</span></li>
    <li><a href="#ix-wounds">Death &amp; dying</a><span class="pg">177</span></li>
    <li><a href="#ix-s-debt">Debt Called In, the (Sign)</a><span class="pg">197</span></li>
    <li><a href="#ix-s-debt">Debt Collected (Sign)</a><span class="pg">197</span></li>
    <li><a href="#ix-three-debts">Debts, the three (Old Dark)</a><span class="pg">124</span></li>
    <li><a href="#ix-reckoning">Defense</a><span class="pg">20</span></li>
    <li><a href="#ix-degrees">Degrees of success</a><span class="pg">12</span></li>
    <li><a href="#ix-demoralize">Demoralize</a><span class="pg">138</span></li>
    <li><a href="#ix-difficulty">Difficulty Classes</a><span class="pg">12</span></li>
    <li><a href="#ix-reactions">Dive for Cover (reaction)</a><span class="pg">172</span></li>
    <li><a href="#ix-nerve-pool">Dread Checks</a><span class="pg">182</span></li>
    <li><a href="#ix-c-drifter">Drifter (Calling)</a><span class="pg">45</span></li>
    <li><a href="#ix-o-drover">Drover, the (Origin)</a><span class="pg">25</span></li>
    <li><a href="#ix-o-drummer">Drummer, the (Origin)</a><span class="pg">26</span></li>
    <li class="ix-hd">E</li>
    <li><a href="#edges">Edges</a><span class="pg">142</span></li>
    <li><a href="#calling-edges">Edges of the Callings</a><span class="pg">145</span></li>
    <li><a href="#ix-c-engineer">Engineer (Calling)</a><span class="pg">47</span></li>
    <li><a href="#play">Example of play</a><span class="pg">210</span></li>
    <li><a href="#advancement">Experience &amp; levels</a><span class="pg">207</span></li>
    <li><a href="#ix-m-unction">Extreme Unction (Miracle)</a><span class="pg">106</span></li>
    <li class="ix-hd">F</li>
    <li><a href="#ix-o-gentry">Fallen Gentry, the (Origin)</a><span class="pg">26</span></li>
    <li><a href="#ix-c-prophet">False Prophet (Calling)</a><span class="pg">121</span></li>
    <li><a href="#ix-familiar">Familiar (Witch)</a><span class="pg">130</span></li>
    <li><a href="#ix-e-fan">Fan the Hammer (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-weapon-traits">Fatal die</a><span class="pg">151</span></li>
    <li><a href="#ix-s-ledger">Feed the Ledger (Sign)</a><span class="pg">199</span></li>
    <li><a href="#ix-rel-dollar">Ferryman's Dollar, the (artifact)</a><span class="pg">169</span></li>
    <li><a href="#ix-m-fever">Fever Broken, the (Miracle)</a><span class="pg">110</span></li>
    <li><a href="#ix-ledger">Fight ledger, the (Callings)</a><span class="pg">40</span></li>
    <li><a href="#ix-firearms">Firearms</a><span class="pg">150</span></li>
    <li><a href="#firstpeoples">First Peoples, the</a><span class="pg">32</span></li>
    <li><a href="#ix-e-fleet">Fleet (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-s-foul">Foul the Working (Sign)</a><span class="pg">194</span></li>
    <li><a href="#ix-four-degrees">Four Degrees, in a fight</a><span class="pg">172</span></li>
    <li><a href="#ix-questions">Four Questions, the</a><span class="pg">21</span></li>
    <li><a href="#ix-o-freed">Freed, the (Origin)</a><span class="pg">27</span></li>
    <li><a href="#ix-frightened">Frightened</a><span class="pg">212</span></li>
    <li><a href="#ix-e-frontier-med">Frontier Medicine (Edge)</a><span class="pg">144</span></li>
    <li class="ix-hd">G</li>
    <li><a href="#ix-e-gallows">Gallows Humor (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-c-gambler">Gambler (Calling)</a><span class="pg">53</span></li>
    <li><a href="#ix-rel-deck">Gambler's Marked Deck (relic)</a><span class="pg">165</span></li>
    <li><a href="#ix-o-gambler">Gambler, the (Origin)</a><span class="pg">27</span></li>
    <li><a href="#ix-green-table">Gambling at the green table</a><span class="pg">139</span></li>
    <li><a href="#ix-rel-spurs">Ghost-Iron Spurs (relic)</a><span class="pg">166</span></li>
    <li><a href="#goods">Goods &amp; provisions</a><span class="pg">148</span></li>
    <li><a href="#ix-s-grasping">Grasping Dark, the (Sign)</a><span class="pg">198</span></li>
    <li><a href="#ix-s-greenhand">Green Hand, the (Sign)</a><span class="pg">201</span></li>
    <li><a href="#ix-grievous">Grievous wounds</a><span class="pg">179</span></li>
    <li><a href="#ix-grit">Grit</a><span class="pg">14</span></li>
    <li><a href="#ix-e-calm">Gunfighter's Calm (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-c-gunhand">Gunhand (Calling)</a><span class="pg">57</span></li>
    <li class="ix-hd">H</li>
    <li><a href="#ix-m-handheld">Hand Held (Miracle)</a><span class="pg">113</span></li>
    <li><a href="#ix-m-clasped">Hands Clasped (Miracle)</a><span class="pg">103</span></li>
    <li><a href="#ix-rel-rope">Hanged Man's Rope, the (artifact)</a><span class="pg">168</span></li>
    <li><a href="#ix-rel-coin">Hangman's Coin (relic)</a><span class="pg">165</span></li>
    <li><a href="#ix-e-hard-to-kill">Hard to Kill (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-tonics">Healing &amp; tonics</a><span class="pg">154</span></li>
    <li><a href="#ix-s-hearth">Hearth Unbroken, the (Sign)</a><span class="pg">203</span></li>
    <li><a href="#ix-e-hedge">Hedge Magic (Edge)</a><span class="pg">145</span></li>
    <li><a href="#ix-c-hexer">Hexer (Calling)</a><span class="pg">125</span></li>
    <li><a href="#ix-s-hollow">Hollow Step (Sign)</a><span class="pg">195</span></li>
    <li><a href="#ix-holy">Holy, unholy &amp; unsanctified</a><span class="pg">23</span></li>
    <li><a href="#ix-o-homesteader">Homesteader, the (Origin)</a><span class="pg">27</span></li>
    <li><a href="#ix-horse-nerve">Horse's Nerve, a</a><span class="pg">156</span></li>
    <li><a href="#ix-m-hour">Hour Is Not Yours, the (Miracle)</a><span class="pg">105</span></li>
    <li><a href="#ix-s-hungering">Hungering Hand, the (Sign)</a><span class="pg">199</span></li>
    <li class="ix-hd">I</li>
    <li><a href="#ix-beats">Initiative</a><span class="pg">171</span></li>
    <li><a href="#ix-m-interdict">Interdict, the (Miracle)</a><span class="pg">106</span></li>
    <li><a href="#conflict">Iron Code, the</a><span class="pg">171</span></li>
    <li><a href="#ix-e-iron-gut">Iron Gut (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-rel-star">Iron Star, the (artifact)</a><span class="pg">168</span></li>
    <li><a href="#ix-e-iron-will">Iron Will (Edge)</a><span class="pg">144</span></li>
    <li class="ix-hd">K</li>
    <li><a href="#ix-aiming">Kickback weapons</a><span class="pg">174</span></li>
    <li><a href="#ix-s-knotwind">Knot the Wind (Sign)</a><span class="pg">200</span></li>
    <li class="ix-hd">L</li>
    <li><a href="#ix-o-laborer">Laborer, the (Origin)</a><span class="pg">28</span></li>
    <li><a href="#ix-m-lampunquenched">Lamp Unquenched, The (Miracle)</a><span class="pg">113</span></li>
    <li><a href="#ix-grievous">Lasting Injuries</a><span class="pg">179</span></li>
    <li><a href="#ix-r-laying">Laying the Dead (Rite)</a><span class="pg">204</span></li>
    <li><a href="#ledger">Ledger, the (character sheet)</a><span class="pg">224</span></li>
    <li><a href="#ix-s-lender">Lender's Ear, the (Sign)</a><span class="pg">198</span></li>
    <li><a href="#ix-level-brings">Levels, what they bring</a><span class="pg">208</span></li>
    <li><a href="#ix-m-shared">Life Shared, the (Miracle)</a><span class="pg">111</span></li>
    <li><a href="#ix-m-light">Light Unfailing, a (Miracle)</a><span class="pg">102</span></li>
    <li><a href="#ix-s-listening">Listening, the (Sign)</a><span class="pg">194</span></li>
    <li><a href="#ix-m-litany">Litany of the Saints, the (Miracle)</a><span class="pg">106</span></li>
    <li><a href="#ix-m-weakness">Litany of Weakness, the (Miracle)</a><span class="pg">111</span></li>
    <li><a href="#ix-m-list-liturgy">Liturgy, the (Miracle list)</a><span class="pg">105</span></li>
    <li><a href="#ix-livestock">Livestock &amp; conveyances</a><span class="pg">162</span></li>
    <li><a href="#ix-m-longmercy">Long Mercy, the (Miracle)</a><span class="pg">111</span></li>
    <li><a href="#ix-s-longnight">Long Night, the (Sign)</a><span class="pg">197</span></li>
    <li><a href="#ix-s-longwhisper">Long Whisper, the (Sign)</a><span class="pg">195</span></li>
    <li><a href="#ix-mark">Lost (Mark 6)</a><span class="pg">183</span></li>
    <li class="ix-hd">M</li>
    <li><a href="#ix-o-madam">Madam, the (Origin)</a><span class="pg">28</span></li>
    <li><a href="#ix-mark">Mark, the</a><span class="pg">183</span></li>
    <li><a href="#ix-c-marshal">Marshal (Calling)</a><span class="pg">60</span></li>
    <li><a href="#ix-time">Measures of time, the</a><span class="pg">15</span></li>
    <li><a href="#ix-c-medicine">Medicine Man (Calling)</a><span class="pg">77</span></li>
    <li><a href="#ix-m-list-mending">Mending, the (Miracle list)</a><span class="pg">110</span></li>
    <li><a href="#ix-rel-chain">Meridian Chain, the (artifact)</a><span class="pg">169</span></li>
    <li><a href="#mexicanpeoples">Mexican Frontier, the</a><span class="pg">34</span></li>
    <li><a href="#ix-milestones">Milestones</a><span class="pg">209</span></li>
    <li><a href="#ix-m-dc">Miracle DC</a><span class="pg">102</span></li>
    <li><a href="#ix-m-lists">Miracle lists, the six</a><span class="pg">102</span></li>
    <li><a href="#ix-m-miracle">Miracle Plain, the (Miracle)</a><span class="pg">104</span></li>
    <li><a href="#miracles">Miracles</a><span class="pg">101</span></li>
    <li><a href="#ix-weapon-traits">Misfire</a><span class="pg">151</span></li>
    <li><a href="#ix-modifiers">Modifiers</a><span class="pg">20</span></li>
    <li><a href="#ix-more-arms">More arms &amp; powder</a><span class="pg">157</span></li>
    <li><a href="#ix-c-mountain">Mountain Man (Calling)</a><span class="pg">62</span></li>
    <li><a href="#ix-saddle">Mounted combat</a><span class="pg">177</span></li>
    <li><a href="#ix-mounts">Mounts &amp; tack</a><span class="pg">155</span></li>
    <li><a href="#ix-map">Multiple Attack Penalty</a><span class="pg">172</span></li>
    <li class="ix-hd">N</li>
    <li><a href="#ix-s-nail">Nail and the Name, the (Sign)</a><span class="pg">201</span></li>
    <li><a href="#ix-s-nailshadow">Nail the Shadow (Sign)</a><span class="pg">196</span></li>
    <li><a href="#ix-nerve-pool">Nerve</a><span class="pg">182</span></li>
    <li><a href="#ix-recover-nerve">Nerve, recovering</a><span class="pg">187</span></li>
    <li><a href="#ix-o-news">Newspaperman, the (Origin)</a><span class="pg">29</span></li>
    <li><a href="#ix-s-ninefold">Ninefold Knot, the (Sign)</a><span class="pg">202</span></li>
    <li><a href="#ix-nonlethal">Nonlethal blows</a><span class="pg">180</span></li>
    <li><a href="#ix-m-notwhile">Not While I Stand (Miracle)</a><span class="pg">103</span></li>
    <li><a href="#ix-m-nothingcomesin">Nothing Comes In (Miracle)</a><span class="pg">113</span></li>
    <li class="ix-hd">O</li>
    <li><a href="#ix-offguard">Off-Guard</a><span class="pg">174</span></li>
    <li><a href="#ix-m-offering">Offering, the (Miracle)</a><span class="pg">108</span></li>
    <li><a href="#ix-old-rites">Old Rites, the</a><span class="pg">204</span></li>
    <li><a href="#ix-s-oldwomans">Old Woman's Bargain, the (Sign)</a><span class="pg">203</span></li>
    <li><a href="#ix-s-vein">Open the Vein of the World (Sign)</a><span class="pg">200</span></li>
    <li><a href="#ix-checks">Opposed rolls</a><span class="pg">13</span></li>
    <li><a href="#origins">Origins</a><span class="pg">25</span></li>
    <li><a href="#ix-o-outlaw">Outlaw, the (Origin)</a><span class="pg">29</span></li>
    <li class="ix-hd">P</li>
    <li><a href="#ix-c-padre">Padre (Calling)</a><span class="pg">81</span></li>
    <li><a href="#ix-rel-lantern">Padre's Lantern, the (artifact)</a><span class="pg">168</span></li>
    <li><a href="#ix-e-pathfinder">Pathfinder (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-pf2e">Pathfinder Second Edition</a><span class="pg">11</span></li>
    <li><a href="#ix-patrons">Patrons of the Old Dark, the</a><span class="pg">132</span></li>
    <li><a href="#ix-rel-round">Peacemaker's Last Round, the (artifact)</a><span class="pg">167</span></li>
    <li><a href="#ix-m-pentecost">Pentecost (Miracle)</a><span class="pg">108</span></li>
    <li><a href="#ix-perks">Perks of the Callings</a><span class="pg">40</span></li>
    <li><a href="#ix-s-poppet">Poppet, the (Sign)</a><span class="pg">201</span></li>
    <li><a href="#posse">Posse, ready-made (pregenerated characters)</a><span class="pg">216</span></li>
    <li><a href="#ix-m-poultice">Poultice, the (Miracle)</a><span class="pg">110</span></li>
    <li><a href="#ix-e-powder">Powder Sense (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-e-reload">Practiced Reload (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-c-preacher">Preacher (Calling)</a><span class="pg">85</span></li>
    <li><a href="#ix-sign-price">Price of a Sign (Nerve, Blood, Mark)</a><span class="pg">192</span></li>
    <li><a href="#ix-core-roll">Proficiency</a><span class="pg">11</span></li>
    <li><a href="#ix-c-prospector">Prospector (Calling)</a><span class="pg">67</span></li>
    <li><a href="#ix-prov-dark">Provisions against the dark</a><span class="pg">161</span></li>
    <li><a href="#ix-gear">Provisions, gear &amp; sundries</a><span class="pg">154</span></li>
    <li class="ix-hd">Q</li>
    <li><a href="#ix-e-quick-draw">Quick Draw (Edge)</a><span class="pg">143</span></li>
    <li><a href="#quickref">Quick Reference</a><span class="pg">214</span></li>
    <li class="ix-hd">R</li>
    <li><a href="#ix-o-rail">Railroad Hand, the (Origin)</a><span class="pg">29</span></li>
    <li><a href="#ix-m-rank">Rank of a Miracle</a><span class="pg">101</span></li>
    <li><a href="#ix-sign-rank">Rank, Sign</a><span class="pg">191</span></li>
    <li><a href="#ix-rarity">Rarity — Common, Uncommon &amp; Rare</a><span class="pg">149</span></li>
    <li><a href="#ix-reactions">Reactions</a><span class="pg">172</span></li>
    <li><a href="#ix-r-bones">Reading the Bones (Rite)</a><span class="pg">204</span></li>
    <li><a href="#ix-m-rebuke">Rebuke the Dark (Miracle)</a><span class="pg">104</span></li>
    <li><a href="#ix-m-reckoningfire">Reckoning Fire, the (Miracle)</a><span class="pg">112</span></li>
    <li><a href="#ix-s-reckoning">Reckoning Hour, the (Sign)</a><span class="pg">196</span></li>
    <li><a href="#ix-reloading">Reloading</a><span class="pg">174</span></li>
    <li><a href="#ix-m-list-revival">Revival, the (Miracle list)</a><span class="pg">107</span></li>
    <li><a href="#ix-s-rot">Rot the Wound (Sign)</a><span class="pg">198</span></li>
    <li><a href="#ix-beats">Rounds &amp; turns</a><span class="pg">171</span></li>
    <li class="ix-hd">S</li>
    <li><a href="#ix-saddle">Saddle, fighting from the</a><span class="pg">177</span></li>
    <li><a href="#ix-e-saddle-born">Saddle-Born (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-safety">Safety at the table</a><span class="pg">188</span></li>
    <li><a href="#ix-r-sain">Sain, the (Rite)</a><span class="pg">204</span></li>
    <li><a href="#ix-rel-bell">Saint Dymphna's Bell (artifact)</a><span class="pg">167</span></li>
    <li><a href="#ix-rel-bone">Saint's Finger-Bone (relic)</a><span class="pg">165</span></li>
    <li><a href="#ix-s-salt">Salt &amp; Iron (Sign)</a><span class="pg">193</span></li>
    <li><a href="#ix-rel-salt">Salt of the Forty Martyrs (relic)</a><span class="pg">166</span></li>
    <li><a href="#ix-m-saltline">Salt the Threshold (Miracle)</a><span class="pg">111</span></li>
    <li><a href="#ix-e-salt-wise">Salt-Wise (Edge)</a><span class="pg">145</span></li>
    <li><a href="#ix-holy">Sanctification</a><span class="pg">23</span></li>
    <li><a href="#ix-checks">Saves</a><span class="pg">13</span></li>
    <li><a href="#ix-c-sawbones">Sawbones (Calling)</a><span class="pg">72</span></li>
    <li><a href="#ix-words">Sawbones (the word) &mdash; <em>see</em> Words of the country</a><span class="pg">17</span></li>
    <li><a href="#ix-scores">Scores, generating the</a><span class="pg">20</span></li>
    <li><a href="#ix-o-scout">Scout, the (Origin)</a><span class="pg">30</span></li>
    <li><a href="#ix-services">Services &amp; lodging</a><span class="pg">162</span></li>
    <li><a href="#ix-m-setbone">Set the Bone (Miracle)</a><span class="pg">110</span></li>
    <li><a href="#ix-m-pack">Set the Pack On (Miracle)</a><span class="pg">109</span></li>
    <li><a href="#ix-c-shaman">Shaman (Calling)</a><span class="pg">88</span></li>
    <li><a href="#ix-m-notbemoved">She Will Not Be Moved (Miracle)</a><span class="pg">114</span></li>
    <li><a href="#ix-sign-dc">Sign DC</a><span class="pg">192</span></li>
    <li><a href="#ix-sign-lists">Sign lists, the three</a><span class="pg">192</span></li>
    <li><a href="#ix-m-crossing">Sign of the Cross, the (Miracle)</a><span class="pg">106</span></li>
    <li><a href="#signs">Signs</a><span class="pg">191</span></li>
    <li><a href="#ix-who-works">Signs, who may work</a><span class="pg">204</span></li>
    <li><a href="#ix-m-silverround">Silver the Round (Miracle)</a><span class="pg">112</span></li>
    <li><a href="#ix-c-sister">Sister (Calling)</a><span class="pg">92</span></li>
    <li><a href="#skills">Skills</a><span class="pg">137</span></li>
    <li><a href="#ix-using-skills">Skills, using</a><span class="pg">138</span></li>
    <li><a href="#ix-m-healsleep">Sleep of Healing, the (Miracle)</a><span class="pg">110</span></li>
    <li><a href="#ix-not-shooting">Some things you do not shoot</a><span class="pg">176</span></li>
    <li><a href="#ix-s-sourmilk">Sour the Milk (Sign)</a><span class="pg">200</span></li>
    <li><a href="#ix-reckoning">Speed</a><span class="pg">20</span></li>
    <li><a href="#ix-m-snare">Spirit-Snare, the (Miracle)</a><span class="pg">109</span></li>
    <li><a href="#ix-m-list-spirits">Spirits, the (Miracle list)</a><span class="pg">108</span></li>
    <li><a href="#ix-spoor">Spoor &amp; sign, reading</a><span class="pg">139</span></li>
    <li><a href="#ix-e-steady">Steady Shot (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-m-steadying">Steadying Word, the (Miracle)</a><span class="pg">102</span></li>
    <li><a href="#ix-s-stilling">Stilling, the (Sign)</a><span class="pg">194</span></li>
    <li><a href="#ix-e-stone">Stone Nerve (Edge)</a><span class="pg">144</span></li>
    <li class="ix-hd">T</li>
    <li><a href="#ix-taint">Taint of the Land, the</a><span class="pg">188</span></li>
    <li><a href="#ix-shed-taint">Taint, shedding the</a><span class="pg">190</span></li>
    <li><a href="#ix-take-time">Take 10 / Take 20</a><span class="pg">13</span></li>
    <li><a href="#ix-s-tally">Tally, the (Sign)</a><span class="pg">195</span></li>
    <li><a href="#ix-m-tedeum">Te Deum (Miracle)</a><span class="pg">106</span></li>
    <li><a href="#ix-m-testify">Testify (Miracle)</a><span class="pg">107</span></li>
    <li><a href="#ix-truths">Three Truths, the</a><span class="pg">9</span></li>
    <li><a href="#ix-e-throw">Throw the Stick (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-tone">Tone, on</a><span class="pg">10</span></li>
    <li><a href="#ix-tonics">Tonics &amp; the Sawbones' trade</a><span class="pg">154</span></li>
    <li><a href="#ix-tools">Tools of many trades</a><span class="pg">159</span></li>
    <li><a href="#ix-e-touched">Touched (Edge)</a><span class="pg">145</span></li>
    <li><a href="#ix-e-rawhide">Tough as Rawhide (Edge)</a><span class="pg">143</span></li>
    <li><a href="#ix-e-tracker">Tracker (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-m-weather">Turn the Weather (Miracle)</a><span class="pg">109</span></li>
    <li><a href="#ix-s-turning">Turning, the (Sign)</a><span class="pg">203</span></li>
    <li><a href="#ix-e-two-gun">Two-Gun (Edge)</a><span class="pg">143</span></li>
    <li class="ix-hd">U</li>
    <li><a href="#ix-s-unburden">Unburdening, the (Sign)</a><span class="pg">196</span></li>
    <li><a href="#ix-m-named">Unclean Named, the (Miracle)</a><span class="pg">104</span></li>
    <li><a href="#ix-uncommon">Uncommon goods</a><span class="pg">163</span></li>
    <li><a href="#ix-o-undertaker">Undertaker, the (Origin)</a><span class="pg">30</span></li>
    <li><a href="#ix-s-unmake">Unmake the Working (Sign)</a><span class="pg">197</span></li>
    <li><a href="#ix-unmarked">Unmarked at the threshold, the</a><span class="pg">205</span></li>
    <li><a href="#ix-e-unshakable">Unshakable (Edge)</a><span class="pg">144</span></li>
    <li><a href="#ix-untrained">Untrained skills</a><span class="pg">139</span></li>
    <li class="ix-hd">V</li>
    <li><a href="#ix-o-veteran">Veteran, the (Origin)</a><span class="pg">31</span></li>
    <li><a href="#ix-rel-vial">Vial from the Weeping Spring (artifact)</a><span class="pg">167</span></li>
    <li><a href="#ix-m-list-vigil">Vigil, the (Miracle list)</a><span class="pg">113</span></li>
    <li><a href="#ix-m-vigil">Vigil, the (Miracle)</a><span class="pg">104</span></li>
    <li><a href="#ix-vittles">Vittles &amp; comforts</a><span class="pg">160</span></li>
    <li class="ix-hd">W</li>
    <li><a href="#ix-s-threshold">Ward of the Threshold (Sign)</a><span class="pg">196</span></li>
    <li><a href="#ix-e-warded">Warded (Edge)</a><span class="pg">145</span></li>
    <li><a href="#ix-m-warding">Warding Psalm, the (Miracle)</a><span class="pg">103</span></li>
    <li><a href="#ix-r-salt">Warding Salt (Rite)</a><span class="pg">204</span></li>
    <li><a href="#ix-m-watchkept">Watch Kept, The (Miracle)</a><span class="pg">113</span></li>
    <li><a href="#ix-furniture">Weapon furniture</a><span class="pg">158</span></li>
    <li><a href="#ix-weapon-traits">Weapon traits</a><span class="pg">151</span></li>
    <li><a href="#ix-s-widow">Widow's Curse, the (Sign)</a><span class="pg">202</span></li>
    <li><a href="#ix-rel-locket">Widow's Locket (relic)</a><span class="pg">166</span></li>
    <li><a href="#ix-c-witch">Witch (Calling)</a><span class="pg">128</span></li>
    <li><a href="#ix-c-witchhunter">Witch Hunter (Calling)</a><span class="pg">97</span></li>
    <li><a href="#ix-rel-bottle">Witch-Bottle (relic)</a><span class="pg">165</span></li>
    <li><a href="#ix-s-witchsight">Witch-Sight (Sign)</a><span class="pg">193</span></li>
    <li><a href="#ix-m-smallword">Word to the Small Spirits, a (Miracle)</a><span class="pg">108</span></li>
    <li><a href="#ix-words">Words of the country (glossary)</a><span class="pg">18</span></li>
    <li><a href="#miracles">Work of Faith, The</a><span class="pg">101</span></li>
    <li><a href="#ix-wounds">Wounds, bleeding &amp; death</a><span class="pg">177</span></li>
    <li class="ix-hd">Y</li>
    <li><a href="#ix-1885">Year of 1885, the</a><span class="pg">9</span></li>
  </ul>
  <div class="pageno">56</div>
</section>
</div>
<script>
(function(){
  "use strict";
  var done=false;
  function ready(fn){ if(document.readyState!=='loading'){fn();} else {document.addEventListener('DOMContentLoaded',fn);} }
  function fit(){
    var bp=document.querySelector('.book.pages');
    if(!bp) return;
    var pageW=8.5*96; /* true page width in CSS px */
    var avail=document.documentElement.clientWidth-16;
    var s=Math.min(1, avail/pageW);
    bp.style.setProperty('--book-zoom', s);
  }
  function start(){
    if(done) return; done=true;
    try{ paginate(); }catch(e){ console&&console.warn&&console.warn('pagination skipped',e); }
    fit();
  }

  /* ============================================================
     Pagination runs in up to four passes. A pass flows every
     source block onto fixed 11in sheets, splitting tables, lists,
     boxes, creatures, stat blocks, and paragraphs (at word
     boundaries, keeping two lines on either side of a break) so
     each page fills to the bottom. Between passes, chapters that
     strand a near-empty final page ("runts") are granted a small
     per-page depth bonus — vertical feathering, at most 24px,
     invisible at print scale — and repaginated so the runt is
     absorbed. Feathering that fails to absorb its runt is
     reverted so no chapter trades a thin tail for a thinner one.
     ============================================================ */
  var FEATHER_MAX=24, RUNT_FILL=0.30, PASS_MAX=4;

  function paginate(){
    var origBook=document.querySelector('.book');
    if(!origBook) return;
    var pristine=origBook.cloneNode(true);
    var bonuses={}, banned={};
    var res=null, bookEl=origBook;
    for(var pass=0; pass<PASS_MAX; pass++){
      res=runPass(bookEl, bonuses);
      var changed=false;
      var groups={};
      res.pageMeta.forEach(function(m,idx){
        if(!m.content) return;
        (groups[m.group]=groups[m.group]||[]).push(idx);
      });
      Object.keys(groups).forEach(function(g){
        if(banned[g]) return;
        var pgs=groups[g];
        if(pgs.length<2) return;
        var lastIdx=pgs[pgs.length-1];
        var m=res.pageMeta[lastIdx];
        var used=m.content.scrollHeight;
        if(used<=0 || used/m.max>=RUNT_FILL) {
          return;
        }
        if(bonuses[g]){
          /* feathering failed to absorb this runt: revert it */
          delete bonuses[g]; banned[g]=true; changed=true;
          return;
        }
        /* columnar content (indexes, two-col reference) absorbs roughly twice
           the feather per page, so attempt generously; failures revert */
        var capacity=(pgs.length-1)*FEATHER_MAX;
        if(used>capacity*3){ banned[g]=true; return; }
        bonuses[g]=Math.min(FEATHER_MAX, Math.ceil(used/(pgs.length-1))+6);
        changed=true;
      });
      if(!changed || pass===PASS_MAX-1) break;
      res.frag.parentNode.removeChild(res.frag);
      bookEl=pristine.cloneNode(true);
      bookEl.style.display='none';
      document.body.appendChild(bookEl);
    }
    finalize(res);
  }

  function runPass(book, bonuses){
    var origSections=[].slice.call(book.children).filter(function(n){return n.nodeType===1 && n.classList.contains('page');});
    if(!origSections.length){ return {frag:null,pageEls:[],pageMeta:[]}; }

    var sections=origSections.map(function(sec){
      var runhead=sec.querySelector(':scope > .runhead');
      var chap=null;
      if(runhead){
        var spans=runhead.querySelectorAll('span');
        for(var i=0;i<spans.length;i++){ var t=spans[i].textContent.trim(); if(t && t.indexOf('Blood')<0){ chap=t; break; } }
      }
      var numbered=!!sec.querySelector(':scope > .pageno');
      var isCover=sec.classList.contains('title-page');
      var blocks=[].slice.call(sec.children).filter(function(n){ return n.nodeType===1 && !n.classList.contains('runhead') && !n.classList.contains('pageno'); });
      var isChapter=blocks.length && blocks[0].tagName==='H1';
      return {chap:chap, numbered:numbered, id:sec.id||null, isCover:isCover, isChapter:isChapter, blocks:blocks};
    });

    var frag=document.createElement('div');
    frag.className='book pages';
    book.parentNode.insertBefore(frag,book);
    book.style.display='none';

    var pageEls=[], pageMeta=[];
    var cur=null, max=0, firstPlaced=false, curChap=null, curNumbered=true, curGroup=-1;

    function availFor(pg){
      var cs=getComputedStyle(pg);
      var innerH=pg.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom);
      var rh=pg.querySelector(':scope > .runhead');
      var rhH=rh?rh.offsetHeight+parseFloat(getComputedStyle(rh).marginBottom||0):0;
      var reserve=18;
      return innerH-rhH-reserve+(bonuses[curGroup]||0);
    }
    function fits(content,m){ return content.scrollHeight<=m+1; }
    function makePage(){
      var pg=document.createElement('section'); pg.className='page sheet';
      var rh=null;
      if(curChap){ rh=document.createElement('div'); rh.className='runhead'; pg.appendChild(rh); }
      var content=document.createElement('div'); content.className='sheet-body';
      pg.appendChild(content);
      frag.appendChild(pg);
      cur={pg:pg,content:content}; max=availFor(pg); firstPlaced=false;
      pageEls.push(pg); pageMeta.push({numbered:curNumbered,chap:curChap,rh:rh,content:content,group:curGroup,max:max});
      return cur;
    }
    function fresh(){ return makePage(); }

    /* ---- word-level paragraph splitting (widow/orphan-controlled) ---- */
    function isWordNode(u){ return !(u.nodeType===3 && !/\S/.test(u.textContent)); }
    function splitPara(p, nextC){
      var units=[];
      [].slice.call(p.childNodes).forEach(function(n){
        if(n.nodeType===3){
          var parts=n.textContent.split(/(\s+)/);
          for(var q=0;q<parts.length;q++){ if(parts[q]!=='') units.push(document.createTextNode(parts[q])); }
        } else { units.push(n); }
      });
      var words=0;
      for(var w=0;w<units.length;w++){ if(isWordNode(units[w])) words++; }
      if(words<10) return false;
      var lh=parseFloat(getComputedStyle(p).lineHeight);
      if(!lh||isNaN(lh)){ lh=(parseFloat(getComputedStyle(p).fontSize)||19)*1.5; }
      function fill(n){
        while(p.firstChild) p.removeChild(p.firstChild);
        for(var q=0;q<n;q++) p.appendChild(units[q]);
      }
      var lo=1, hi=units.length-1, best=0;
      while(lo<=hi){
        var mid=(lo+hi)>>1;
        fill(mid);
        if(fits(cur.content,max)){ best=mid; lo=mid+1; } else { hi=mid-1; }
      }
      function decline(){ fill(units.length); return false; }
      if(best<1) return decline();
      fill(best);
      if(p.getBoundingClientRect().height < lh*1.9) return decline();
      /* orphan control: carry at least ~4 words forward */
      var restWords=0;
      for(var r=best;r<units.length;r++){ if(isWordNode(units[r])) restWords++; }
      if(restWords<4){
        var need=4-restWords;
        while(need>0 && best>1){ if(isWordNode(units[best-1])) need--; best--; }
        fill(best);
        if(best<1 || p.getBoundingClientRect().height < lh*1.9) return decline();
      }
      var rest=units.slice(best);
      while(rest.length && !isWordNode(rest[0])) rest.shift();
      if(!rest.length) return decline();
      var cont=nextC();
      var p2=p.cloneNode(false);
      p2.classList.remove('dropcap'); p2.classList.remove('lead');
      if(p2.id) p2.removeAttribute('id');
      /* if the block opened with a small-caps tag (keeper notes, Found lines),
         repeat it on the carried half with a (cont.) marker */
      var tag=p.querySelector(':scope > .kn-tag, :scope > .cf-tag');
      if(tag && rest.indexOf(tag)<0){
        var t2=tag.cloneNode(true);
        t2.appendChild(document.createTextNode(' (cont.)'));
        p2.appendChild(t2);
        if(t2.classList.contains('cf-tag')) p2.appendChild(document.createTextNode(' '));
      }
      for(var q2=0;q2<rest.length;q2++) p2.appendChild(rest[q2]);
      cont.appendChild(p2);
      /* widow control: a lone short line at the top of the new page reads
         poorly; feed it words from the kept half while room remains */
      var frontAnchor=p2.firstChild;
      if(frontAnchor && frontAnchor.nodeType===1 && frontAnchor.classList && (frontAnchor.classList.contains('kn-tag')||frontAnchor.classList.contains('cf-tag'))){ frontAnchor=frontAnchor.nextSibling; }
      var guard=24;
      while(guard-->0 && p2.getBoundingClientRect().height < lh*1.9 && p.childNodes.length>4){
        var lastN=p.lastChild;
        p.removeChild(lastN);
        p2.insertBefore(lastN, frontAnchor);
        frontAnchor=lastN;
        if(p.getBoundingClientRect().height < lh*1.9){
          p.appendChild(p2.removeChild(lastN));
          break;
        }
      }
      if(!fits(cur.content,max)){ splitPara(p2, nextC); }
      firstPlaced=true;
      return true;
    }
    function isParaLike(b){
      if(b.tagName==='P') return true;
      if(b.tagName==='DIV' && b.classList && b.classList.contains('keeper-note')) return true;
      if(b.tagName==='DIV' && b.classList && (b.classList.contains('quote')||b.classList.contains('narr'))) return true;
      return false;
    }

    function splitTable(table){
      var thead=table.querySelector('thead');
      var tbody=table.querySelector('tbody');
      if(!tbody){ firstPlaced=true; return; }
      var notAlone=!!table.previousElementSibling;
      var rows=[].slice.call(tbody.rows);
      for(var k=0;k<rows.length;k++){ tbody.removeChild(rows[k]); }
      var i=0;
      while(i<rows.length){
        tbody.appendChild(rows[i]);
        if(!fits(cur.content,max)){
          if(tbody.rows.length>1){
            tbody.removeChild(rows[i]);
            fresh();
            var ct=table.cloneNode(false);
            if(thead) ct.appendChild(thead.cloneNode(true));
            var ntb=document.createElement('tbody'); ct.appendChild(ntb);
            cur.content.appendChild(ct);
            table=ct; tbody=ntb; notAlone=false;
          } else if(notAlone){
            tbody.removeChild(rows[i]);
            if(table.parentNode) table.parentNode.removeChild(table);
            fresh();
            var ct2=table.cloneNode(false);
            if(thead) ct2.appendChild(thead.cloneNode(true));
            var ntb2=document.createElement('tbody'); ct2.appendChild(ntb2);
            cur.content.appendChild(ct2);
            table=ct2; tbody=ntb2; notAlone=false;
          } else { i++; }
        } else { i++; }
      }
      if(tbody && !tbody.rows.length && table.parentNode){ table.parentNode.removeChild(table); }
      firstPlaced=true;
    }
    function splitList(list){
      var notAlone=!!list.previousElementSibling;
      var items=[].slice.call(list.children);
      for(var k=0;k<items.length;k++){ list.removeChild(items[k]); }
      var i=0;
      while(i<items.length){
        list.appendChild(items[i]);
        if(!fits(cur.content,max)){
          if(list.children.length>1){
            list.removeChild(items[i]);
            fresh();
            var nl=list.cloneNode(false);
            cur.content.appendChild(nl);
            list=nl; notAlone=false;
          } else if(notAlone){
            list.removeChild(items[i]);
            if(list.parentNode) list.parentNode.removeChild(list);
            fresh();
            var nl2=list.cloneNode(false);
            cur.content.appendChild(nl2);
            list=nl2; notAlone=false;
          } else { i++; }
        } else { i++; }
      }
      if(list && !list.children.length && list.parentNode){ list.parentNode.removeChild(list); }
      firstPlaced=true;
    }
    function _mkFrag(box, head){
      fresh();
      var nb=box.cloneNode(false);
      if(head){ var nh=head.cloneNode(true); nh.innerHTML+=' <span class="sb-cont">(cont.)</span>'; nb.appendChild(nh); }
      cur.content.appendChild(nb);
      return nb;
    }
    /* trailing headings/labels must not be stranded at the bottom of a
       container fragment when the block after them carries forward */
    function pullTrailingHeads(fromBox){
      var carry=[], last=fromBox.lastElementChild;
      while(last && (/^H[1-6]$/.test(last.tagName) || (last.classList && (
            last.classList.contains('cr-kind') || last.classList.contains('statline') )))){
        carry.unshift(last); fromBox.removeChild(last); last=fromBox.lastElementChild;
      }
      return carry;
    }
    function splitContainer(box, headSel){
      var head=headSel?box.querySelector(headSel):null;
      var items=[].slice.call(box.children).filter(function(c){return c!==head;});
      for(var k=0;k<items.length;k++){ box.removeChild(items[k]); }
      var notAlone=!!box.previousElementSibling;
      var curBox=box, placed=0, i=0, justRetried=false;
      function contFrag(){
        curBox=_mkFrag(box, head); placed=1; notAlone=false; return curBox;
      }
      /* a stat block child too tall for the space left in its creature entry
         can carry its remaining lines into the next fragment, keeping the
         labelled head with at least a couple of lines */
      function splitStatChild(item){
        var sh=item.querySelector(':scope > .sb-head');
        var sps=[].slice.call(item.children).filter(function(c){return c!==sh;});
        if(sps.length<2) return false;
        /* keep item attached; strip its stat lines */
        for(var z=0;z<sps.length;z++){ item.removeChild(sps[z]); }
        if(!fits(cur.content,max)){
          /* even the bare head doesn't fit — put the lines back and give up */
          for(var z2=0;z2<sps.length;z2++){ item.appendChild(sps[z2]); }
          return false;
        }
        var curSB=item, sp=0, si=0;
        while(si<sps.length){
          curSB.appendChild(sps[si]);
          if(fits(cur.content,max)){ si++; sp++; continue; }
          if(sp>0){
            curSB.removeChild(sps[si]);
            contFrag();
            var nsb=item.cloneNode(false);
            if(sh){ var nh=sh.cloneNode(true); nh.innerHTML+=' <span class="sb-cont">(cont.)</span>'; nsb.appendChild(nh); }
            curBox.appendChild(nsb); curSB=nsb; sp=0;
          } else {
            curSB.removeChild(sps[si]);
            if(curSB.parentNode) curSB.parentNode.removeChild(curSB);
            contFrag();
            var nsb2=item.cloneNode(false); if(sh) nsb2.appendChild(sh.cloneNode(true));
            for(var j=si;j<sps.length;j++){ nsb2.appendChild(sps[j]); }
            curBox.appendChild(nsb2);
            si=sps.length;
          }
        }
        return true;
      }
      while(i<items.length){
        var item=items[i];
        curBox.appendChild(item);
        if(fits(cur.content,max)){ i++; placed++; justRetried=false; continue; }
        /* a multi-item list child can itself be split across fragments */
        if((item.tagName==='UL'||item.tagName==='OL') && item.children.length>1){
          var lis=[].slice.call(item.children);
          for(var z=0;z<lis.length;z++){ item.removeChild(lis[z]); }
          var curList=item, lp=0, li=0;
          while(li<lis.length){
            curList.appendChild(lis[li]);
            if(fits(cur.content,max)){ li++; lp++; placed++; continue; }
            if(lp>0){
              curList.removeChild(lis[li]);
              curBox=_mkFrag(box, head);
              var nl=item.cloneNode(false); curBox.appendChild(nl); curList=nl; lp=0;
            } else if(placed>0 || notAlone){
              curList.removeChild(lis[li]);
              if(curList.parentNode && !curList.children.length){ curList.parentNode.removeChild(curList); }
              curBox=_mkFrag(box, head);
              var nl2=item.cloneNode(false); curBox.appendChild(nl2); curList=nl2; lp=0; notAlone=false;
            } else { li++; lp++; placed++; }
          }
          i++; placed++; justRetried=false; continue;
        }
        /* a long paragraph-like child can split at a word boundary to fill
           the remaining gap before the fragment carries forward */
        if(isParaLike(item) && (placed>0 || notAlone || !firstPlaced)){
          if(splitPara(item, contFrag)){ i++; placed++; justRetried=false; continue; }
        }
        /* a stat block child can carry its trailing lines forward when a
           useful share of it fits in the gap */
        if(item.tagName==='DIV' && item.classList && item.classList.contains('statblock') && (placed>0 || notAlone)){
          item.parentNode.removeChild(item);
          var gap=max-cur.content.scrollHeight;
          curBox.appendChild(item);
          if(gap>=120 && splitStatChild(item)){ i++; placed++; justRetried=false; continue; }
        }
        if(placed>0 && !justRetried){
          curBox.removeChild(item);
          var carry=pullTrailingHeads(curBox);
          if(head && curBox===box && curBox.children.length===1 && curBox.firstElementChild===head){
            /* only the entry's title would stay behind — move the whole box
               to the fresh page instead of stranding an orphaned heading */
            if(curBox.parentNode) curBox.parentNode.removeChild(curBox);
            fresh();
            cur.content.appendChild(box);
            curBox=box; placed=carry.length; notAlone=false; justRetried=true;
            for(var c0=0;c0<carry.length;c0++){ curBox.appendChild(carry[c0]); }
          } else {
            if(!curBox.children.length && curBox.parentNode){ curBox.parentNode.removeChild(curBox); }
            curBox=_mkFrag(box, head); placed=carry.length; notAlone=false; justRetried=true;
            for(var c=0;c<carry.length;c++){ curBox.appendChild(carry[c]); }
          }
          /* retry the same item on the fresh fragment (do not advance i) */
        } else if(placed===0 && notAlone){
          /* header + first item won't fit this gap: move the whole box whole */
          curBox.removeChild(item);
          if(curBox.parentNode) curBox.parentNode.removeChild(curBox);
          fresh();
          var ob=box.cloneNode(false); if(head) ob.appendChild(head.cloneNode(true));
          for(var j=i;j<items.length;j++){ ob.appendChild(items[j]); }
          cur.content.appendChild(ob); firstPlaced=true; return;
        } else { i++; placed++; justRetried=false; }
      }
      firstPlaced=true;
    }
    function splitBox(box){ splitContainer(box, ':scope > h3, :scope > h4'); }
    function tooBig(block){
      if(block.tagName==='TABLE'){ splitTable(block); }
      else if(block.tagName==='UL'||block.tagName==='OL'){ splitList(block); }
      else if(block.tagName==='P'){
        if(!splitPara(block, function(){ fresh(); return cur.content; })){ firstPlaced=true; }
      }
      else if(block.tagName==='DIV'){
        if(block.classList && block.classList.contains('statblock')) splitContainer(block, ':scope > .sb-head');
        else if(block.classList && block.classList.contains('twocol')) splitContainer(block, null);
        else if(block.classList && block.classList.contains('creature')) splitContainer(block, ':scope > .cr-name');
        else if(block.classList && block.classList.contains('keeper-note')){
          if(!splitPara(block, function(){ fresh(); return cur.content; })){ firstPlaced=true; }
        }
        else splitBox(block);
      }
      else { firstPlaced=true; }
    }
    function isSplitFill(b){
      /* A block overflowing a partially-filled page may be split to fill the gap
         instead of moving whole and leaving blank space. */
      if(b.tagName==='TABLE'){ var tb=b.querySelector('tbody'); return !!tb && tb.rows.length>1; }
      if(b.tagName==='UL'||b.tagName==='OL'){ return b.children.length>1 && !(b.classList&&b.classList.contains('toc')); }
      if(b.tagName==='P'){ return !(b.classList&&(b.classList.contains('chapter-sub')||b.classList.contains('statline'))) && (b.textContent||'').length>150; }
      if(b.tagName==='DIV' && b.classList){
        if(b.classList.contains('quote')||b.classList.contains('equation')||b.classList.contains('plate')) return false;
        if(b.classList.contains('statblock')) return b.querySelectorAll(':scope > p').length>1;
        if(b.classList.contains('twocol')) return b.children.length>1;
        if(b.classList.contains('creature')) return b.children.length>1;
        if(b.classList.contains('keeper-note')) return (b.textContent||'').length>200;
        if(b.classList.contains('box')){
          var h=b.querySelector(':scope > h3, :scope > h4');
          var kids=[].slice.call(b.children).filter(function(c){return c!==h;});
          if(kids.length>1) return true;
          if(kids.length===1 && kids[0].tagName==='P' && (kids[0].textContent||'').length>200) return true;
          var lst=b.querySelector(':scope > ul, :scope > ol');
          return !!lst && lst.children.length>1;
        }
      }
      return false;
    }
    function trySplitFill(block){
      /* returns true when the block was handled (split in place); false when
         the split was declined and the caller should move the block whole */
      if(isParaLike(block)){
        return splitPara(block, function(){ fresh(); return cur.content; });
      }
      tooBig(block);
      return true;
    }
    function placeBlock(block){
      var before=cur.content.scrollHeight;
      cur.content.appendChild(block);
      if(fits(cur.content,max)){ firstPlaced=true; return; }
      if(!firstPlaced){ tooBig(block); return; }
      /* page already has content and the block overflows it.
         If a meaningful gap remains and the block can be split, fill the gap in place
         instead of moving the whole block down (which would leave blank space). */
      if(isSplitFill(block) && (max-before) > max*0.10){
        if(trySplitFill(block)) return;
      }
      cur.content.removeChild(block);
      var prev=cur.content;
      var trailing=[], node=prev.lastChild;
      while(node && node.nodeType===1 && /^H[1-6]$/.test(node.tagName)){ trailing.unshift(node); node=node.previousSibling; }
      var hasOther=false, n2=node;
      while(n2){ if(n2.nodeType===1){ hasOther=true; break; } n2=n2.previousSibling; }
      if(trailing.length && !hasOther){
        cur.content.appendChild(block);
        if(fits(cur.content,max)){ firstPlaced=true; } else { tooBig(block); }
      } else {
        var carry=trailing.length?trailing:[];
        carry.forEach(function(t){ prev.removeChild(t); });
        fresh();
        carry.forEach(function(t){ cur.content.appendChild(t); });
        cur.content.appendChild(block);
        if(fits(cur.content,max)){ firstPlaced=true; } else { tooBig(block); }
      }
    }

    sections.forEach(function(sd){
      if(sd.isCover){
        curGroup++;
        var pg=document.createElement('section'); pg.className='page sheet title-page';
        sd.blocks.forEach(function(b){ pg.appendChild(b); });
        if(sd.id) pg.id=sd.id;
        frag.appendChild(pg); pageEls.push(pg); pageMeta.push({numbered:false,chap:null,rh:null,content:null,group:curGroup,max:0});
        cur=null;
        return;
      }
      if(sd.id && sd.blocks.length){ sd.blocks[0].id=sd.id; }
      var forceFresh = sd.isChapter || !sd.numbered || cur===null;
      if(forceFresh){
        curGroup++;
        curChap=sd.chap; curNumbered=sd.numbered;
        makePage();
      } else {
        curChap=sd.chap;
      }
      sd.blocks.forEach(placeBlock);
    });

    book.parentNode.removeChild(book);
    return {frag:frag, pageEls:pageEls, pageMeta:pageMeta};
  }

  function finalize(res){
    if(!res || !res.frag) return;
    var pageEls=res.pageEls, pageMeta=res.pageMeta;
    pageMeta.forEach(function(m,idx){
      var phys=idx+1;
      if(m.rh){
        if(phys%2===0){ m.rh.innerHTML='<span class="l">'+m.chap+'</span><span>Blood &amp; Grit</span>'; }
        else { m.rh.innerHTML='<span class="l">Blood &amp; Grit</span><span>'+m.chap+'</span>'; }
      }
      if(m.numbered){
        var pn=document.createElement('div'); pn.className='pageno'; pn.textContent=phys;
        pageEls[idx].appendChild(pn);
      }
    });

    [].slice.call(document.querySelectorAll('span.pg')).forEach(function(span){
      var li=span.parentNode;
      var a=li.querySelector('a[href^="#"]'); if(!a) return;
      var id=a.getAttribute('href').slice(1);
      var t=document.getElementById(id); if(!t) return;
      var pg=t.classList&&t.classList.contains('page')?t:(t.closest?t.closest('.page'):null);
      if(!pg) return;
      var idx=pageEls.indexOf(pg);
      if(idx>=0) span.textContent=String(idx+1);
    });

    // The page number is a sibling of the anchor, not inside it, so a reader who taps the
    // NUMBER -- which on a phone is a good half of what the eye aims at -- hits nothing at all.
    // Rather than move 800-odd spans inside their anchors across six books (and break both
    // measure_index.py's patcher and the resolver directly above), the row delegates: a click
    // anywhere on the number, or on the dotted leader between, follows the entry's own link.
    ['toc2','ix'].forEach(function(cls){
      [].slice.call(document.querySelectorAll('ul.'+cls)).forEach(function(ul){
        ul.addEventListener('click',function(ev){
          if(ev.target.closest('a')) return;
          var li=ev.target.closest('li'); if(!li) return;
          var a=li.querySelector('a[href^="#"]'); if(!a) return;
          a.click();
        });
      });
    });

    res.frag.classList.add('ready');
  }

  ready(function(){
    if(document.fonts&&document.fonts.ready){
      document.fonts.ready.then(start);
      setTimeout(start,2000);
    } else { start(); }
    var t; window.addEventListener('resize',function(){ clearTimeout(t); t=setTimeout(fit,120); });
    window.addEventListener('orientationchange',fit);
  });
})();

</script>
</body>
</html>
"""

html = SRC

# Drop the player-facing map of Perdition Basin into Appendix E.
html = html.replace("<!--PERDITION_MAP-->", player_map_html())

# Grow the simple Contents into a generated two-level detailed Contents.
html = add_detailed_toc(html)

refs = sorted(set(re.findall(r'assets/img\d+\.\w+', html)))
for ref in refs:
    if not os.path.exists(ref):
        sys.exit(f"missing asset: {ref}")
    mime = mimetypes.guess_type(ref)[0] or "application/octet-stream"
    b64 = base64.b64encode(open(ref, "rb").read()).decode("ascii")
    html = html.replace(ref, f"data:{mime};base64,{b64}")

open(OUT, "w", encoding="utf-8", newline="").write(html)
print(f"built {OUT}: {len(html)} bytes, {len(refs)} image(s) inlined: {', '.join(refs)}")

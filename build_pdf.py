#!/usr/bin/env python3
"""Generate a magazine-grade HTML ebook from markdown.

Usage:
  python3 build_pdf.py translated.md ebook.html
"""

import html
import os
import re
import sys

DEFAULT_MD_PATH = '~/.openclaw-autoclaw/workspace/claude-ebook/创业者的AI实战手册_中文版.md'
DEFAULT_OUT_PATH = '~/.openclaw-autoclaw/workspace/claude-ebook/创业者的AI实战手册.html'

MD_PATH = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('PDF_TO_EBOOK_MD', DEFAULT_MD_PATH))
OUT_PATH = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else os.environ.get('PDF_TO_EBOOK_HTML', DEFAULT_OUT_PATH))
BASE_DIR = os.path.dirname(os.path.abspath(MD_PATH))

with open(MD_PATH, encoding='utf-8') as f:
    md = f.read()

sections = []
current = {'type': 'preamble', 'lines': []}

for line in md.split('\n'):
    if line.startswith('# ') and not line.startswith('## '):
        if current['lines']:
            sections.append(current)
        title_text = line[2:]
        if re.match(r'^第[一二三四五六七八九十百千万0-9]+章\s', title_text):
            m = re.match(r'^(第[一二三四五六七八九十百千万0-9]+章)\s+(.+)', title_text)
            current = {'type': 'chapter', 'num': m.group(1), 'title': m.group(2), 'lines': [line]}
        elif title_text.startswith('附录'):
            current = {'type': 'appendix', 'title': title_text, 'lines': [line]}
        else:
            current = {'type': 'cover', 'title': title_text, 'lines': [line]}
    else:
        current['lines'].append(line)

if current['lines']:
    sections.append(current)

toc_entries = []
for s in sections:
    if s['type'] == 'chapter':
        toc_entries.append(f'{s["num"]}  {s["title"]}')
    elif s['type'] == 'appendix':
        toc_entries.append(s['title'])

book_title = next((s.get('title') for s in sections if s['type'] == 'cover'), os.path.splitext(os.path.basename(MD_PATH))[0])


def inline_md_to_html(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def image_to_html(line):
    m = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
    if not m:
        return None
    alt, src = m.groups()
    alt_html = html.escape(alt)
    src_html = html.escape(src)
    kind = 'table-shot' if re.search(r'(table|表)', alt, re.I) else 'figure-shot'
    return (
        f'<figure class="figure-block {kind}">'
        '<div class="figure-frame">'
        f'<img src="{src_html}" alt="{alt_html}">'
        '</div>'
        f'<figcaption><span>VISUAL NOTE</span>{alt_html}</figcaption>'
        '</figure>'
    )


def section_body_to_html(lines):
    out = []
    in_code = False
    in_quote = False
    in_table = False
    for line in lines:
        if line.strip().startswith('```'):
            out.append('</pre>' if in_code else '<pre class="code-block">')
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line)); continue
        if line.strip() == '---':
            out.append('<hr class="section-divider">'); continue
        image_html = image_to_html(line)
        if image_html:
            if in_table:
                out.append('</table></div>'); in_table = False
            out.append(image_html)
            continue
        if line.strip().startswith('> '):
            content = inline_md_to_html(line.strip()[2:])
            if not in_quote: out.append('<blockquote>'); in_quote = True
            out.append(f'<p>{content}</p>'); continue
        elif in_quote and not line.strip().startswith('>'):
            out.append('</blockquote>'); in_quote = False
        if line.startswith('## '): out.append(f'<h2>{inline_md_to_html(line[3:])}</h2>'); continue
        if line.startswith('### '): out.append(f'<h3>{inline_md_to_html(line[4:])}</h3>'); continue
        if line.startswith('# ') and not line.startswith('## '): continue
        if line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c.startswith('-') for c in cells if c.strip()): continue
            tag = 'th' if not in_table else 'td'
            if not in_table:
                out.append('<div class="table-block"><table>')
                in_table = True
            out.append(f'<tr>{"".join(f"<{tag}>{inline_md_to_html(c)}</{tag}>" for c in cells)}</tr>')
            continue
        elif in_table:
            out.append('</table></div>'); in_table = False
        if line.strip().startswith('- '):
            out.append(f'<li>{inline_md_to_html(line.strip()[2:])}</li>'); continue
        if line.strip():
            if line.strip().startswith('**') and line.strip().endswith('**'):
                out.append(f'<p class="bold-para">{inline_md_to_html(line.strip()[2:-2])}</p>')
            else:
                out.append(f'<p>{inline_md_to_html(line)}</p>')
        else:
            out.append('<br>')
    if in_quote: out.append('</blockquote>')
    if in_table: out.append('</table></div>')
    return '\n'.join(out)


# Build body
body_parts = []
reader_nav_entries = [
    {'id': 'cover', 'label': '封面', 'kind': 'meta'},
    {'id': 'contents', 'label': '目录', 'kind': 'meta'},
]
chapter_index = 0
for s in sections:
    if s['type'] == 'cover':
        title = html.escape(s['title'])
        if '\uff1a' in title:
            main, sub = title.split('\uff1a', 1)
        elif ':' in title:
            main, sub = title.split(':', 1)
        else:
            main, sub = title, ''
        sub_html = f'<div class="cover-subtitle">{sub}</div>' if sub else ''
        body_parts.append(f'''<section class="cover-page page-spread" id="cover">
  <div class="cover-grid"></div>
  <div class="cover-content">
    <div class="cover-kicker">TRANSLATED RESEARCH EBOOK</div>
    <h1 class="cover-title">{main}</h1>
    {sub_html}
    <div class="cover-rule"></div>
    <div class="cover-meta">\u4e2d\u6587\u7cbe\u6392\u7248 &middot; PDF TO EBOOK &middot; READING EDITION</div>
  </div>
</section>''')
    elif s['type'] in ('chapter', 'appendix'):
        chapter_index += 1
        chapter_id = f'chapter-{chapter_index}'
        label = '\u9644 \u5f55' if s['type'] == 'appendix' else s['num']
        reader_nav_entries.append({'id': chapter_id, 'label': f'{label} {s["title"]}', 'kind': 'chapter'})
        body_parts.append(f'''<section class="chapter-page page-spread" id="{chapter_id}">
  <div class="chapter-grid"></div>
  <div class="chapter-content">
    <div class="chapter-number">{label}</div>
    <h1 class="chapter-title">{html.escape(s['title'])}</h1>
    <div class="chapter-rule"></div>
  </div>
</section>''')
        bh = section_body_to_html(s['lines'][1:])
        if bh.strip():
            body_parts.append(f'<main class="content-wrapper" id="{chapter_id}-content">\n{bh}\n</main>')
    elif s['type'] == 'preamble':
        bh = section_body_to_html(s['lines'])
        if bh.strip():
            body_parts.append(f'<main class="content-wrapper">\n{bh}\n</main>')

# Insert TOC after cover
final_parts = []
toc_done = False
for part in body_parts:
    final_parts.append(part)
    if 'cover-page' in part and not toc_done:
        rows = '\n'.join(
            f'<div class="toc-item"><span class="toc-num">{i+1}</span><span class="toc-dot">\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7</span><span class="toc-title">{html.escape(e)}</span></div>'
            for i, e in enumerate(toc_entries))
        final_parts.append(f'''<section class="toc-page page-spread" id="contents">
  <div class="toc-grid"></div>
  <div class="toc-content">
    <div class="chapter-number">\u76ee \u5f55</div>
    <h1 class="toc-heading">Contents</h1>
    <div class="toc-list">{rows}</div>
  </div>
</section>''')
        toc_done = True

body_html = '\n'.join(final_parts)

reader_nav_html = '\n'.join(
    f'<a class="reader-nav-link {entry["kind"]}" href="#{entry["id"]}"><span>{i:02d}</span>{html.escape(entry["label"])}</a>'
    for i, entry in enumerate(reader_nav_entries, 1)
)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{html.escape(book_title)}</title>
<style>
  :root {{
    --paper: #fbfaf7;
    --paper-2: #f2f0eb;
    --ink: #111114;
    --muted: #6b6b72;
    --hairline: #dedbd2;
    --blue: #0038ff;
    --blue-dark: #0627a8;
    --lime: #dfff42;
    --orange: #ff6b2f;
    --soft-blue: #eef2ff;
    --code: #f5f5f2;
    --reader-width: min(760px, calc(100vw - 4rem));
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  @page {{ size: A4; margin: 2.35cm 2.1cm; }}

  html, body {{ width: 100%; background-color: var(--paper); }}
  html {{ scroll-behavior:smooth; }}
  body {{
    font-family: 'PingFang SC','Hiragino Sans GB','Microsoft YaHei','STHeiti',sans-serif;
    font-size: 11.2pt; line-height: 1.85; color: var(--ink);
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
    font-feature-settings: "kern" 1;
    orphans: 3; widows: 3;
  }}

  .page-spread {{
    width: 100vw; min-height: 100vh;
    background: var(--paper);
    display: flex; align-items: center; justify-content: center;
    page-break-before: always; page-break-after: always;
    position: relative; overflow: hidden; margin: 0;
  }}
  .cover-page {{
    background:
      linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px),
      linear-gradient(180deg, rgba(255,255,255,.05) 1px, transparent 1px),
      radial-gradient(circle at 82% 18%, rgba(223,255,66,.35), transparent 22%),
      linear-gradient(135deg, var(--blue) 0%, var(--blue-dark) 100%);
    background-size: 38px 38px, 38px 38px, auto, auto;
    color: #fff;
  }}
  .cover-page::before {{
    content:""; position:absolute; inset:7vh 6vw auto auto;
    width:28vw; height:28vw; border:1px solid rgba(255,255,255,.28);
    background: repeating-linear-gradient(135deg, rgba(255,255,255,.22) 0 1px, transparent 1px 9px);
    opacity:.75;
  }}
  .cover-grid,.toc-grid,.chapter-grid {{
    position:absolute; inset:0; opacity:.45; pointer-events:none;
    background-image: radial-gradient(currentColor 1px, transparent 1.2px);
    background-size: 18px 18px; color: rgba(17,17,20,.18);
  }}
  .cover-grid {{ color: rgba(255,255,255,.22); }}
  .cover-content,.toc-content,.chapter-content {{
    position: relative; z-index:2;
    width:min(78vw, 860px); padding:5vh 0;
  }}

  .cover-kicker,.cover-meta,.chapter-number,.toc-num,.toc-heading {{
    font-family:'SF Mono','JetBrains Mono','Menlo',monospace;
    text-transform:uppercase;
  }}
  .cover-kicker {{
    font-size:10pt; letter-spacing:.24em; color:rgba(255,255,255,.75);
    border-bottom:1px solid rgba(255,255,255,.26); padding-bottom:1.1rem;
  }}
  .cover-title {{
    font-size: clamp(42pt, 8vw, 74pt); font-weight:200;
    letter-spacing:0; line-height:.98; margin:9vh 0 2vh;
    max-width:11ch;
  }}
  .cover-subtitle {{ font-size:18pt; color:rgba(255,255,255,.86); line-height:1.45; max-width:28ch; }}
  .cover-rule {{ width:100%; height:2px; background:#fff; margin:8vh 0 1.2rem; opacity:.86; }}
  .cover-meta {{ font-size:9pt; color:rgba(255,255,255,.72); letter-spacing:.18em; }}

  .toc-heading {{
    font-size:12pt; color:var(--blue); letter-spacing:.18em;
    margin:.5rem 0 4vh;
  }}
  .toc-content {{ width:var(--reader-width); }}
  .toc-list {{ text-align:left; margin:0 auto; width:var(--reader-width); border-top:3px solid var(--ink); }}
  .toc-item {{
    display:grid; grid-template-columns:3rem 1fr auto; gap:1rem; align-items:baseline;
    padding:1rem 0; border-bottom:1px solid var(--hairline);
    font-size:11.5pt;
  }}
  .toc-num {{ color:var(--blue); font-weight:700; font-size:12pt; }}
  .toc-dot {{ color:#c9c9c9; overflow:hidden; white-space:nowrap; }}
  .toc-title {{ color:var(--ink); font-weight:600; }}

  .chapter-page {{
    align-items:flex-end; justify-content:flex-start;
    background: linear-gradient(180deg, var(--paper) 0%, var(--paper-2) 100%);
  }}
  .chapter-page::after {{
    content:""; position:absolute; left:0; bottom:0; width:100%; height:18vh;
    background:var(--blue); z-index:0;
  }}
  .chapter-content {{ margin:0 auto 19vh; width:var(--reader-width); }}
  .chapter-number {{
    font-size:13pt; font-weight:700; color:var(--blue);
    letter-spacing:.26em; margin-bottom:2vh;
  }}
  .chapter-title {{
    font-size: clamp(34pt, 5.8vw, 58pt); font-weight:200;
    letter-spacing:0; line-height:1.08; color:var(--ink);
    max-width:13ch;
  }}
  .chapter-rule {{ width:38%; height:3px; background:var(--blue); margin-top:5vh; }}

  .content-wrapper {{
    width:var(--reader-width); margin:0 auto; padding:0 0 2.2rem;
    background:var(--paper) !important;
    -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important;
  }}
  .content-wrapper::before {{
    content:"PDF TO EBOOK · CHINESE EDITION";
    display:block; font-family:'SF Mono','Menlo',monospace; font-size:8pt;
    color:var(--muted); letter-spacing:.18em; border-bottom:1px solid var(--hairline);
    padding-bottom:.55rem; margin-bottom:1.7rem;
  }}

  h2 {{
    font-size:21pt; font-weight:300; line-height:1.25; color:var(--ink);
    margin:2.9rem 0 1rem; padding-top:1.4rem;
    border-top:3px solid var(--ink);
    page-break-after:avoid;
    break-after:avoid;
  }}
  h3 {{
    font-size:13.2pt; font-weight:700; color:var(--ink);
    margin:1.8rem 0 .7rem; padding-left:.8rem;
    border-left:4px solid var(--blue); page-break-after:avoid;
    break-after:avoid;
  }}
  p {{
    margin:.58rem 0; text-align:left; text-indent:0;
    orphans:3; widows:3;
  }}
  p.bold-para {{
    font-weight:700; color:var(--ink); text-indent:0;
    background:var(--soft-blue); border-left:5px solid var(--blue);
    padding:.7rem .9rem; margin:1rem 0;
    page-break-inside:avoid; break-inside:avoid;
  }}
  li {{
    margin:.3rem 0 .3rem 2em; padding-left:.5em; list-style:none; position:relative;
    page-break-inside:avoid; break-inside:avoid;
  }}
  li::before {{ content:'\u25a0'; position:absolute; left:-1.5em; color:var(--blue); font-size:.62em; top:.42em; }}
  .table-block {{
    margin:1.4rem 0;
    page-break-inside:avoid;
    break-inside:avoid;
    break-before:auto;
    break-after:auto;
  }}
  table {{
    width:100%; border-collapse:separate; border-spacing:0; margin:0;
    font-size:9.5pt; border:1px solid var(--hairline);
    background:#fff; page-break-inside:avoid; break-inside:avoid;
  }}
  thead, tbody, tr, th, td {{ page-break-inside:avoid; break-inside:avoid; }}
  th {{ background:var(--ink); color:#fff; font-weight:700; padding:.7rem .85rem; text-align:left; font-size:9pt; }}
  td {{ padding:.62rem .85rem; border-bottom:1px solid var(--hairline); vertical-align:top; }}
  tr:nth-child(even) td {{ background:#f7f7f4; }}
  tr:last-child td {{ border-bottom:none; }}
  blockquote {{
    margin:1.5rem 0; padding:1rem 1.25rem 1rem 1.6rem; background:#fff;
    border-left:6px solid var(--blue); box-shadow:0 12px 32px rgba(0,0,0,.06);
    page-break-inside:avoid;
    break-inside:avoid;
  }}
  blockquote p {{ margin:.2rem 0; text-indent:0; color:#393941; font-size:11.4pt; }}
  pre.code-block {{
    background:var(--code); padding:1rem 1.1rem;
    font-family:'SF Mono',Menlo,monospace; font-size:9pt; line-height:1.5;
    overflow-x:auto; margin:1rem 0; border:1px solid var(--hairline);
  }}
  code {{
    font-family:'SF Mono',Menlo,monospace; font-size:.92em;
    background:var(--code); padding:.08rem .28rem; border:1px solid var(--hairline);
  }}
  .figure-block {{
    margin:1.8rem -1.15rem 2.1rem; padding:1rem;
    background:#fff; border:1px solid var(--hairline);
    page-break-inside:avoid;
    break-inside:avoid;
  }}
  .figure-frame {{
    background:#fff; padding:.4rem; border:1px solid #ece8df;
    page-break-inside:avoid; break-inside:avoid;
  }}
  .figure-block img {{
    display:block; max-width:100%; max-height:68vh; width:auto; height:auto;
    margin:0 auto; background:#fff; object-fit:contain;
    page-break-inside:avoid; break-inside:avoid;
  }}
  .figure-block figcaption {{
    margin-top:.75rem; color:var(--ink); font-size:9.4pt; line-height:1.55;
    text-align:left; display:grid; grid-template-columns:7.5rem 1fr; gap:.8rem;
    border-top:1px solid var(--hairline); padding-top:.65rem;
    page-break-inside:avoid; break-inside:avoid;
  }}
  .figure-block figcaption span {{
    font-family:'SF Mono','Menlo',monospace; color:var(--blue); letter-spacing:.14em;
    font-size:8pt; text-transform:uppercase;
  }}
  .table-shot {{ background:#f7f7f4; }}
  strong {{ color:var(--ink); font-weight:800; }}
  hr.section-divider {{ border:none; text-align:center; margin:2rem 0; }}
  hr.section-divider::after {{ content:'\u25a0 \u25a0 \u25a0'; color:var(--blue); font-size:8pt; letter-spacing:.6em; }}

  .reader-nav {{
    position:fixed; right:18px; top:18px; bottom:18px; z-index:50;
    width:220px; padding:14px 12px;
    background:rgba(251,250,247,.92); backdrop-filter:blur(14px);
    border:1px solid rgba(17,17,20,.12);
    box-shadow:0 20px 60px rgba(0,0,0,.12);
    overflow:auto;
    transition:width .2s ease, padding .2s ease;
  }}
  .reader-nav-toggle {{
    width:100%; border:0; background:transparent; color:var(--blue);
    display:flex; align-items:center; justify-content:space-between; gap:8px;
    font-family:'SF Mono','Menlo',monospace; font-size:10px;
    letter-spacing:.18em; text-transform:uppercase; cursor:pointer;
    padding:4px 4px 10px; border-bottom:2px solid var(--ink);
    margin-bottom:8px; text-align:left;
  }}
  .reader-nav-toggle::after {{ content:"−"; font-size:14px; line-height:1; color:var(--ink); }}
  .reader-nav-links {{ display:block; }}
  .reader-nav.is-collapsed {{
    width:48px; padding:10px 8px; bottom:auto; overflow:hidden;
  }}
  .reader-nav.is-collapsed .reader-nav-toggle {{
    writing-mode:vertical-rl; min-height:150px; border-bottom:0; margin-bottom:0;
    border-left:2px solid var(--ink); padding:6px 4px; justify-content:flex-start;
  }}
  .reader-nav.is-collapsed .reader-nav-toggle::after {{ content:"+"; writing-mode:horizontal-tb; margin-top:8px; }}
  .reader-nav.is-collapsed .reader-nav-links {{ display:none; }}
  .reader-nav.is-collapsed .reader-nav-title-full {{ display:none; }}
  .reader-nav.is-collapsed .reader-nav-title-short {{ display:inline; }}
  .reader-nav-title-short {{ display:none; }}
  .reader-nav-title-full {{ display:inline; }}
  .reader-nav-link {{
    display:grid; grid-template-columns:28px minmax(0,1fr); gap:8px; align-items:start;
    padding:8px 4px; text-decoration:none; color:var(--ink);
    border-bottom:1px solid var(--hairline);
    font-size:12px; line-height:1.35;
    text-align:left;
  }}
  .reader-nav-link span {{
    font-family:'SF Mono','Menlo',monospace; color:var(--blue);
    font-size:10px; letter-spacing:.08em;
  }}
  .reader-nav-link.meta {{ color:var(--muted); }}
  .reader-nav-link:hover {{ color:var(--blue); background:var(--soft-blue); }}

  @media screen and (max-width: 1180px) {{
    .reader-nav {{
      left:12px; right:12px; top:auto; bottom:12px; width:auto; max-height:32vh;
      display:block;
    }}
    .reader-nav-link {{ grid-template-columns:28px 1fr; }}
  }}

  @media print {{
    @page {{ size: A4; margin: 2.35cm 2.1cm; }}
    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
    html, body {{ max-width: none; padding: 0; font-size: 10.35pt; background: var(--paper) !important; }}
    .cover-page,.toc-page,.chapter-page {{
      width:100%; height:100vh;
      -webkit-print-color-adjust:exact; print-color-adjust:exact;
    }}
    :root {{ --reader-width: 100%; }}
    .content-wrapper {{ width:var(--reader-width); margin:0 auto; padding:0 0 2rem; background:var(--paper) !important; -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
    .chapter-content,.toc-content,.toc-list {{ width:var(--reader-width); }}
    h2 {{ page-break-before:auto; page-break-after:avoid; }}
    h3 {{ page-break-after:avoid; }}
    p {{ orphans:3; widows:3; }}
    blockquote,.table-block,table,tr,td,th,.figure-block,.figure-frame,.figure-block img,.figure-block figcaption,p.bold-para {{
      page-break-inside:avoid !important;
      break-inside:avoid !important;
    }}
    .figure-block img {{ max-height:66vh; }}
    .reader-nav {{ display:none !important; }}
  }}
</style>
</head>
<body>
<aside class="reader-nav" id="readerNav" aria-label="HTML \u9605\u8bfb\u76ee\u5f55">
  <button class="reader-nav-toggle" id="readerNavToggle" type="button" aria-controls="readerNavLinks" aria-expanded="true">
    <span class="reader-nav-title-full">Reading Navigation</span>
    <span class="reader-nav-title-short">Nav</span>
  </button>
  <div class="reader-nav-links" id="readerNavLinks">
    {reader_nav_html}
  </div>
</aside>
{body_html}
<script>
  (function() {{
    const nav = document.getElementById('readerNav');
    const btn = document.getElementById('readerNavToggle');
    const key = 'pdf-to-ebook-reader-nav-collapsed';
    if (!nav || !btn) return;
    function setCollapsed(on) {{
      nav.classList.toggle('is-collapsed', on);
      btn.setAttribute('aria-expanded', on ? 'false' : 'true');
      try {{ localStorage.setItem(key, on ? '1' : '0'); }} catch (e) {{}}
    }}
    try {{ setCollapsed(localStorage.getItem(key) === '1'); }} catch (e) {{}}
    btn.addEventListener('click', function() {{
      setCollapsed(!nav.classList.contains('is-collapsed'));
    }});
  }})();
</script>
</body>
</html>'''

os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)) or '.', exist_ok=True)

with open(OUT_PATH, 'w') as f:
    f.write(html)

print(f'OK {len(html)} bytes, {len(sections)} sections, {len(toc_entries)} TOC entries')

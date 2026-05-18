#!/usr/bin/env python3
"""Generate beautifully designed HTML ebook from markdown."""

import re, os

MD_PATH = os.path.expanduser('~/.openclaw-autoclaw/workspace/claude-ebook/创业者的AI实战手册_中文版.md')
OUT_PATH = os.path.expanduser('~/.openclaw-autoclaw/workspace/claude-ebook/创业者的AI实战手册.html')

with open(MD_PATH) as f:
    md = f.read()

sections = []
current = {'type': 'preamble', 'lines': []}

for line in md.split('\n'):
    if line.startswith('# ') and not line.startswith('## '):
        if current['lines']:
            sections.append(current)
        title_text = line[2:]
        if re.match(r'^第[一二三四五六七八九十]+章\s', title_text):
            m = re.match(r'^(第[一二三四五六七八九十]+章)\s+(.+)', title_text)
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


def section_body_to_html(lines):
    out = []
    in_code = False
    in_quote = False
    for line in lines:
        if line.strip().startswith('```'):
            out.append('</pre>' if in_code else '<pre class="code-block">')
            in_code = not in_code
            continue
        if in_code:
            out.append(line); continue
        if line.strip() == '---':
            out.append('<hr class="section-divider">'); continue
        if line.strip().startswith('> '):
            content = line.strip()[2:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            if not in_quote: out.append('<blockquote>'); in_quote = True
            out.append(f'<p>{content}</p>'); continue
        elif in_quote and not line.strip().startswith('>'):
            out.append('</blockquote>'); in_quote = False
        if line.startswith('## '): out.append(f'<h2>{line[3:]}</h2>'); continue
        if line.startswith('### '): out.append(f'<h3>{line[4:]}</h3>'); continue
        if line.startswith('# ') and not line.startswith('## '): continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        if line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c.startswith('-') for c in cells if c.strip()): continue
            tag = 'th' if (out and out[-1] == '<table>') else 'td'
            if not out or out[-1] != '<table>': out.append('<table>')
            out.append(f'<tr>{"".join(f"<{tag}>{c}</{tag}>" for c in cells)}</tr>')
            continue
        elif out and out[-1].startswith('<tr>') and not line.startswith('|'):
            out.append('</table>')
        if line.strip().startswith('- '):
            out.append(f'<li>{line.strip()[2:]}</li>'); continue
        if line.strip():
            if line.strip().startswith('**') and line.strip().endswith('**'):
                out.append(f'<p class="bold-para">{line.strip()[2:-2]}</p>')
            else:
                out.append(f'<p>{line}</p>')
        else:
            out.append('<br>')
    if in_quote: out.append('</blockquote>')
    return '\n'.join(out)


# Build body
body_parts = []
for s in sections:
    if s['type'] == 'cover':
        title = s['title']
        if '\uff1a' in title:
            main, sub = title.split('\uff1a', 1)
        elif ':' in title:
            main, sub = title.split(':', 1)
        else:
            main, sub = title, ''
        sub_html = f'<div class="cover-subtitle">{sub}</div>' if sub else ''
        body_parts.append(f'''<div class="cover-page">
  <div class="cover-content">
    <div class="cover-line"></div>
    <h1 class="cover-title">{main}</h1>
    {sub_html}
    <div class="cover-line"></div>
    <div class="cover-meta">Anthropic &middot; 2026 &middot; \u4e2d\u6587\u7248</div>
  </div>
</div>''')
    elif s['type'] in ('chapter', 'appendix'):
        label = '\u9644 \u5f55' if s['type'] == 'appendix' else s['num']
        body_parts.append(f'''<div class="chapter-page">
  <div class="chapter-content">
    <div class="chapter-number">{label}</div>
    <h1 class="chapter-title">{s['title']}</h1>
    <div class="chapter-dot"></div>
  </div>
</div>''')
        bh = section_body_to_html(s['lines'][1:])
        if bh.strip():
            body_parts.append(f'<div class="content-wrapper">\n{bh}\n</div>')
    elif s['type'] == 'preamble':
        bh = section_body_to_html(s['lines'])
        if bh.strip():
            body_parts.append(f'<div class="content-wrapper">\n{bh}\n</div>')

# Insert TOC after cover
final_parts = []
toc_done = False
for part in body_parts:
    final_parts.append(part)
    if 'cover-page' in part and not toc_done:
        rows = '\n'.join(
            f'<div class="toc-item"><span class="toc-num">{i+1}</span><span class="toc-dot">\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7</span><span class="toc-title">{e}</span></div>'
            for i, e in enumerate(toc_entries))
        final_parts.append(f'''<div class="toc-page">
  <div class="toc-content">
    <div class="chapter-number">\u76ee \u5f55</div>
    <div class="toc-list">{rows}</div>
  </div>
</div>''')
        toc_done = True

body_html = '\n'.join(final_parts)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>\u521b\u4e1a\u8005\u7684 AI \u5b9e\u6218\u624b\u518c</title>
<style>
  :root {{
    --bg: #faf7f2;
    --bg2: #f5efe4;
    --gold: #c9a84c;
    --gold2: #a07030;
    --dk: #1a1a2e;
    --txt: #2d2d2d;
    --accent: #d4a574;
    --border: #e8e0d5;
    --hl: #fef9f3;
    --code: #f4f1ec;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  @page {{ size: A4; margin: 2.8cm 2.5cm; }}

  html, body {{ width: 100%; background-color: #ffffff; }}
  body {{
    font-family: 'STSong','Songti SC','PingFang SC',serif;
    font-size: 12pt; line-height: 1.9; color: var(--txt);
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }}

  .cover-page,.toc-page,.chapter-page {{
    width: 100vw; min-height: 100vh;
    background: linear-gradient(160deg,var(--bg) 0%,#faf7f2 40%,var(--bg2) 100%);
    display: flex; align-items: center; justify-content: center;
    page-break-before: always; page-break-after: always;
    position: relative; overflow: hidden; margin: 0;
  }}
  .cover-page::after,.toc-page::after,.chapter-page::after {{
    content:''; position: absolute; top:0; left:0;
    width:10px; height:100%;
    background: linear-gradient(180deg,var(--gold) 0%,var(--gold2) 100%); z-index:1;
  }}
  .cover-content,.toc-content,.chapter-content {{
    text-align: center; position: relative; z-index:2;
    padding:4rem 3rem; max-width:600px;
  }}

  .cover-title {{
    font-family: 'PingFang SC','Heiti SC',sans-serif;
    font-size:32pt; font-weight:700; color:var(--dk);
    letter-spacing:.06em; line-height:1.4; margin:1rem 0;
  }}
  .cover-subtitle {{ font-size:14pt; color:#8b7355; letter-spacing:.1em; margin:.8rem 0; }}
  .cover-line {{ width:60px; height:1.5px; background:var(--gold); margin:1rem auto; }}
  .cover-meta {{ font-size:10pt; color:#b0a090; letter-spacing:.2em; margin-top:1.5rem; }}

  .toc-list {{ text-align:left; margin:2.5rem auto 0; max-width:440px; }}
  .toc-item {{
    display:flex; align-items:baseline; padding:.6rem 0;
    border-bottom:1px dotted var(--border); font-size:11pt;
    font-family:'PingFang SC','Heiti SC',sans-serif;
  }}
  .toc-item:last-child {{ border-bottom:none; }}
  .toc-num {{ color:var(--gold); font-weight:700; font-size:14pt; min-width:1.8rem; }}
  .toc-dot {{ flex:1; color:#d0c8b8; overflow:hidden; white-space:nowrap; margin:0 .5rem; }}
  .toc-title {{ color:var(--dk); font-weight:500; white-space:nowrap; }}

  .chapter-number {{
    font-family:'PingFang SC','Heiti SC',sans-serif;
    font-size:12pt; font-weight:500; color:var(--gold);
    letter-spacing:.3em; margin-bottom:1.5rem;
  }}
  .chapter-title {{
    font-family:'PingFang SC','Heiti SC',sans-serif;
    font-size:26pt; font-weight:700; color:var(--dk);
    letter-spacing:.06em; line-height:1.5;
  }}
  .chapter-dot {{ width:6px; height:6px; background:var(--gold); border-radius:50%; margin:2rem auto 0; }}

  .content-wrapper {{ max-width:680px; margin:0 auto; padding:0 0 2rem; background:#ffffff !important; -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}

  h2 {{
    font-family:'PingFang SC','Heiti SC',sans-serif;
    font-size:18pt; font-weight:700; color:var(--dk);
    margin:2.5rem 0 1rem; padding-top:1.5rem; letter-spacing:.03em;
    page-break-after:avoid;
  }}
  h3 {{
    font-family:'PingFang SC','Heiti SC',sans-serif;
    font-size:13pt; font-weight:600; color:var(--dk);
    margin:1.6rem 0 .6rem; padding-left:.7rem;
    border-left:3px solid var(--accent); page-break-after:avoid;
  }}
  p {{ margin:.5rem 0; text-align:justify; text-indent:2em; }}
  p.bold-para {{ font-weight:600; color:var(--dk); }}
  li {{ margin:.3rem 0 .3rem 2em; padding-left:.5em; list-style:none; position:relative; }}
  li::before {{ content:'\u2022'; position:absolute; left:-1.5em; color:var(--accent); font-weight:bold; }}
  table {{
    width:100%; border-collapse:collapse; margin:1.2rem 0; font-size:10pt;
    border-radius:6px; overflow:hidden;
    box-shadow:0 1px 4px rgba(0,0,0,.06); page-break-inside:avoid;
  }}
  th {{ background:var(--dk); color:#fff; font-weight:600; padding:.6rem 1rem; text-align:left; font-size:9.5pt; }}
  td {{ padding:.5rem 1rem; border-bottom:1px solid var(--border); }}
  tr:last-child td {{ border-bottom:none; }}
  blockquote {{
    margin:1.2rem 0; padding:.8rem 1.2rem; background:var(--hl);
    border-left:4px solid var(--accent); border-radius:0 6px 6px 0; page-break-inside:avoid;
  }}
  blockquote p {{ margin:.2rem 0; text-indent:0; color:#666; }}
  pre.code-block {{
    background:var(--code); padding:.8rem 1rem; border-radius:6px;
    font-family:'SF Mono',Menlo,monospace; font-size:9pt; line-height:1.5;
    overflow-x:auto; margin:1rem 0; border:1px solid var(--border);
  }}
  strong {{ color:var(--dk); font-weight:700; }}
  hr.section-divider {{ border:none; text-align:center; margin:2rem 0; }}
  hr.section-divider::after {{ content:'\u25c6 \u25c6 \u25c6'; color:var(--accent); font-size:9pt; letter-spacing:.5em; }}

  @media print {{
    @page {{ size: A4; margin: 2.8cm 2.5cm; }}
    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
    html, body {{ max-width: none; padding: 0; font-size: 10.5pt; background: #ffffff !important; }}
    .cover-page,.toc-page,.chapter-page {{
      width:100%; height:100vh;
      -webkit-print-color-adjust:exact; print-color-adjust:exact;
    }}
    .content-wrapper {{ max-width:680px; margin:0 auto; padding:0 0 2rem; background:#ffffff !important; -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
    h2 {{ page-break-before:auto; page-break-after:avoid; }}
    blockquote,table {{ page-break-inside:avoid; }}
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>'''

with open(OUT_PATH, 'w') as f:
    f.write(html)

print(f'OK {len(html)} bytes, {len(sections)} sections, {len(toc_entries)} TOC entries')

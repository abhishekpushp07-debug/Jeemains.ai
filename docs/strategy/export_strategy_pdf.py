"""Build the portable strategy reference. Documentation tooling, not app runtime.

Isolated dependencies: reportlab==4.4.10, Markdown==3.10.2, PyMuPDF.
Example: PYTHONPATH=/tmp/tejas-pdf-tools python docs/strategy/export_strategy_pdf.py
Only allowlisted documentation is exported; original source PDFs and raw logs are excluded.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import fitz
import markdown
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'frontend/public/downloads'
NAME = 'Tejas_10_Packet_Strategy_v1.0.pdf'
SOURCES = [
    'docs/strategy/CONTEXT_RESTORE_SNAPSHOT.md',
    'docs/strategy/TEN_PACKET_STRATEGY.md',
    'docs/strategy/SLO_AND_WORKLOAD.md',
    'docs/strategy/QUALIFICATION_AND_HANDOFF.md',
    'docs/audit/AUDIT_REPORT.md',
    'docs/audit/RULEBOOK_ERRATA.md',
    'docs/audit/REQUIREMENTS_MATRIX.md',
    'docs/audit/analytics_60_matrix.csv',
]
TOKENS = {
    'maroon': '#5C0025', 'ink': '#111827', 'muted': '#4B5563',
    'line': '#E5E7EB', 'soft': '#F6E9EE', 'paper': '#FFFFFF',
    'table_head': '#F3F4F6', 'stripe': '#FAFAFA',
    'margin_x': 16 * mm, 'margin_y': 18 * mm,
    'body': 10.5, 'small': 9, 'caption': 8, 'code': 9,
    'h1': 18, 'h2': 14, 'h3': 12, 'cover': 26,
    'after': 6, 'pad': 5, 'heading_before': 14,
}
STAMP = datetime.now(timezone.utc)
DATE = STAMP.strftime('%Y-%m-%d')
W, H = A4
WIDTH = W - 2 * TOKENS['margin_x']
MANIFEST = [{
    'path': path,
    'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
} for path in SOURCES]
SOURCE_DIGEST = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True).encode()).hexdigest()

font_dir = Path('/usr/share/fonts/truetype/liberation')
for name, file in [
    ('Body', 'LiberationSans-Regular.ttf'), ('BodyBold', 'LiberationSans-Bold.ttf'),
    ('BodyItalic', 'LiberationSans-Italic.ttf'), ('BodyBI', 'LiberationSans-BoldItalic.ttf'),
    ('Code', 'LiberationMono-Regular.ttf'),
]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / file)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBI')

styles = {}
styles['body'] = ParagraphStyle('body', fontName='Body', fontSize=TOKENS['body'],
    leading=TOKENS['body'] * 1.35, textColor=colors.HexColor(TOKENS['ink']),
    spaceAfter=TOKENS['after'], splitLongWords=True, allowWidows=0, allowOrphans=0)
for name, size in [('h1', TOKENS['h1']), ('h2', TOKENS['h2']), ('h3', TOKENS['h3'])]:
    styles[name] = ParagraphStyle(name, parent=styles['body'], fontName='BodyBold',
        fontSize=size, leading=size * 1.2, textColor=colors.HexColor(TOKENS['maroon']),
        spaceBefore=TOKENS['heading_before'], spaceAfter=8, keepWithNext=True)
styles['small'] = ParagraphStyle('small', parent=styles['body'], fontSize=TOKENS['small'], leading=12)
styles['cell'] = ParagraphStyle('cell', parent=styles['small'], spaceAfter=0)
styles['code'] = ParagraphStyle('code', parent=styles['small'], fontName='Code',
    fontSize=TOKENS['code'], leading=11.5, backColor=colors.HexColor(TOKENS['table_head']), borderPadding=8)
styles['bullet'] = ParagraphStyle('bullet', parent=styles['body'], leftIndent=15, firstLineIndent=-10)
styles['cover'] = ParagraphStyle('cover', parent=styles['h1'], fontSize=TOKENS['cover'], leading=32)
styles['toc0'] = ParagraphStyle('toc0', parent=styles['body'], fontName='BodyBold',
    fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4)
styles['toc1'] = ParagraphStyle('toc1', parent=styles['body'], leftIndent=14,
    fontSize=10, leading=13, spaceBefore=2, spaceAfter=3)


class StrategyDoc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=TOKENS['margin_x'],
            rightMargin=TOKENS['margin_x'], topMargin=TOKENS['margin_y'],
            bottomMargin=TOKENS['margin_y'], title='Tejas — 10-Packet Strategy | Portable Reference v1.0',
            author='Tejas Project', subject='Strategy snapshot; implementation not started; 500k unqualified')
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='main', frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Body', 8)
        canvas.setFillColor(colors.HexColor(TOKENS['muted']))
        if doc.page > 1:
            canvas.drawString(self.leftMargin, H - 11 * mm, 'TEJAS  /  10-PACKET STRATEGY')
            canvas.drawRightString(W - self.rightMargin, H - 11 * mm, 'PORTABLE REFERENCE — NOT A RELEASE CERTIFICATE')
        canvas.setStrokeColor(colors.HexColor(TOKENS['line']))
        canvas.line(self.leftMargin, H - 14 * mm, W - self.rightMargin, H - 14 * mm)
        canvas.line(self.leftMargin, 14 * mm, W - self.rightMargin, 14 * mm)
        canvas.drawString(self.leftMargin, 9 * mm, f'v1.0  |  {DATE} UTC')
        canvas.drawCentredString(W / 2, 9 * mm, f'Sources {SOURCE_DIGEST[:8]}')
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, '_outline'):
            level, title, key = flowable._outline
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level, closed=False)
            self.notify('TOCEntry', (level, html.escape(title), self.page, key))


story = []
heading_counter = 0


def heading(text, level=0, style='h1'):
    global heading_counter
    heading_counter += 1
    para = Paragraph(html.escape(text), styles[style])
    para._outline = (level, text, f'section-{heading_counter}')
    story.append(para)


def para(text, style='body'):
    story.append(Paragraph(text, styles[style]))


def rich(elem):
    out = html.escape(elem.text or '')
    for child in elem:
        content = rich(child)
        if child.tag == 'strong':
            out += '<b>' + content + '</b>'
        elif child.tag == 'em':
            out += '<i>' + content + '</i>'
        elif child.tag == 'code':
            out += '<font name="Code" size="9">' + content + '</font>'
        elif child.tag == 'a':
            href = child.get('href', '')
            if href.startswith(('https://', 'http://')):
                out += f'<a href="{html.escape(href, quote=True)}" color="{TOKENS["maroon"]}">{content}</a>'
            else:
                out += content
        elif child.tag == 'br':
            out += '<br/>'
        else:
            out += content
        out += html.escape(child.tail or '')
    return out


def table(rows):
    count = len(rows[0])
    # Small ID/status columns stay legible. Wide narrative audit rows become
    # labelled records rather than cramped five-column tables.
    if count >= 5 or (count == 4 and rows[0][0].getPlainText() == 'ID'):
        labels = [x.getPlainText() for x in rows[0]]
        for row in rows[1:]:
            start = len(story)
            para('<b>' + html.escape(row[0].getPlainText()) + '</b>', 'h3')
            for label, value in zip(labels[1:], row[1:]):
                para('<b>' + html.escape(label) + ':</b> ' + value.text, 'small')
            story[start:] = [KeepTogether(story[start:])]
        return
    if count == 2:
        ratios = [0.30, 0.70]
    elif count == 3:
        ratios = [0.26, 0.29, 0.45]
    elif count == 4:
        ratios = [0.13, 0.51, 0.18, 0.18]
    else:
        ratios = [1 / count] * count
    tbl = Table(rows, colWidths=[WIDTH * x for x in ratios], repeatRows=1,
        hAlign='LEFT', spaceBefore=4, spaceAfter=10)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(TOKENS['table_head'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(TOKENS['paper']), colors.HexColor(TOKENS['stripe'])]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), TOKENS['pad']),
        ('RIGHTPADDING', (0, 0), (-1, -1), TOKENS['pad']),
        ('TOPPADDING', (0, 0), (-1, -1), TOKENS['pad']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), TOKENS['pad']),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.HexColor(TOKENS['maroon'])),
        ('LINEBELOW', (0, 1), (-1, -1), 0.3, colors.HexColor(TOKENS['line'])),
    ]))
    story.append(tbl)


def render_markdown(text, section_title=None, packets=False):
    # Python-Markdown requires a blank before a list following prose. Add only
    # presentation whitespace, leaving embedded original sources unchanged.
    lines = []
    fenced = False
    for line in text.splitlines():
        if line.startswith('```'):
            fenced = not fenced
        if not fenced and re.match(r'^(?:- |\d+\. )', line):
            if lines and lines[-1].strip() and not re.match(r'^(?:- |\d+\. )', lines[-1]):
                lines.append('')
        lines.append(line)
    tree = ET.fromstring('<root>' + markdown.markdown('\n'.join(lines), extensions=['tables', 'fenced_code']) + '</root>')
    title_seen = False
    for elem in tree:
        tag = elem.tag
        if tag == 'h1':
            title = section_title if section_title and not title_seen else ''.join(elem.itertext())
            heading(title)
            title_seen = True
        elif tag in ('h2', 'h3', 'h4'):
            title = ''.join(elem.itertext())
            if packets and re.match(r'Packet \d{2} ', title):
                story.append(PageBreak())
                heading(title, level=1, style='h1')
            else:
                para(rich(elem), 'h2' if tag == 'h2' else 'h3')
        elif tag == 'p':
            para(rich(elem), 'h3' if ''.join(elem.itertext()) == 'Build/deliver' else 'body')
        elif tag in ('ul', 'ol'):
            start = int(elem.get('start', 1))
            for index, li in enumerate(elem.findall('li'), start=start):
                prefix = '•' if tag == 'ul' else f'{index}.'
                para(html.escape(prefix) + ' ' + rich(li), 'bullet')
        elif tag == 'table':
            rows = []
            for tr in elem.iter('tr'):
                row = []
                for td in tr:
                    content = rich(td)
                    if td.tag == 'th':
                        content = '<b>' + content + '</b>'
                    row.append(Paragraph(content, styles['cell']))
                rows.append(row)
            table(rows)
        elif tag == 'pre':
            for line in ''.join(elem.itertext()).splitlines():
                wrapped = textwrap.wrap(line, width=82, replace_whitespace=False, drop_whitespace=False) or [' ']
                for part in wrapped:
                    para(html.escape(part).replace(' ', '&#160;'), 'code')
        elif tag == 'blockquote':
            for p in elem:
                para(rich(p), 'small')
        elif tag != 'hr':
            raise ValueError(f'Unhandled Markdown block: {tag}')


def source_section(path, title=None, packets=False):
    story.append(PageBreak())
    render_markdown((ROOT / path).read_text(), title, packets)


OUT.mkdir(parents=True, exist_ok=True)
para('TEJAS / ENGINEERING REFERENCE', 'h3')
story.append(Spacer(1, 20 * mm))
para('10-Packet<br/>Implementation Strategy', 'cover')
para('Portable reference for a 5-lakh concurrent-attempt target', 'h2')
para('Full strategy • measurable gates • audit baseline • context restore', 'body')
story.append(Spacer(1, 10 * mm))
para('<b>STATUS: STRATEGY SNAPSHOT — IMPLEMENTATION NOT STARTED</b>')
para('Packet 1 is approved to begin after this PDF is delivered. This document does not certify capacity, fix audit findings, provision infrastructure, rotate staff credentials, or approve an exam for publication.')
para('<b>Non-negotiable:</b> phone-only student entry, matte-maroon UI, exact question–solution pairing, offline answer recovery and honest evidence-backed progress.')
para(f'<b>Version:</b> 1.0<br/><b>Generated:</b> {STAMP.isoformat(timespec="seconds")}<br/><b>Included:</b> all 10 packets, SLO/workload contract, operator gates, full audit/errata, 62 requirement rows and 60 analysis records.')
para('Keep this file with the five original specification PDFs. Upload it in a future session and ask the agent to read “Context restore” before continuing.', 'small')

source_section(SOURCES[0])
story.append(PageBreak())
para('Contents', 'h1')
para('Click an entry or use the PDF bookmarks. Appendices are reference material, not extra implementation packets.', 'small')
toc = TableOfContents()
toc.levelStyles = [styles['toc0'], styles['toc1']]
toc.dotsMinLevel = 0
story.append(toc)

source_section(SOURCES[1], 'The 10-packet strategy — full source', packets=True)
source_section(SOURCES[2], 'Appendix A — Workload and SLO contract')
source_section(SOURCES[3], 'Appendix B — Qualification and operator handoff')
source_section(SOURCES[4], 'Appendix C — Full architecture audit')
source_section(SOURCES[5], 'Appendix C.1 — Rulebook errata')
source_section(SOURCES[6], 'Appendix D — All 62 audited requirement rows')

story.append(PageBreak())
heading('Appendix E — All 60 analysis records')
para('Source: docs/audit/analytics_60_matrix.csv. These are historical implementation-status records, not full metric definitions or passing acceptance tests. All 60 analyses are mandatory. Analytics IDs A01–A60 are a separate namespace from audit defect IDs A01–A08.')
for row in csv.DictReader(io.StringIO((ROOT / SOURCES[7]).read_text())):
    start = len(story)
    para(html.escape(f'{row["id"]} — {row["name"]}'), 'h3')
    for key, label in [('pdf_page', 'PDF-04 page'), ('status', 'Status'), ('observation', 'Observation'), ('evidence', 'Evidence'), ('scope_note', 'Scope note')]:
        para('<b>' + label + ':</b> ' + html.escape(row[key]), 'small')
    story[start:] = [KeepTogether(story[start:])]

story.append(PageBreak())
heading('Appendix F — Traceability and source hashes')
para('The following SHA-256 identities bind this export to its source snapshot. The full text of the allowlisted Markdown documents and original analytics CSV is also embedded as PDF file attachments for exact recovery in compatible PDF tools. Raw test reports, original specification PDFs, credentials and source URLs are excluded.')
for item in MANIFEST:
    para(html.escape(item['path']), 'h3')
    para('SHA-256: ' + item['sha256'], 'code')
para('Source-bundle digest (canonical source inventory): ' + SOURCE_DIGEST, 'small')
script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
para('Generator: docs/strategy/export_strategy_pdf.py', 'small')
para('SHA-256: ' + script_hash, 'code')
para('Renderer dependencies: ReportLab 4.4.10; Markdown 3.10.2; PyMuPDF ' + fitz.VersionBind, 'small')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
para('Repository baseline commit: ' + commit + '. The working tree also contains uncommitted documentation; the file hashes above identify the exported content.', 'small')
para('Original five specification PDFs — identities only', 'h2')
guides = json.loads((ROOT / 'docs/source_guides/manifest.json').read_text())
for guide in sorted(guides, key=lambda g: g['name']):
    actual = hashlib.sha256((ROOT / 'docs/source_guides' / guide['name']).read_bytes()).hexdigest()
    if actual != guide['sha256']:
        raise ValueError('Source PDF hash mismatch; export stopped')
    para(html.escape(guide['name']), 'h3')
    para(f'Pages: {guide["pages"]}. Original PDF not embedded.', 'small')
    para('SHA-256: ' + guide['sha256'], 'code')
para('Total: 177 source pages. This identity list does not replace the original clauses or prove complete atomic traceability.', 'small')

story.append(PageBreak())
heading('Appendix G — Status and next development action')
para('<b>All ten packets: NOT STARTED implementation at this snapshot.</b> Packet 1 is approved next; later packets remain dependency-gated.')
para('Open correctness/security findings are recorded in Appendix C; their owning repair packets are listed in Appendix B. No application code, database, environment value, credential or session was changed to produce this export.')
para('Credential incident: rotation and session revocation are still pending separate confirmation and secure authorized execution.')
para('The original paper and QA fixture status in the audit are historical observations, not freshly verified database state in this export.')
para('The strategy references two absent coverage artifacts: coverage_manifest.json and COVERAGE_MATRIX.md. Resolve this in Packet 1; do not assume the 62-row audit matrix maps every mandatory clause of all five PDFs.')
para('Legacy rulebook guidance saying 40 analyses is superseded by the source requirement for all 60. The source strategy’s “proposed for approval” label is historical; see the current user decision in Context restore. No approval of all proposed SLOs, operator decisions or launch readiness is inferred.')
para('Next: inspect the current repository, then execute Packet 1’s rules, safety and regression baseline. Do not silently implement later packets or claim 500k readiness.')
para('This is a searchable, bookmarked reference PDF. Formal tagged-PDF/PDF-UA accessibility certification is not claimed.', 'small')

raw_path = OUT / '_strategy_rendered.pdf'
StrategyDoc(raw_path).multiBuild(story)
doc = fitz.open(raw_path)
for page in doc:
    footer = f'Page {page.number + 1} / {len(doc)}'
    page.insert_textbox(fitz.Rect(W - TOKENS['margin_x'] - 85, H - 12 * mm, W - TOKENS['margin_x'], H - 6 * mm),
        footer, fontsize=8, fontname='helv', color=(0.294, 0.333, 0.388), align=fitz.TEXT_ALIGN_RIGHT)
for path in SOURCES:
    doc.embfile_add(Path(path).name, (ROOT / path).read_bytes(), filename=Path(path).name,
        desc='Source snapshot: ' + path)
manifest = {
    'version': '1.0', 'generated_at_utc': STAMP.isoformat(), 'sources': MANIFEST,
    'bundle_sha256': SOURCE_DIGEST, 'generator_sha256': script_hash,
    'guide_identities': [{k: g[k] for k in ['name', 'sha256', 'pages']} for g in guides],
    'implementation_status': 'NOT_STARTED', 'capacity_status': 'UNQUALIFIED',
}
doc.embfile_add('source_manifest.json', json.dumps(manifest, indent=2).encode(),
    filename='source_manifest.json', desc='No URLs or credentials; content identity only')
final_path = OUT / NAME
doc.save(final_path, garbage=4, deflate=True)
page_count = len(doc)
doc.close()
raw_path.unlink()
manifest['pdf_sha256'] = hashlib.sha256(final_path.read_bytes()).hexdigest()
manifest['pdf_pages'] = page_count
manifest['pdf_bytes'] = final_path.stat().st_size
(ROOT / 'docs/strategy/PDF_EXPORT_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'path': str(final_path), 'pages': page_count, 'bytes': final_path.stat().st_size, 'sha256': manifest['pdf_sha256']}))

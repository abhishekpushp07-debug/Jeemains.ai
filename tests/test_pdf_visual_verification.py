"""Visual verification of PDF content - render key pages and verify specific elements."""
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("Missing PyMuPDF. Install with: pip install PyMuPDF")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / 'frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf'
OUTPUT_DIR = ROOT / 'test_reports/pdf_renders'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def render_page(doc, page_num, output_name, description):
    """Render a specific page to PNG."""
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for clarity
    output_path = OUTPUT_DIR / f"{output_name}.png"
    pix.save(str(output_path))
    print(f"✅ Rendered {description}: {output_path}")
    return output_path

def main():
    print("=" * 70)
    print("PDF VISUAL VERIFICATION")
    print("=" * 70)
    
    doc = fitz.open(PDF_PATH)
    print(f"\nLoaded PDF: {len(doc)} pages\n")
    
    # Get TOC/bookmarks to find actual page numbers
    toc = doc.get_toc()
    page_map = {}
    for level, title, page_num in toc:
        page_map[title] = page_num - 1  # Convert to 0-indexed
    
    # Key pages to render (derive from bookmarks where possible)
    renders = [
        (0, "01_cover", "Cover page"),
        (3, "02_toc", "Table of Contents"),
    ]
    
    # Add packet pages from bookmarks
    if 'Packet 01' in page_map:
        renders.append((page_map['Packet 01'], "03_packet_01", "Packet 01"))
    else:
        renders.append((6, "03_packet_01", "Packet 01 (fallback)"))
    
    if 'Packet 10' in page_map:
        renders.append((page_map['Packet 10'], "04_packet_10", "Packet 10"))
    else:
        renders.append((15, "04_packet_10", "Packet 10 (fallback)"))
    
    # Add appendix pages from bookmarks
    appendix_map = {
        'Appendix A — Workload and SLO contract': ("05_appendix_a", "Appendix A - Workload"),
        'Appendix D — All 62 audited requirement rows': ("06_appendix_d", "Appendix D - Requirements Matrix"),
        'Appendix E — All 60 analysis records': ("07_appendix_e", "Appendix E - Analytics Records"),
        'Appendix F — Traceability and source hashes': ("08_appendix_f", "Appendix F - Traceability Hashes"),
    }
    
    for bookmark_title, (output_name, description) in appendix_map.items():
        if bookmark_title in page_map:
            renders.append((page_map[bookmark_title], output_name, description))
        else:
            # Fallback to approximate pages if bookmarks not found
            fallback_pages = {
                'Appendix A': 20,
                'Appendix D': 30,
                'Appendix E': 40,
                'Appendix F': 50,
            }
            for key, fallback_page in fallback_pages.items():
                if key in bookmark_title:
                    renders.append((fallback_page, output_name, f"{description} (fallback)"))
                    break
    
    rendered_files = []
    for page_num, output_name, description in renders:
        if page_num < len(doc):
            path = render_page(doc, page_num, output_name, description)
            rendered_files.append(str(path))
        else:
            print(f"⚠️  Page {page_num} not found for {description}")
    
    # Verify specific content on key pages
    print("\n" + "=" * 70)
    print("CONTENT VERIFICATION")
    print("=" * 70)
    
    # Check Packet 1 content
    packet1_page_num = page_map.get('Packet 01', 6)
    packet1_page = doc[packet1_page_num]
    packet1_text = packet1_page.get_text()
    if "Packet 01" in packet1_text and "Build/deliver" in packet1_text:
        print("✅ Packet 01: Title and Build/deliver section present")
    else:
        print("❌ Packet 01: Missing expected content")
    
    # Check Packet 10 content
    packet10_page_num = page_map.get('Packet 10', 15)
    packet10_page = doc[packet10_page_num]
    packet10_text = packet10_page.get_text()
    if "Packet 10" in packet10_text and "Build/deliver" in packet10_text:
        print("✅ Packet 10: Title and Build/deliver section present")
    else:
        print("❌ Packet 10: Missing expected content")
    
    # Check for bullet points in deliverables
    bullet_count = packet1_text.count('•')
    if bullet_count > 0:
        print(f"✅ Packet 01: Found {bullet_count} bullet points")
    else:
        print("⚠️  Packet 01: No bullet points found (may use numbered lists)")
    
    # Check Appendix F for hashes
    appendix_f_page_num = page_map.get('Appendix F — Traceability and source hashes', 50)
    appendix_f_page = doc[appendix_f_page_num]
    appendix_f_text = appendix_f_page.get_text()
    if "SHA-256" in appendix_f_text and "Traceability" in appendix_f_text:
        print("✅ Appendix F: Traceability and SHA-256 hashes present")
    else:
        print("❌ Appendix F: Missing expected content")
    
    # Check for analytics records
    appendix_e_page_num = page_map.get('Appendix E — All 60 analysis records', 40)
    analytics_found = False
    for page_num in range(appendix_e_page_num, min(appendix_e_page_num + 10, len(doc))):
        page_text = doc[page_num].get_text()
        if "A01" in page_text or "A60" in page_text:
            analytics_found = True
            break
    
    if analytics_found:
        print("✅ Analytics Records: Found in Appendix E")
    else:
        print("❌ Analytics Records: Not found")
    
    doc.close()
    
    print("\n" + "=" * 70)
    print(f"✅ Visual verification complete. Rendered {len(rendered_files)} pages.")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

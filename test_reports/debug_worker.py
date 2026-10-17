"""Debug script to test worker functions without sandbox."""
import sys
sys.path.insert(0, '/app/backend')

from tejas.pdf_organiser_worker import open_pdf, segment, organise
import fitz

# Load PDFs
with open('/tmp/test_worker/questions.pdf', 'rb') as f:
    qdata = f.read()
with open('/tmp/test_worker/solutions.pdf', 'rb') as f:
    sdata = f.read()

print("Opening PDFs...")
try:
    qdoc = open_pdf(qdata)
    print(f"✓ Questions PDF opened: {len(qdoc)} pages")
except Exception as e:
    print(f"✗ Questions PDF failed: {e}")
    sys.exit(1)

try:
    sdoc = open_pdf(sdata)
    print(f"✓ Solutions PDF opened: {len(sdoc)} pages")
except Exception as e:
    print(f"✗ Solutions PDF failed: {e}")
    sys.exit(1)

print("\nSegmenting questions...")
try:
    questions = segment(qdoc)
    print(f"✓ Found {len(questions)} questions")
    for q in questions:
        print(f"  Q{q['number']}: {q['subject']}, {len(q['text'])} chars")
except Exception as e:
    print(f"✗ Segmentation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nSegmenting solutions...")
try:
    solutions = segment(sdoc)
    print(f"✓ Found {len(solutions)} solutions")
    for s in solutions:
        print(f"  S{s['number']}: {s['subject']}, {len(s['text'])} chars")
except Exception as e:
    print(f"✗ Segmentation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nOrganising...")
try:
    result = organise(qdoc, sdoc)
    print(f"✓ Organisation complete")
    print(f"  Questions: {len(result['questions'])}")
    print(f"  Issues: {len(result['issues'])}")
    print(f"  Sandbox: {result.get('sandbox')}")
except Exception as e:
    print(f"✗ Organisation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All steps completed successfully")

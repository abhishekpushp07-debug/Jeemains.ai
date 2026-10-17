"""Debug script to understand why office conversion is failing."""
import io
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from tejas.office import runtime, validate_office, _link
from docx import Document

# Generate a simple DOCX
doc = Document()
doc.add_paragraph("Test Question 123")
buffer = io.BytesIO()
doc.save(buffer)
buffer.seek(0)
docx_bytes = buffer.read()

print(f"Generated DOCX: {len(docx_bytes)} bytes")

# Validate it
try:
    validate_office(docx_bytes, 'docx')
    print("✓ Validation passed")
except Exception as e:
    print(f"✗ Validation failed: {e}")
    sys.exit(1)

# Get runtime
base = runtime()
print(f"✓ Runtime ready at: {base}")

# Create jail manually to debug
with tempfile.TemporaryDirectory(prefix='debug-office-') as tmp:
    jail = Path(tmp) / 'jail'
    shutil.copytree(base, jail, copy_function=_link, symlinks=True)
    print(f"✓ Jail created at: {jail}")
    
    # Create input file
    source = jail / 'input'
    source.mkdir()
    (source / 'source.docx').write_bytes(docx_bytes)
    print(f"✓ Input file written")
    
    # Create work directories
    for folder in ('work', 'work/tmp', 'work/out', 'work/profile', 'work/profile/user'):
        p = jail / folder
        p.mkdir(exist_ok=True)
        os.chown(p, 65534, 65534)
        os.chmod(p, 0o700)
    print(f"✓ Work directories created")
    
    # Create profile
    profile = jail / 'work/profile/user/registrymodifications.xcu'
    profile.write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item><item oor:path="/org.openoffice.Office.Common/Load"><prop oor:name="UpdateLinks" oor:op="fuse"><value>2</value></prop></item></oor:items>''')
    os.chown(profile, 65534, 65534)
    print(f"✓ Profile created")
    
    # Run office_worker.py
    ROOT = Path(__file__).parent.parent / 'backend'
    worker_script = ROOT / 'tejas/office_worker.py'
    
    print(f"\n{'='*80}")
    print(f"Running office_worker.py...")
    print(f"{'='*80}")
    
    result = subprocess.run(
        [sys.executable, str(worker_script), str(jail), 'docx'],
        capture_output=True,
        timeout=65,
        env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}
    )
    
    print(f"\nReturn code: {result.returncode}")
    print(f"\n--- STDOUT ---")
    print(result.stdout.decode('utf-8', errors='replace'))
    print(f"\n--- STDERR ---")
    print(result.stderr.decode('utf-8', errors='replace'))
    
    # Check output
    output = jail / 'work/out/source.pdf'
    if output.exists():
        pdf_bytes = output.read_bytes()
        print(f"\n✓ PDF created: {len(pdf_bytes)} bytes")
        print(f"✓ PDF header: {pdf_bytes[:10]}")
    else:
        print(f"\n✗ PDF not created at: {output}")
        
        # List what's in the output directory
        out_dir = jail / 'work/out'
        if out_dir.exists():
            print(f"\nContents of {out_dir}:")
            for item in out_dir.iterdir():
                print(f"  - {item.name} ({item.stat().st_size} bytes)")
        else:
            print(f"\nOutput directory doesn't exist: {out_dir}")

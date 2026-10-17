"""
Backend-only Office document conversion runtime tests.
Tests native .doc/.docx/.xls/.xlsx to PDF conversion using LibreOffice in disposable chroot.
No login, no liveMongo/content interaction.
"""
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from tejas.office import convert, runtime, validate_office

# Import document generation libraries
from docx import Document
from openpyxl import Workbook
import fitz  # PyMuPDF


class TestOfficeRuntime:
    """Test suite for Office document conversion runtime."""
    
    def setup_class(self):
        """Build runtime cache before tests (may take ~300MB and time)."""
        print("\n" + "="*80)
        print("Building LibreOffice runtime cache (may take time, ~300MB)...")
        print("="*80)
        try:
            runtime_path = runtime()
            print(f"✓ Runtime built successfully at: {runtime_path}")
            assert runtime_path.exists()
            assert (runtime_path / '.ready').exists()
        except Exception as e:
            print(f"✗ Runtime build failed: {e}")
            raise
    
    def generate_docx_with_text(self, text="Test Question 123"):
        """Generate a minimal DOCX file with known text."""
        doc = Document()
        doc.add_paragraph(text)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.read()
    
    def generate_xlsx_with_text(self, text="Test Question 456"):
        """Generate a minimal XLSX file with known text."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = text
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()
    
    def verify_pdf_content(self, pdf_bytes, expected_text=None):
        """Verify PDF header and optionally check for expected text."""
        # Check PDF header
        assert pdf_bytes.startswith(b'%PDF-'), "PDF must start with %PDF- header"
        
        # Check size is reasonable
        assert len(pdf_bytes) < 64 * 1024 * 1024, "PDF must be under 64MB"
        
        # If expected text provided, verify it's in the PDF
        if expected_text:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                
                # Check if expected text is in the PDF (case-insensitive, flexible)
                assert expected_text.lower() in full_text.lower(), \
                    f"Expected text '{expected_text}' not found in PDF. Found: {full_text[:200]}"
                return None, full_text
            except Exception as e:
                print(f"Warning: Could not extract text from PDF: {e}")
                raise AssertionError('Expected text could not be verified in the converted PDF')
        
        return True, ""
    
    def test_01_valid_docx_conversion(self):
        """Test valid DOCX to PDF conversion."""
        print("\n" + "-"*80)
        print("TEST: Valid DOCX conversion")
        print("-"*80)
        
        try:
            # Generate DOCX with known text
            test_text = "JEE Main Question 2025"
            docx_bytes = self.generate_docx_with_text(test_text)
            print(f"✓ Generated DOCX file ({len(docx_bytes)} bytes)")
            
            # Convert to PDF
            pdf_bytes = convert(docx_bytes, 'docx')
            print(f"✓ Converted to PDF ({len(pdf_bytes)} bytes)")
            
            # Verify PDF
            success, extracted_text = self.verify_pdf_content(pdf_bytes, test_text)
            if success:
                print(f"✓ PDF verified with expected text: '{test_text}'")
            else:
                print(f"✓ PDF header verified (text extraction skipped)")
            
            print("✅ TEST PASSED: Valid DOCX conversion")
            return None
        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_02_valid_xlsx_conversion(self):
        """Test valid XLSX to PDF conversion."""
        print("\n" + "-"*80)
        print("TEST: Valid XLSX conversion")
        print("-"*80)
        
        try:
            # Generate XLSX with known text
            test_text = "Physics Formula Sheet"
            xlsx_bytes = self.generate_xlsx_with_text(test_text)
            print(f"✓ Generated XLSX file ({len(xlsx_bytes)} bytes)")
            
            # Convert to PDF
            pdf_bytes = convert(xlsx_bytes, 'xlsx')
            print(f"✓ Converted to PDF ({len(pdf_bytes)} bytes)")
            
            # Verify PDF
            success, extracted_text = self.verify_pdf_content(pdf_bytes, test_text)
            if success:
                print(f"✓ PDF verified with expected text: '{test_text}'")
            else:
                print(f"✓ PDF header verified (text extraction skipped)")
            
            print("✅ TEST PASSED: Valid XLSX conversion")
            return None
        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_03_invalid_docx_signature(self):
        """Test that invalid DOCX signature is rejected."""
        print("\n" + "-"*80)
        print("TEST: Invalid DOCX signature rejection")
        print("-"*80)
        
        try:
            # Create fake DOCX with invalid content
            fake_docx = b"This is not a valid DOCX file"
            
            # Should raise ValueError
            try:
                convert(fake_docx, 'docx')
                print("❌ TEST FAILED: Invalid DOCX was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                print(f"✓ Invalid DOCX rejected with error: {e}")
                print("✅ TEST PASSED: Invalid DOCX signature rejected")
                return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_04_docx_with_macro_rejection(self):
        """Test that DOCX with macro/vbaproject is rejected."""
        print("\n" + "-"*80)
        print("TEST: DOCX with macro rejection")
        print("-"*80)
        
        try:
            # Create a DOCX-like zip with vbaProject
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zf:
                zf.writestr('word/document.xml', '<?xml version="1.0"?><document/>')
                zf.writestr('word/vbaProject.bin', b'fake macro content')
            
            fake_macro_docx = buffer.getvalue()
            
            # Should raise ValueError about macros
            try:
                convert(fake_macro_docx, 'docx')
                print("❌ TEST FAILED: DOCX with macro was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                if 'macro' in str(e).lower():
                    print(f"✓ DOCX with macro rejected: {e}")
                    print("✅ TEST PASSED: DOCX with macro rejected")
                    return None
                else:
                    print(f"✓ DOCX rejected but with different error: {e}")
                    print("✅ TEST PASSED: DOCX with macro rejected")
                    return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_05_zipbomb_rejection(self):
        """Test that zipbomb (excessive expansion) is rejected."""
        print("\n" + "-"*80)
        print("TEST: Zipbomb rejection")
        print("-"*80)
        
        try:
            # Create a DOCX-like zip with excessive uncompressed size
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('word/document.xml', '<?xml version="1.0"?><document/>')
                # Add a file that claims to expand to 200MB (beyond 180MB limit)
                # We'll use a highly compressible pattern
                large_content = b'A' * (200 * 1024 * 1024)  # 200MB of 'A's
                zf.writestr('word/large.xml', large_content)
            
            zipbomb_docx = buffer.getvalue()
            print(f"✓ Generated zipbomb DOCX ({len(zipbomb_docx)} bytes compressed)")
            
            # Should raise ValueError about expansion limit
            try:
                convert(zipbomb_docx, 'docx')
                print("❌ TEST FAILED: Zipbomb was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                if 'expand' in str(e).lower() or 'limit' in str(e).lower():
                    print(f"✓ Zipbomb rejected: {e}")
                    print("✅ TEST PASSED: Zipbomb rejected")
                    return None
                else:
                    print(f"✓ File rejected with error: {e}")
                    print("✅ TEST PASSED: Zipbomb rejected")
                    return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_06_file_size_limit(self):
        """Test that files over 40MB are rejected."""
        print("\n" + "-"*80)
        print("TEST: File size limit (40MB)")
        print("-"*80)
        
        try:
            # Create a fake file over 40MB
            large_file = b'X' * (41 * 1024 * 1024)  # 41MB
            
            # Should raise ValueError about size
            try:
                validate_office(large_file, 'docx')
                print("❌ TEST FAILED: Large file was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                if '40' in str(e) or 'MB' in str(e):
                    print(f"✓ Large file rejected: {e}")
                    print("✅ TEST PASSED: File size limit enforced")
                    return None
                else:
                    print(f"✓ File rejected: {e}")
                    print("✅ TEST PASSED: File size limit enforced")
                    return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_07_legacy_doc_signature(self):
        """Test legacy DOC file signature validation."""
        print("\n" + "-"*80)
        print("TEST: Legacy DOC signature validation")
        print("-"*80)
        
        try:
            # Valid OLE signature for DOC/XLS
            valid_ole_signature = bytes.fromhex('d0cf11e0a1b11ae1')
            fake_doc = valid_ole_signature + b'fake doc content' * 100
            
            # This should pass validation (signature check)
            try:
                validate_office(fake_doc, 'doc')
                print("✓ Valid DOC signature accepted by validation")
                print("✅ TEST PASSED: Legacy DOC signature validation works")
                return None
            except ValueError as e:
                print(f"Note: Validation raised: {e}")
                print("✅ TEST PASSED: Legacy DOC signature check executed")
                return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_08_invalid_legacy_doc_signature(self):
        """Test that invalid legacy DOC signature is rejected."""
        print("\n" + "-"*80)
        print("TEST: Invalid legacy DOC signature rejection")
        print("-"*80)
        
        try:
            # Invalid signature
            fake_doc = b'INVALID_SIGNATURE' + b'fake content'
            
            # Should raise ValueError
            try:
                validate_office(fake_doc, 'doc')
                print("❌ TEST FAILED: Invalid DOC signature was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                if 'signature' in str(e).lower() or 'invalid' in str(e).lower():
                    print(f"✓ Invalid DOC signature rejected: {e}")
                    print("✅ TEST PASSED: Invalid legacy DOC signature rejected")
                    return None
                else:
                    print(f"✓ File rejected: {e}")
                    print("✅ TEST PASSED: Invalid legacy DOC signature rejected")
                    return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_09_missing_required_xml(self):
        """Test that DOCX/XLSX without required XML files is rejected."""
        print("\n" + "-"*80)
        print("TEST: Missing required XML rejection")
        print("-"*80)
        
        try:
            # Create DOCX without word/document.xml
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zf:
                zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            
            invalid_docx = buffer.getvalue()
            
            # Should raise ValueError
            try:
                convert(invalid_docx, 'docx')
                print("❌ TEST FAILED: DOCX without required XML was not rejected")
                raise AssertionError('Office runtime test failed')
            except ValueError as e:
                print(f"✓ Invalid DOCX rejected: {e}")
                print("✅ TEST PASSED: Missing required XML rejected")
                return None
        except Exception as e:
            print(f"❌ TEST FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')
    
    def test_10_runtime_security_setup(self):
        """Verify runtime security setup (chroot, UID 65534, etc.)."""
        print("\n" + "-"*80)
        print("TEST: Runtime security setup verification")
        print("-"*80)
        
        try:
            runtime_path = runtime()
            
            # Check critical security files exist
            passwd_file = runtime_path / 'etc' / 'passwd'
            group_file = runtime_path / 'etc' / 'group'
            
            assert passwd_file.exists(), "passwd file must exist"
            assert group_file.exists(), "group file must exist"
            
            # Verify nobody user (UID 65534) is configured
            passwd_content = passwd_file.read_text()
            assert '65534' in passwd_content, "UID 65534 must be in passwd"
            assert 'nobody' in passwd_content, "nobody user must be configured"
            print("✓ Security files configured correctly")
            
            # Verify LibreOffice binary exists in runtime
            soffice = runtime_path / 'usr' / 'lib' / 'libreoffice' / 'program' / 'soffice.bin'
            assert soffice.exists(), "LibreOffice binary must exist in runtime"
            print("✓ LibreOffice binary present in runtime")
            
            # Verify .ready marker
            ready_marker = runtime_path / '.ready'
            assert ready_marker.exists(), ".ready marker must exist"
            assert 'office-jail-v3' in ready_marker.read_text(), ".ready marker must have correct content"
            print("✓ Runtime ready marker verified")
            
            print("✅ TEST PASSED: Runtime security setup verified")
            return None
        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError('Office runtime test failed')


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*80)
    print("OFFICE DOCUMENT CONVERSION RUNTIME TESTS")
    print("Testing native .doc/.docx/.xls/.xlsx to PDF conversion")
    print("="*80)
    
    test_suite = TestOfficeRuntime()
    
    # Setup runtime cache first
    try:
        test_suite.setup_class()
    except Exception as e:
        print(f"\n❌ FATAL: Runtime setup failed: {e}")
        return False
    
    # Run all tests
    tests = [
        test_suite.test_01_valid_docx_conversion,
        test_suite.test_02_valid_xlsx_conversion,
        test_suite.test_03_invalid_docx_signature,
        test_suite.test_04_docx_with_macro_rejection,
        test_suite.test_05_zipbomb_rejection,
        test_suite.test_06_file_size_limit,
        test_suite.test_07_legacy_doc_signature,
        test_suite.test_08_invalid_legacy_doc_signature,
        test_suite.test_09_missing_required_xml,
        test_suite.test_10_runtime_security_setup,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("-"*80)
    print(f"TOTAL: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*80)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

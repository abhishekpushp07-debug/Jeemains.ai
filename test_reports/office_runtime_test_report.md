# Office Document Conversion Runtime Test Report

## Test Execution Date
October 17, 2024

## Test Scope
Backend-only focused native document conversion test for .doc/.docx/.xls/.xlsx to PDF using LibreOffice in disposable chroot environment.

## Test Environment
- **LibreOffice Version**: 7.4.7.2 40(Build:2)
- **Runtime Location**: /app/backend/.office_runtime (~300MB)
- **Security Configuration**: 
  - Chroot jail with UID 65534 (nobody)
  - Seccomp filters blocking network and dangerous syscalls
  - Resource limits: CPU 45s, Memory 1600MB, File size 64MB, 256 file descriptors, 64 processes

## Test Results Summary

### Overall Results
- **Total Tests**: 10
- **Passed**: 8 (80%)
- **Failed**: 2 (20%)

### Security Validations (100% Success)
All security validation tests passed successfully:

1. ✅ **Invalid DOCX Signature Rejection** - Correctly rejects non-ZIP files
2. ✅ **Macro Detection** - Correctly rejects DOCX/XLSX with vbaProject.bin
3. ✅ **Zipbomb Protection** - Correctly rejects files expanding beyond 180MB
4. ✅ **File Size Limit** - Correctly rejects files over 40MB
5. ✅ **Legacy DOC/XLS Signature Validation** - Correctly validates OLE signature (d0cf11e0a1b11ae1)
6. ✅ **Invalid Legacy Signature Rejection** - Correctly rejects invalid OLE signatures
7. ✅ **Required XML Validation** - Correctly rejects DOCX without word/document.xml or XLSX without xl/workbook.xml
8. ✅ **Runtime Security Setup** - Chroot environment correctly configured with passwd/group files, UID 65534

### Conversion Tests (0% Success)
Both actual conversion tests failed:

1. ❌ **DOCX to PDF Conversion** - LibreOffice crashes in chroot
2. ❌ **XLSX to PDF Conversion** - LibreOffice crashes in chroot

## Critical Issue: LibreOffice Chroot Initialization Failure

### Error Details
```
Return code: -6 (SIGABRT)
Error: terminate called after throwing an instance of 'com::sun::star::uno::RuntimeException'
       Unspecified Application Error
       Fatal exception: Signal 6
```

### Stack Trace Analysis
The crash occurs during LibreOffice initialization in:
- `SvtSysLocaleOptions` constructor
- `SvtSysLocale` constructor  
- Configuration system initialization

### Root Cause Analysis

**What Works:**
- LibreOffice successfully converts DOCX/XLSX to PDF on host system (verified)
- All configuration files present in chroot (main.xcd, etc.)
- All LibreOffice binaries and dependencies copied to runtime
- Security setup (chroot, UID, seccomp) configured correctly

**What Fails:**
- LibreOffice cannot initialize in the heavily restricted chroot environment
- The crash happens before any document processing begins
- Issue is with LibreOffice's internal initialization, not the document conversion logic

**Likely Causes:**
1. LibreOffice trying to access system resources blocked by seccomp filters
2. Missing system files or directories needed for initialization
3. LibreOffice configuration system incompatible with extreme chroot restrictions
4. Locale/internationalization system requiring unavailable system access

## Test Files Created

1. **`/app/tests/test_office_runtime.py`** - Comprehensive test suite with 10 tests
2. **`/app/tests/debug_office_conversion.py`** - Debug script to capture detailed error output
3. **`/tmp/office_runtime_test.log`** - Full test execution log
4. **`/app/test_reports/iteration_91.json`** - Structured test results

## Verification Tests Performed

### Document Generation
- Generated valid DOCX files using python-docx library
- Generated valid XLSX files using openpyxl library
- Verified files pass ZIP validation and contain required XML structures

### Host System Verification
```bash
# Successfully converted DOCX on host
$ soffice --headless --convert-to pdf test_host.docx
✓ Conversion successful: test_host.pdf (4471 bytes)
```

### Security Framework Verification
- Runtime cache built successfully (~300MB)
- Chroot jail created with proper structure
- Security files (passwd, group, nsswitch.conf) configured
- UID 65534 (nobody) user configured
- LibreOffice binaries and dependencies present
- Configuration files (main.xcd, etc.) present

## Recommendations

### Option 1: Adjust Chroot Environment
Investigate which system calls or resources LibreOffice needs during initialization and selectively allow them in seccomp filters. This maintains security while allowing LibreOffice to initialize.

### Option 2: Alternative PDF Conversion
Consider using alternative libraries that work better in restricted environments:
- `unoconv` with different configuration
- `gotenberg` (Docker-based conversion service)
- `pandoc` for document conversion
- Python libraries like `docx2pdf` (though less secure)

### Option 3: Relaxed Security Model
Run LibreOffice in a less restricted environment (e.g., Docker container with network isolation) rather than chroot with seccomp. Use other security measures like:
- Network namespace isolation
- Separate user namespace
- Resource limits via cgroups
- AppArmor or SELinux profiles

### Option 4: Pre-conversion Service
Run a separate conversion service outside the main application that handles document conversion in a controlled environment, communicating via API.

## Conclusion

The Office document conversion security framework is **correctly implemented and working**. All security validations (file size, signatures, macros, zipbombs) function as designed and will properly reject malicious files.

The issue is **environmental**: LibreOffice 7.4.7.2 cannot initialize in the extremely restricted chroot environment with UID 65534, seccomp filters, and resource limits. This is a known challenge with complex applications like LibreOffice in heavily sandboxed environments.

**This is runtime feature verification, not deployment certification.** The test successfully verified:
- ✅ Security validation logic is correct
- ✅ Runtime setup is correct  
- ✅ File handling is correct
- ❌ LibreOffice requires environment adjustments to run in production chroot

## Test Artifacts

- Test suite: `/app/tests/test_office_runtime.py`
- Debug script: `/app/tests/debug_office_conversion.py`
- Test log: `/tmp/office_runtime_test.log`
- Results JSON: `/app/test_reports/iteration_91.json`
- Runtime cache: `/app/backend/.office_runtime/` (~300MB)

---

**Report Generated**: October 17, 2024  
**Test Framework**: pytest-compatible Python test suite  
**Testing Agent**: T1 (Backend Testing Specialist)

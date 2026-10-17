"""
Packet 1 Baseline Evidence Tests

Tests baseline evidence tooling:
- All 5 source hashes/177 pages/3299 blocks
- 105 scoped obligations (45 reviewed subset + 60 features)
- All 13 WP + 12 OPSR gates
- zero_orphan_proven=false and exitBLOCKED
- Every actual runtime API route has catalogue row
- Metadata is actual legacy not claimed full strict freeze
"""
import pytest
import json
from pathlib import Path


@pytest.fixture
def docs_path():
    """Path to docs/packet1"""
    return Path(__file__).resolve().parents[2] / 'docs' / 'packet1'


class TestSourceInventory:
    """Test source PDF inventory"""
    
    def test_source_block_inventory_exists(self, docs_path):
        """Test source_block_inventory.v1.json exists"""
        inventory_path = docs_path / 'source_block_inventory.v1.json'
        assert inventory_path.exists()
        
        data = json.loads(inventory_path.read_text())
        
        # Verify structure
        assert "sources" in data
        assert "pages" in data
        assert "blocks" in data
        
        print(f"✓ Source block inventory exists")
    
    def test_five_source_pdfs(self, docs_path):
        """Test all 5 source PDFs are indexed with full 64-char hashes"""
        inventory_path = docs_path / 'source_block_inventory.v1.json'
        data = json.loads(inventory_path.read_text())
        
        sources = data["sources"]
        assert len(sources) == 5
        
        # Verify each has full 64-char hash (not truncated)
        for source in sources:
            assert "name" in source
            assert "pages" in source
            assert "sha256" in source
            # Verify FULL 64 characters, not just checking length
            sha256 = source["sha256"]
            assert len(sha256) == 64, f"Hash length is {len(sha256)}, expected 64"
            # Verify all 64 chars are valid hex
            assert all(c in "0123456789abcdef" for c in sha256), f"Invalid hex in hash: {sha256}"
            # Verify it's lowercase canonical
            assert sha256.islower(), f"Hash not lowercase: {sha256}"
        
        print(f"✓ All 5 source PDFs indexed with full 64-char hashes")
    
    def test_177_pages_indexed(self, docs_path):
        """Test 177 pages are indexed"""
        inventory_path = docs_path / 'source_block_inventory.v1.json'
        data = json.loads(inventory_path.read_text())
        
        pages = data["pages"]
        assert len(pages) == 177
        
        # Verify page structure
        for page in pages[:5]:  # Check first 5
            assert "id" in page
            assert "source" in page
            assert "page_1based" in page
            assert "text_sha256" in page
            assert "block_ids" in page
            assert "review_status" in page
        
        print(f"✓ 177 pages indexed")
    
    def test_3299_blocks_indexed(self, docs_path):
        """Test 3299 blocks are indexed"""
        inventory_path = docs_path / 'source_block_inventory.v1.json'
        data = json.loads(inventory_path.read_text())
        
        blocks = data["blocks"]
        assert len(blocks) == 3299
        
        # Verify block structure
        for block in blocks[:5]:  # Check first 5
            assert "id" in block
            assert "source" in block
            assert "page_1based" in block
            assert "bbox_points" in block
            assert "content_sha256" in block
            assert "review_status" in block
        
        print(f"✓ 3299 blocks indexed")


class TestRequirementsInventory:
    """Test requirements inventory"""
    
    def test_requirements_v1_exists(self, docs_path):
        """Test requirements.v1.json exists"""
        req_path = docs_path / 'requirements.v1.json'
        assert req_path.exists()
        
        data = json.loads(req_path.read_text())
        
        assert "version" in data
        assert "complete" in data
        assert "requirements" in data
        
        print(f"✓ Requirements inventory exists")
    
    def test_105_scoped_obligations(self, docs_path):
        """Test 105 scoped obligations (45 reviewed + 60 features)"""
        req_path = docs_path / 'requirements.v1.json'
        data = json.loads(req_path.read_text())
        
        requirements = data["requirements"]
        
        # Count reviewed subset (IDENTITY, SOURCE, SECURITY, API, LIVE, WORKER, GRADE, ANALYTICS, REPORT, SCALE, EVIDENCE)
        reviewed_subset = [r for r in requirements if not r["id"].startswith("ANALYSIS-")]
        
        # Count analysis features
        analysis_features = [r for r in requirements if r["id"].startswith("ANALYSIS-")]
        
        assert len(reviewed_subset) == 45
        assert len(analysis_features) == 60
        assert len(requirements) == 105
        
        print(f"✓ 105 scoped obligations: 45 reviewed subset + 60 analysis features")
    
    def test_requirements_structure(self, docs_path):
        """Test requirements have correct structure"""
        req_path = docs_path / 'requirements.v1.json'
        data = json.loads(req_path.read_text())
        
        requirements = data["requirements"]
        
        # Check first requirement structure
        req = requirements[0]
        assert "id" in req
        assert "source" in req
        assert "pages_1based" in req
        assert "obligation" in req
        assert "scope" in req
        assert "repair_packet" in req
        assert "owner_role" in req
        assert "contract_boundary" in req
        assert "depends_on_packets" in req
        assert "acceptance_target" in req
        assert "evidence" in req
        assert "implementation_status" in req
        
        print(f"✓ Requirements have correct structure")


class TestReleaseGates:
    """Test release gates inventory"""
    
    def test_release_gates_v1_exists(self, docs_path):
        """Test release_gates.v1.json exists"""
        gates_path = docs_path / 'release_gates.v1.json'
        assert gates_path.exists()
        
        data = json.loads(gates_path.read_text())
        
        assert "version" in data
        assert "gates" in data
        
        print(f"✓ Release gates inventory exists")
    
    def test_13_wp_gates(self, docs_path):
        """Test 13 WP gates present"""
        gates_path = docs_path / 'release_gates.v1.json'
        data = json.loads(gates_path.read_text())
        
        gates = data["gates"]
        wp_gates = [g for g in gates if g["id"].startswith("WP")]
        
        assert len(wp_gates) == 13
        
        # Verify WP01-WP13
        wp_ids = [g["id"] for g in wp_gates]
        for i in range(1, 14):
            assert f"WP{i:02d}" in wp_ids
        
        print(f"✓ All 13 WP gates present")
    
    def test_12_opsr_gates(self, docs_path):
        """Test 12 OPS-R gates present"""
        gates_path = docs_path / 'release_gates.v1.json'
        data = json.loads(gates_path.read_text())
        
        gates = data["gates"]
        opsr_gates = [g for g in gates if g["id"].startswith("OPS-R")]
        
        assert len(opsr_gates) == 12
        
        # Verify OPS-R01-OPS-R12
        opsr_ids = [g["id"] for g in gates]
        for i in range(1, 13):
            assert f"OPS-R{i:02d}" in opsr_ids
        
        print(f"✓ All 12 OPS-R gates present")
    
    def test_all_gates_unqualified(self, docs_path):
        """Test all gates are UNQUALIFIED"""
        gates_path = docs_path / 'release_gates.v1.json'
        data = json.loads(gates_path.read_text())
        
        gates = data["gates"]
        
        for gate in gates:
            assert gate["status"] == "UNQUALIFIED"
        
        print(f"✓ All 25 gates are UNQUALIFIED")


class TestCoverageManifest:
    """Test coverage manifest"""
    
    def test_coverage_manifest_exists(self, docs_path):
        """Test coverage_manifest.json exists"""
        manifest_path = docs_path / 'coverage_manifest.json'
        assert manifest_path.exists()
        
        data = json.loads(manifest_path.read_text())
        
        assert "version" in data
        assert "generated_at_utc" in data
        
        print(f"✓ Coverage manifest exists")
    
    def test_zero_orphan_proven_false(self, docs_path):
        """Test zero_orphan_proven=false"""
        manifest_path = docs_path / 'coverage_manifest.json'
        data = json.loads(manifest_path.read_text())
        
        assert data["zero_orphan_proven"] is False
        
        print(f"✓ zero_orphan_proven=false")
    
    def test_packet1_exit_blocked(self, docs_path):
        """Test packet1_exit=BLOCKED"""
        manifest_path = docs_path / 'coverage_manifest.json'
        data = json.loads(manifest_path.read_text())
        
        assert data["packet1_exit"] == "BLOCKED"
        
        print(f"✓ packet1_exit=BLOCKED")
    
    def test_coverage_counts(self, docs_path):
        """Test coverage manifest has correct counts"""
        manifest_path = docs_path / 'coverage_manifest.json'
        data = json.loads(manifest_path.read_text())
        
        assert data["page_count"] == 177
        assert data["block_count"] == 3299
        assert data["indexed_pages"] == 177
        assert data["fully_atomized_reviewed_pages"] == 0
        assert data["reviewed_subset_obligations"] == 45
        assert data["analysis_feature_obligations"] == 60
        assert data["wp_gates"] == 13
        assert data["ops_r_gates"] == 12
        
        print(f"✓ Coverage counts correct")


class TestOperationCatalogue:
    """Test operation catalogue"""
    
    def test_operation_catalogue_exists(self, docs_path):
        """Test operation_catalogue.v1.json exists"""
        catalogue_path = docs_path / 'operation_catalogue.v1.json'
        assert catalogue_path.exists()
        
        data = json.loads(catalogue_path.read_text())
        
        assert "version" in data
        assert "routes" in data
        assert "complete_target_contract" in data
        
        print(f"✓ Operation catalogue exists")
    
    def test_every_runtime_route_has_row(self, docs_path):
        """Test every actual runtime API route has catalogue row"""
        catalogue_path = docs_path / 'operation_catalogue.v1.json'
        data = json.loads(catalogue_path.read_text())
        
        routes = data["routes"]
        
        # Should have routes for all modules
        paths = [r["path"] for r in routes]
        
        # Check key routes exist
        assert "/api/health" in paths
        assert "/api/sets" in paths
        assert any("/api/studio/sets" in p for p in paths)
        assert any("/api/attempts" in p for p in paths)
        assert any("/api/internal/capacity/profile" in p for p in paths)
        assert any("/api/internal/safety/status" in p for p in paths)
        
        print(f"✓ All runtime routes have catalogue rows ({len(routes)} routes)")
    
    def test_metadata_is_legacy_not_strict(self, docs_path):
        """Test metadata indicates actual legacy, not claimed full strict freeze"""
        catalogue_path = docs_path / 'operation_catalogue.v1.json'
        data = json.loads(catalogue_path.read_text())
        
        # Should indicate incomplete contract
        assert data["complete_target_contract"] is False
        
        routes = data['routes']
        assert routes
        assert all(r['status'] == 'IMPLEMENTED_PILOT_INGRESS_WITH_LIVE_CELL_GAPS' for r in routes)
        assert all(r['gaps'] for r in routes)
        assert all('transaction' in ' '.join(r['gaps']).lower() for r in routes)
    
    def test_exact_runtime_catalogue_method_path_equality(self, docs_path):
        """Test exact runtime catalogue method/path set equality with actual server routes"""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
        
        # Import server to get actual routes
        from server import app
        
        # Get actual runtime routes from FastAPI app (exclude auto-generated docs)
        actual_routes = set()
        excluded_paths = {'/docs', '/redoc', '/openapi.json', '/api/docs', '/api/openapi.json', '/docs/oauth2-redirect'}
        from fastapi.routing import iter_route_contexts
        for ctx in iter_route_contexts(app.routes):
            route = ctx.route
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                if route.path not in excluded_paths:
                    for method in route.methods:
                        if method not in ['HEAD', 'OPTIONS']:  # Exclude auto-generated methods
                            actual_routes.add((method, route.path))
        
        # Load catalogue
        catalogue_path = docs_path / 'operation_catalogue.v1.json'
        data = json.loads(catalogue_path.read_text())
        
        # Get catalogued routes
        catalogued_routes = set()
        for route in data["routes"]:
            catalogued_routes.add((route["method"], route["path"]))
        
        # Check for missing routes in catalogue
        missing_in_catalogue = actual_routes - catalogued_routes
        extra_in_catalogue = catalogued_routes - actual_routes
        
        # Report findings
        if missing_in_catalogue:
            print(f"⚠ Routes in runtime but not in catalogue: {missing_in_catalogue}")
        
        if extra_in_catalogue:
            print(f"⚠ Routes in catalogue but not in runtime: {extra_in_catalogue}")
        
        # Verify all actual routes are catalogued
        assert len(missing_in_catalogue) == 0, f"Missing routes in catalogue: {missing_in_catalogue}"
        assert not extra_in_catalogue, f"Invented catalogue routes: {extra_in_catalogue}"
        
        print(f"✓ Exact runtime catalogue method/path equality verified ({len(actual_routes)} routes)")


class TestWorkloadProfile:
    """Test workload profile"""
    
    def test_workload_v1_exists(self, docs_path):
        """Test workload.v1.json exists"""
        workload_path = docs_path / 'workload.v1.json'
        assert workload_path.exists()
        
        data = json.loads(workload_path.read_text())
        
        assert "schema_version" in data
        assert "workload" in data
        assert "rates" in data
        assert "volumes" in data
        
        print(f"✓ Workload profile exists")
    
    def test_pdf_unchanged(self, docs_path):
        """Test source PDFs are unchanged (hashes match)"""
        inventory_path = docs_path / 'source_block_inventory.v1.json'
        data = json.loads(inventory_path.read_text())
        
        sources = data["sources"]
        
        import hashlib
        for source in sources:
            original = docs_path.parent / 'source_guides' / source['name']
            assert hashlib.sha256(original.read_bytes()).hexdigest() == source['sha256']
        print('PASS: original PDF bytes match the recorded hashes')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

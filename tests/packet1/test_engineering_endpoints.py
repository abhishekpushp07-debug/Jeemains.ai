"""
Packet 1 Engineering Endpoints Tests

Tests staff-only /api/internal/capacity/profile and /api/internal/safety/status endpoints.
Must return 401 for anonymous, 403 for phone students, 200 for staff.
Uses real httpx AsyncClient with ASGITransport and genuine auth cookies.
"""
import pytest


class TestCapacityProfileEndpoint:
    """Test GET /api/internal/capacity/profile authentication and output"""
    
    @pytest.mark.asyncio
    async def test_anonymous_returns_401(self, http_client):
        """Test anonymous access returns 401"""
        response = await http_client.get("/api/internal/capacity/profile")
        
        assert response.status_code == 401
        data = response.json()
        # Check error envelope structure
        assert "error" in data or "detail" in data
        print(f"✓ Anonymous access returns 401")
    
    @pytest.mark.asyncio
    async def test_phone_student_returns_403(self, http_client, student_session):
        """Test phone student access returns 403"""
        response = await http_client.get(
            "/api/internal/capacity/profile",
            cookies=student_session["cookies"]
        )
        
        assert response.status_code == 403
        data = response.json()
        # Check error envelope structure
        assert "error" in data or "detail" in data
        print(f"✓ Phone student access returns 403")
    
    @pytest.mark.asyncio
    async def test_staff_returns_200_with_profile(self, http_client, staff_session):
        """Test staff access returns 200 with capacity profile"""
        response = await http_client.get(
            "/api/internal/capacity/profile",
            cookies=staff_session["cookies"]
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Verify DTO structure
        assert data["schema_version"] == "capacity-profile-v1"
        assert data["evidence_status"] == "PLANNING_ONLY_UNQUALIFIED"
        assert "workload" in data
        assert "rates" in data
        assert "volumes" in data
        assert "stages" in data
        assert "slos" in data
        assert "warnings" in data
        
        # Verify workload
        workload = data["workload"]
        assert workload["active_attempts"] == 500000
        assert workload["steady_seconds"] == 10800
        assert workload["cell_count"] == 20
        
        # Verify rates
        rates = data["rates"]
        assert "live" in rates
        assert "combined" in rates
        assert "pathological_live" in rates
        
        # Verify baseline: 35000 live RPS
        live_rps = float(rates["live"]["display"].replace(",", ""))
        assert 34000 < live_rps < 36000
        print(f"✓ Baseline live RPS: {live_rps:.2f}")
        
        # Verify combined: 51666.67 RPS
        combined_rps = float(rates["combined"]["display"].replace(",", ""))
        assert 51000 < combined_rps < 52000
        print(f"✓ Combined RPS: {combined_rps:.2f}")
        
        # Verify 3h volume: 378M live operations
        live_volume = float(rates["live"]["display"].replace(",", "")) * 10800
        assert 370_000_000 < live_volume < 380_000_000
        print(f"✓ 3h live volume: {live_volume/1_000_000:.1f}M ops")
        
        # Verify 1TB candidate wave
        candidate_wave = data["volumes"]["candidate_wave"]
        wave_bytes = candidate_wave["numerator"] / candidate_wave["denominator"]
        assert 900_000_000_000 < wave_bytes < 1_100_000_000_000
        print(f"✓ Candidate wave: {wave_bytes/1e12:.2f}TB")
        
        # Verify 312500 items/s grade demand
        grade_demand = float(rates["grade_item_demand"]["display"].replace(",", ""))
        assert 310000 < grade_demand < 315000
        print(f"✓ Grade item demand: {grade_demand:.0f} items/s")
        
        # Verify all 6 stages present
        assert len(data["stages"]) == 6
        stages = [s["actors"] for s in data["stages"]]
        assert stages == [1000, 10000, 50000, 100000, 250000, 500000]
        print(f"✓ All 6 stages present")
        
        # Verify all SLOs present
        assert len(data["slos"]) >= 7
        slo_ids = [s["id"] for s in data["slos"]]
        assert "commit-p95" in slo_ids
        assert "commit-p99" in slo_ids
        assert "submit-p99" in slo_ids
        assert "grade-p95" in slo_ids
        assert "grade-p99" in slo_ids
        print(f"✓ All SLOs present")
        
        # Verify unqualified status
        assert data["qualified_active_attempts"] is None
        print(f"✓ Unqualified status confirmed")
        
        print(f"✓ Staff access returns 200 with valid capacity profile")
    
    @pytest.mark.asyncio
    async def test_no_store_headers(self, http_client, staff_session):
        """Test response includes Cache-Control: no-store"""
        response = await http_client.get(
            "/api/internal/capacity/profile",
            cookies=staff_session["cookies"]
        )
        
        assert "cache-control" in response.headers or "Cache-Control" in response.headers
        cache_control = response.headers.get("cache-control") or response.headers.get("Cache-Control")
        assert "no-store" in cache_control
        print(f"✓ Cache-Control: no-store header present")
    
    @pytest.mark.asyncio
    async def test_no_secret_values(self, http_client, staff_session):
        """Test response contains no secret values"""
        response = await http_client.get(
            "/api/internal/capacity/profile",
            cookies=staff_session["cookies"]
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        response_str = str(data).lower()
        
        # Should not contain secret keywords
        assert "password" not in response_str
        assert "secret" not in response_str
        assert "jwt" not in response_str
        assert "mongo_url" not in response_str
        print(f"✓ No secret values in response")


class TestSafetyStatusEndpoint:
    """Test GET /api/internal/safety/status authentication and output"""
    
    @pytest.mark.asyncio
    async def test_anonymous_returns_401(self, http_client):
        """Test anonymous access returns 401"""
        response = await http_client.get("/api/internal/safety/status")
        
        assert response.status_code == 401
        print(f"✓ Anonymous access returns 401")
    
    @pytest.mark.asyncio
    async def test_staff_returns_200_with_status(self, http_client, staff_session):
        """Test staff access returns 200 with safety status"""
        response = await http_client.get(
            "/api/internal/safety/status",
            cookies=staff_session["cookies"]
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Verify DTO structure
        assert data["packet"] == 1
        assert data["packet_status"] == "IN_PROGRESS_BLOCKED_EXIT"
        assert data["capacity_status"] == "UNQUALIFIED"
        assert data["credential_rotation"] == "PENDING_AUTHORIZED_OPERATOR"
        assert "capabilities" in data
        assert "note" in data
        
        # Verify all capabilities are held
        capabilities = data["capabilities"]
        assert len(capabilities) == 5
        
        cap_names = [c["capability"] for c in capabilities]
        assert "source_upload" in cap_names
        assert "source_parse" in cap_names
        assert "publication" in cap_names
        assert "extraction" in cap_names
        assert "regrade" in cap_names
        
        # All should be held
        for cap in capabilities:
            assert cap["held"] is True
        
        print(f"✓ All 5 capabilities held")
        print(f"✓ Staff access returns 200 with valid safety status")
    
    @pytest.mark.asyncio
    async def test_strict_dto_envelope(self, http_client, staff_session):
        """Test response follows strict DTO envelope"""
        response = await http_client.get(
            "/api/internal/safety/status",
            cookies=staff_session["cookies"]
        )
        
        assert response.status_code == 200
        envelope = response.json()
        assert set(envelope) == {'data', 'error', 'meta'}
        assert envelope['error'] is None
        data = envelope['data']
        # Should only have expected fields
        expected_fields = {"packet", "packet_status", "capacity_status", 
                         "credential_rotation", "capabilities", "note"}
        actual_fields = set(data.keys())
        
        # Allow extra envelope fields from FastAPI
        assert expected_fields == actual_fields
        print(f"✓ Strict DTO envelope validated")


class TestEngineeringEndpointSecurity:
    """Test security properties of engineering endpoints"""
    
    @pytest.mark.asyncio
    async def test_no_auth_override_entire_app(self, http_client, staff_session, clean_db):
        """Test staff auth does not override entire app authentication"""
        # Staff auth should only work for internal endpoints, not bypass all auth
        
        # Internal endpoint should work
        response1 = await http_client.get(
            "/api/internal/capacity/profile",
            cookies=staff_session["cookies"]
        )
        assert response1.status_code == 200
        
        # Seed a different student's private record; staff role grants no ownership.
        from uuid import uuid4
        private_id = str(uuid4())
        await clean_db.tejas_attempts.insert_one({'id': private_id, 'user_id': str(uuid4()), 'created_at': 1})
        response2 = await http_client.get('/api/attempts', cookies=staff_session['cookies'])
        assert response2.status_code == 200
        assert response2.json()['data']['items'] == []
        response3 = await http_client.get('/api/attempts/' + private_id, cookies=staff_session['cookies'])
        assert response3.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invalid_config_rejects(self):
        """Test invalid workload config is rejected"""
        # This tests the capacity.calculate() validation
        from tejas.capacity import Workload, calculate
        
        # Valid config should work
        valid = Workload(active_attempts=500000)
        profile = calculate(valid)
        assert profile.workload.active_attempts == 500000
        
        # Invalid config should raise
        with pytest.raises(Exception):
            invalid = Workload(active_attempts=600000)  # Exceeds max
        
        print(f"✓ Invalid config rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

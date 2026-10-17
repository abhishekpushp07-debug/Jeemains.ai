"""
Packet 1 Safety Holds Tests

Tests that HTTP source upload, parse, publish, extract, and regrade operations
are held with 503 responses BEFORE receive/parse/database/storage.
Uses real httpx AsyncClient with proper error envelope assertions.
"""
import pytest


class TestSafetyHolds:
    """Test capability holds reject operations before parsing"""
    
    @pytest.mark.asyncio
    async def test_source_upload_held(self, http_client):
        """Test POST /api/studio/sets/{id}/files returns 503 before multipart parsing"""
        set_id = "test-set-123"
        
        # Attempt upload (should be held before parsing)
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/files",
            data={"kind": "questions"},
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope: error.code, not root code
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        assert "Retry-After" in response.headers or "retry-after" in response.headers
        assert "X-Tejas-Safety-Hold" in response.headers or "x-tejas-safety-hold" in response.headers
        print(f"✓ Source upload held with 503")
    
    @pytest.mark.asyncio
    async def test_source_parse_page_held(self, http_client):
        """Test GET /api/studio/files/{id}/page/{page} returns 503"""
        file_id = "test-file-123"
        
        response = await http_client.get(f"/api/studio/files/{file_id}/page/1")
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        assert "Retry-After" in response.headers or "retry-after" in response.headers
        print(f"✓ Source page preview held with 503")
    
    @pytest.mark.asyncio
    async def test_source_parse_text_held(self, http_client):
        """Test GET /api/studio/files/{id}/text/{page} returns 503"""
        file_id = "test-file-123"
        
        response = await http_client.get(f"/api/studio/files/{file_id}/text/1")
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Source text extraction held with 503")
    
    @pytest.mark.asyncio
    async def test_publication_held(self, http_client):
        """Test POST /api/studio/sets/{id}/publish returns 503"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/publish",
            json={"confirm": True}
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Publication held with 503")
    
    @pytest.mark.asyncio
    async def test_extraction_held(self, http_client):
        """Test POST /api/studio/sets/{id}/extract returns 503"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/extract",
            json={"replace_drafts": True}
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Extraction held with 503")
    
    @pytest.mark.asyncio
    async def test_regrade_held(self, http_client):
        """Test POST /api/studio/sets/{id}/regrade returns 503"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/regrade",
            json={"note": "Test correction note for regrade"}
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Regrade held with 503")
    
    @pytest.mark.asyncio
    async def test_asset_preview_held(self, http_client):
        """Test GET /api/studio/sets/{id}/questions/{qid}/asset/{kind}/{index} returns 503"""
        set_id = "test-set-123"
        qid = "test-question-123"
        
        response = await http_client.get(
            f"/api/studio/sets/{set_id}/questions/{qid}/asset/question/0"
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Asset preview held with 503")
    
    @pytest.mark.asyncio
    async def test_health_not_held(self, http_client):
        """Test GET /api/health is NOT held (should return 200)"""
        response = await http_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "ok"
        print(f"✓ Health endpoint not held (200 OK)")
    
    @pytest.mark.asyncio
    async def test_student_answer_not_held(self, http_client):
        """Test student answer operations are NOT held"""
        # Student operations should not be blocked by safety holds
        # (They will fail with auth errors, but not 503 capability_held)
        
        response = await http_client.get("/api/sets")
        
        assert response.status_code == 200
        assert response.json()['error'] is None
        assert response.json()['data']['items'] == []
        
        print(f"✓ Student catalogue not held")
    
    @pytest.mark.asyncio
    async def test_trailing_slash_cannot_bypass(self, http_client):
        """Test trailing slash cannot bypass holds"""
        set_id = "test-set-123"
        
        # Try with trailing slash
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/publish/",
            json={"confirm": True}
        )
        
        assert response.status_code == 503
        data = response.json()
        
        # Check proper error envelope
        assert data['data'] is None
        assert data['error']['code'] == 'capability_held'
        
        print(f"✓ Trailing slash cannot bypass hold")
    
    @pytest.mark.asyncio
    async def test_encoded_path_cannot_bypass(self, http_client):
        """Test URL-encoded paths cannot bypass holds"""
        set_id = "test-set-123"
        
        # Try with encoded slash
        response = await http_client.post(
            f"/api/studio/sets/{set_id}%2Fpublish",
            json={"confirm": True}
        )
        
        # Should either be 503 (held) or 404 (not found), but not 200
        assert response.status_code in (503, 404)
        if response.status_code == 503:
            data = response.json()
            if "error" in data:
                assert data["error"]["code"] == "capability_held"
            else:
                assert data.get("code") == "capability_held" or "capability" in str(data).lower()
        
        print(f"✓ Encoded path cannot bypass hold")
    
    @pytest.mark.asyncio
    async def test_options_not_blocked(self, http_client):
        """Test OPTIONS requests are not blocked"""
        set_id = "test-set-123"
        
        response = await http_client.options(f"/api/studio/sets/{set_id}/publish")
        
        # OPTIONS should not be held (CORS preflight)
        if response.status_code == 503:
            data = response.json()
            if "error" in data:
                assert data["error"]["code"] != "capability_held"
            else:
                assert data.get("code") != "capability_held"
        
        print(f"✓ OPTIONS not blocked by holds")


class TestHoldHeaders:
    """Test hold responses include correct headers"""
    
    @pytest.mark.asyncio
    async def test_hold_includes_retry_after(self, http_client):
        """Test held responses include Retry-After header"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/publish",
            json={"confirm": True}
        )
        
        assert "Retry-After" in response.headers or "retry-after" in response.headers
        retry_after_key = "Retry-After" if "Retry-After" in response.headers else "retry-after"
        retry_after = int(response.headers[retry_after_key])
        assert retry_after > 0
        print(f"✓ Retry-After header present: {retry_after}s")
    
    @pytest.mark.asyncio
    async def test_hold_includes_safety_header(self, http_client):
        """Test held responses include X-Tejas-Safety-Hold header"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/publish",
            json={"confirm": True}
        )
        
        assert "X-Tejas-Safety-Hold" in response.headers or "x-tejas-safety-hold" in response.headers
        safety_key = "X-Tejas-Safety-Hold" if "X-Tejas-Safety-Hold" in response.headers else "x-tejas-safety-hold"
        assert response.headers[safety_key] == "packet-1"
        print(f"✓ X-Tejas-Safety-Hold header present")
    
    @pytest.mark.asyncio
    async def test_hold_includes_cache_control(self, http_client):
        """Test held responses include Cache-Control: no-store"""
        set_id = "test-set-123"
        
        response = await http_client.post(
            f"/api/studio/sets/{set_id}/publish",
            json={"confirm": True}
        )
        
        assert "Cache-Control" in response.headers or "cache-control" in response.headers
        cache_key = "Cache-Control" if "Cache-Control" in response.headers else "cache-control"
        assert "no-store" in response.headers[cache_key]
        print(f"✓ Cache-Control: no-store header present")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

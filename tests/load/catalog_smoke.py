#!/usr/bin/env python3
"""
READ-ONLY HTTP benchmark for chapter catalog endpoints.

Guarded constraints:
- Uses REACT_APP_BACKEND_URL from frontend/.env (no hardcoded hosts/secrets)
- ONLY /api/chapter-exams and /api/sets endpoints
- Finite default 40 requests max 100
- Concurrency max 4
- Rate <=5 rps GLOBAL including workers
- Timeouts max 10sec
- Duration bounded
- Reports actual count, p50/p95/p99, HTTP errors/codes, limit/retry-after not hidden
- Endpoint distribution, versions, environment disclaimer UNQUALIFIED_500K
- No fake concurrency extrapolation
"""

import asyncio
import json
import os
import sys
import math
from datetime import datetime, timezone
import platform
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import httpx
from dotenv import dotenv_values


class CatalogSmokeTest:
    """Bounded READ-ONLY HTTP benchmark for catalog endpoints."""
    
    def __init__(self, base_url: str, max_requests: int = 40, max_workers: int = 4, max_rps: float = 5.0):
        """
        Initialize smoke test with guarded constraints.
        
        Args:
            base_url: Backend URL from frontend/.env
            max_requests: Total requests (default 40, max 100)
            max_workers: Concurrent workers (max 4)
            max_rps: Global rate limit (max 5 rps)
        """
        if not 1 <= max_requests <= 100:
            raise ValueError('max_requests must be 1..100')
        if not 1 <= max_workers <= 4:
            raise ValueError('max_workers must be 1..4')
        if not math.isfinite(max_rps) or not 1 <= max_rps <= 5:
            raise ValueError('max_rps must be finite and 1..5')
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise ValueError('Use a plain HTTP(S) origin without credentials, paths or query strings')
        
        self.base_url = base_url.rstrip('/')
        self.max_requests = max_requests
        self.max_workers = max_workers
        self.max_rps = max_rps
        self.min_interval = 1.0 / max_rps  # Minimum time between requests
        
        # Allowed endpoints only
        self.endpoints = [
            '/api/chapter-exams',
            '/api/chapter-exams?subject=Physics',
            '/api/chapter-exams?subject=Chemistry',
            '/api/chapter-exams?subject=Mathematics',
            '/api/chapter-exams?page=1',
            '/api/chapter-exams?page=2',
        ]
        
        # Metrics
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
        self.last_request_time = 0
        self.lock = asyncio.Lock()
    
    async def rate_limited_request(self, client: httpx.AsyncClient, endpoint: str) -> Dict:
        """Make a rate-limited HTTP request."""
        if endpoint not in self.endpoints:
            raise ValueError('Only declared read-only catalogue endpoints are permitted')
        # Global rate limiting
        async with self.lock:
            now = time.perf_counter()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.perf_counter()
        
        url = f"{self.base_url}{endpoint}"
        start = time.perf_counter()
        
        try:
            response = await client.get(url, timeout=10.0)
            duration = time.perf_counter() - start
            
            result = {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration_ms': duration * 1000,
                'timestamp': start,
                'success': 200 <= response.status_code < 300,
            }
            
            # Check for rate limit headers
            if 'Retry-After' in response.headers:
                result['retry_after'] = response.headers['Retry-After']
            if 'X-RateLimit-Remaining' in response.headers:
                result['rate_limit_remaining'] = response.headers['X-RateLimit-Remaining']
            
            return result
            
        except httpx.TimeoutException:
            duration = time.perf_counter() - start
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'duration_ms': duration * 1000,
                'timestamp': start,
                'success': False,
                'error': 'timeout',
            }
        except Exception as e:
            duration = time.perf_counter() - start
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'duration_ms': duration * 1000,
                'timestamp': start,
                'success': False,
                'error': str(e),
            }
    
    async def worker(self, worker_id: int, client: httpx.AsyncClient, request_count: int):
        """Worker coroutine to make requests."""
        for i in range(request_count):
            endpoint = self.endpoints[i % len(self.endpoints)]
            result = await self.rate_limited_request(client, endpoint)
            
            if result['success']:
                self.results.append(result)
            else:
                self.errors.append(result)
    
    async def run(self) -> Dict:
        """Run the smoke test and return metrics."""
        print(f"Starting catalog smoke test:")
        print(f"  Base URL: {self.base_url}")
        print(f"  Total requests: {self.max_requests}")
        print(f"  Workers: {self.max_workers}")
        print(f"  Max RPS: {self.max_rps}")
        print()
        
        start_time = time.perf_counter()
        
        # Distribute requests across workers
        requests_per_worker = self.max_requests // self.max_workers
        remainder = self.max_requests % self.max_workers
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for i in range(self.max_workers):
                count = requests_per_worker + (1 if i < remainder else 0)
                tasks.append(self.worker(i, client, count))
            
            self.aborted = False
            try:
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=110)
            except asyncio.TimeoutError:
                self.aborted = True
        
        total_duration = time.perf_counter() - start_time
        
        # Calculate metrics
        metrics = self.calculate_metrics(total_duration)
        
        return metrics
    
    def calculate_metrics(self, total_duration: float) -> Dict:
        """Calculate performance metrics."""
        all_requests = self.results + self.errors
        total_count = len(all_requests)
        success_count = len(self.results)
        error_count = len(self.errors)
        
        # Include failures/timeouts so a fast-success minority cannot hide overload.
        durations = sorted(r['duration_ms'] for r in all_requests)
        def percentile(p):
            return durations[max(0, math.ceil(len(durations) * p) - 1)] if durations else None
        p50, p95, p99 = (percentile(p) for p in (.50, .95, .99))
        
        # Status code distribution
        status_codes = defaultdict(int)
        for r in all_requests:
            status_codes[r['status_code']] += 1
        
        # Endpoint distribution
        endpoint_dist = defaultdict(int)
        for r in all_requests:
            endpoint_dist[r['endpoint']] += 1
        
        # Error details
        error_details = []
        for e in self.errors:
            error_details.append({
                'endpoint': e['endpoint'],
                'status_code': e['status_code'],
                'error': e.get('error', 'http_error'),
                'duration_ms': e['duration_ms'],
            })
        
        # Check for rate limiting
        rate_limited = any(r['status_code'] == 429 or 'retry_after' in r for r in all_requests)
        
        # Get git head if available
        try:
            git_head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            git_head = 'not_available'
        
        metrics = {
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'versions': {'python': platform.python_version(), 'httpx': httpx.__version__, 'git_head': git_head},
            'raw_requests': sorted(all_requests, key=lambda r:r['timestamp']),
            'aborted': getattr(self,'aborted',False),
            'latency_method': 'Nearest-rank, all completed requests including HTTP failures and timeouts; includes network and ingress. Not server-only SLO measurement.',
            'test_config': {
                'base_url': self.base_url,
                'total_requests': self.max_requests,
                'workers': self.max_workers,
                'max_rps': self.max_rps,
            },
            'summary': {
                'total_requests': total_count,
                'successful_requests': success_count,
                'failed_requests': error_count,
                'success_rate': success_count / total_count if total_count > 0 else 0,
                'total_duration_sec': total_duration,
                'actual_rps': total_count / total_duration if total_duration > 0 else 0,
            },
            'latency_ms': {
                'p50': round(p50, 2) if p50 is not None else None,
                'p95': round(p95, 2) if p95 is not None else None,
                'p99': round(p99, 2) if p99 is not None else None,
            },
            'status_codes': dict(status_codes),
            'endpoint_distribution': dict(endpoint_dist),
            'rate_limited': rate_limited,
            'errors': error_details,
            'environment_disclaimer': 'UNQUALIFIED_500K - This is a bounded smoke test with 40-100 requests at max 5 rps. NOT a capacity qualification for 500k users.',
            'test_scope': 'READ-ONLY catalog endpoints only. No write operations, no authentication flows, no high load testing.',
        }
        
        return metrics
    
    def print_report(self, metrics: Dict):
        """Print human-readable report."""
        print("\n" + "="*80)
        print("CATALOG SMOKE TEST REPORT")
        print("="*80)
        print()
        
        print("Configuration:")
        for key, value in metrics['test_config'].items():
            print(f"  {key}: {value}")
        print()
        
        print("Summary:")
        for key, value in metrics['summary'].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        print()
        
        print("Latency (ms):")
        for key, value in metrics['latency_ms'].items():
            print(f"  {key}: {value}")
        print()
        
        print("Status Codes:")
        for code, count in sorted(metrics['status_codes'].items()):
            print(f"  {code}: {count}")
        print()
        
        print("Endpoint Distribution:")
        for endpoint, count in sorted(metrics['endpoint_distribution'].items()):
            print(f"  {endpoint}: {count}")
        print()
        
        if metrics['rate_limited']:
            print("⚠️  Rate limiting detected (Retry-After headers present)")
            print()
        
        if metrics['errors']:
            print(f"Errors ({len(metrics['errors'])}):")
            for error in metrics['errors'][:10]:  # Show first 10
                print(f"  {error['endpoint']} - {error.get('error', error['status_code'])}")
            if len(metrics['errors']) > 10:
                print(f"  ... and {len(metrics['errors']) - 10} more")
            print()
        
        print("Environment Disclaimer:")
        print(f"  {metrics['environment_disclaimer']}")
        print()
        print("Test Scope:")
        print(f"  {metrics['test_scope']}")
        print()
        print("="*80)


def main():
    """Main entry point."""
    # Load backend URL from frontend/.env
    root = Path(__file__).resolve().parents[2]
    env_path = root / 'frontend' / '.env'
    
    if not env_path.exists():
        print(f"Error: {env_path} not found")
        sys.exit(1)
    
    env_vars = dotenv_values(env_path)
    base_url = env_vars.get('REACT_APP_BACKEND_URL')
    
    if not base_url:
        print("Error: REACT_APP_BACKEND_URL not found in frontend/.env")
        sys.exit(1)
    
    # Parse command line arguments
    max_requests = int(os.environ.get('MAX_REQUESTS', '40'))
    max_workers = int(os.environ.get('MAX_WORKERS', '4'))
    max_rps = float(os.environ.get('MAX_RPS', '5.0'))
    
    # Reject unsafe or malformed budgets rather than silently changing them.
    
    # Run test
    test = CatalogSmokeTest(base_url, max_requests, max_workers, max_rps)
    metrics = asyncio.run(test.run())
    
    # Print report
    test.print_report(metrics)
    
    # Save metrics
    output_path = root / 'test_reports' / 'capacity_catalog_smoke.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics saved to: {output_path}")
    
    # Exit with error if too many failures
    if metrics['summary']['failed_requests'] or metrics['summary']['total_requests'] != max_requests or metrics['aborted']:
        print('\nFAIL: Errors or incomplete bounded run')
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
READ-ONLY BSON bytes benchmark: Full set metadata vs BOOK_CHAPTER_PROJECT.

Measures the byte size difference between full chapter set documents and
projected metadata-only documents using BOOK_CHAPTER_PROJECT.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import bson
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient


async def measure_bson_bytes():
    """Measure BSON bytes for full vs projected chapter set metadata."""
    
    # Load MongoDB connection from backend/.env
    root = Path(__file__).resolve().parents[2]
    env_path = root / 'backend' / '.env'
    
    if not env_path.exists():
        print(f"Error: {env_path} not found")
        sys.exit(1)
    
    env_vars = dotenv_values(env_path)
    mongo_url = env_vars.get('MONGO_URL')
    db_name = env_vars.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("Error: MONGO_URL or DB_NAME not found in backend/.env")
        sys.exit(1)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    sets = db.tejas_sets
    
    # BOOK_CHAPTER_PROJECT from chapter_books.py
    BOOK_CHAPTER_PROJECT = {
        'id': 1, 'title': 1, 'chapter_number': 1, 'chapter_subject': 1,
        'questions.number': 1, 'start_page': 1, 'end_page': 1, 'key_page': 1,
        'verification': 1, 'independent_check': 1, 'revision': 1,
        'start_at': 1, 'end_at': 1, 'live_enabled': 1, '_id': 0
    }
    
    # Find chapter book sets
    chapter_sets = await sets.find({'chapter_book_id': {'$exists': True}, 'qa_only': {'$ne': True}, 'status': 'published', 'live_enabled': True}).to_list(100)
    
    if not chapter_sets:
        print("No chapter book sets found in database")
        client.close()
        return {
            'error': 'No chapter book sets found',
            'full_count': 0,
            'projected_count': 0,
            'full_bytes': 0,
            'projected_bytes': 0,
        }
    
    # Measure full documents
    full_bytes = sum(len(bson.encode(doc)) for doc in chapter_sets)
    full_count = len(chapter_sets)
    
    # Fetch projected documents
    projected_sets = await sets.find(
        {'chapter_book_id': {'$exists': True}, 'qa_only': {'$ne': True}, 'status': 'published', 'live_enabled': True},
        BOOK_CHAPTER_PROJECT
    ).to_list(100)
    
    # Measure projected documents
    projected_bytes = sum(len(bson.encode(doc)) for doc in projected_sets)
    projected_count = len(projected_sets)
    
    client.close()
    
    # Calculate savings
    bytes_saved = full_bytes - projected_bytes
    percent_saved = (bytes_saved / full_bytes * 100) if full_bytes > 0 else 0
    
    results = {
        'full_metadata': {
            'count': full_count,
            'total_bytes': full_bytes,
            'avg_bytes_per_doc': full_bytes // full_count if full_count > 0 else 0,
        },
        'projected_metadata': {
            'count': projected_count,
            'total_bytes': projected_bytes,
            'avg_bytes_per_doc': projected_bytes // projected_count if projected_count > 0 else 0,
        },
        'savings': {
            'bytes_saved': bytes_saved,
            'percent_saved': round(percent_saved, 2),
        },
        'projection_fields': list(BOOK_CHAPTER_PROJECT.keys()),
        'note': 'BOOK_CHAPTER_PROJECT excludes question text, options, answers, solutions, and source refs',
    }
    
    return results


def print_report(results: dict):
    """Print human-readable report."""
    print("\n" + "="*80)
    print("BSON BYTES BENCHMARK: Full vs Projected Chapter Set Metadata")
    print("="*80)
    print()
    
    if 'error' in results:
        print(f"Error: {results['error']}")
        return
    
    print("Full Metadata (all fields):")
    print(f"  Document count: {results['full_metadata']['count']}")
    print(f"  Total bytes: {results['full_metadata']['total_bytes']:,}")
    print(f"  Avg bytes per doc: {results['full_metadata']['avg_bytes_per_doc']:,}")
    print()
    
    print("Projected Metadata (BOOK_CHAPTER_PROJECT):")
    print(f"  Document count: {results['projected_metadata']['count']}")
    print(f"  Total bytes: {results['projected_metadata']['total_bytes']:,}")
    print(f"  Avg bytes per doc: {results['projected_metadata']['avg_bytes_per_doc']:,}")
    print()
    
    print("Savings:")
    print(f"  Bytes saved: {results['savings']['bytes_saved']:,}")
    print(f"  Percent saved: {results['savings']['percent_saved']}%")
    print()
    
    print("Projection Fields:")
    for field in results['projection_fields']:
        print(f"  - {field}")
    print()
    
    print("Note:")
    print(f"  {results['note']}")
    print()
    print("="*80)


def main():
    """Main entry point."""
    results = asyncio.run(measure_bson_bytes())
    
    # Print report
    print_report(results)
    
    # Save results
    root = Path(__file__).resolve().parents[2]
    output_path = root / 'test_reports' / 'bson_bytes_benchmark.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_path}")
    
    sys.exit(0)


if __name__ == '__main__':
    main()

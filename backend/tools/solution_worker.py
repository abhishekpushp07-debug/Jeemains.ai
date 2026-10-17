"""Standalone gpt-6-astra ten-mark solution worker (single instance via file lock)."""
import asyncio, fcntl, logging, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

LOCK = open('/tmp/ten-mark-worker.lock', 'w')
try:
    fcntl.flock(LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(0)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s')
from tejas.mock_solutions import worker

asyncio.run(worker())

"""Paused legacy solution worker; --pause-pending retains unfinished work in MongoDB."""
import argparse, asyncio, logging, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s')
from tejas.mock_solutions import PAUSE_MESSAGE, pause_pending
from tejas.db import client


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-pending', action='store_true', help='Pause unfinished legacy AI jobs without deleting them.')
    parser.add_argument('--manual', action='store_true', help='Drain only persisted owner-click requests.')
    args = parser.parse_args()
    try:
        if args.manual:
            import fcntl
            from tejas.manual_solutions import run_manual
            with open('/tmp/manual-solution-worker.lock', 'w') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return
                await run_manual()
        elif args.pause_pending:
            print(await pause_pending())
        else:
            logging.warning(PAUSE_MESSAGE)
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(main())

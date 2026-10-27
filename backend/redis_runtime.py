"""Supervisor-owned, private, disposable metadata cache. No TCP listener/persistence."""
import json
import os
from pathlib import Path


def main():
    config = json.loads(Path(__file__).with_name('redis_runtime.json').read_text())
    socket = Path(config['socket_path'])
    socket.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    socket.parent.chmod(0o700)
    os.execvp('redis-server', [
        'redis-server', '--port', '0', '--protected-mode', 'yes',
        '--unixsocket', str(socket), '--unixsocketperm', '700',
        '--save', '', '--appendonly', 'no', '--maxmemory', config['maxmemory'],
        '--maxmemory-policy', 'allkeys-lru', '--loglevel', 'notice',
    ])


if __name__ == '__main__':
    main()
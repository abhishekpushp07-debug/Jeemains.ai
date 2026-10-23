"""Byte-bounded, thread-safe read-through cache. Never an authorization boundary."""

from collections import OrderedDict
from threading import RLock


class ByteCache:
    def __init__(self, max_bytes):
        self.limit = max_bytes
        self.size = 0
        self.data = OrderedDict()
        self.lock = RLock()

    def get(self, key):
        with self.lock:
            value = self.data.get(key)
            if value is not None:
                self.data.move_to_end(key)
            return value

    def put(self, key, value):
        if len(value) > self.limit:
            return value
        with self.lock:
            if key in self.data:
                self.size -= len(self.data.pop(key))
            self.data[key] = value
            self.size += len(value)
            while self.size > self.limit:
                _, v = self.data.popitem(last=False)
                self.size -= len(v)
        return value

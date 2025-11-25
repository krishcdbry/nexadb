#!/usr/bin/env python3
"""
NexaDB Storage Engine - LSM-Tree Implementation
================================================

Core storage engine using Log-Structured Merge Tree (LSM) design.
Optimized for write-heavy workloads with efficient reads.

Key Features:
- Write-Ahead Log (WAL) for durability
- MemTable (in-memory sorted structure)
- SSTables (Sorted String Tables on disk)
- Compaction (garbage collection)
- Crash recovery
"""

import os
import json
import time
import threading
from typing import Optional, Dict, List, Tuple
from collections import OrderedDict
import pickle
import struct


class MemTable:
    """
    In-memory sorted data structure (Red-Black Tree equivalent using OrderedDict)

    Operations:
    - Insert: O(log n)
    - Get: O(log n)
    - Range scan: O(log n + k) where k = results
    """

    def __init__(self, max_size: int = 1024 * 1024):  # 1MB default
        self.data = OrderedDict()
        self.size = 0
        self.max_size = max_size

    def put(self, key: str, value: bytes) -> bool:
        """
        Insert key-value pair.
        Returns True if MemTable is full and needs flush.
        """
        if key in self.data:
            old_size = len(self.data[key])
            self.size -= old_size

        self.data[key] = value
        self.size += len(value)

        # Keep sorted
        self.data.move_to_end(key)
        self.data = OrderedDict(sorted(self.data.items()))

        return self.size >= self.max_size

    def get(self, key: str) -> Optional[bytes]:
        """Get value by key"""
        return self.data.get(key)

    def delete(self, key: str):
        """Mark key as deleted (tombstone)"""
        self.data[key] = b'__TOMBSTONE__'

    def range_scan(self, start_key: str, end_key: str) -> List[Tuple[str, bytes]]:
        """Scan keys in range [start_key, end_key]"""
        results = []
        for k, v in self.data.items():
            if start_key <= k <= end_key:
                if v != b'__TOMBSTONE__':
                    results.append((k, v))
        return results

    def all_items(self) -> List[Tuple[str, bytes]]:
        """Get all key-value pairs (for flushing)"""
        return list(self.data.items())

    def clear(self):
        """Clear all data"""
        self.data.clear()
        self.size = 0


class WAL:
    """
    Write-Ahead Log for crash recovery and durability.

    Every write is first written to WAL before updating MemTable.
    On crash, WAL is replayed to rebuild MemTable.

    Format: [timestamp|operation|key_len|key|value_len|value]
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = open(filepath, 'ab')  # Append mode

    def append(self, operation: str, key: str, value: bytes):
        """Append operation to WAL"""
        timestamp = int(time.time() * 1000)

        # Encode: timestamp(8) | op_len(4) | op | key_len(4) | key | value_len(4) | value
        entry = struct.pack('Q', timestamp)  # 8 bytes timestamp

        op_bytes = operation.encode('utf-8')
        entry += struct.pack('I', len(op_bytes))
        entry += op_bytes

        key_bytes = key.encode('utf-8')
        entry += struct.pack('I', len(key_bytes))
        entry += key_bytes

        entry += struct.pack('I', len(value))
        entry += value

        self.file.write(entry)
        self.file.flush()
        os.fsync(self.file.fileno())  # Force write to disk

    def replay(self) -> List[Tuple[str, str, bytes]]:
        """
        Replay WAL to recover operations.
        Returns list of (operation, key, value)
        """
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            return []

        operations = []
        with open(self.filepath, 'rb') as f:
            while True:
                # Read timestamp
                ts_bytes = f.read(8)
                if not ts_bytes:
                    break

                # Read operation
                op_len_bytes = f.read(4)
                if not op_len_bytes:
                    break
                op_len = struct.unpack('I', op_len_bytes)[0]
                operation = f.read(op_len).decode('utf-8')

                # Read key
                key_len = struct.unpack('I', f.read(4))[0]
                key = f.read(key_len).decode('utf-8')

                # Read value
                value_len = struct.unpack('I', f.read(4))[0]
                value = f.read(value_len)

                operations.append((operation, key, value))

        return operations

    def clear(self):
        """Clear WAL (after successful flush)"""
        self.file.close()
        os.remove(self.filepath)
        self.file = open(self.filepath, 'ab')

    def close(self):
        """Close WAL file"""
        self.file.close()


class SSTable:
    """
    Sorted String Table - Immutable on-disk data structure.

    Format:
    - Index: {key: file_offset} (for fast lookups)
    - Data: Sorted key-value pairs

    SSTable files are immutable once written.
    Multiple SSTables are merged during compaction.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.index = {}  # key -> offset
        self.data_file = None

    @staticmethod
    def create(filepath: str, data: List[Tuple[str, bytes]]):
        """Create new SSTable from sorted data"""
        sstable = SSTable(filepath)

        # Write data file
        data_filepath = f"{filepath}.data"
        index_filepath = f"{filepath}.index"

        with open(data_filepath, 'wb') as f:
            for key, value in sorted(data):
                offset = f.tell()
                sstable.index[key] = offset

                # Write: key_len(4) | key | value_len(4) | value
                key_bytes = key.encode('utf-8')
                f.write(struct.pack('I', len(key_bytes)))
                f.write(key_bytes)
                f.write(struct.pack('I', len(value)))
                f.write(value)

        # Write index
        with open(index_filepath, 'wb') as f:
            pickle.dump(sstable.index, f)

        return sstable

    def load(self):
        """Load SSTable index into memory"""
        index_filepath = f"{self.filepath}.index"
        if os.path.exists(index_filepath):
            with open(index_filepath, 'rb') as f:
                self.index = pickle.load(f)

        self.data_file = open(f"{self.filepath}.data", 'rb')

    def get(self, key: str) -> Optional[bytes]:
        """Get value by key"""
        if key not in self.index:
            return None

        offset = self.index[key]
        self.data_file.seek(offset)

        # Read key_len and key (skip)
        key_len = struct.unpack('I', self.data_file.read(4))[0]
        self.data_file.read(key_len)

        # Read value
        value_len = struct.unpack('I', self.data_file.read(4))[0]
        value = self.data_file.read(value_len)

        return value if value != b'__TOMBSTONE__' else None

    def range_scan(self, start_key: str, end_key: str) -> List[Tuple[str, bytes]]:
        """Scan keys in range"""
        results = []
        for key in sorted(self.index.keys()):
            if start_key <= key <= end_key:
                value = self.get(key)
                if value is not None:
                    results.append((key, value))
        return results

    def all_items(self) -> List[Tuple[str, bytes]]:
        """Get all key-value pairs"""
        results = []
        for key in sorted(self.index.keys()):
            value = self.get(key)
            if value is not None:
                results.append((key, value))
        return results

    def close(self):
        """Close SSTable files"""
        if self.data_file:
            self.data_file.close()

    def delete(self):
        """Delete SSTable files"""
        self.close()
        data_filepath = f"{self.filepath}.data"
        index_filepath = f"{self.filepath}.index"

        if os.path.exists(data_filepath):
            os.remove(data_filepath)
        if os.path.exists(index_filepath):
            os.remove(index_filepath)


class LSMStorageEngine:
    """
    Main LSM-Tree Storage Engine

    Architecture:
    1. Writes go to WAL + MemTable
    2. When MemTable full → Flush to SSTable (Level 0)
    3. Background compaction merges SSTables
    4. Reads check: MemTable → SSTable L0 → SSTable L1 → ...

    This provides:
    - Fast writes (append-only WAL + in-memory MemTable)
    - Durable writes (WAL)
    - Efficient reads (MemTable + indexed SSTables)
    - Space efficiency (compaction removes old/deleted data)
    """

    def __init__(self, data_dir: str, memtable_size: int = 1024 * 1024):
        self.data_dir = data_dir
        self.memtable_size = memtable_size

        os.makedirs(data_dir, exist_ok=True)

        # Active MemTable
        self.memtable = MemTable(max_size=memtable_size)

        # WAL
        wal_path = os.path.join(data_dir, 'wal.log')
        self.wal = WAL(wal_path)

        # SSTables (Level 0, Level 1, etc.)
        self.sstables: List[SSTable] = []

        # Compaction thread
        self.compaction_thread = None
        self.running = True
        self.compaction_lock = threading.Lock()

        # Recovery
        self._recover()

        # Start background compaction
        self._start_compaction_thread()

    def _recover(self):
        """Recover from crash by replaying WAL"""
        print("[RECOVERY] Replaying WAL...")
        operations = self.wal.replay()

        for op, key, value in operations:
            if op == 'PUT':
                self.memtable.put(key, value)
            elif op == 'DELETE':
                self.memtable.delete(key)

        print(f"[RECOVERY] Recovered {len(operations)} operations")

        # Load existing SSTables
        self._load_sstables()

    def _load_sstables(self):
        """Load all SSTable files from disk"""
        sstable_files = sorted([
            f for f in os.listdir(self.data_dir)
            if f.endswith('.data')
        ])

        for filename in sstable_files:
            filepath = os.path.join(self.data_dir, filename.replace('.data', ''))
            sstable = SSTable(filepath)
            sstable.load()
            self.sstables.append(sstable)

        print(f"[RECOVERY] Loaded {len(self.sstables)} SSTables")

    def put(self, key: str, value: bytes):
        """
        Insert key-value pair

        Process:
        1. Write to WAL (durability)
        2. Write to MemTable (fast access)
        3. If MemTable full → Flush to SSTable
        """
        # Write to WAL first (durability)
        self.wal.append('PUT', key, value)

        # Write to MemTable
        needs_flush = self.memtable.put(key, value)

        if needs_flush:
            self._flush_memtable()

    def get(self, key: str) -> Optional[bytes]:
        """
        Get value by key

        Search order:
        1. MemTable (most recent)
        2. SSTables (newest to oldest)
        """
        # Check MemTable first
        value = self.memtable.get(key)
        if value is not None:
            return value if value != b'__TOMBSTONE__' else None

        # Check SSTables (newest first)
        for sstable in reversed(self.sstables):
            value = sstable.get(key)
            if value is not None:
                return value

        return None

    def delete(self, key: str):
        """
        Delete key (using tombstone marker)

        Actual deletion happens during compaction.
        """
        self.wal.append('DELETE', key, b'__TOMBSTONE__')
        self.memtable.delete(key)

    def range_scan(self, start_key: str, end_key: str) -> List[Tuple[str, bytes]]:
        """
        Scan keys in range [start_key, end_key]

        Merges results from MemTable and all SSTables.
        """
        results = {}

        # First, collect ALL keys from MemTable (including tombstones)
        # This ensures tombstones block SSTable values
        for k, v in self.memtable.data.items():
            if start_key <= k <= end_key:
                results[k] = v

        # Then collect from SSTables, but only if not in MemTable
        for sstable in self.sstables:
            for key, value in sstable.range_scan(start_key, end_key):
                if key not in results:  # MemTable has priority (including tombstones)
                    results[key] = value

        # Filter tombstones and sort
        final_results = [
            (k, v) for k, v in sorted(results.items())
            if v != b'__TOMBSTONE__'
        ]

        return final_results

    def _flush_memtable(self):
        """
        Flush MemTable to SSTable (Level 0)

        Called when MemTable reaches max size.
        """
        print(f"[FLUSH] Flushing MemTable ({self.memtable.size} bytes)")

        with self.compaction_lock:
            # Create new SSTable
            timestamp = int(time.time() * 1000)
            sstable_path = os.path.join(self.data_dir, f'sstable_{timestamp}')

            data = self.memtable.all_items()
            sstable = SSTable.create(sstable_path, data)
            sstable.load()

            self.sstables.append(sstable)

            # Clear MemTable and WAL
            self.memtable.clear()
            self.wal.clear()

            print(f"[FLUSH] Created SSTable: {sstable_path}")

    def _start_compaction_thread(self):
        """Start background compaction thread"""
        def compaction_loop():
            while self.running:
                time.sleep(10)  # Compact every 10 seconds
                if len(self.sstables) >= 3:  # Compact if 3+ SSTables
                    self._compact()

        self.compaction_thread = threading.Thread(target=compaction_loop, daemon=True)
        self.compaction_thread.start()

    def _compact(self):
        """
        Compact SSTables (merge and remove tombstones)

        Process:
        1. Merge all SSTables
        2. Remove duplicate keys (keep latest)
        3. Remove tombstones
        4. Write new SSTable
        5. Delete old SSTables
        """
        print(f"[COMPACTION] Starting compaction of {len(self.sstables)} SSTables")

        with self.compaction_lock:
            if len(self.sstables) < 2:
                return

            # Collect all data
            all_data = {}
            for sstable in self.sstables:
                for key, value in sstable.all_items():
                    all_data[key] = value  # Latest value wins

            # Remove tombstones
            compacted_data = [
                (k, v) for k, v in all_data.items()
                if v != b'__TOMBSTONE__'
            ]

            # Create new compacted SSTable
            timestamp = int(time.time() * 1000)
            compacted_path = os.path.join(self.data_dir, f'compacted_{timestamp}')
            new_sstable = SSTable.create(compacted_path, compacted_data)
            new_sstable.load()

            # Delete old SSTables
            for sstable in self.sstables:
                sstable.delete()

            # Replace with compacted SSTable
            self.sstables = [new_sstable]

            print(f"[COMPACTION] Complete. Compacted to {len(compacted_data)} entries")

    def close(self):
        """Shutdown storage engine"""
        print("[SHUTDOWN] Closing NexaDB storage engine...")

        self.running = False
        if self.compaction_thread:
            self.compaction_thread.join(timeout=5)

        # Flush MemTable if not empty
        if self.memtable.size > 0:
            self._flush_memtable()

        # Close all SSTables
        for sstable in self.sstables:
            sstable.close()

        self.wal.close()
        print("[SHUTDOWN] Storage engine closed")

    def stats(self) -> Dict:
        """Get database statistics"""
        total_keys = len(self.memtable.data)
        for sstable in self.sstables:
            total_keys += len(sstable.index)

        return {
            'memtable_size': self.memtable.size,
            'memtable_keys': len(self.memtable.data),
            'num_sstables': len(self.sstables),
            'total_keys': total_keys,
            'data_dir': self.data_dir
        }


if __name__ == '__main__':
    # Example usage
    print("="*60)
    print("NexaDB Storage Engine - Example Usage")
    print("="*60)

    # Create storage engine
    db = LSMStorageEngine(data_dir='./nexadb_data')

    # Insert data
    print("\n[TEST] Inserting 1000 key-value pairs...")
    for i in range(1000):
        db.put(f'key_{i:04d}', f'value_{i}'.encode())

    # Retrieve data
    print("\n[TEST] Retrieving keys...")
    print(f"key_0000: {db.get('key_0000')}")
    print(f"key_0500: {db.get('key_0500')}")
    print(f"key_0999: {db.get('key_0999')}")

    # Range scan
    print("\n[TEST] Range scan (key_0010 to key_0020):")
    results = db.range_scan('key_0010', 'key_0020')
    for key, value in results[:5]:
        print(f"  {key}: {value}")

    # Delete
    print("\n[TEST] Deleting key_0500...")
    db.delete('key_0500')
    print(f"key_0500 after delete: {db.get('key_0500')}")

    # Stats
    print("\n[STATS] Database statistics:")
    stats = db.stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Close
    time.sleep(2)  # Let compaction run
    db.close()

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

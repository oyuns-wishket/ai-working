#!/usr/bin/env python3
"""Serialize one session's cleanup across native hooks and Paseo plugins."""
import fcntl
import json
import os
import stat
import sys


def main():
    lock_path, node, hook = sys.argv[1:]
    os.makedirs(os.path.dirname(lock_path), mode=0o700, exist_ok=True)
    # Never unlink a lock file: waiters must keep referring to the same inode.
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as lock:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Cleanup lock is not a regular file")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"status": "busy"}))
            return 0
        # Replace this process so the lock survives exactly as long as cleanup,
        # even when a provider kills the whole process tree during shutdown.
        os.set_inheritable(fd, True)
        os.execv(node, [node, hook, "--cleanup-locked", "--archive-cleanup"])


if __name__ == "__main__":
    sys.exit(main())

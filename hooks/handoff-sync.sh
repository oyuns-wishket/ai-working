#!/bin/sh
# Retired compatibility entry point. Session hooks must never edit Git history or
# push a branch. The agent updates HANDOFF in the authorized task closeout.
# Keep this file so stale installations also become harmless after bootstrap.
exit 0

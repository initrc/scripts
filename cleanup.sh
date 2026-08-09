#!/bin/sh

# requires fd and trash (brew install)
# `fd -HI` finds hidden and ignored files 

dry_run=false

[ "$1" = "-d" ] && dry_run=true && shift

pattern=$1

# The key trick is set -- ...:
# after saving your search term in pattern, it replaces the positional arguments
# ($1, $2, etc.) with your list of search directories. Then "$@" expands to all
# of those directories while correctly preserving paths containing spaces like
# Application Support.
set -- \
  "$HOME/Library/Application Support" \
  "$HOME/Library/Preferences" \
  "$HOME/Library/Containers" \
  "$HOME/Library/Group Containers" \
  "$HOME/Library/Caches" \
  "$HOME/Library/Logs" \
  "$HOME/Library/HTTPStorages" \
  "$HOME/Library/WebKit" \
  "$HOME/Library/Saved Application State" \
  "$HOME/Library/Application Scripts" \
  "$HOME/.local/share" \
  "$HOME/.local/state"

[ "$dry_run" = true ] && exec fd -HI "$pattern" "$@"

exec fd -HI "$pattern" "$@" -x trash


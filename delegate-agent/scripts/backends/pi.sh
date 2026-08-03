#!/bin/sh
set -eu

: "${DELEGATE_ROOT:?DELEGATE_ROOT is required}"
: "${DELEGATE_MODEL:?DELEGATE_MODEL is required}"
: "${DELEGATE_PROMPT_FILE:?DELEGATE_PROMPT_FILE is required}"
: "${DELEGATE_MODE:?DELEGATE_MODE is required}"

prompt=$(cat "$DELEGATE_PROMPT_FILE")
cd "$DELEGATE_ROOT"

set -- pi
case "$DELEGATE_MODEL" in
  */*) set -- "$@" --model "$DELEGATE_MODEL" ;;
  *) set -- "$@" --provider opencode-go --model "$DELEGATE_MODEL" ;;
esac

# Keep read-only calls read-only; work calls are still confined by the outer macOS sandbox.
tools=read,grep,find,ls
if [ "$DELEGATE_MODE" = work ]; then
  tools=read,grep,find,ls,edit,write,bash
fi

set -- "$@" \
  --thinking minimal \
  --mode json \
  --no-session \
  --no-extensions \
  --no-skills \
  --no-context-files \
  --no-approve \
  --tools "$tools" \
  --print \
  "$prompt"
exec "$@"

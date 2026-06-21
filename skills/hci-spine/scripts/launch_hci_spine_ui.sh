#!/usr/bin/env bash
# Launch the hci-spine intake wizard in an external terminal window.
# macOS (Terminal.app) + Linux (gnome-terminal / konsole / xterm).
# Usage: launch_hci_spine_ui.sh [output_dir]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WIZARD="$SCRIPT_DIR/intake_wizard.py"
OUTPUT_DIR="${1:-hci_spine_output}"

if [ ! -f "$WIZARD" ]; then
    echo "hci-spine intake wizard not found: $WIZARD" >&2
    exit 1
fi

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "Python 3 not found. Install Python and retry." >&2
    exit 1
fi

# Resolve OUTPUT_DIR to an absolute path so the new terminal (which starts in
# $HOME) writes to the caller's project, not the home directory.
OUTPUT_ABS="$(cd "$(dirname "$OUTPUT_DIR")" 2>/dev/null && pwd)/$(basename "$OUTPUT_DIR")" || OUTPUT_ABS="$PWD/$OUTPUT_DIR"

CMD="$PYTHON \"$WIZARD\" --keyboard-ui --output-dir \"$OUTPUT_ABS\"; echo ''; echo 'hci-spine intake finished. Config in: $OUTPUT_ABS'; echo 'Close this window after checking.'; exec bash"

case "$(uname -s)" in
    Darwin)
        osascript -e "tell application \"Terminal\" to do script \"$CMD\"" -e 'tell application "Terminal" to activate'
        ;;
    Linux)
        if command -v gnome-terminal &>/dev/null; then
            gnome-terminal -- bash -c "$CMD"
        elif command -v konsole &>/dev/null; then
            konsole -e bash -c "$CMD"
        elif command -v xterm &>/dev/null; then
            xterm -e bash -c "$CMD" &
        else
            echo "No supported terminal found. Run directly:" >&2
            echo "  $PYTHON $WIZARD --in-place --output-dir $OUTPUT_DIR" >&2
            exit 1
        fi
        ;;
    *)
        echo "Unsupported OS: $(uname -s). Run: $PYTHON $WIZARD --in-place" >&2
        exit 1
        ;;
esac

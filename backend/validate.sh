#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

show_menu() {
    echo ""
    echo "============================================"
    echo "  VALIDATION MENU"
    echo "============================================"
    echo "  1) validate.py    — Functional tests"
    echo "  2) pen_test.py    — Security tests"
    echo "  3) delete_thread.py — Cleanup test sessions (MongoDB)"
    echo "  0) Exit"
    echo "============================================"
    echo ""
}

run_cmd() {
    local label="$1"
    shift
    echo ""
    echo ">>> [$label] Starting..."
    echo ""
    PYTHONUNBUFFERED=1 uv run python "$@"
    local rc=$?
    echo ""
    if [ $rc -eq 0 ]; then
        echo ">>> [$label] FINISHED — All passed"
    else
        echo ">>> [$label] FINISHED — Exit code $rc"
    fi
    echo ""
    echo "Press ENTER to return to menu..."
    read -r
}

while true; do
    show_menu
    printf "Choice: "
    read -r choice
    case "$choice" in
        1)
            run_cmd "validate.py" -m validation.validate
            ;;
        2)
            run_cmd "pen_test.py" -m validation.pen_test
            ;;
        3)
            run_cmd "delete_thread.py" -m validation.delete_thread
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice. Try again."
            sleep 1
            ;;
    esac
done

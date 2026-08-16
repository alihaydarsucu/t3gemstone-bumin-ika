#!/usr/bin/env bash
# GCS (Ground Control Station) launch helper.
#
# Starts the sim container (if not running) and launches the browser-based
# GCS inside it in a single host-side command. Avoids the paste race of
# interactive `docker exec` (see docs/tr/gcs.md, section 2).
#
# Usage (from repo root):
#   ./tools/gcs.sh                      # office.world (default)
#   ./tools/gcs.sh world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world
#   ./tools/gcs.sh house                # shortcut for the house world
#
# After launch, open http://localhost:8000 in your browser.

set -euo pipefail

CONTAINER="${GEMSTONE_CONTAINER:-gemstone_sim}"
WEB_PORT="${GCS_WEB_PORT:-8000}"

# Start container if not running yet.
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "[gcs.sh] Starting container '$CONTAINER' ..."
    docker start "$CONTAINER" >/dev/null
fi

# Resolve house shortcut to an explicit world_file launch arg.
if [ "${1:-}" = "house" ]; then
    shift
    set -- world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/house.world "$@"
fi

echo "[gcs.sh] Launching GCS in '$CONTAINER' ..."
echo "[gcs.sh] Open http://localhost:${WEB_PORT} in your browser after it boots."

docker exec -it "$CONTAINER" bash -lc "
    source /opt/ros/humble/setup.bash &&
    source /ros_ws/install/setup.bash &&
    ros2 launch gemstone_gcs gcs_bringup.launch.py $*"

# The launch runs attached (Ctrl+C stops it). Log line for the user.
echo "[gcs.sh] GCS stopped."

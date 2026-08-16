#!/usr/bin/env bash
# GCS (Ground Control Station) + robot launch helper.
#
# Starts the sim container (if not running) and launches either side inside
# it in a single host-side command. Avoids the paste race of interactive
# `docker exec` (see docs/tr/gcs.md, section 2).
#
# In the real world the robot side runs on the robot's onboard computer and
# the GCS web side on a separate ground-station machine, both connected over
# the ROS graph (ROS_DOMAIN_ID / DDS). These two modes mirror that split.
#
# Usage (from repo root):
#   ./tools/gcs.sh robot                 # robot side: sim + Nav2 + exploration + RViz (office.world)
#   ./tools/gcs.sh robot house           # robot side with house.world
#   ./tools/gcs.sh robot enable_rviz:=false
#   ./tools/gcs.sh web                   # GCS web side: rosbridge + web_video + web UI
#   ./tools/gcs.sh both                  # robot + web in two detached execs (default)
#
# After launch, open http://localhost:8000 in your browser (web/both modes).

set -euo pipefail

CONTAINER="${GEMSTONE_CONTAINER:-gemstone_sim}"
WEB_PORT="${GCS_WEB_PORT:-8000}"

# Start container if not running yet.
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "[gcs.sh] Starting container '$CONTAINER' ..."
    docker start "$CONTAINER" >/dev/null
fi

LAUNCH_CMD="source /opt/ros/humble/setup.bash && source /ros_ws/install/setup.bash &&"

robot_cmd() {
    local extra=""
    local world="office.world"
    if [ "${1:-}" = "house" ]; then
        world="house.world"
        shift
    fi
    if [ "${1:-}" = "office" ]; then
        world="office.world"
        shift
    fi
    extra="$*"
    echo "$LAUNCH_CMD ros2 launch gemstone_frontier_explorer auto_mapping.launch.py \
        world_file:=/ros_ws/install/gemstone_sim/share/gemstone_sim/worlds/$world \
        enable_rviz:=true $extra"
}

web_cmd() {
    echo "$LAUNCH_CMD ros2 launch gemstone_gcs gcs_bringup.launch.py $*"
}

MODE="${1:-both}"

case "$MODE" in
    robot)
        shift
        echo "[gcs.sh] Launching robot side in '$CONTAINER' (RViz + sim + Nav2) ..."
        docker exec -it "$CONTAINER" bash -lc "$(robot_cmd "$@")"
        echo "[gcs.sh] Robot side stopped."
        ;;
    web)
        shift
        echo "[gcs.sh] Launching GCS web side in '$CONTAINER' ..."
        echo "[gcs.sh] Open http://localhost:${WEB_PORT} in your browser after it boots."
        docker exec -it "$CONTAINER" bash -lc "$(web_cmd "$@")"
        echo "[gcs.sh] GCS web side stopped."
        ;;
    both)
        shift
        echo "[gcs.sh] Launching robot side (detached) then GCS web side ..."
        echo "[gcs.sh] Open http://localhost:${WEB_PORT} in your browser after it boots."
        docker exec -d "$CONTAINER" bash -lc "$(robot_cmd "$@")" >/dev/null
        docker exec -it "$CONTAINER" bash -lc "$(web_cmd)"
        echo "[gcs.sh] GCS web side stopped (robot side still running)."
        ;;
    *)
        echo "Usage: $0 [robot|web|both] [world_file...|house|office]" >&2
        exit 1
        ;;
esac

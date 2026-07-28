FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-lc"]

RUN apt-get update && apt-get install -y \
    git \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    python3-serial \
    python3-opencv \
    ros-humble-v4l2-camera \
    ros-humble-cv-bridge \
    ros-humble-slam-toolbox \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-imu-filter-madgwick \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-xacro \
    ros-humble-diagnostic-updater \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

# rf2o_laser_odometry ve sllidar_ros2 apt'ta binary olarak dagitilmadigi
# icin kaynak koddan clone edilir (bkz. docs/tr/build.md).
RUN mkdir -p src && \
    (test -d src/rf2o_laser_odometry || git clone --depth 1 https://github.com/MAPIRlab/rf2o_laser_odometry.git src/rf2o_laser_odometry) && \
    (test -d src/sllidar_ros2 || git clone --depth 1 https://github.com/Slamtec/sllidar_ros2.git src/sllidar_ros2)

RUN rosdep init 2>/dev/null || true && rosdep update

CMD ["/bin/bash"]

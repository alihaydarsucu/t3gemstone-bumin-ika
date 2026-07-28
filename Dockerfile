FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-lc"]

RUN apt-get update && apt-get install -y \
    git \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

RUN rosdep init 2>/dev/null || true && rosdep update

CMD ["/bin/bash"]

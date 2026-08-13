from gemstone_exploration_demo.naive_obstacle_avoidance import decide_naive_avoidance


def test_goes_forward_when_path_clear():
    command = decide_naive_avoidance(
        front_distance=2.0,
        left_distance=2.0,
        right_distance=2.0,
        distance_threshold=0.8,
        forward_speed=0.15,
        turn_speed=0.4,
    )
    assert command.linear_x == 0.15
    assert command.angular_z == 0.0


def test_turns_when_front_blocked():
    command = decide_naive_avoidance(
        front_distance=0.5,
        left_distance=2.0,
        right_distance=2.0,
        distance_threshold=0.8,
        forward_speed=0.15,
        turn_speed=0.4,
    )
    assert command.linear_x == 0.0
    assert command.angular_z == 0.4


def test_turns_when_only_side_blocked():
    command = decide_naive_avoidance(
        front_distance=2.0,
        left_distance=0.3,
        right_distance=2.0,
        distance_threshold=0.8,
        forward_speed=0.15,
        turn_speed=0.4,
    )
    assert command.linear_x == 0.0
    assert command.angular_z == 0.4


def test_threshold_boundary_is_exclusive():
    command = decide_naive_avoidance(
        front_distance=0.8,
        left_distance=2.0,
        right_distance=2.0,
        distance_threshold=0.8,
        forward_speed=0.15,
        turn_speed=0.4,
    )
    assert command.linear_x == 0.0
    assert command.angular_z == 0.4

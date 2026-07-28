cmake_minimum_required(VERSION 3.8)
project(gemstone_imu)

if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 11)
endif()
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(diagnostic_updater REQUIRED)

add_executable(icm20948_driver_node
  src/icm20948_driver_node.cpp
  src/icm20948.c
)

target_include_directories(icm20948_driver_node PRIVATE include)
target_link_libraries(icm20948_driver_node m)

ament_target_dependencies(icm20948_driver_node
  rclcpp
  sensor_msgs
  diagnostic_updater
)

install(TARGETS
  icm20948_driver_node
  DESTINATION lib/${PROJECT_NAME})

ament_package()

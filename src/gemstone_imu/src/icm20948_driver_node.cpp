// gemstone_imu: T3 Gemstone O1 karti uzerindeki dahili ICM-20948 IMU'yu
// SPI (varsayilan /dev/spidev0.3, bkz. docs.t3gemstone.org) uzerinden okuyup
// sensor_msgs/Imu olarak yayinlar. Surucu kutuphanesi (icm20948.c/.h) T3
// Foundation'in resmi ornek kodudur, bu dosya sadece onu bir ROS 2 node'una
// baglar.
//
// Orientation (roll/pitch/yaw) burada hesaplanmiyor: orientation_covariance[0]
// -1 olarak isaretlenir, yani "orientation saglanmiyor". Gercek yonelim
// gerekiyorsa bu topic'i imu_filter_madgwick (Madgwick/EKF) ile besleyin.

#include <chrono>
#include <cmath>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "diagnostic_updater/diagnostic_updater.hpp"
#include "diagnostic_updater/publisher.hpp"

extern "C" {
#include "icm20948.h"
}

using namespace std::chrono_literals;

static constexpr double G_TO_MS2 = 9.80665;
static constexpr double DEG_TO_RAD = M_PI / 180.0;

class Icm20948DriverNode : public rclcpp::Node
{
public:
  Icm20948DriverNode() : Node("icm20948_driver_node"), diagnostic_updater_(this)
  {
    this->declare_parameter<std::string>("spi_device", "/dev/spidev0.3");
    this->declare_parameter<std::string>("frame_id", "imu_link");
    this->declare_parameter<double>("publish_rate_hz", 100.0);

    std::string spi_device = this->get_parameter("spi_device").as_string();
    frame_id_ = this->get_parameter("frame_id").as_string();
    double rate = this->get_parameter("publish_rate_hz").as_double();

    static char tag[] = "icm20948";
    handle_ = icm20948_create(&data_, tag);
    if (handle_ == nullptr) {
      RCLCPP_FATAL(this->get_logger(), "icm20948_create basarisiz oldu");
      throw std::runtime_error("icm20948_create failed");
    }

    if (icm20948_spi_bus_init(handle_, spi_device.c_str()) != 0) {
      RCLCPP_FATAL(this->get_logger(), "SPI bus baslatilamadi: %s", spi_device.c_str());
      throw std::runtime_error("icm20948_spi_bus_init failed");
    }

    if (icm20948_configure(handle_, ACCE_FS_8G, GYRO_FS_2000DPS) != 0) {
      RCLCPP_FATAL(this->get_logger(), "ICM-20948 yapilandirilamadi");
      throw std::runtime_error("icm20948_configure failed");
    }

    // Sensorun oturmasi icin kisa bir bekleme
    for (int i = 0; i < 100; i++) {
      icm20948_get_temp(handle_);
      rclcpp::sleep_for(1ms);
    }

    publisher_ = this->create_publisher<sensor_msgs::msg::Imu>("imu/data_raw", 50);

    diagnostic_updater_.setHardwareID(spi_device);
    diagnostic_updater_.add("ICM-20948 IMU", this, &Icm20948DriverNode::run_diagnostics);

    auto period = std::chrono::duration<double>(1.0 / rate);
    timer_ = this->create_wall_timer(
      std::chrono::duration_cast<std::chrono::milliseconds>(period),
      std::bind(&Icm20948DriverNode::timer_callback, this));

    RCLCPP_INFO(this->get_logger(), "ICM-20948 IMU surucusu basladi: %s, frame_id=%s, rate=%.1f Hz",
                spi_device.c_str(), frame_id_.c_str(), rate);
  }

  ~Icm20948DriverNode() override
  {
    if (handle_) {
      icm20948_delete(handle_);
    }
  }

private:
  void timer_callback()
  {
    if (icm20948_get_acce(handle_) != 0 || icm20948_get_gyro(handle_) != 0) {
      RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000, "IMU okuma basarisiz");
      consecutive_failures_++;
      return;
    }
    consecutive_failures_ = 0;
    last_read_ok_ = this->now();

    auto msg = sensor_msgs::msg::Imu();
    msg.header.stamp = this->now();
    msg.header.frame_id = frame_id_;

    // Orientation hesaplamiyoruz (Madgwick/EKF bu isi ustlenecek)
    msg.orientation_covariance[0] = -1.0;

    // g -> m/s^2
    msg.linear_acceleration.x = data_.ax * G_TO_MS2;
    msg.linear_acceleration.y = data_.ay * G_TO_MS2;
    msg.linear_acceleration.z = data_.az * G_TO_MS2;

    // deg/s -> rad/s
    msg.angular_velocity.x = data_.gx * DEG_TO_RAD;
    msg.angular_velocity.y = data_.gy * DEG_TO_RAD;
    msg.angular_velocity.z = data_.gz * DEG_TO_RAD;

    for (auto &c : msg.linear_acceleration_covariance) c = 0.0;
    msg.linear_acceleration_covariance[0] = 0.04;
    msg.linear_acceleration_covariance[4] = 0.04;
    msg.linear_acceleration_covariance[8] = 0.04;

    for (auto &c : msg.angular_velocity_covariance) c = 0.0;
    msg.angular_velocity_covariance[0] = 0.02;
    msg.angular_velocity_covariance[4] = 0.02;
    msg.angular_velocity_covariance[8] = 0.02;

    publisher_->publish(msg);
    diagnostic_updater_.force_update();
  }

  void run_diagnostics(diagnostic_updater::DiagnosticStatusWrapper & stat)
  {
    if (consecutive_failures_ == 0) {
      stat.summary(diagnostic_msgs::msg::DiagnosticStatus::OK, "IMU okunuyor");
    } else if (consecutive_failures_ < 10) {
      stat.summary(diagnostic_msgs::msg::DiagnosticStatus::WARN, "Ardisik IMU okuma hatasi");
    } else {
      stat.summary(diagnostic_msgs::msg::DiagnosticStatus::ERROR, "IMU cok sayida ardisik hata verdi");
    }
    stat.add("ardisik_hata_sayisi", consecutive_failures_);
  }

  icm20948_handle_t handle_ = nullptr;
  icm20948_data_t data_{};
  std::string frame_id_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  diagnostic_updater::Updater diagnostic_updater_;
  int consecutive_failures_ = 0;
  rclcpp::Time last_read_ok_;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  try {
    auto node = std::make_shared<Icm20948DriverNode>();
    rclcpp::spin(node);
  } catch (const std::exception& e) {
    RCLCPP_FATAL(rclcpp::get_logger("gemstone_imu"), "Fatal hata: %s", e.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}

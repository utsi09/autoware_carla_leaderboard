#include "autoware_carla_cpp_bridge/lidar_bridge.hpp"
#include <cmath>
#include <memory>

namespace autoware_carla_cpp_bridge
{

LidarBridge::LidarBridge(
  const std::string & node_name,
  const std::string & input_topic,
  const std::string & output_topic,
  const std::string & frame_id,
  size_t num_channels,
  const rclcpp::NodeOptions & options)
: Node(node_name, options),
  frame_id_(frame_id),
  num_channels_(num_channels)
{
  RCLCPP_INFO(this->get_logger(), "LidarBridge Node '%s' started.", node_name.c_str());

  // Fault injection: gaussian noise along each ray (meters), 0.0 = off.
  // Set at runtime: ros2 param set /<node> noise_sigma 0.1
  // Optional sector gate: noise only within +-width/2 around the center
  // azimuth (deg, sensor frame, x forward / y left). width 360 = everywhere.
  this->declare_parameter<double>("noise_sigma", 0.0);
  this->declare_parameter<double>("noise_yaw_center", 0.0);
  this->declare_parameter<double>("noise_yaw_width", 360.0);
  // [v4.6 lso] 오염 섹터 — 커버 투과율 모델 (Trierweiler 2019 실측 + Goodin
  // 2019 검출문턱: 섹터 내 강도 x T^2, rho*T^2/R^2 < P_min 이면 미검출 소실
  // -> 멀고 어두운 표적부터 죽는 거리·반사율 의존 소실이 자동으로 나온다)
  this->declare_parameter<double>("cover_transmission", 1.0);
  this->declare_parameter<double>("dropout_yaw_center", 0.0);
  this->declare_parameter<double>("dropout_yaw_width", 0.0);
  // [v4.6 lcl] 강수 — Beer-Lambert 감쇠(Goodin 2019: alpha=0.01*Rr^0.6 [1/m],
  // Rr=강우량 mm/h) + 거리지터 sigma=0.02*R*(1-e^-Rr)^2 + 근거리 클러터
  // (LISA/Hahner: 후방산란 클러터는 센서 근처 편중 -> 2차 근접편중 샘플링)
  this->declare_parameter<double>("rain_rate_mmh", 0.0);
  this->declare_parameter<int>("clutter_points", 0);
  this->declare_parameter<double>("clutter_range_m", 10.0);
  this->declare_parameter<double>("range_max_m", 100.0);

  // Publisher
  rclcpp::QoS qos(rclcpp::KeepLast(5));
  qos.best_effort();
  lidar_pub_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(output_topic, qos);

  rclcpp::QoS diagnostic_qos(rclcpp::KeepLast(5));
  diagnostic_qos.reliable();
  diagnostic_qos.transient_local();
  ready_state_pub_ = this->create_publisher<diagnostic_msgs::msg::DiagnosticStatus>(
    "/ready_state",
    diagnostic_qos
  );

  sync_timer_ = this->create_wall_timer(
    std::chrono::milliseconds(200),
    std::bind(&LidarBridge::syncTimerCallback, this)
  );

  // Subscriber
  lidar_sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
    input_topic,
    10,
    std::bind(&LidarBridge::lidarCallback, this, std::placeholders::_1)
  );

  _aw_time_sub_ = this->create_subscription<rosgraph_msgs::msg::Clock>(
    "/autoware_time",
    10,
    std::bind(&LidarBridge::clockCallback, this, std::placeholders::_1)
  );

  sync_state_sub_ = this->create_subscription<std_msgs::msg::Bool>(
    "/awcarla/sync_state",
    10,
    std::bind(&LidarBridge::syncStateCallback, this, std::placeholders::_1)
  );

}

void LidarBridge::clockCallback(const rosgraph_msgs::msg::Clock::SharedPtr msg)
{
  aw_time_ = msg->clock;
}

void LidarBridge::lidarCallback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
{
  sensor_msgs::msg::PointCloud2 modified_msg;
  modified_msg.header = msg->header;
  modified_msg.header.frame_id = frame_id_;
  modified_msg.header.stamp = aw_time_;

  size_t total_points = msg->width * msg->height;
  size_t points_per_channel = total_points / num_channels_;
  size_t valid_point_count = points_per_channel * num_channels_;

  const int clutter_n = static_cast<int>(this->get_parameter("clutter_points").as_int());

  modified_msg.point_step = 16;
  modified_msg.row_step = modified_msg.point_step * valid_point_count;
  modified_msg.width = valid_point_count;
  modified_msg.height = 1;
  modified_msg.is_dense = true;
  modified_msg.data.resize((valid_point_count + std::max(clutter_n, 0)) * modified_msg.point_step);

  // Resize fields
  modified_msg.fields.resize(6);

  modified_msg.fields[0].name = "x";
  modified_msg.fields[0].offset = 0;
  modified_msg.fields[0].datatype = sensor_msgs::msg::PointField::FLOAT32;
  modified_msg.fields[0].count = 1;

  modified_msg.fields[1].name = "y";
  modified_msg.fields[1].offset = 4;
  modified_msg.fields[1].datatype = sensor_msgs::msg::PointField::FLOAT32;
  modified_msg.fields[1].count = 1;

  modified_msg.fields[2].name = "z";
  modified_msg.fields[2].offset = 8;
  modified_msg.fields[2].datatype = sensor_msgs::msg::PointField::FLOAT32;
  modified_msg.fields[2].count = 1;

  modified_msg.fields[3].name = "intensity";
  modified_msg.fields[3].offset = 12;
  modified_msg.fields[3].datatype = sensor_msgs::msg::PointField::UINT8;
  modified_msg.fields[3].count = 1;

  modified_msg.fields[4].name = "return_type";
  modified_msg.fields[4].offset = 13;
  modified_msg.fields[4].datatype = sensor_msgs::msg::PointField::UINT8;
  modified_msg.fields[4].count = 1;

  modified_msg.fields[5].name = "channel";
  modified_msg.fields[5].offset = 14;
  modified_msg.fields[5].datatype = sensor_msgs::msg::PointField::UINT16;
  modified_msg.fields[5].count = 1;

  struct PointXYZIRC {
      float x;
      float y;
      float z;
      uint8_t intensity;
      uint8_t return_type;
      uint16_t channel;
  };

  PointXYZIRC* points = reinterpret_cast<PointXYZIRC*>(modified_msg.data.data());

  const float sigma = static_cast<float>(this->get_parameter("noise_sigma").as_double());
  const float yaw_c = static_cast<float>(this->get_parameter("noise_yaw_center").as_double());
  const float yaw_w = static_cast<float>(this->get_parameter("noise_yaw_width").as_double());
  const float cover_T = static_cast<float>(this->get_parameter("cover_transmission").as_double());
  const float drop_c = static_cast<float>(this->get_parameter("dropout_yaw_center").as_double());
  const float drop_w = static_cast<float>(this->get_parameter("dropout_yaw_width").as_double());
  const float rain_rr = static_cast<float>(this->get_parameter("rain_rate_mmh").as_double());
  const float clutter_range = static_cast<float>(this->get_parameter("clutter_range_m").as_double());
  const float range_max = static_cast<float>(this->get_parameter("range_max_m").as_double());
  // 검출 문턱 (Goodin 2019): P_min = 0.9/(pi * R_max^2)
  const float pmin = 0.9f / (3.1415926f * range_max * range_max);
  const float rain_alpha = rain_rr > 0.0f ? 0.01f * std::pow(rain_rr, 0.6f) : 0.0f;
  const float rain_jit = rain_rr > 0.0f
      ? 0.02f * std::pow(1.0f - std::exp(-rain_rr), 2.0f) : 0.0f;
  std::normal_distribution<float> noise_dist(0.0f, sigma > 0.0f ? sigma : 1.0f);
  std::normal_distribution<float> stdnorm(0.0f, 1.0f);
  std::uniform_real_distribution<float> uni(0.0f, 1.0f);

  size_t out = 0;
  for (size_t i = 0; i < valid_point_count; ++i) {
      const uint8_t* src = &msg->data[i * msg->point_step];

      float x = *reinterpret_cast<const float*>(src + 0);
      float y = *reinterpret_cast<const float*>(src + 4);
      float z = *reinterpret_cast<const float*>(src + 8);
      float intensity_f = *reinterpret_cast<const float*>(src + 12);

      const float r2 = x * x + y * y + z * z;
      const float r = std::sqrt(r2);
      float rho = std::clamp(intensity_f, 0.0f, 1.0f);  // CARLA 강도 = 반사율 프록시

      // [lso] 오염 섹터: 강도 x T^2 (커버 왕복 투과), 문턱 미달 -> 미검출
      if (cover_T < 1.0f && drop_w > 0.0f) {
        float az = std::atan2(y, x) * 57.29578f;
        float d = std::fabs(az - drop_c);
        if (d > 180.0f) d = 360.0f - d;
        if (d <= drop_w * 0.5f) {
          rho *= cover_T * cover_T;
          if (r2 > 0.01f && rho / r2 < pmin) continue;
        }
      }
      // [lcl] 강수 감쇠: Beer-Lambert 왕복, 문턱 미달 -> 소실 + 거리 지터
      if (rain_alpha > 0.0f && r > 0.01f) {
        rho *= std::exp(-2.0f * rain_alpha * r);
        if (rho / r2 < pmin) continue;
        const float sj = rain_jit * r;  // Goodin: sigma = 0.02*R*(1-e^-Rr)^2
        if (sj > 0.0f) {
          const float scale = 1.0f + sj * stdnorm(rng_) / r;
          x *= scale; y *= scale; z *= scale;
        }
      }
      intensity_f = rho;

      if (sigma > 0.0f) {
        bool in_sector = yaw_w >= 360.0f;
        if (!in_sector) {
          float az = std::atan2(y, x) * 57.29578f;
          float d = std::fabs(az - yaw_c);
          if (d > 180.0f) d = 360.0f - d;
          in_sector = d <= yaw_w * 0.5f;
        }
        if (in_sector) {
          // radial distance noise, equivalent to CARLA's lidar noise_stddev
          const float r = std::sqrt(x * x + y * y + z * z);
          if (r > 0.01f) {
            const float scale = 1.0f + noise_dist(rng_) / r;
            x *= scale;
            y *= scale;
            z *= scale;
          }
        }
      }

      uint8_t intensity = static_cast<uint8_t>(std::clamp(intensity_f * 255.0f, 0.0f, 255.0f));

      points[out].x = x;
      points[out].y = y;
      points[out].z = z;
      points[out].intensity = intensity;
      points[out].return_type = 0;
      points[out].channel = static_cast<uint16_t>(i % num_channels_);
      ++out;
  }

  // [lcl] 근거리 클러터 주입: 강수/물보라의 저강도 부유 점.
  // 거리는 근접 편중(2차) 샘플링 — LISA/Hahner 후방산란 프로파일(센서 근처
  // 집중)의 단순화. u^2 로 2 m 쪽에 밀도 집중.
  if (clutter_n > 0) {
    for (int k = 0; k < clutter_n; ++k) {
      const float az = uni(rng_) * 6.2831853f;
      const float u = uni(rng_);
      const float r = 2.0f + u * u * std::max(clutter_range - 2.0f, 0.1f);
      const float zz = -0.4f + uni(rng_) * 1.6f;
      points[out].x = r * std::cos(az);
      points[out].y = r * std::sin(az);
      points[out].z = zz;
      points[out].intensity = 4;
      points[out].return_type = 0;
      points[out].channel = static_cast<uint16_t>(k % num_channels_);
      ++out;
    }
  }

  modified_msg.width = out;
  modified_msg.row_step = modified_msg.point_step * out;
  modified_msg.data.resize(out * modified_msg.point_step);

    lidar_pub_->publish(modified_msg);

    if (sync_state_){
      last_lidar_msg_ = modified_msg;
      last_lidar_msg_received = true;
    }

    diagnostic_msgs::msg::DiagnosticStatus status;
    status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    status.name = this->get_name();
    ready_state_pub_->publish(status);
}

void LidarBridge::setSyncState()
{

  RCLCPP_INFO(this->get_logger(), "Setting lidar sync state to true.");
  sync_state_ = true;
  
}

void LidarBridge::unsetSyncState()
{
  RCLCPP_INFO(this->get_logger(), "Setting lidar sync state to false.");
  sync_state_ = false;
  last_lidar_msg_received = false;
}

void LidarBridge::syncStateCallback(const std_msgs::msg::Bool::SharedPtr msg)
{
    if (msg->data) {
        this->setSyncState();
    } else {
        this->unsetSyncState();
    }
}

void LidarBridge::syncTimerCallback()
{
  if (!sync_state_) {
    return;
  }

  if (last_lidar_msg_received) {
    last_lidar_msg_.header.stamp = aw_time_;
    lidar_pub_->publish(last_lidar_msg_);
  }
}


}  // namespace autoware_carla_cpp_bridge

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  if (argc < 5) {
    RCLCPP_ERROR(rclcpp::get_logger("lidar_bridge"), "Usage: lidar_bridge_node <input_topic> <output_topic> <frame_id> <num_channels>");
    return 1;
  }

  std::string input_topic = argv[1];
  std::string output_topic = argv[2];
  std::string frame_id = argv[3];
  size_t num_channels = std::stoul(argv[4]);

  auto node = std::make_shared<autoware_carla_cpp_bridge::LidarBridge>(
    "lidar_bridge_node", input_topic, output_topic, frame_id, num_channels);

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
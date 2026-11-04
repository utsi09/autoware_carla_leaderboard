#!/usr/bin/env bash
# Eagleye 구성 점검: nf 1회를 --eagleye 로 띄우고, 주행 시작 후 WAIT초 뒤 Eagleye 내부 토픽·EKF 오차를 찍는다.
#   사용: experiments/eagleye_probe.sh [WAIT=60]
cd /home/taewook/autoware_carla_leaderboard
WAIT=${1:-60}
R=experiments/results
LOG=$R/eagleye_probe.log
: > $LOG
rm -f $R/DISK_FULL
python3 -u experiments/experiment_runner.py --mrm-off --record --eagleye --method ours --npc def --t 10 \
  --no-log-archive --fault nf --sev-value nf --rep 0 > $R/eagleye_probe_runner.log 2>&1 &
RPID=$!
until grep -q "start leaderboard" $R/eagleye_probe_runner.log 2>/dev/null; do sleep 3; kill -0 $RPID 2>/dev/null || { echo "runner died" | tee -a $LOG; exit 1; }; done
sleep 5
until grep -aq "timer armed" $R/leaderboard.log 2>/dev/null; do sleep 3; kill -0 $RPID 2>/dev/null || { echo "runner died before driving" | tee -a $LOG; exit 1; }; done
echo "$(date +%T) driving; probing in ${WAIT}s" | tee -a $LOG
sleep $WAIT
export ROS_DOMAIN_ID=0 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp CYCLONEDDS_URI=/home/taewook/cyclone_localhost.xml
source /opt/ros/humble/setup.bash; source /home/taewook/autoware_awcl/autoware/install/setup.bash
# Eagleye 네임스페이스는 twist_source 에 따라 바뀐다 (pose_estimator / twist_estimator / pose_twist_estimator) → 노드 목록에서 찾는다
P=$(ros2 node list 2>/dev/null | grep -m1 "/eagleye/" | sed 's#/eagleye/.*#/eagleye#'); P=${P:-/localization/pose_estimator/eagleye}
echo "eagleye namespace: $P"
{
echo "== topic rates"
for t in /sensing/gnss/nav_sat_fix /sensing/gnss/ecef_velocity $P/gnss/rtklib_nav $P/velocity $P/velocity_scale_factor $P/heading_1st $P/heading_interpolate_3rd $P/enu_absolute_pos $P/enu_absolute_pos_interpolate $P/fix $P/geo_pose_with_covariance /localization/pose_estimator/pose_with_covariance /localization/kinematic_state; do
  printf "%-40s " "${t#$P/}"; timeout 5 ros2 topic hz "$t" 2>&1 | grep -m1 -E "average rate|not appear|invalid" || echo "no msgs"
done
echo "== rtklib_nav sample"; timeout 5 ros2 topic echo --once $P/gnss/rtklib_nav 2>/dev/null | grep -E "tow|ecef_vel" -A3 | head -8
echo "== velocity_scale_factor"; timeout 5 ros2 topic echo --once $P/velocity_scale_factor 2>/dev/null | grep -E "scale_factor:|enabled_status|estimate_status" | head -3
echo "== heading_interpolate_3rd"; timeout 5 ros2 topic echo --once $P/heading_interpolate_3rd 2>/dev/null | grep -E "heading_angle|enabled_status|estimate_status" | head -3
echo "== EKF vs GT"; timeout 5 ros2 topic echo --once /localization/kinematic_state --field pose.pose.position 2>/dev/null | head -2
f=$(ls -t $R/gt/eg-*.csv | head -1); grep ",ego," "$f" | tail -1 | cut -d, -f1-9
echo "== eagleye warnings (autoware.log)"; grep -a -i "eagleye\|gnss_converter" $R/autoware.log | grep -a -i "warn\|error" | sed 's/\[[0-9.]*\]//' | sort | uniq -c | sort -rn | head -8 | cut -c1-160
echo "== converter stdout"; grep -a "velocity_source\|llh_source\|subscribe_rtklib" $R/autoware.log | head -4
} 2>&1 | tee -a $LOG
echo "$(date +%T) probe done; letting the case finish" | tee -a $LOG
wait $RPID
grep -a "\[runner\] result\|\[live\]" $R/eagleye_probe_runner.log | tee -a $LOG

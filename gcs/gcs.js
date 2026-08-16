'use strict';

// --- ROS bağlantısı ---
let ros = null;
let connected = false;

const $ = (id) => document.getElementById(id);
const log = (msg) => { $('log').textContent = msg; };

// --- Topic/subscriber referansları ---
let mapSub = null;
let odomSub = null;
let statusSub = null;
let coverageSub = null;
let frontiersSub = null;
let markerSub = null;

const mapImage = { data: null, width: 0, height: 0, resolution: 0, origin: { x: 0, y: 0 } };
let robotPose = { x: 0, y: 0, th: 0 };

function connect() {
  if (ros && connected) { ros.close(); }
  const host = $('host').value || 'localhost';
  const port = $('port').value || '9090';
  ros = new ROSLIB.Ros({ url: `ws://${host}:${port}` });

  ros.on('connection', () => {
    connected = true;
    $('conn-state').textContent = 'Bağlı';
    $('conn-state').className = 'on';
    log(`rosbridge ${host}:${port} bağlı.`);
    subscribeAll();
  });
  ros.on('error', (e) => { log(`Bağlantı hatası: ${e.message}`); });
  ros.on('close', () => {
    connected = false;
    $('conn-state').textContent = 'Kapalı';
    $('conn-state').className = 'off';
    log('Bağlantı kapandı.');
  });
}

// --- Abonelikler ---
function subscribeAll() {
  mapSub = new ROSLIB.Topic({ ros, name: '/map', messageType: 'nav_msgs/msg/OccupancyGrid' });
  mapSub.subscribe((msg) => {
    mapImage.width = msg.info.width;
    mapImage.height = msg.info.height;
    mapImage.resolution = msg.info.resolution;
    mapImage.origin = msg.info.origin.position;
    mapImage.data = msg.data;
    drawMap();
  });

  odomSub = new ROSLIB.Topic({ ros, name: '/odom', messageType: 'nav_msgs/msg/Odometry' });
  odomSub.subscribe((msg) => {
    robotPose.x = msg.pose.pose.position.x;
    robotPose.y = msg.pose.pose.position.y;
    const q = msg.pose.pose.orientation;
    robotPose.th = Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
    drawMap();
  });

  statusSub = new ROSLIB.Topic({ ros, name: '/exploration/status', messageType: 'std_msgs/msg/String' });
  statusSub.subscribe((msg) => { $('status-val').textContent = msg.data; });

  coverageSub = new ROSLIB.Topic({ ros, name: '/exploration/coverage', messageType: 'std_msgs/msg/Float32' });
  coverageSub.subscribe((msg) => { $('coverage-val').textContent = (msg.data * 100).toFixed(1) + '%'; });

  frontiersSub = new ROSLIB.Topic({ ros, name: '/exploration/frontiers', messageType: 'visualization_msgs/msg/MarkerArray' });
  frontiersSub.subscribe((msg) => { frontierMarkers = msg.markers; drawMap(); });

  markerSub = new ROSLIB.Topic({ ros, name: '/exploration/current_goal', messageType: 'visualization_msgs/msg/Marker' });
  markerSub.subscribe((msg) => { currentGoal = msg; drawMap(); });
}

let frontierMarkers = [];
let currentGoal = null;

// --- Harita çizimi ---
const canvas = $('map-canvas');
const ctx = canvas.getContext('2d');

function worldToPx(x, y) {
  // OccupancyGrid row-major: satır 0 en üstte (y=origin.y+height*res), satır
  // arttıkça y azalır. Ekranda y aşağıya doğru büyür -> çevir.
  const px = (x - mapImage.origin.x) / mapImage.resolution;
  const py = (mapImage.origin.y + mapImage.height * mapImage.resolution - y) / mapImage.resolution;
  return { x: px, y: py };
}

function drawMap() {
  if (!mapImage.data || mapImage.width === 0) { return; }

  const w = mapImage.width;
  const h = mapImage.height;
  // Canvas sabit iç çözünürlükte kalır (800x600). Harita bu alana ölçeklenir.
  const scale = Math.min(canvas.width / w, canvas.height / h);

  const img = ctx.createImageData(canvas.width, canvas.height);
  const d = img.data;
  for (let y = 0; y < canvas.height; y++) {
    const srcY = Math.min(h - 1, Math.floor(y / scale));
    for (let x = 0; x < canvas.width; x++) {
      const srcX = Math.min(w - 1, Math.floor(x / scale));
      const v = mapImage.data[srcY * w + srcX];
      let c;
      if (v === -1) c = [128, 128, 128, 255];      // bilinmeyen
      else if (v > 60) c = [229, 57, 53, 255];      // duvar
      else if (v > 20) c = [230, 200, 120, 255];    // inflate
      else c = [240, 240, 240, 255];                // boş
      const i = (y * canvas.width + x) * 4;
      d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = c[3];
    }
  }
  ctx.putImageData(img, 0, 0);

  drawMarkers(scale);
  drawRobot(scale);
}

function drawMarkers(scale) {
  // frontier küme markerları (MarkerArray, nokta bulutu / SPHERE_LIST)
  for (const m of frontierMarkers) {
    ctx.fillStyle = 'rgba(76, 175, 80, 0.85)';
    for (const p of m.points || []) {
      const px = worldToPx(p.x, p.y);
      ctx.fillRect(px.x * scale - 1.5, px.y * scale - 1.5, 3, 3);
    }
    if (m.pose && !m.points) {
      const px = worldToPx(m.pose.position.x, m.pose.position.y);
      ctx.beginPath();
      ctx.arc(px.x * scale, px.y * scale, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  // hedef ok
  if (currentGoal && currentGoal.pose) {
    const px = worldToPx(currentGoal.pose.position.x, currentGoal.pose.position.y);
    ctx.strokeStyle = 'rgba(255, 152, 0, 0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(px.x * scale, px.y * scale);
    const t = currentGoal.pose.orientation;
    const th = Math.atan2(2 * (t.w * t.z + t.x * t.y), 1 - 2 * (t.y * t.y + t.z * t.z));
    ctx.lineTo((px.x + 12 * Math.cos(th)) * scale, (px.y + 12 * Math.sin(th)) * scale);
    ctx.stroke();
  }
}

function drawRobot(scale) {
  const p = worldToPx(robotPose.x, robotPose.y);
  const cx = p.x * scale;
  const cy = p.y * scale;
  // Robot gerçek dünya boyutuyla çizilir (yarıçap ~0.10 m, ok ~0.20 m) ki
  // harita büyüdükçe/zoom-out olunca robot da orantılı küçülsün.
  const radiusPx = (0.10 / mapImage.resolution) * scale;
  const lenPx = (0.22 / mapImage.resolution) * scale;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-robotPose.th);  // ekran y ekseni çevrili olduğu için eksi
  ctx.fillStyle = 'rgba(79, 195, 247, 0.9)';
  ctx.beginPath();
  ctx.arc(0, 0, radiusPx, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = Math.max(1, scale * 0.3);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(lenPx, 0);
  ctx.stroke();
  ctx.restore();
}

// --- Teleop ---
let velTopic = null;

function sendVel(linear, angular) {
  if (!connected || !ros) return;
  if (!velTopic) {
    velTopic = new ROSLIB.Topic({
      ros,
      name: '/cmd_vel_nav',
      messageType: 'geometry_msgs/msg/Twist',
    });
  }
  const twist = new ROSLIB.Message({ linear: { x: linear, y: 0, z: 0 }, angular: { x: 0, y: 0, z: angular } });
  velTopic.publish(twist);
}

function currentSpeed() {
  return {
    v: parseFloat($('vel-x').value),
    th: parseFloat($('vel-th').value),
  };
}

let keyInterval = null;
let kbActive = false;   // klavye teleop'u ancak 'Klavye Kontrolünü Aç' tıklandığında çalışır

function setKbActive(on) {
  kbActive = on;
  const b = $('kb-toggle');
  b.textContent = on ? 'Klavye Kontrolünü Kapat' : 'Klavye Kontrolünü Aç';
  b.className = on ? 'active' : '';
  const s = $('kb-state');
  s.textContent = on ? 'Klavye aktif — ok tuşlarıyla sür' : 'Klavye kapalı';
  s.className = on ? 'on' : 'off';
  if (!on) stopKey();
}

function startKey(dx, dy) {
  stopKey();
  const { v, th } = currentSpeed();
  // dx: dönüş, dy: ileri
  keyInterval = setInterval(() => sendVel(dy * v, dx * th), 100);
}
function stopKey() {
  if (keyInterval) { clearInterval(keyInterval); keyInterval = null; }
  sendVel(0, 0);
}

// --- Keşif servisleri ---
function callService(name, cb) {
  const srv = new ROSLIB.Service({ ros, name, serviceType: 'std_srvs/srv/Trigger' });
  const req = new ROSLIB.ServiceRequest({});
  srv.callService(req, (res) => {
    log(`${name} -> success=${res.success} msg="${res.message}"`);
    if (cb) cb(res);
  });
}

// --- Bağlama ---
$('connect').addEventListener('click', connect);

document.querySelectorAll('.grid .k').forEach((btn) => {
  btn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    startKey(parseFloat(btn.dataset.dx), parseFloat(btn.dataset.dy));
  });
  btn.addEventListener('pointerup', stopKey);
  btn.addEventListener('pointerleave', stopKey);
});

window.addEventListener('keydown', (e) => {
  if (!kbActive) return;
  if (e.target.tagName === 'INPUT') return;
  const map = {
    ArrowUp: [0, 1], w: [0, 1], W: [0, 1],
    ArrowDown: [0, -1], s: [0, -1], S: [0, -1],
    ArrowLeft: [1, 0], a: [1, 0], A: [1, 0],
    ArrowRight: [-1, 0], d: [-1, 0], D: [-1, 0],
  };
  const k = map[e.key];
  if (k) { e.preventDefault(); startKey(k[0], k[1]); }
  if (e.key === ' ') { e.preventDefault(); stopKey(); }
});
window.addEventListener('keyup', (e) => {
  if (!kbActive) return;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'W', 's', 'S', 'a', 'A', 'd', 'D'].includes(e.key)) {
    stopKey();
  }
});

$('kb-toggle').addEventListener('click', () => setKbActive(!kbActive));

$('stop').addEventListener('click', () => { stopKey(); sendVel(0, 0); });
$('start').addEventListener('click', () => callService('/exploration/start'));
$('stopx').addEventListener('click', () => callService('/exploration/stop'));
$('save').addEventListener('click', () => callService('/exploration/save_map'));
$('cam-apply').addEventListener('click', () => {
  const topic = $('cam-topic').value.trim();
  $('camera').src = `http://${$('host').value || 'localhost'}:8080/stream?topic=${topic}`;
});

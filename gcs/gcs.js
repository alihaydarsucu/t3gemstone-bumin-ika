'use strict';

let ros = null;
let connected = false;
let killed = false;

const $ = (id) => document.getElementById(id);

let mapSub = null, odomSub = null, statusSub = null, coverageSub = null;
let frontiersSub = null, markerSub = null, velSub = null, rosoutSub = null;

const mapImage = { data: null, width: 0, height: 0, resolution: 0, origin: { x: 0, y: 0 } };
let robotPose = { x: 0, y: 0, th: 0 };
let currentVel = { linear: 0, angular: 0 };

let mode = 'duruyor';

// --- Toast ---
function showToast(msg, type) {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast' + (type ? ' ' + type : '');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.className = 'toast hidden'; }, 3000);
}

// --- Konsol ---
const MAX_CONSOLE = 200;
function consoleLog(msg, cls) {
  const el = $('console-log');
  if (!el) return;
  const d = document.createElement('div');
  d.className = 'log-line ' + (cls || 'log-info');
  const now = new Date();
  const ts = now.toLocaleTimeString('tr-TR', { hour12: false });
  d.textContent = '[' + ts + '] ' + msg;
  el.appendChild(d);
  while (el.children.length > MAX_CONSOLE) el.removeChild(el.firstChild);
  el.scrollTop = el.scrollHeight;
}

// --- Mod gostergesi ---
function setMode(m) {
  mode = m;
  const badge = $('mode-badge');
  if (!badge) return;
  badge.className = 'mode-badge mode-' + m;
  const labels = { duruyor: 'DURUYOR', otonom: 'OTONOM', manuel: 'MANUEL' };
  badge.textContent = labels[m] || m.toUpperCase();
}

// --- Connect ---
function connect() {
  if (ros && connected) { ros.close(); }
  const host = $('host').value || 'localhost';
  const port = $('port').value || '9090';
  ros = new ROSLIB.Ros({ url: 'ws://' + host + ':' + port });

  ros.on('connection', () => {
    connected = true;
    killed = false;
    $('conn-state').textContent = 'BAGLI';
    $('conn-state').className = 'on';
    $('resume').classList.add('hidden');
    $('estop').classList.remove('hidden');
    document.body.classList.remove('estop-active');
    consoleLog('rosbridge ' + host + ':' + port + ' baglandi.', 'log-info');
    subscribeAll();
    startCameraStream();
    setKbActive(true);
    setMode('duruyor');
    document.activeElement.blur();
  });
  ros.on('error', (e) => { consoleLog('Baglanti hatasi: ' + e.message, 'log-error'); });
  ros.on('close', () => {
    connected = false;
    killed = false;
    $('conn-state').textContent = 'KAPALI';
    $('conn-state').className = 'off';
    consoleLog('Baglanti kapandi.', 'log-warn');
    velSub = null;
    rosoutSub = null;
    setMode('duruyor');
  });
}

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
  statusSub.subscribe((msg) => {
    $('status-val').textContent = msg.data;
    if (!killed && msg.data && msg.data.trim().length > 0) {
      const lower = msg.data.toLowerCase();
      if (lower.includes('running') || lower.includes('active') || lower.includes('aktiv')) {
        setMode('otonom');
      }
    }
  });

  coverageSub = new ROSLIB.Topic({ ros, name: '/exploration/coverage', messageType: 'std_msgs/msg/Float32' });
  coverageSub.subscribe((msg) => { $('coverage-val').textContent = (msg.data * 100).toFixed(1) + '%'; });

  frontiersSub = new ROSLIB.Topic({ ros, name: '/exploration/frontiers', messageType: 'visualization_msgs/msg/MarkerArray' });
  frontiersSub.subscribe((msg) => { frontierMarkers = msg.markers; drawMap(); });

  markerSub = new ROSLIB.Topic({ ros, name: '/exploration/current_goal', messageType: 'visualization_msgs/msg/Marker' });
  markerSub.subscribe((msg) => { currentGoal = msg; drawMap(); });

  velSub = new ROSLIB.Topic({ ros, name: '/cmd_vel_nav', messageType: 'geometry_msgs/msg/Twist' });
  velSub.subscribe((msg) => {
    currentVel.linear = msg.linear.x;
    currentVel.angular = msg.angular.z;
    updateSpeedDisplay();
  });

  rosoutSub = new ROSLIB.Topic({ ros, name: '/rosout', messageType: 'rcl_interfaces/msg/Log' });
  rosoutSub.subscribe((msg) => {
    const cls = msg.level >= 40 ? 'log-error' : msg.level >= 30 ? 'log-warn' : msg.level >= 20 ? 'log-info' : 'log-debug';
    consoleLog('[' + msg.name + '] ' + msg.msg, cls);
  });
}

function updateSpeedDisplay() {
  const el = $('speed-display');
  if (!el) return;
  el.innerHTML = '<span class="val">' + currentVel.linear.toFixed(2) + ' m/s</span> &middot; <span class="val">' + currentVel.angular.toFixed(2) + ' rad/s</span>';
}

let frontierMarkers = [];
let currentGoal = null;

// --- Harita cizimi (aspect-ratio korumali) ---
const canvas = $('map-canvas');
const ctx = canvas.getContext('2d');
const offCanvas = document.createElement('canvas');
const offCtx = offCanvas.getContext('2d');

function worldToPx(x, y) {
  const px = (x - mapImage.origin.x) / mapImage.resolution;
  const py = (mapImage.origin.y + mapImage.height * mapImage.resolution - y) / mapImage.resolution;
  return { x: px, y: py };
}

function drawMap() {
  if (!mapImage.data || mapImage.width === 0) return;
  const w = mapImage.width;
  const h = mapImage.height;
  const scale = Math.min(canvas.width / w, canvas.height / h);
  const drawW = Math.round(w * scale);
  const drawH = Math.round(h * scale);

  offCanvas.width = drawW;
  offCanvas.height = drawH;
  const img = offCtx.createImageData(drawW, drawH);
  const d = img.data;
  for (let y = 0; y < drawH; y++) {
    const srcY = Math.min(h - 1, Math.max(0, h - 1 - Math.floor(y / scale)));
    for (let x = 0; x < drawW; x++) {
      const srcX = Math.min(w - 1, Math.floor(x / scale));
      const v = mapImage.data[srcY * w + srcX];
      let c;
      if (v === -1) c = [55, 60, 80, 255];
      else if (v > 60) c = [220, 50, 50, 255];
      else if (v > 20) c = [180, 140, 70, 255];
      else c = [225, 228, 235, 255];
      const i = (y * drawW + x) * 4;
      d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = c[3];
    }
  }
  offCtx.putImageData(img, 0, 0);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const ox = Math.round((canvas.width - drawW) / 2);
  const oy = Math.round((canvas.height - drawH) / 2);
  ctx.drawImage(offCanvas, ox, oy);

  drawMarkers(scale, ox, oy);
  drawRobot(scale, ox, oy);
}

function drawMarkers(scale, ox, oy) {
  for (const m of frontierMarkers) {
    ctx.fillStyle = 'rgba(34, 201, 122, 0.85)';
    for (const p of m.points || []) {
      const px = worldToPx(p.x, p.y);
      ctx.fillRect(ox + px.x * scale - 1.5, oy + px.y * scale - 1.5, 3, 3);
    }
    if (m.pose && !m.points) {
      const px = worldToPx(m.pose.position.x, m.pose.position.y);
      ctx.beginPath();
      ctx.arc(ox + px.x * scale, oy + px.y * scale, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  if (currentGoal && currentGoal.pose) {
    const px = worldToPx(currentGoal.pose.position.x, currentGoal.pose.position.y);
    ctx.strokeStyle = 'rgba(240, 168, 48, 0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(ox + px.x * scale, oy + px.y * scale);
    const t = currentGoal.pose.orientation;
    const th = Math.atan2(2 * (t.w * t.z + t.x * t.y), 1 - 2 * (t.y * t.y + t.z * t.z));
    ctx.lineTo(ox + (px.x + 12 * Math.cos(th)) * scale, oy + (px.y - 12 * Math.sin(th)) * scale);
    ctx.stroke();
  }
}

function drawRobot(scale, ox, oy) {
  const p = worldToPx(robotPose.x, robotPose.y);
  const cx = ox + p.x * scale;
  const cy = oy + p.y * scale;
  const radiusPx = (0.10 / mapImage.resolution) * scale;
  const lenPx = (0.22 / mapImage.resolution) * scale;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-robotPose.th);
  ctx.fillStyle = 'rgba(78, 140, 255, 0.9)';
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
  if (killed && (linear !== 0 || angular !== 0)) return;
  if (!velTopic) {
    velTopic = new ROSLIB.Topic({ ros, name: '/cmd_vel_nav', messageType: 'geometry_msgs/msg/Twist' });
  }
  const twist = new ROSLIB.Message({ linear: { x: linear, y: 0, z: 0 }, angular: { x: 0, y: 0, z: angular } });
  velTopic.publish(twist);
}

function currentSpeed() {
  return { v: parseFloat($('vel-x').value), th: parseFloat($('vel-th').value) };
}

let keyInterval = null;
let kbActive = false;
let activeKeyEl = null;
const activeKeys = new Set();

function setKbActive(on) {
  kbActive = on;
  const s = $('kb-state');
  const b = $('kb-toggle');
  if (s) {
    s.textContent = on ? 'Aktif' : 'Kapali';
    s.className = on ? 'on' : 'off';
  }
  if (b) {
    b.textContent = on ? 'Klavyeyi Kapat' : 'Klavyeyi Ac';
  }
  if (!on) stopKey();
}

function startKey(dx, dy, keyEl) {
  if (keyInterval) { clearInterval(keyInterval); keyInterval = null; }
  const { v, th } = currentSpeed();
  keyInterval = setInterval(() => {
    if (killed) return;
    sendVel(dy * v, dx * th);
  }, 100);
  if (keyEl) { keyEl.classList.add('pressed'); activeKeyEl = keyEl; }
  if (!killed) setMode('manuel');
}

function stopKey() {
  if (keyInterval) { clearInterval(keyInterval); keyInterval = null; }
  sendVel(0, 0);
  if (activeKeyEl) { activeKeyEl.classList.remove('pressed'); activeKeyEl = null; }
  if (mode === 'manuel' && activeKeys.size === 0) setMode('duruyor');
}

// --- Kesif servisleri ---
function callService(name, cb) {
  const srv = new ROSLIB.Service({ ros, name, serviceType: 'std_srvs/srv/Trigger' });
  const req = new ROSLIB.ServiceRequest({});
  srv.callService(req, (res) => {
    consoleLog(name + ' -> ' + (res.success ? 'OK' : 'HATA') + ' "' + res.message + '"', res.success ? 'log-info' : 'log-warn');
    if (cb) cb(res);
  });
}

// --- Harita PNG kaydet ---
function saveMapPng() {
  const link = document.createElement('a');
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  link.download = 'harita-' + ts + '.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
  showToast('Harita PNG olarak kaydedildi!', 'ok');
  consoleLog('Harita PNG kaydedildi: ' + link.download, 'log-info');
}

// --- Acil durdurma ---
function emergencyStop() {
  stopKey();
  activeKeys.clear();
  sendVel(0, 0);
  if (connected) callService('/exploration/stop');
  killed = true;
  setMode('duruyor');
  $('estop').classList.add('hidden');
  $('resume').classList.remove('hidden');
  document.body.classList.add('estop-active');
  setKbActive(false);
  // tekrar tekrar sifir hiz gonder (rosbridge gecikmesine karsi)
  for (let i = 1; i <= 5; i++) {
    setTimeout(() => sendVel(0, 0), i * 100);
  }
  showToast('ACIL DURDURMA aktif!', 'error');
  consoleLog('*** ACIL DURDURMA ***', 'log-error');
}

function resumeControl() {
  killed = false;
  $('estop').classList.remove('hidden');
  $('resume').classList.add('hidden');
  document.body.classList.remove('estop-active');
  setKbActive(true);
  showToast('Kontrol devam ediyor.', 'ok');
  consoleLog('Kontrol devam ediyor.', 'log-info');
}

// --- Olay baglama ---
$('connect').addEventListener('click', connect);

$('kb-toggle').addEventListener('click', () => {
  if (killed) { showToast('Once acil durdurmayi kaldirin!', 'warn'); return; }
  setKbActive(!kbActive);
});

document.querySelectorAll('.grid .k').forEach((btn) => {
  btn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    if (killed || !kbActive) return;
    activeKeys.add(btn.id);
    startKey(parseFloat(btn.dataset.dx), parseFloat(btn.dataset.dy), btn);
  });
  btn.addEventListener('pointerup', () => {
    activeKeys.delete(btn.id);
    if (activeKeys.size === 0) stopKey();
  });
  btn.addEventListener('pointerleave', () => {
    activeKeys.delete(btn.id);
    if (activeKeys.size === 0) stopKey();
  });
});

const keyButtonMap = {
  ArrowUp: 'btn-up', ArrowDown: 'btn-down', ArrowLeft: 'btn-left', ArrowRight: 'btn-right',
  w: 'btn-up', W: 'btn-up', s: 'btn-down', S: 'btn-down',
  a: 'btn-left', A: 'btn-left', d: 'btn-right', D: 'btn-right',
};

window.addEventListener('keydown', (e) => {
  if (!kbActive || killed) return;
  const keyMap = {
    ArrowUp: [0, 1], w: [0, 1], W: [0, 1],
    ArrowDown: [0, -1], s: [0, -1], S: [0, -1],
    ArrowLeft: [1, 0], a: [1, 0], A: [1, 0],
    ArrowRight: [-1, 0], d: [-1, 0], D: [-1, 0],
  };
  const k = keyMap[e.key];
  if (k) {
    e.preventDefault();
    if (activeKeys.has(e.key)) return;
    activeKeys.add(e.key);
    const el = $(keyButtonMap[e.key]);
    startKey(k[0], k[1], el);
  }
  if (e.key === ' ') { e.preventDefault(); activeKeys.clear(); stopKey(); }
});

window.addEventListener('keyup', (e) => {
  if (!kbActive) return;
  activeKeys.delete(e.key);
  if (activeKeys.size === 0) {
    stopKey();
  } else {
    const keyMap = {
      ArrowUp: [0, 1], w: [0, 1], W: [0, 1],
      ArrowDown: [0, -1], s: [0, -1], S: [0, -1],
      ArrowLeft: [1, 0], a: [1, 0], A: [1, 0],
      ArrowRight: [-1, 0], d: [-1, 0], D: [-1, 0],
    };
    const remaining = [...activeKeys];
    const last = remaining[remaining.length - 1];
    const k = keyMap[last];
    if (k) startKey(k[0], k[1], $(keyButtonMap[last]));
  }
});

$('estop').addEventListener('click', emergencyStop);
$('resume').addEventListener('click', resumeControl);
$('start').addEventListener('click', () => {
  if (killed) { showToast('Once acil durdurmayi kaldirin!', 'warn'); return; }
  callService('/exploration/start');
});
$('stopx').addEventListener('click', () => {
  callService('/exploration/stop');
  if (mode === 'otonom') setMode('duruyor');
});
$('save').addEventListener('click', () => {
  saveMapPng();
  if (connected) callService('/exploration/save_map');
});
$('cam-apply').addEventListener('click', startCameraStream);

function startCameraStream() {
  const host = $('host').value || 'localhost';
  const topic = $('cam-topic').value.trim();
  const cam = $('camera');
  const status = $('cam-status');
  const ts = Date.now();
  const url = 'http://' + host + ':8080/stream?topic=' + topic + '&nocache=' + ts;
  cam.src = url;
  status.textContent = 'Baglaniyor...';
  status.className = 'cam-status pending';
  const check = setTimeout(() => {
    if (cam.naturalWidth > 0) {
      status.textContent = 'Yayinda';
      status.className = 'cam-status on';
    } else {
      status.textContent = 'Baglanamadi';
      status.className = 'cam-status off';
    }
  }, 3000);
  cam.onload = () => { clearTimeout(check); status.textContent = 'Yayinda'; status.className = 'cam-status on'; };
  cam.onerror = () => { clearTimeout(check); status.textContent = 'Baglanamadi'; status.className = 'cam-status off'; };
}

// --- Sayfa yuklenince otomatik baglan ---
setTimeout(connect, 500);

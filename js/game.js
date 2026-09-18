// Falange Dorada — hyper-casual multiplier runner, Greek temple theme.
// Pure Canvas2D pseudo-3D engine (no external libraries): a perspective
// projector maps world (x,y,z) points to screen space, and everything —
// marble colonnades, temple gateways, hoplites, gates, coins, the Talos
// boss, lasers — is drawn as projected billboards / quads sorted
// back-to-front (painter's algorithm).
(() => {
'use strict';

// ---------- Constants ----------
const LANES = [-2.2, 0, 2.2];
const FORWARD_SPEED = 11;
const LANE_LERP = 0.18;
const BOSS_Z = -520;
const WORLD_START_Z = 30;
const MAX_DISPLAY = 130; // sprite cap for perf; real squad count is uncapped in math
const FAR_CLIP = 340; // max render distance

// ---------- Canvas / projection ----------
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let W = 0, H = 0, DPR = 1;
let FOCAL = 500, HORIZON_Y = 300, CENTER_X = 200;

function resize() {
  const rect = canvas.parentElement.getBoundingClientRect();
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = rect.width; H = rect.height;
  canvas.width = Math.round(W * DPR);
  canvas.height = Math.round(H * DPR);
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  FOCAL = H * 0.92;
  HORIZON_Y = H * 0.40;
  CENTER_X = W / 2;
}
window.addEventListener('resize', resize);

const camera = { x: 0, y: 4.3, z: WORLD_START_Z + 8 };

// project world point -> {sx, sy, scale, depth, ok}
function project(x, y, z) {
  const depth = camera.z - z;
  if (depth < 0.6) return { ok: false, depth };
  const scale = FOCAL / depth;
  return {
    ok: true,
    depth,
    scale,
    sx: CENTER_X + (x - camera.x) * scale,
    sy: HORIZON_Y - (y - camera.y) * scale,
  };
}

function fogFactor(depth) {
  const start = FAR_CLIP * 0.35;
  if (depth <= start) return 1;
  const f = 1 - (depth - start) / (FAR_CLIP - start);
  return Math.max(0, Math.min(1, f));
}

// ---------- Colors (marble temple / Greek theme) ----------
const COL = {
  sky1: '#cfe8ff', sky2: '#8fc6ee', sky3: '#4a90d9',
  fog: '#cfe8ff',
  sand1: '#efe9da', sand2: '#c9c0a8',
  cliffA: '#f3efe3', cliffB: '#d8d2c2', cliffC: '#b7ae98',
  arch: '#e4ddc8', archDark: '#a89f89',
  blueBody: '#e0a83f', blueBodyDark: '#9c6c1f', blueVisor: '#fff3c4', blueGlow: '#ffdf8a',
  redBody: '#7a2b2b', redBodyDark: '#431616', redVisor: '#ff7a63', redGlow: '#ff5a3c',
  gold: '#b8823c', goldDark: '#6b4a1f', stinger: '#ff8a2a',
  laser: '#ffe066',
  gate: 'rgba(232,185,58,0.32)', gateEdge: '#e8b93a',
  coin: '#ffd24a', coinDark: '#b97e15',
  heroCrest: '#f6f1e2', enemyCrest: '#1c1c1c',
  laurel: '#5a8a4a',
};

// ---------- World scenery (static): a marble colonnade flanking the path,
// with temple-facade gateways (columns + architrave + pediment) spanning it
// at intervals.
const scenery = [];

function buildWorld() {
  const colXs = [-8.0, 8.0];
  colXs.forEach((baseX) => {
    let z = 32;
    while (z > BOSS_Z - 40) {
      const height = 8.5 + Math.random() * 2.2;
      scenery.push({ type: 'column', x: baseX, z, height });
      z -= 4.2 + Math.random() * 1.3;
    }
  });

  const templeZs = [-32, -145, -262, -382, BOSS_Z - 8];
  templeZs.forEach((z, i) => {
    const s = i === templeZs.length - 1 ? 1.7 : 1;
    scenery.push({ type: 'temple', z, scale: s });
  });

  scenery.sort((a, b) => a.z - b.z); // ascending (most negative/farthest first)
}
buildWorld();

function drawColumn(p) {
  const depth = camera.z - p.z;
  if (depth < 0 || depth > FAR_CLIP) return;
  const fog = fogFactor(depth);
  ctx.globalAlpha = fog;

  const hw = 0.5;
  const topL = project(p.x - hw, p.height, p.z);
  const topR = project(p.x + hw, p.height, p.z);
  const botR = project(p.x + hw, 0, p.z);
  const botL = project(p.x - hw, 0, p.z);
  if (!topL.ok || !topR.ok) { ctx.globalAlpha = 1; return; }

  // fluted shaft
  const grad = ctx.createLinearGradient(botL.sx, 0, botR.sx, 0);
  grad.addColorStop(0, COL.cliffC);
  grad.addColorStop(0.5, COL.cliffA);
  grad.addColorStop(1, COL.cliffC);
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(botL.sx, botL.sy); ctx.lineTo(topL.sx, topL.sy);
  ctx.lineTo(topR.sx, topR.sy); ctx.lineTo(botR.sx, botR.sy);
  ctx.closePath(); ctx.fill();

  ctx.strokeStyle = 'rgba(120,110,90,0.35)';
  ctx.lineWidth = 1;
  for (let k = 1; k < 4; k++) {
    const fx = p.x - hw + (hw * 2) * (k / 4);
    const a = project(fx, p.height, p.z);
    const b = project(fx, 0, p.z);
    if (a.ok && b.ok) { ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke(); }
  }

  // capital (top cap, wider)
  const capHW = hw * 1.6, capH = 0.5;
  const cTL = project(p.x - capHW, p.height + capH, p.z);
  const cTR = project(p.x + capHW, p.height + capH, p.z);
  if (cTL.ok && cTR.ok) {
    ctx.fillStyle = COL.archDark;
    ctx.beginPath();
    ctx.moveTo(topL.sx, topL.sy);
    ctx.lineTo(cTL.sx, cTL.sy); ctx.lineTo(cTR.sx, cTR.sy); ctx.lineTo(topR.sx, topR.sy);
    ctx.closePath(); ctx.fill();
  }

  // base (stylobate)
  const bHW = hw * 1.4, bH = 0.3;
  const bTL = project(p.x - bHW, bH, p.z);
  const bTR = project(p.x + bHW, bH, p.z);
  const bBR = project(p.x + bHW, 0, p.z);
  const bBL = project(p.x - bHW, 0, p.z);
  if (bTL.ok && bTR.ok) {
    ctx.fillStyle = COL.archDark;
    ctx.beginPath();
    ctx.moveTo(bBL.sx, bBL.sy); ctx.lineTo(bTL.sx, bTL.sy); ctx.lineTo(bTR.sx, bTR.sy); ctx.lineTo(bBR.sx, bBR.sy);
    ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawTemple(p) {
  const depth = camera.z - p.z;
  if (depth < 0 || depth > FAR_CLIP) return;
  const s = p.scale;
  const fog = fogFactor(depth);
  ctx.globalAlpha = fog;
  ctx.fillStyle = COL.arch;
  ctx.strokeStyle = COL.archDark;
  ctx.lineWidth = 2;

  const legs = [[-6.4 * s, 6.4 * s, 0.6 * s], [6.4 * s, 6.4 * s, 0.6 * s]];
  legs.forEach(([lx, ly, lhw]) => {
    const tl = project(lx - lhw, ly * 2, p.z);
    const tr = project(lx + lhw, ly * 2, p.z);
    const br = project(lx + lhw, 0, p.z);
    const bl = project(lx - lhw, 0, p.z);
    if (tl.ok && tr.ok && br.ok && bl.ok) {
      ctx.beginPath();
      ctx.moveTo(bl.sx, bl.sy); ctx.lineTo(tl.sx, tl.sy); ctx.lineTo(tr.sx, tr.sy); ctx.lineTo(br.sx, br.sy);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
  });

  const beamY = 12.8 * s;
  const tl = project(-7.6 * s, beamY + 1.4 * s, p.z);
  const tr = project(7.6 * s, beamY + 1.4 * s, p.z);
  const br = project(7.6 * s, beamY - 1.4 * s, p.z);
  const bl = project(-7.6 * s, beamY - 1.4 * s, p.z);
  if (tl.ok && tr.ok && br.ok && bl.ok) {
    ctx.beginPath();
    ctx.moveTo(bl.sx, bl.sy); ctx.lineTo(tl.sx, tl.sy); ctx.lineTo(tr.sx, tr.sy); ctx.lineTo(br.sx, br.sy);
    ctx.closePath(); ctx.fill(); ctx.stroke();
  }

  // triangular pediment above the architrave
  const apex = project(0, beamY + 1.4 * s + 3.2 * s, p.z);
  const pedL = project(-7.6 * s, beamY + 1.4 * s, p.z);
  const pedR = project(7.6 * s, beamY + 1.4 * s, p.z);
  if (apex.ok && pedL.ok && pedR.ok) {
    ctx.fillStyle = COL.cliffA;
    ctx.beginPath();
    ctx.moveTo(pedL.sx, pedL.sy); ctx.lineTo(apex.sx, apex.sy); ctx.lineTo(pedR.sx, pedR.sy);
    ctx.closePath(); ctx.fill(); ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

function drawSceneryPiece(p) {
  if (p.type === 'column') drawColumn(p);
  else if (p.type === 'temple') drawTemple(p);
}

function drawBackground() {
  // sky
  const skyGrad = ctx.createLinearGradient(0, 0, 0, HORIZON_Y);
  skyGrad.addColorStop(0, COL.sky3);
  skyGrad.addColorStop(0.55, COL.sky2);
  skyGrad.addColorStop(1, COL.sky1);
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, W, HORIZON_Y);

  // sun glow
  const sunX = CENTER_X + Math.sin(camera.x * 0.02) * 20;
  const sunY = HORIZON_Y * 0.55;
  const glow = ctx.createRadialGradient(sunX, sunY, 4, sunX, sunY, H * 0.5);
  glow.addColorStop(0, 'rgba(255,244,210,0.95)');
  glow.addColorStop(0.35, 'rgba(255,214,140,0.35)');
  glow.addColorStop(1, 'rgba(255,214,140,0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, HORIZON_Y * 1.4);

  // god rays (soft streaks)
  ctx.save();
  ctx.globalAlpha = 0.10;
  ctx.fillStyle = '#fff6da';
  for (let i = -3; i <= 3; i++) {
    const bx = sunX + i * 46;
    ctx.beginPath();
    ctx.moveTo(bx - 10, 0);
    ctx.lineTo(bx + 10, 0);
    ctx.lineTo(bx + 70, HORIZON_Y);
    ctx.lineTo(bx - 70, HORIZON_Y);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();

  // ground
  const groundGrad = ctx.createLinearGradient(0, HORIZON_Y, 0, H);
  groundGrad.addColorStop(0, COL.fog);
  groundGrad.addColorStop(0.18, COL.sand2);
  groundGrad.addColorStop(1, COL.sand1);
  ctx.fillStyle = groundGrad;
  ctx.fillRect(0, HORIZON_Y, W, H - HORIZON_Y);
}

function drawLaneLines() {
  const vp = { sx: CENTER_X + (0 - camera.x) * 0, sy: HORIZON_Y };
  [-1.1, 1.1, -3.5, 3.5].forEach((lx, i) => {
    const near = project(lx, 0, camera.z - 1.5);
    if (!near.ok) return;
    ctx.strokeStyle = i < 2 ? 'rgba(255,255,255,0.35)' : 'rgba(120,110,90,0.22)';
    ctx.lineWidth = i < 2 ? 2.5 : 6;
    ctx.beginPath();
    ctx.moveTo(near.sx, near.sy);
    ctx.lineTo(CENTER_X, HORIZON_Y);
    ctx.stroke();
  });
}

// ---------- Soldier / creature sprite drawing ----------
// Sprite sizes are defined in WORLD units and multiplied by `scale` (px per
// world unit, from project()) to get pixel dimensions — never raw pixels.
const SOLDIER_W = 0.52, SOLDIER_H = 0.95, SOLDIER_HEAD_R = 0.22, SOLDIER_BOB = 0.07;

function drawSoldier(sx, sy, scale, colorBody, colorBodyDark, colorVisor, popScale, bobT, crestColor) {
  const s = scale * (popScale === undefined ? 1 : popScale);
  if (s < 1) return;
  const bodyW = SOLDIER_W * s, bodyH = SOLDIER_H * s;
  const bob = Math.sin(bobT) * SOLDIER_BOB * s;
  const y = sy - bodyH * 0.42 + bob;
  ctx.save();
  ctx.translate(sx, y);
  // shadow
  ctx.globalAlpha = 0.28;
  ctx.fillStyle = '#000';
  ctx.beginPath();
  ctx.ellipse(0, bodyH * 0.48, bodyW * 0.5, bodyW * 0.18, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;
  // round hoplite shield, behind the body on one side
  ctx.fillStyle = colorBodyDark;
  ctx.beginPath();
  ctx.ellipse(-bodyW * 0.46, bodyH * 0.05, bodyW * 0.32, bodyW * 0.38, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = crestColor || '#c0392b';
  ctx.lineWidth = Math.max(1, bodyW * 0.05);
  ctx.stroke();
  // tunic flare (pteruges skirt)
  ctx.fillStyle = colorBodyDark;
  ctx.beginPath();
  ctx.moveTo(-bodyW * 0.42, bodyH * 0.4);
  ctx.lineTo(bodyW * 0.42, bodyH * 0.4);
  ctx.lineTo(bodyW * 0.5, bodyH * 0.6);
  ctx.lineTo(-bodyW * 0.5, bodyH * 0.6);
  ctx.closePath();
  ctx.fill();
  // body (bronze cuirass)
  const grad = ctx.createLinearGradient(-bodyW / 2, 0, bodyW / 2, 0);
  grad.addColorStop(0, colorBodyDark);
  grad.addColorStop(0.5, colorBody);
  grad.addColorStop(1, colorBodyDark);
  ctx.fillStyle = grad;
  roundRect(-bodyW / 2, -bodyH * 0.15, bodyW, bodyH * 0.55, bodyW * 0.28);
  ctx.fill();
  // belt
  ctx.fillStyle = colorBodyDark;
  ctx.fillRect(-bodyW / 2, bodyH * 0.26, bodyW, bodyH * 0.06);
  // head (Corinthian helmet)
  const headR = bodyW * 0.42;
  const headY = -bodyH * 0.28;
  ctx.beginPath();
  ctx.arc(0, headY, headR, 0, Math.PI * 2);
  ctx.fillStyle = colorBody;
  ctx.fill();
  // crest (horsehair plume)
  ctx.fillStyle = crestColor || '#c0392b';
  ctx.beginPath();
  ctx.ellipse(0, headY - headR * 0.95, headR * 1.15, headR * 0.4, 0, 0, Math.PI * 2);
  ctx.fill();
  // nose guard
  ctx.fillStyle = colorBodyDark;
  ctx.fillRect(-headR * 0.08, headY - headR * 0.1, headR * 0.16, headR * 0.9);
  // eye-slit glow
  ctx.fillStyle = colorVisor;
  ctx.shadowColor = colorVisor;
  ctx.shadowBlur = 6 * s;
  roundRect(-headR * 0.62, headY - headR * 0.32, headR * 1.24, headR * 0.4, headR * 0.2);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.restore();
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

const COIN_R = 0.17;
function drawCoinSprite(sx, sy, scale, spin) {
  const r = COIN_R * scale;
  const squash = Math.max(0.15, Math.abs(Math.cos(spin)));
  ctx.save();
  ctx.translate(sx, sy);
  ctx.globalAlpha = 0.25;
  ctx.fillStyle = '#000';
  ctx.beginPath(); ctx.ellipse(0, r * 0.9, r * 0.8, r * 0.25, 0, 0, Math.PI * 2); ctx.fill();
  ctx.globalAlpha = 1;
  ctx.scale(squash, 1);
  const grad = ctx.createLinearGradient(-r, 0, r, 0);
  grad.addColorStop(0, COL.coinDark);
  grad.addColorStop(0.5, COL.coin);
  grad.addColorStop(1, COL.coinDark);
  ctx.fillStyle = grad;
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.lineWidth = Math.max(1, r * 0.12);
  ctx.beginPath(); ctx.arc(0, 0, r * 0.62, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
}

const DEBRIS_SIZE = 0.13;
function drawDebrisSprite(sx, sy, scale, rot, color) {
  const s = DEBRIS_SIZE * scale;
  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(rot);
  ctx.fillStyle = color;
  ctx.fillRect(-s / 2, -s / 2, s, s);
  ctx.restore();
}

// ---------- Player squad ----------
const player = {
  x: 0, laneIndex: 1, targetX: 0, z: WORLD_START_Z,
  count: 3, displayScale: [],
};

function formationOffsets(n) {
  const perRow = 6;
  const offsets = [];
  for (let i = 0; i < n; i++) {
    const row = Math.floor(i / perRow);
    const col = i % perRow;
    const inThisRow = Math.min(perRow, n - row * perRow);
    const startOffset = -(inThisRow - 1) / 2;
    offsets.push({ x: (startOffset + col) * 0.62, z: row * 0.6 });
  }
  return offsets;
}

let runCycle = 0;

function drawPlayerSquad() {
  const n = Math.min(player.count, MAX_DISPLAY);
  const offsets = formationOffsets(n);
  while (player.displayScale.length < n) player.displayScale.push(0);
  player.displayScale.length = n;

  const items = [];
  for (let i = 0; i < n; i++) {
    const off = offsets[i];
    const wx = player.x + off.x;
    const wz = player.z + off.z;
    const bobT = runCycle * 9 + i * 1.3;
    items.push({ wx, wz, bobT, idx: i });
  }
  items.sort((a, b) => a.wz - b.wz); // draw farthest (smallest z) first, nearest last
  for (const it of items) {
    const proj = project(it.wx, 0, it.wz);
    if (!proj.ok || proj.depth > FAR_CLIP) continue;
    player.displayScale[it.idx] = Math.min(1, (player.displayScale[it.idx] || 0) + 0.09);
    const pop = player.displayScale[it.idx];
    const fog = fogFactor(proj.depth);
    ctx.globalAlpha = fog;
    drawSoldier(proj.sx, proj.sy, proj.scale, COL.blueBody, COL.blueBodyDark, COL.blueVisor, pop, it.bobT, COL.heroCrest);
    ctx.globalAlpha = 1;
  }
}

// ---------- Camera update ----------
function updateCamera() {
  const targetX = player.x * 0.55;
  const targetZ = player.z + 8;
  camera.x += (targetX - camera.x) * 0.14;
  camera.z += (targetZ - camera.z) * 0.22;
}

// ---------- Lasers ----------
const activeLasers = []; // {x, z1, z2, life}
let laserTimer = 0;
function spawnLaserBurst() {
  const n = Math.min(player.count, 10);
  for (let i = 0; i < n; i++) {
    const lane = (Math.random() - 0.5) * 1.7;
    activeLasers.push({ x: player.x + lane, z1: player.z + 0.3, z2: player.z - 9 - Math.random() * 5, life: 0.12 });
  }
  AudioFX.laser();
}
function updateLasers(dt) {
  laserTimer -= dt;
  if ((state.mode === 'run' || state.mode === 'boss') && laserTimer <= 0 && player.count > 0) {
    laserTimer = 0.1;
    spawnLaserBurst();
  }
  for (let i = activeLasers.length - 1; i >= 0; i--) {
    activeLasers[i].life -= dt;
    if (activeLasers[i].life <= 0) activeLasers.splice(i, 1);
  }
}
function drawLasers() {
  for (const l of activeLasers) {
    const a = project(l.x, 0.9, l.z1);
    const b = project(l.x, 0.9, l.z2);
    if (!a.ok || !b.ok) continue;
    ctx.save();
    ctx.globalAlpha = Math.max(0, l.life / 0.12);
    ctx.strokeStyle = COL.laser;
    ctx.shadowColor = COL.laser;
    ctx.shadowBlur = 10;
    ctx.lineWidth = Math.max(1.5, 3 * a.scale / 60);
    ctx.beginPath();
    ctx.moveTo(a.sx, a.sy);
    ctx.lineTo(b.sx, b.sy);
    ctx.stroke();
    ctx.restore();
  }
}

// ---------- Particles ----------
const particles = []; // {x,y,z,vx,vy,vz,life,kind,rot,spin,color}
function spawnCoinBurst(x, z, count) {
  for (let i = 0; i < Math.min(count, 70); i++) {
    particles.push({
      x: x + (Math.random() - 0.5) * 1.5, y: 1 + Math.random(), z: z + (Math.random() - 0.5) * 1.5,
      vx: (Math.random() - 0.5) * 6, vy: 5 + Math.random() * 5, vz: (Math.random() - 0.5) * 6,
      life: 1.5 + Math.random() * 0.7, kind: 'coin', rot: Math.random() * 6, spin: 6 + Math.random() * 6,
    });
  }
}
function spawnExplosion(x, z, color) {
  for (let i = 0; i < 20; i++) {
    particles.push({
      x, y: 1, z,
      vx: (Math.random() - 0.5) * 9, vy: 3 + Math.random() * 7, vz: (Math.random() - 0.5) * 9,
      life: 0.8 + Math.random() * 0.4, kind: 'debris', rot: Math.random() * 6, spin: (Math.random() - 0.5) * 14, color,
    });
  }
}
function updateParticles(dt) {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.vy -= 16 * dt;
    p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
    p.rot += p.spin * dt;
    if (p.y < 0.15) { p.y = 0.15; p.vy *= -0.4; p.vx *= 0.7; p.vz *= 0.7; }
    p.life -= dt;
    if (p.life <= 0) particles.splice(i, 1);
  }
}
function drawParticles() {
  const sorted = [...particles].sort((a, b) => a.z - b.z);
  for (const p of sorted) {
    const proj = project(p.x, p.y, p.z);
    if (!proj.ok || proj.depth > FAR_CLIP) continue;
    ctx.globalAlpha = fogFactor(proj.depth) * Math.min(1, p.life);
    if (p.kind === 'coin') drawCoinSprite(proj.sx, proj.sy, proj.scale * 0.7, p.rot);
    else drawDebrisSprite(proj.sx, proj.sy, proj.scale, p.rot, p.color || '#ff6633');
    ctx.globalAlpha = 1;
  }
}

// ---------- Obstacles: gates, enemy squads, coins ----------
const obstacles = [];

function spawnLevel() {
  const defs = [
    { type: 'gate', z: -40, op: 'x2' },
    { type: 'coins', z: -70, lanes: [0, 2] },
    { type: 'enemy', z: -110, lanes: [1], count: 3 },
    { type: 'gate', z: -155, op: 'x3' },
    { type: 'enemy', z: -200, lanes: [2], count: 5 },
    { type: 'coins', z: -225, lanes: [0, 1] },
    { type: 'gate', z: -250, op: '+5' },
    { type: 'enemy', z: -295, lanes: [0, 1], count: 8 },
    { type: 'gate', z: -330, op: 'x2' },
    { type: 'coins', z: -350, lanes: [0, 1, 2] },
    { type: 'enemy', z: -390, lanes: [0, 1, 2], count: 14 },
    { type: 'gate', z: -430, op: '/2' },
    { type: 'coins', z: -460, lanes: [0, 1, 2] },
  ];

  defs.forEach(def => {
    if (def.type === 'gate') {
      obstacles.push({ type: 'gate', z: def.z, op: def.op, used: false });
    } else if (def.type === 'enemy') {
      def.lanes.forEach(laneIdx => {
        obstacles.push({ type: 'enemy', z: def.z, laneIdx, count: def.count, used: false, displayScale: [] });
      });
    } else if (def.type === 'coins') {
      def.lanes.forEach(laneIdx => {
        for (let k = 0; k < 5; k++) {
          obstacles.push({ type: 'coin', z: def.z - k * 1.3, laneIdx, used: false, spin: Math.random() * 6 });
        }
      });
    }
  });
}

function drawGate(o) {
  const depth = camera.z - o.z;
  if (depth < 0 || depth > FAR_CLIP) return;
  const tl = project(-7.5, 6.5, o.z);
  const tr = project(7.5, 6.5, o.z);
  const br = project(7.5, 0, o.z);
  const bl = project(-7.5, 0, o.z);
  if (!tl.ok || !tr.ok) return;
  const fog = fogFactor(depth);
  ctx.save();
  ctx.globalAlpha = 0.34 * fog;
  ctx.fillStyle = COL.gateEdge;
  ctx.beginPath();
  ctx.moveTo(bl.sx, bl.sy); ctx.lineTo(tl.sx, tl.sy); ctx.lineTo(tr.sx, tr.sy); ctx.lineTo(br.sx, br.sy);
  ctx.closePath(); ctx.fill();
  ctx.globalAlpha = 0.8 * fog;
  ctx.strokeStyle = COL.gateEdge;
  ctx.lineWidth = 4;
  ctx.shadowColor = COL.gateEdge;
  ctx.shadowBlur = 16;
  ctx.stroke();
  ctx.shadowBlur = 0;
  // label
  const mid = project(0, 3.6, o.z);
  if (mid.ok) {
    ctx.globalAlpha = fog;
    ctx.fillStyle = '#ffffff';
    ctx.font = `900 ${Math.max(10, mid.scale * 0.85)}px system-ui, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = COL.gateEdge;
    ctx.shadowBlur = 14;
    const label = o.op === 'x2' ? 'x2' : o.op === 'x3' ? 'x3' : o.op === '+5' ? '+5' : '÷2';
    ctx.fillText(label, mid.sx, mid.sy);
    ctx.shadowBlur = 0;
    // laurel wreath flanking the label
    const r = mid.scale * 0.9;
    ctx.strokeStyle = COL.laurel;
    ctx.lineWidth = Math.max(1.5, mid.scale * 0.05);
    ctx.beginPath();
    ctx.arc(mid.sx, mid.sy, r, Math.PI * 0.65, Math.PI * 1.35);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(mid.sx, mid.sy, r, -Math.PI * 0.35, Math.PI * 0.35);
    ctx.stroke();
  }
  ctx.restore();
}

function drawEnemyCluster(o) {
  const n = Math.min(o.count, 30);
  const offsets = formationOffsets(n);
  while (o.displayScale.length < n) o.displayScale.push(1);
  const items = offsets.map((off, i) => ({ wx: LANES[o.laneIdx] + off.x, wz: o.z + off.z, idx: i }));
  items.sort((a, b) => a.wz - b.wz);
  for (const it of items) {
    const proj = project(it.wx, 0, it.wz);
    if (!proj.ok || proj.depth > FAR_CLIP || proj.depth < 0) continue;
    ctx.globalAlpha = fogFactor(proj.depth);
    drawSoldier(proj.sx, proj.sy, proj.scale, COL.redBody, COL.redBodyDark, COL.redVisor, 1, runCycle * 8 + it.idx, COL.enemyCrest);
    ctx.globalAlpha = 1;
  }
}

function drawCoinObstacle(o) {
  const proj = project(LANES[o.laneIdx], 1, o.z);
  if (!proj.ok || proj.depth > FAR_CLIP || proj.depth < 0) return;
  ctx.globalAlpha = fogFactor(proj.depth);
  o.spin += 0.12;
  drawCoinSprite(proj.sx, proj.sy, proj.scale, o.spin);
  ctx.globalAlpha = 1;
}

// ---------- Boss: Talos, the bronze colossus of Greek myth ----------
const BOSS_W = 4.6, BOSS_H = 3.6;
let boss = null;
function buildBoss() {
  return { x: 0, y: 0, z: BOSS_Z - 6, hp: 420, maxHp: 420, alive: true, shakeT: 0, spawnT: 0 };
}

function drawBoss() {
  if (!boss) return;
  const proj = project(boss.x, 0, boss.z);
  if (!proj.ok) return;
  const s = proj.scale;
  const fog = fogFactor(proj.depth);
  ctx.save();
  ctx.globalAlpha = fog;
  ctx.translate(proj.sx, proj.sy);

  const shakeX = Math.sin(boss.shakeT * 42) * 0.03 * s;
  ctx.translate(shakeX, 0);

  // shadow
  ctx.globalAlpha = 0.3 * fog;
  ctx.fillStyle = '#000';
  ctx.beginPath(); ctx.ellipse(0, 0.15 * s, 2.6 * s, 0.6 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.globalAlpha = fog;

  const legW = 0.85 * s, legH = 2.9 * s;
  const legStep = Math.sin(boss.shakeT * 2.2) * 0.12 * s;
  ctx.fillStyle = COL.goldDark;
  ctx.fillRect(-1.15 * s - legW / 2, -legH + legStep, legW, legH);
  ctx.fillRect(1.15 * s - legW / 2, -legH - legStep, legW, legH);

  const bw = BOSS_W * s, bh = BOSS_H * s;
  const torsoBottomY = -legH;
  const torsoTopY = torsoBottomY - bh;

  // sword arm, raised — drawn first so the torso overlaps the shoulder joint
  ctx.save();
  ctx.translate(bw * 0.56, torsoTopY + bh * 0.18);
  ctx.rotate(-0.65 + Math.sin(boss.shakeT * 6) * 0.06);
  ctx.fillStyle = COL.goldDark;
  ctx.fillRect(-0.32 * s, 0, 0.64 * s, 2.3 * s);
  ctx.save();
  ctx.translate(0, 2.3 * s);
  ctx.fillStyle = '#dfe6ea';
  ctx.beginPath();
  ctx.moveTo(-0.16 * s, 0); ctx.lineTo(0.16 * s, 0); ctx.lineTo(0.08 * s, -2.3 * s); ctx.lineTo(-0.08 * s, -2.3 * s);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = COL.goldDark;
  ctx.fillRect(-0.3 * s, -0.05 * s, 0.6 * s, 0.28 * s);
  ctx.restore();
  ctx.restore();

  // shield arm
  ctx.save();
  ctx.translate(-bw * 0.58, torsoTopY + bh * 0.4);
  ctx.rotate(0.15);
  ctx.fillStyle = COL.goldDark;
  ctx.fillRect(-0.3 * s, 0, 0.6 * s, 1.8 * s);
  ctx.beginPath();
  ctx.ellipse(0, 1.85 * s, 1.05 * s, 1.25 * s, 0, 0, Math.PI * 2);
  ctx.fillStyle = COL.gold;
  ctx.fill();
  ctx.strokeStyle = COL.goldDark;
  ctx.lineWidth = Math.max(1, 0.08 * s);
  ctx.stroke();
  ctx.restore();

  // torso
  const grad = ctx.createLinearGradient(-bw / 2, 0, bw / 2, 0);
  grad.addColorStop(0, COL.goldDark); grad.addColorStop(0.5, COL.gold); grad.addColorStop(1, COL.goldDark);
  ctx.fillStyle = grad;
  roundRect(-bw / 2, torsoTopY, bw, bh, bw * 0.14);
  ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.25)';
  ctx.lineWidth = Math.max(1, 0.05 * s);
  ctx.stroke();

  // cracks near death, glowing molten-bronze ichor beneath
  const hpFrac = boss.hp / boss.maxHp;
  if (hpFrac < 0.6) {
    ctx.save();
    ctx.globalAlpha = fog * (1 - hpFrac) * 0.9;
    ctx.strokeStyle = '#3a2200';
    ctx.lineWidth = Math.max(1, 0.045 * s);
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      const sx0 = (Math.random() - 0.5) * bw * 0.7;
      const sy0 = torsoTopY + Math.random() * bh;
      ctx.moveTo(sx0, sy0);
      ctx.lineTo(sx0 + (Math.random() - 0.5) * 0.9 * s, sy0 + (Math.random() - 0.5) * 0.9 * s);
      ctx.stroke();
    }
    ctx.restore();
    if (hpFrac < 0.3) {
      ctx.save();
      ctx.globalAlpha = fog * 0.5 * (Math.sin(boss.shakeT * 20) * 0.5 + 0.5);
      ctx.fillStyle = COL.stinger;
      ctx.shadowColor = COL.stinger;
      ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.ellipse(0, torsoTopY + bh * 0.4, bw * 0.15, bh * 0.12, 0, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.restore();
    }
  }

  // head, Corinthian-style helmet with crest
  const headR = bw * 0.17;
  const headY = torsoTopY - headR * 0.5;
  ctx.fillStyle = COL.gold;
  ctx.beginPath(); ctx.arc(0, headY, headR, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#8b2e1f';
  ctx.beginPath(); ctx.ellipse(0, headY - headR * 1.0, headR * 1.3, headR * 0.5, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = COL.goldDark;
  ctx.fillRect(-headR * 0.1, headY - headR * 0.1, headR * 0.2, headR * 0.9);
  // glowing molten eyes
  ctx.fillStyle = COL.stinger;
  ctx.shadowColor = COL.stinger;
  ctx.shadowBlur = 14;
  ctx.beginPath(); ctx.ellipse(-headR * 0.34, headY, headR * 0.16, headR * 0.1, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(headR * 0.34, headY, headR * 0.16, headR * 0.1, 0, 0, Math.PI * 2); ctx.fill();
  ctx.shadowBlur = 0;

  ctx.restore();
}

function enterBossFight() {
  state.mode = 'boss';
  boss = buildBoss();
  els.bossHudWrap.classList.remove('hidden');
  toast('¡TALOS!');
}

function updateBoss(dt) {
  if (!boss || !boss.alive) return;
  boss.spawnT += dt;
  if (boss.spawnT < 0.4) return;
  const dps = 14 + player.count * 4;
  boss.hp -= dps * dt;
  boss.shakeT += dt;
  els.bossHpBar.style.width = Math.max(0, (boss.hp / boss.maxHp) * 100) + '%';

  if (boss.hp <= 0 && boss.alive) {
    boss.alive = false;
    spawnExplosion(boss.x, boss.z, '#ffb347');
    spawnExplosion(boss.x, boss.z, '#ff7a3c');
    spawnCoinBurst(boss.x, boss.z, 80);
    AudioFX.explosion();
    els.bossHudWrap.classList.add('hidden');
    boss = null;
    setTimeout(() => victory(), 1400);
  }
}

// ---------- Game state ----------
const state = { mode: 'start', coins: 0, distance: 0, enemyDefeated: 0 };

const els = {
  squadCount: document.getElementById('squadCount'),
  coinCount: document.getElementById('coinCount'),
  progressBar: document.getElementById('progressBar'),
  toast: document.getElementById('toast'),
  bossHudWrap: document.getElementById('bossHudWrap'),
  bossHpBar: document.getElementById('bossHpBar'),
  screenStart: document.getElementById('screen-start'),
  screenGameOver: document.getElementById('screen-gameover'),
  screenVictory: document.getElementById('screen-victory'),
  goStats: document.getElementById('goStats'),
  vicStats: document.getElementById('vicStats'),
};

function toast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.remove('show');
  void els.toast.offsetWidth;
  els.toast.classList.add('show');
}

function updateHud() {
  els.squadCount.textContent = player.count;
  els.coinCount.textContent = state.coins;
  const pct = Math.min(100, (Math.abs(player.z - WORLD_START_Z) / Math.abs(BOSS_Z - WORLD_START_Z)) * 100);
  els.progressBar.style.width = pct + '%';
}

// ---------- Input ----------
function setLane(idx) {
  player.laneIndex = Math.max(0, Math.min(2, idx));
  player.targetX = LANES[player.laneIndex];
}
function moveLeft() { if (state.mode === 'run' || state.mode === 'boss') setLane(player.laneIndex - 1); }
function moveRight() { if (state.mode === 'run' || state.mode === 'boss') setLane(player.laneIndex + 1); }

window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') moveLeft();
  if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') moveRight();
});

let touchStartX = null;
canvas.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
canvas.addEventListener('touchend', (e) => {
  if (touchStartX === null) return;
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(dx) > 30) { dx > 0 ? moveRight() : moveLeft(); }
  touchStartX = null;
}, { passive: true });

// ---------- Game flow ----------
function resetGame() {
  obstacles.length = 0;
  particles.length = 0;
  activeLasers.length = 0;
  boss = null;

  player.count = 3;
  player.x = 0; player.targetX = 0; player.laneIndex = 1;
  player.z = WORLD_START_Z;
  player.displayScale = [];

  camera.x = 0; camera.z = WORLD_START_Z + 8;

  state.mode = 'run';
  state.coins = 0;
  state.distance = 0;

  spawnLevel();
  updateHud();
}

function showScreen(el) {
  [els.screenStart, els.screenGameOver, els.screenVictory].forEach(s => s.classList.add('hidden'));
  if (el) el.classList.remove('hidden');
}

function gameOver() {
  state.mode = 'gameover';
  AudioFX.gameOver();
  els.goStats.textContent = `Distancia recorrida: ${Math.round(Math.abs(player.z - WORLD_START_Z))}m · Dracmas: ${state.coins}`;
  showScreen(els.screenGameOver);
}

function victory() {
  state.mode = 'victory';
  AudioFX.victory();
  els.vicStats.textContent = `Falange final: ${player.count} guerreros · Dracmas: ${state.coins}`;
  showScreen(els.screenVictory);
}

document.getElementById('btnStart').addEventListener('click', () => {
  AudioFX.unlock();
  resetGame();
  showScreen(null);
});
document.getElementById('btnRetry').addEventListener('click', () => { resetGame(); showScreen(null); });
document.getElementById('btnAgain').addEventListener('click', () => { resetGame(); showScreen(null); });

// ---------- Obstacle logic ----------
function applyGateOp(op) {
  let msg = '';
  switch (op) {
    case 'x2': player.count = Math.round(player.count * 2); msg = 'x2!'; AudioFX.gatePositive(); break;
    case 'x3': player.count = Math.round(player.count * 3); msg = 'x3!'; AudioFX.gatePositive(); break;
    case '+5': player.count += 5; msg = '+5!'; AudioFX.gatePositive(); break;
    case '/2': player.count = Math.max(1, Math.floor(player.count / 2)); msg = '÷2'; AudioFX.gateNegative(); break;
  }
  player.count = Math.min(player.count, 999);
  toast(msg);
}

function handleObstacles() {
  for (const o of obstacles) {
    if (o.used) continue;
    const dz = player.z - o.z;
    if (o.type === 'gate') {
      if (dz > -1 && dz < 1.4) {
        o.used = true;
        applyGateOp(o.op);
      }
    } else if (o.type === 'coin') {
      const sameLaneish = Math.abs(player.x - LANES[o.laneIdx]) < 1.1;
      if (sameLaneish && dz > -0.8 && dz < 1.2) {
        o.used = true;
        state.coins += 1;
        AudioFX.coin();
      }
    } else if (o.type === 'enemy') {
      const sameLaneish = Math.abs(player.x - LANES[o.laneIdx]) < 1.15;
      if (sameLaneish && dz > -1.2 && dz < 1.4) {
        o.used = true;
        if (player.count > o.count) {
          player.count -= o.count;
          state.enemyDefeated += o.count;
          spawnExplosion(LANES[o.laneIdx], o.z, '#ff5533');
          AudioFX.hitEnemy();
          toast(`-${o.count} 💥`);
        } else {
          spawnExplosion(player.x, player.z, '#3ad1ff');
          gameOver();
          return;
        }
      }
    }
  }
}

// ---------- Draw dynamic world (obstacles, sorted back-to-front) ----------
function drawDynamicWorld() {
  const drawables = [];
  for (const o of obstacles) {
    if (o.used) continue;
    const depth = camera.z - o.z;
    if (depth < -6 || depth > FAR_CLIP) continue;
    drawables.push({ z: o.z, draw: () => {
      if (o.type === 'gate') drawGate(o);
      else if (o.type === 'enemy') drawEnemyCluster(o);
      else if (o.type === 'coin') drawCoinObstacle(o);
    }});
  }
  drawables.sort((a, b) => a.z - b.z); // farthest (most negative) first
  for (const d of drawables) d.draw();
}

// ---------- Main loop ----------
let lastT = performance.now();
function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, (now - lastT) / 1000);
  lastT = now;

  if (state.mode === 'run') {
    player.z -= FORWARD_SPEED * dt;
    if (player.z <= BOSS_Z + 14) {
      player.z = BOSS_Z + 14;
      enterBossFight();
    }
    handleObstacles();
  } else if (state.mode === 'boss') {
    updateBoss(dt);
  }

  player.x += (player.targetX - player.x) * LANE_LERP;
  runCycle += dt * (state.mode === 'gameover' ? 0 : 10);

  updateLasers(dt);
  updateParticles(dt);
  updateCamera();

  // ---- render ----
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  drawLaneLines();

  // static scenery: draw far-to-near (scenery sorted ascending by z already; z more negative = farther)
  for (let i = 0; i < scenery.length; i++) drawSceneryPiece(scenery[i]);

  drawDynamicWorld();
  if (state.mode === 'boss' || (boss && boss.alive)) drawBoss();
  drawPlayerSquad();
  drawParticles();
  drawLasers();

  updateHud();

  requestAnimationFrame; // no-op reference kept for clarity
}

resize();
updateHud();
requestAnimationFrame(animate);
})();

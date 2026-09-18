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
const LEVEL_END_Z = -600;
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

// ---------- Mini 3D engine ----------
// Real 3D geometry (boxes + N-gon discs), not flat sprites: each part is
// authored in local world-unit coordinates relative to an actor's ground
// point, optionally rotated around a pivot (for limbs/weapons), placed in
// world space, then every face is perspective-projected via project(),
// back-face-culled, lit by a fixed "sun" direction, and all faces from all
// parts are painter's-algorithm sorted together so overlapping limbs occlude
// correctly.
const LIGHT_DIR = vnorm([-0.45, 0.8, 0.35]);
const VIEW_DIR = vnorm([0, -0.3, 1]);

function vnorm(v) {
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / l, v[1] / l, v[2] / l];
}
function vdot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function vadd(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function vsub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }

function rotateAxis(p, axis, angle) {
  const c = Math.cos(angle), s = Math.sin(angle);
  const [x, y, z] = p;
  if (axis === 'x') return [x, y * c - z * s, y * s + z * c];
  if (axis === 'y') return [x * c + z * s, y, -x * s + z * c];
  return [x * c - y * s, x * s + y * c, z]; // 'z'
}
function rotateAroundPivot(p, pivot, axis, angle) {
  return vadd(rotateAxis(vsub(p, pivot), axis, angle), pivot);
}

// Unit-cube corner offsets (scaled by half-extents) and face definitions,
// shared by every box — only the half-extents/center/rotation differ per part.
const BOX_FACES = [
  { idx: [0, 1, 2, 3], n: [0, 0, -1] },  // back
  { idx: [4, 5, 6, 7], n: [0, 0, 1] },   // front
  { idx: [0, 3, 7, 4], n: [-1, 0, 0] },  // left
  { idx: [1, 5, 6, 2], n: [1, 0, 0] },   // right
  { idx: [0, 4, 5, 1], n: [0, -1, 0] },  // bottom
  { idx: [3, 2, 6, 7], n: [0, 1, 0] },   // top
];
function boxCorners(cx, cy, cz, hw, hh, hd) {
  return [
    [cx - hw, cy - hh, cz - hd], [cx + hw, cy - hh, cz - hd], [cx + hw, cy + hh, cz - hd], [cx - hw, cy + hh, cz - hd],
    [cx - hw, cy - hh, cz + hd], [cx + hw, cy - hh, cz + hd], [cx + hw, cy + hh, cz + hd], [cx - hw, cy + hh, cz + hd],
  ];
}

function shadeColor(hex, factor) {
  const n = parseInt(hex.slice(1), 16);
  let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  r = Math.max(0, Math.min(255, Math.round(r * factor)));
  g = Math.max(0, Math.min(255, Math.round(g * factor)));
  b = Math.max(0, Math.min(255, Math.round(b * factor)));
  return `rgb(${r},${g},${b})`;
}

// Appends a box part's visible faces (world-projected) to `out`.
function pushBoxFaces(out, actor, part) {
  const [cx, cy, cz] = part.center;
  const [hw, hh, hd] = part.half;
  let corners = boxCorners(cx, cy, cz, hw, hh, hd);
  let xformNormal = (n) => n;
  if (part.rot) {
    const { axis, angle, pivot } = part.rot;
    corners = corners.map(p => rotateAroundPivot(p, pivot, axis, angle));
    xformNormal = (n) => rotateAxis(n, axis, angle);
  }
  const world = corners.map(p => [p[0] + actor.x, p[1] + actor.y, p[2] + actor.z]);
  for (const face of BOX_FACES) {
    const wn = xformNormal(face.n);
    if (vdot(wn, VIEW_DIR) < 0.04) continue;
    const proj = face.idx.map(i => project(world[i][0], world[i][1], world[i][2]));
    if (proj.some(pp => !pp.ok)) continue;
    const depth = (proj[0].depth + proj[1].depth + proj[2].depth + proj[3].depth) / 4;
    const light = Math.max(0.32, Math.min(1.15, vdot(wn, LIGHT_DIR) * 0.85 + 0.45));
    out.push({ depth, pts: proj, color: shadeColor(part.color, light) });
  }
}

// Appends an N-gon disc part's single visible face (a shield, etc).
function pushDiscFace(out, actor, part) {
  const [cx, cy, cz] = part.center;
  const segs = part.segments || 10;
  const axis = vnorm(part.normalAxis);
  // build two basis vectors perpendicular to axis
  const up = Math.abs(axis[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  let bx = vnorm([up[1] * axis[2] - up[2] * axis[1], up[2] * axis[0] - up[0] * axis[2], up[0] * axis[1] - up[1] * axis[0]]);
  let by = [axis[1] * bx[2] - axis[2] * bx[1], axis[2] * bx[0] - axis[0] * bx[2], axis[0] * bx[1] - axis[1] * bx[0]];
  let local = [];
  for (let i = 0; i < segs; i++) {
    const t = (i / segs) * Math.PI * 2;
    const r = part.radius;
    local.push([
      cx + (bx[0] * Math.cos(t) + by[0] * Math.sin(t)) * r,
      cy + (bx[1] * Math.cos(t) + by[1] * Math.sin(t)) * r,
      cz + (bx[2] * Math.cos(t) + by[2] * Math.sin(t)) * r,
    ]);
  }
  let normal = axis;
  if (part.rot) {
    const { axis: rotAxis, angle, pivot } = part.rot;
    local = local.map(p => rotateAroundPivot(p, pivot, rotAxis, angle));
    normal = rotateAxis(normal, rotAxis, angle);
  }
  if (vdot(normal, VIEW_DIR) < 0.04) return;
  const world = local.map(p => [p[0] + actor.x, p[1] + actor.y, p[2] + actor.z]);
  const proj = world.map(p => project(p[0], p[1], p[2]));
  if (proj.some(pp => !pp.ok)) return;
  const depth = proj.reduce((s, pp) => s + pp.depth, 0) / proj.length;
  const light = Math.max(0.32, Math.min(1.15, vdot(normal, LIGHT_DIR) * 0.85 + 0.45));
  out.push({ depth, pts: proj, color: shadeColor(part.color, light) });
  if (part.rim) {
    const rimLight = Math.min(1.15, light * 1.1);
    out.push({ depth: depth - 0.01, pts: proj.map(p => ({ sx: p.sx, sy: p.sy })), color: null, strokeOnly: part.rim, lineWidth: proj[0].scale * 0.05 });
  }
}

// Draws a full actor (array of box/disc parts) as a depth-sorted face list.
function drawActor3D(actor, parts) {
  const faces = [];
  for (const part of parts) {
    if (part.kind === 'disc') pushDiscFace(faces, actor, part);
    else pushBoxFaces(faces, actor, part);
  }
  faces.sort((a, b) => b.depth - a.depth); // farthest first (painter's algorithm)
  for (const f of faces) {
    ctx.beginPath();
    ctx.moveTo(f.pts[0].sx, f.pts[0].sy);
    for (let i = 1; i < f.pts.length; i++) ctx.lineTo(f.pts[i].sx, f.pts[i].sy);
    ctx.closePath();
    if (f.strokeOnly) {
      ctx.strokeStyle = f.strokeOnly;
      ctx.lineWidth = Math.max(1, f.lineWidth);
      ctx.stroke();
    } else {
      ctx.fillStyle = f.color;
      ctx.fill();
    }
  }
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

// ---------- Progression: weapons, armor, enemy types, boss themes ----------
// Weapon tier: raises effective offense (player.count * power) in combat
// math, and recolors the ranged bolts.
const WEAPON_TIERS = [
  { name: 'Espada de Bronce', power: 1.0, cost: 0, laser: '#ffe066' },
  { name: 'Lanza de Hierro', power: 1.3, cost: 25, laser: '#cfeaff' },
  { name: 'Jabalina de Fuego', power: 1.7, cost: 60, laser: '#ff9a52' },
  { name: 'Rayo de Zeus', power: 2.3, cost: 120, laser: '#e0b3ff' },
];
// Armor tier: mitigates enemy effective threat and reduces casualties on a
// win, and recolors the hero cuirass.
const ARMOR_TIERS = [
  { name: 'Coraza de Bronce', defense: 0.0, cost: 0, body: '#e0a83f', bodyDark: '#9c6c1f' },
  { name: 'Coraza de Hierro', defense: 0.15, cost: 25, body: '#a9b2ba', bodyDark: '#5b636a' },
  { name: 'Coraza de Plata', defense: 0.30, cost: 60, body: '#dfe6ea', bodyDark: '#8b939a' },
  { name: 'Armadura de Aegis', defense: 0.45, cost: 120, body: '#fff3c4', bodyDark: '#e0b84a' },
];

// Enemy variety: a power multiplier (effective threat) plus a visual profile.
const ENEMY_TYPES = {
  debil: { power: 0.7, sizeMult: 0.85, body: '#b0524a', bodyDark: '#6e2f28', crest: '#8a8a8a', label: 'Explorador' },
  raso: { power: 1.0, sizeMult: 1.0, body: '#7a2b2b', bodyDark: '#431616', crest: '#1c1c1c', label: 'Soldado' },
  elite: { power: 1.4, sizeMult: 1.18, body: '#3a1414', bodyDark: '#1a0808', crest: '#ff8a2a', label: 'Élite' },
};

// Boss themes: each mini/final boss reuses the same Talos-style rig but with
// a visibly different palette, weapon, size and name so no two encounters
// look identical.
const BOSS_THEMES = [
  {
    name: 'ARGOS, CENTINELA DE BRONCE', weapon: 'sword', scale: 1.0, maxHp: 260,
    body: '#b8823c', bodyDark: '#6b4a1f', crest: '#8b2e1f', eye: '#ff8a2a', shield: '#b8823c', shieldDark: '#6b4a1f', metal: '#dfe6ea',
  },
  {
    name: 'CRONOS MENOR, EL ACORAZADO', weapon: 'axe', scale: 1.15, maxHp: 360,
    body: '#8e97a0', bodyDark: '#454b52', crest: '#1c1c1c', eye: '#4ad1ff', shield: '#8e97a0', shieldDark: '#454b52', metal: '#e9edf0',
  },
  {
    name: 'TALOS, EL COLOSO DE BRONCE', weapon: 'hammer', scale: 1.35, maxHp: 480,
    body: '#c9973f', bodyDark: '#7a5620', crest: '#f6f1e2', eye: '#ff8a2a', shield: '#c9973f', shieldDark: '#7a5620', metal: '#fff3c4',
  },
];

// ---------- Save data: persistent bank + equipped gear across runs ----------
const SAVE_KEY = 'falangeDorada_save_v1';
function loadSave() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        bank: parsed.bank | 0,
        weaponTier: Math.max(0, Math.min(WEAPON_TIERS.length - 1, parsed.weaponTier | 0)),
        armorTier: Math.max(0, Math.min(ARMOR_TIERS.length - 1, parsed.armorTier | 0)),
      };
    }
  } catch (e) { /* localStorage unavailable, fall back to defaults */ }
  return { bank: 0, weaponTier: 0, armorTier: 0 };
}
function persistSave() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); } catch (e) { /* ignore */ }
}
const save = loadSave();

// Boss checkpoints along the run — one every ~200 units, the last one at
// the level's end. Each uses a different BOSS_THEMES entry.
const bossCheckpoints = [
  { z: -200, theme: BOSS_THEMES[0] },
  { z: -400, theme: BOSS_THEMES[1] },
  { z: LEVEL_END_Z, theme: BOSS_THEMES[2] },
];

// ---------- World scenery (static): a marble colonnade flanking the path,
// with temple-facade gateways (columns + architrave + pediment) spanning it
// at intervals.
const scenery = [];

function buildWorld() {
  const colXs = [-8.0, 8.0];
  colXs.forEach((baseX) => {
    let z = 32;
    while (z > LEVEL_END_Z - 40) {
      const height = 8.5 + Math.random() * 2.2;
      scenery.push({ type: 'column', x: baseX, z, height });
      z -= 4.2 + Math.random() * 1.3;
    }
  });

  // A temple gateway just ahead of the start, plus one right at each boss
  // checkpoint for a dramatic arrival.
  const templeZs = [-32, ...bossCheckpoints.map(c => c.z - 8)];
  templeZs.forEach((z, i) => {
    const s = i === templeZs.length - 1 ? 1.7 : 1 + i * 0.12;
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

function drawSoldier(sx, sy, scale, colorBody, colorBodyDark, colorVisor, popScale, bobT, crestColor, sizeMult) {
  const s = scale * (popScale === undefined ? 1 : popScale) * (sizeMult || 1);
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
  // shield glint (rim-light, suggests curvature)
  ctx.strokeStyle = 'rgba(255,255,255,0.35)';
  ctx.lineWidth = Math.max(1, bodyW * 0.04);
  ctx.beginPath();
  ctx.arc(-bodyW * 0.46, bodyH * 0.05, bodyW * 0.24, Math.PI * 1.1, Math.PI * 1.5);
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
  // body (cuirass) — gradient + a soft vertical highlight for a rounded,
  // less flat-shaded look
  const grad = ctx.createLinearGradient(-bodyW / 2, 0, bodyW / 2, 0);
  grad.addColorStop(0, colorBodyDark);
  grad.addColorStop(0.5, colorBody);
  grad.addColorStop(1, colorBodyDark);
  ctx.fillStyle = grad;
  roundRect(-bodyW / 2, -bodyH * 0.15, bodyW, bodyH * 0.55, bodyW * 0.28);
  ctx.fill();
  ctx.save();
  ctx.clip();
  const sheen = ctx.createLinearGradient(-bodyW * 0.1, -bodyH * 0.15, bodyW * 0.28, -bodyH * 0.15);
  sheen.addColorStop(0, 'rgba(255,255,255,0.32)');
  sheen.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = sheen;
  ctx.fillRect(-bodyW * 0.1, -bodyH * 0.15, bodyW * 0.38, bodyH * 0.55);
  ctx.restore();
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
  // helmet gloss highlight
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.beginPath();
  ctx.ellipse(-headR * 0.32, headY - headR * 0.28, headR * 0.28, headR * 0.16, -0.5, 0, Math.PI * 2);
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
  const armor = ARMOR_TIERS[save.armorTier];

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
    drawSoldier(proj.sx, proj.sy, proj.scale, armor.body, armor.bodyDark, COL.blueVisor, pop, it.bobT, COL.heroCrest);
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
  const laserColor = WEAPON_TIERS[save.weaponTier].laser;
  for (const l of activeLasers) {
    const a = project(l.x, 0.9, l.z1);
    const b = project(l.x, 0.9, l.z2);
    if (!a.ok || !b.ok) continue;
    ctx.save();
    ctx.globalAlpha = Math.max(0, l.life / 0.12);
    ctx.strokeStyle = laserColor;
    ctx.shadowColor = laserColor;
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
    // Act 1: start -> boss checkpoint 1 (z -200)
    { type: 'gate', z: -40, op: 'x2' },
    { type: 'coins', z: -70, lanes: [0, 2] },
    { type: 'enemy', z: -110, lanes: [1], count: 3, etype: 'raso' },
    { type: 'gate', z: -155, op: 'x3' },
    { type: 'enemy', z: -180, lanes: [2], count: 4, etype: 'debil' },

    // Act 2: boss 1 -> boss checkpoint 2 (z -400)
    { type: 'gate', z: -240, op: '+5' },
    { type: 'enemy', z: -280, lanes: [0, 1], count: 10, etype: 'raso' },
    { type: 'coins', z: -300, lanes: [0, 1, 2] },
    { type: 'gate', z: -330, op: 'x2' },
    { type: 'enemy', z: -365, lanes: [1], count: 14, etype: 'elite' },

    // Act 3: boss 2 -> boss checkpoint 3 / level end (z -600)
    { type: 'gate', z: -440, op: 'x3' },
    { type: 'enemy', z: -470, lanes: [0, 1, 2], count: 20, etype: 'raso' },
    { type: 'coins', z: -490, lanes: [0, 1, 2] },
    { type: 'gate', z: -520, op: '/2' },
    { type: 'enemy', z: -550, lanes: [0, 2], count: 16, etype: 'elite' },
    { type: 'coins', z: -570, lanes: [0, 1, 2] },
  ];

  defs.forEach(def => {
    if (def.type === 'gate') {
      obstacles.push({ type: 'gate', z: def.z, op: def.op, used: false });
    } else if (def.type === 'enemy') {
      def.lanes.forEach(laneIdx => {
        obstacles.push({ type: 'enemy', z: def.z, laneIdx, count: def.count, etype: def.etype || 'raso', used: false, displayScale: [] });
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
  const etype = ENEMY_TYPES[o.etype] || ENEMY_TYPES.raso;
  for (const it of items) {
    const proj = project(it.wx, 0, it.wz);
    if (!proj.ok || proj.depth > FAR_CLIP || proj.depth < 0) continue;
    ctx.globalAlpha = fogFactor(proj.depth);
    drawSoldier(proj.sx, proj.sy, proj.scale, etype.body, etype.bodyDark, COL.redVisor, 1, runCycle * 8 + it.idx, etype.crest, etype.sizeMult);
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

// ---------- Boss: giant warriors from Greek myth, one per checkpoint ----------
// Each boss reuses the same humanoid rig but is driven by a BOSS_THEMES
// entry (colors, weapon, size, HP, name) so every encounter is visibly its
// own creature.
let boss = null;
let bossCheckpointIndex = 0;
let nextCheckpoint = 0; // index into bossCheckpoints of the next one to trigger

function buildBoss(checkpoint) {
  return {
    x: 0, y: 0, z: checkpoint.z - 6, theme: checkpoint.theme,
    hp: checkpoint.theme.maxHp, maxHp: checkpoint.theme.maxHp,
    alive: true, shakeT: 0, spawnT: 0,
  };
}

// Builds the boss's rigid parts list in world units (real 3D boxes/discs,
// not flat sprites) for the given animation time. `theme.scale` uniformly
// scales every dimension so each boss theme reads as a different-sized
// creature.
function buildBossParts(theme, shakeT, hpFrac) {
  const S = theme.scale;
  const parts = [];

  const legHalf = [0.22 * S, 0.75 * S, 0.24 * S];
  const legY = 0.75 * S;
  parts.push({ center: [-0.42 * S, legY, 0], half: legHalf, color: theme.bodyDark });
  parts.push({ center: [0.42 * S, legY, 0], half: legHalf, color: theme.bodyDark });

  const legTop = 1.5 * S;
  const torsoHalf = [1.05 * S, 0.85 * S, 0.55 * S];
  const torsoCenterY = legTop + torsoHalf[1];
  const torsoTop = torsoCenterY + torsoHalf[1];

  // Shield arm + shield (left / -X side)
  const shoulderL = [-1.15 * S, torsoCenterY + 0.3 * S, 0.1 * S];
  const armHalf = [0.2 * S, 0.55 * S, 0.2 * S];
  const shieldRot = { axis: 'z', angle: 0.2 + Math.sin(shakeT * 2) * 0.03, pivot: shoulderL };
  parts.push({ center: [shoulderL[0], shoulderL[1] - armHalf[1], shoulderL[2]], half: armHalf, color: theme.bodyDark, rot: shieldRot });
  parts.push({
    kind: 'disc', center: [shoulderL[0] - 0.15 * S, shoulderL[1] - 0.55 * S, shoulderL[2] + 0.25 * S],
    normalAxis: [-0.82, 0.05, 0.45], radius: 0.72 * S, segments: 10, color: theme.shield, rot: null,
  });

  // Weapon arm + weapon head (right / +X side), raised in a battle stance
  const shoulderR = [1.15 * S, torsoCenterY + 0.35 * S, 0.1 * S];
  const swingAngle = 2.25 + Math.sin(shakeT * 6) * 0.09;
  const weaponArmHalf = [0.2 * S, 0.6 * S, 0.2 * S];
  const armRot = { axis: 'z', angle: swingAngle, pivot: shoulderR };
  parts.push({ center: [shoulderR[0], shoulderR[1] - weaponArmHalf[1], shoulderR[2]], half: weaponArmHalf, color: theme.bodyDark, rot: armRot });

  const tip = [shoulderR[0], shoulderR[1] - weaponArmHalf[1] * 2, shoulderR[2]];
  if (theme.weapon === 'axe') {
    parts.push({ center: [tip[0], tip[1] - 0.35 * S, tip[2]], half: [0.12 * S, 0.35 * S, 0.12 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0] + 0.32 * S, tip[1] - 0.55 * S, tip[2]], half: [0.3 * S, 0.28 * S, 0.06 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0] - 0.32 * S, tip[1] - 0.55 * S, tip[2]], half: [0.3 * S, 0.28 * S, 0.06 * S], color: theme.metal, rot: armRot });
  } else if (theme.weapon === 'hammer') {
    parts.push({ center: [tip[0], tip[1] - 0.55 * S, tip[2]], half: [0.4 * S, 0.4 * S, 0.4 * S], color: theme.metal, rot: armRot });
  } else { // sword
    parts.push({ center: [tip[0], tip[1] - 0.55 * S, tip[2]], half: [0.09 * S, 0.55 * S, 0.05 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 0.08 * S, tip[2]], half: [0.26 * S, 0.06 * S, 0.1 * S], color: theme.bodyDark, rot: armRot });
  }

  // Torso
  parts.push({ center: [0, torsoCenterY, 0], half: torsoHalf, color: theme.body });

  // Head + Corinthian helmet crest
  const headHalf = [0.34 * S, 0.32 * S, 0.34 * S];
  const headCenterY = torsoTop + headHalf[1] + 0.08 * S;
  parts.push({ center: [0, headCenterY, 0], half: headHalf, color: theme.body });
  parts.push({
    center: [0, headCenterY + headHalf[1] + 0.16 * S, -0.02 * S], half: [0.42 * S, 0.16 * S, 0.58 * S], color: theme.crest,
    rot: { axis: 'x', angle: -0.3, pivot: [0, headCenterY + headHalf[1], 0] },
  });
  parts.push({ center: [0, headCenterY - 0.02 * S, headHalf[2] * 0.7], half: [0.06 * S, 0.26 * S, 0.05 * S], color: theme.bodyDark });

  return { parts, torsoCenterY, torsoHalf, headCenterY };
}

function drawBoss() {
  if (!boss) return;
  const theme = boss.theme;
  const projCheck = project(boss.x, 0, boss.z);
  if (!projCheck.ok) return;
  const fog = fogFactor(projCheck.depth);
  const hpFrac = boss.hp / boss.maxHp;

  const rig = buildBossParts(theme, boss.shakeT, hpFrac);
  const shakeOffset = Math.sin(boss.shakeT * 42) * 0.025;
  const actor = { x: boss.x + shakeOffset, y: boss.y, z: boss.z };

  // ground shadow
  const shadowProj = project(boss.x, 0.02, boss.z);
  if (shadowProj.ok) {
    ctx.save();
    ctx.globalAlpha = 0.32 * fog;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(shadowProj.sx, shadowProj.sy, 2.2 * shadowProj.scale * theme.scale, 0.55 * shadowProj.scale * theme.scale, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  ctx.save();
  ctx.globalAlpha = fog;
  drawActor3D(actor, rig.parts);
  ctx.restore();

  // glowing eyes + damage cracks/ichor glow, as a 2D overlay on the head/torso
  const eyeProj = project(actor.x, rig.headCenterY, actor.z + 0.34 * theme.scale * 0.7);
  if (eyeProj.ok) {
    const es = eyeProj.scale * theme.scale;
    ctx.save();
    ctx.globalAlpha = fog;
    ctx.fillStyle = theme.eye;
    ctx.shadowColor = theme.eye;
    ctx.shadowBlur = 14;
    ctx.beginPath(); ctx.ellipse(eyeProj.sx - 0.13 * es, eyeProj.sy, 0.055 * es, 0.04 * es, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(eyeProj.sx + 0.13 * es, eyeProj.sy, 0.055 * es, 0.04 * es, 0, 0, Math.PI * 2); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.restore();
  }

  if (hpFrac < 0.6) {
    const chestProj = project(actor.x, rig.torsoCenterY, actor.z + rig.torsoHalf[2]);
    if (chestProj.ok) {
      const cs = chestProj.scale * theme.scale;
      ctx.save();
      ctx.globalAlpha = fog * (1 - hpFrac) * 0.9;
      ctx.strokeStyle = '#2a1800';
      ctx.lineWidth = Math.max(1, 0.045 * cs);
      for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        const sx0 = chestProj.sx + (Math.random() - 0.5) * 1.6 * cs;
        const sy0 = chestProj.sy + (Math.random() - 0.5) * 1.2 * cs;
        ctx.moveTo(sx0, sy0);
        ctx.lineTo(sx0 + (Math.random() - 0.5) * 0.7 * cs, sy0 + (Math.random() - 0.5) * 0.7 * cs);
        ctx.stroke();
      }
      ctx.restore();
      if (hpFrac < 0.3) {
        ctx.save();
        ctx.globalAlpha = fog * 0.55 * (Math.sin(boss.shakeT * 20) * 0.5 + 0.5);
        ctx.fillStyle = theme.eye;
        ctx.shadowColor = theme.eye;
        ctx.shadowBlur = 16;
        ctx.beginPath(); ctx.ellipse(chestProj.sx, chestProj.sy, 0.32 * cs, 0.26 * cs, 0, 0, Math.PI * 2); ctx.fill();
        ctx.shadowBlur = 0;
        ctx.restore();
      }
    }
  }
}

function enterBossFight(checkpointIndex) {
  bossCheckpointIndex = checkpointIndex;
  const checkpoint = bossCheckpoints[checkpointIndex];
  state.mode = 'boss';
  boss = buildBoss(checkpoint);
  els.bossHudWrap.classList.remove('hidden');
  els.bossLabel.textContent = checkpoint.theme.name;
  toast(`¡${checkpoint.theme.name.split(',')[0]}!`);
}

function updateBoss(dt) {
  if (!boss || !boss.alive) return;
  boss.spawnT += dt;
  if (boss.spawnT < 0.4) return;
  const weapon = WEAPON_TIERS[save.weaponTier];
  const dps = (14 + player.count * 4) * weapon.power;
  boss.hp -= dps * dt;
  boss.shakeT += dt;
  els.bossHpBar.style.width = Math.max(0, (boss.hp / boss.maxHp) * 100) + '%';

  if (boss.hp <= 0 && boss.alive) {
    boss.alive = false;
    spawnExplosion(boss.x, boss.z, '#ffb347');
    spawnExplosion(boss.x, boss.z, '#ff7a3c');
    spawnCoinBurst(boss.x, boss.z, 50 + bossCheckpointIndex * 20);
    AudioFX.explosion();
    els.bossHudWrap.classList.add('hidden');
    boss = null;
    const wasFinal = bossCheckpointIndex >= bossCheckpoints.length - 1;
    setTimeout(() => {
      if (wasFinal) {
        victory();
      } else {
        nextCheckpoint = bossCheckpointIndex + 1;
        state.mode = 'run';
        toast('¡Continúa la falange!');
      }
    }, 1400);
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
  bossLabel: document.getElementById('bossLabel'),
  screenStart: document.getElementById('screen-start'),
  screenGameOver: document.getElementById('screen-gameover'),
  screenVictory: document.getElementById('screen-victory'),
  screenArmory: document.getElementById('screen-armory'),
  goStats: document.getElementById('goStats'),
  vicStats: document.getElementById('vicStats'),
  bankAmount: document.getElementById('bankAmount'),
  bankAmount2: document.getElementById('bankAmount2'),
  weaponList: document.getElementById('weaponList'),
  armorList: document.getElementById('armorList'),
};

function updateBankDisplays() {
  els.bankAmount.textContent = save.bank;
  els.bankAmount2.textContent = save.bank;
}

function toast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.remove('show');
  void els.toast.offsetWidth;
  els.toast.classList.add('show');
}

function updateHud() {
  els.squadCount.textContent = player.count;
  els.coinCount.textContent = state.coins;
  const pct = Math.min(100, (Math.abs(player.z - WORLD_START_Z) / Math.abs(LEVEL_END_Z - WORLD_START_Z)) * 100);
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
  nextCheckpoint = 0;
  bossCheckpointIndex = 0;
  els.bossHudWrap.classList.add('hidden');

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
  [els.screenStart, els.screenGameOver, els.screenVictory, els.screenArmory].forEach(s => s.classList.add('hidden'));
  if (el) el.classList.remove('hidden');
}

function bankCoins() {
  save.bank += state.coins;
  persistSave();
  updateBankDisplays();
}

function gameOver() {
  state.mode = 'gameover';
  AudioFX.gameOver();
  bankCoins();
  els.goStats.textContent = `Distancia recorrida: ${Math.round(Math.abs(player.z - WORLD_START_Z))}m · Dracmas: ${state.coins} (banco: ${save.bank})`;
  showScreen(els.screenGameOver);
}

function victory() {
  state.mode = 'victory';
  AudioFX.victory();
  bankCoins();
  els.vicStats.textContent = `Falange final: ${player.count} guerreros · Dracmas: ${state.coins} (banco: ${save.bank})`;
  showScreen(els.screenVictory);
}

document.getElementById('btnStart').addEventListener('click', () => {
  AudioFX.unlock();
  resetGame();
  showScreen(null);
});
document.getElementById('btnRetry').addEventListener('click', () => { resetGame(); showScreen(null); });
document.getElementById('btnAgain').addEventListener('click', () => { resetGame(); showScreen(null); });

// ---------- Armory (upgrade shop) ----------
function renderShopList(container, tiers, currentTierKey, onBuy) {
  container.innerHTML = '';
  const currentTier = save[currentTierKey];
  tiers.forEach((tier, i) => {
    const row = document.createElement('div');
    row.className = 'shopRow';
    const owned = i <= currentTier;
    const isNext = i === currentTier + 1;
    const statLabel = tier.power !== undefined ? `Poder x${tier.power.toFixed(2)}` : `Defensa ${Math.round(tier.defense * 100)}%`;
    let actionHtml;
    if (owned) {
      actionHtml = i === currentTier ? '<span class="shopStatus equipped">EQUIPADO</span>' : '<span class="shopStatus">poseído</span>';
    } else if (isNext) {
      const affordable = save.bank >= tier.cost;
      actionHtml = `<button class="shopBuy" data-idx="${i}" ${affordable ? '' : 'disabled'}>${tier.cost} 🪙</button>`;
    } else {
      actionHtml = '<span class="shopStatus locked">🔒</span>';
    }
    row.innerHTML = `<div class="shopInfo"><div class="shopName">${tier.name}</div><div class="shopStat">${statLabel}</div></div>${actionHtml}`;
    container.appendChild(row);
  });
  container.querySelectorAll('.shopBuy').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx, 10);
      onBuy(idx);
    });
  });
}

function renderArmory() {
  updateBankDisplays();
  renderShopList(els.weaponList, WEAPON_TIERS, 'weaponTier', (idx) => {
    const tier = WEAPON_TIERS[idx];
    if (save.bank < tier.cost || idx !== save.weaponTier + 1) return;
    save.bank -= tier.cost;
    save.weaponTier = idx;
    persistSave();
    AudioFX.coin();
    renderArmory();
  });
  renderShopList(els.armorList, ARMOR_TIERS, 'armorTier', (idx) => {
    const tier = ARMOR_TIERS[idx];
    if (save.bank < tier.cost || idx !== save.armorTier + 1) return;
    save.bank -= tier.cost;
    save.armorTier = idx;
    persistSave();
    AudioFX.coin();
    renderArmory();
  });
}

document.getElementById('btnArmory').addEventListener('click', () => {
  renderArmory();
  showScreen(els.screenArmory);
});
document.getElementById('btnArmoryBack').addEventListener('click', () => {
  showScreen(els.screenStart);
});

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
        const weapon = WEAPON_TIERS[save.weaponTier];
        const armor = ARMOR_TIERS[save.armorTier];
        const etype = ENEMY_TYPES[o.etype] || ENEMY_TYPES.raso;
        const effPlayer = player.count * weapon.power;
        const effEnemy = o.count * etype.power * (1 - armor.defense);
        if (effPlayer > effEnemy) {
          const losses = Math.max(1, Math.round(o.count * (1 - armor.defense * 0.5)));
          player.count = Math.max(1, player.count - losses);
          state.enemyDefeated += o.count;
          spawnExplosion(LANES[o.laneIdx], o.z, '#ff5533');
          AudioFX.hitEnemy();
          toast(`-${losses} 💥`);
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
    const checkpoint = bossCheckpoints[nextCheckpoint];
    if (checkpoint && player.z <= checkpoint.z + 14) {
      player.z = checkpoint.z + 14;
      enterBossFight(nextCheckpoint);
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
updateBankDisplays();
requestAnimationFrame(animate);
})();

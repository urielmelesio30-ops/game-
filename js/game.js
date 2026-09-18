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
const LEVEL_END_Z = -800;
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

// Accepts either '#rrggbb' or an 'rgb(r,g,b)' string — callers sometimes
// pre-tint a color (itself via shadeColor) before it reaches the 3D
// engine's own per-face lighting pass, so this must tolerate its own output.
function shadeColor(color, factor) {
  let r, g, b;
  if (color.charCodeAt(0) === 35 /* '#' */) {
    const n = parseInt(color.slice(1), 16);
    r = (n >> 16) & 255; g = (n >> 8) & 255; b = n & 255;
  } else {
    const m = color.match(/[\d.]+/g);
    r = +m[0]; g = +m[1]; b = +m[2];
  }
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

// Appends a flat quad panel (e.g. a cape) given 4 explicit local corner
// points (in order around the perimeter); its normal is derived from the
// corners themselves so it shades correctly as it rotates/flutters.
function pushPanelFace(out, actor, part) {
  let pts = part.points;
  if (part.rot) {
    const { axis, angle, pivot } = part.rot;
    pts = pts.map(p => rotateAroundPivot(p, pivot, axis, angle));
  }
  const e1 = vsub(pts[1], pts[0]);
  const e2 = vsub(pts[2], pts[0]);
  let normal = vnorm([e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]);
  if (vdot(normal, VIEW_DIR) < -0.04) normal = normal.map(v => -v); // panels are thin: shade whichever side faces us
  if (vdot(normal, VIEW_DIR) < 0.04) return;
  const world = pts.map(p => [p[0] + actor.x, p[1] + actor.y, p[2] + actor.z]);
  const proj = world.map(p => project(p[0], p[1], p[2]));
  if (proj.some(pp => !pp.ok)) return;
  const depth = proj.reduce((s, pp) => s + pp.depth, 0) / proj.length;
  const light = Math.max(0.32, Math.min(1.15, vdot(normal, LIGHT_DIR) * 0.85 + 0.45));
  out.push({ depth, pts: proj, color: shadeColor(part.color, light) });
}

// Draws a full actor (array of box/disc/panel parts) as a depth-sorted face list.
function drawActor3D(actor, parts, opts) {
  const faces = [];
  for (const part of parts) {
    if (part.kind === 'disc') pushDiscFace(faces, actor, part);
    else if (part.kind === 'panel') pushPanelFace(faces, actor, part);
    else pushBoxFaces(faces, actor, part);
  }
  faces.sort((a, b) => b.depth - a.depth); // farthest first (painter's algorithm)
  const outline = opts && opts.outline;
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
      if (outline) {
        // a crisp dark rim per face — the cheapest way to keep each warrior
        // reading as a distinct silhouette even when packed shoulder to
        // shoulder in a big phalanx
        ctx.strokeStyle = 'rgba(24,16,10,0.45)';
        ctx.lineWidth = Math.max(0.6, f.pts[0].scale * 0.014);
        ctx.stroke();
      }
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

// Night palette — blended in with COL as the run progresses toward Ares.
const NIGHT = {
  sky1: '#2a3a6b', sky2: '#141c42', sky3: '#080b22',
  fog: '#232f5c',
  sand1: '#4a4560', sand2: '#302c48',
  mtn1: '#2c3660', mtn2: '#1c2444',
};

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function lerpColor(hexA, hexB, t) {
  if (t <= 0) return hexA;
  if (t >= 1) return hexB;
  const a = hexToRgb(hexA), b = hexToRgb(hexB);
  const r = Math.round(a[0] + (b[0] - a[0]) * t);
  const g = Math.round(a[1] + (b[1] - a[1]) * t);
  const bl = Math.round(a[2] + (b[2] - a[2]) * t);
  return `rgb(${r},${g},${bl})`;
}

// 0 = full day, 1 = full night — day holds through acts 1-2, dusk creeps in
// around Talos (act 3), and it's fully dark by the time Ares appears.
function computeDayT(z) {
  if (z >= -400) return 0;
  if (z >= -600) return ((-400 - z) / 200) * 0.4;
  if (z >= -750) return 0.4 + ((-600 - z) / 150) * 0.6;
  return 1;
}

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
// win. Spartans fight bare-chested, so this tier instead reskins the shield
// (bronze -> iron -> silver -> the radiant Aegis) — a hoplite's real pride.
const ARMOR_TIERS = [
  { name: 'Escudo de Bronce', defense: 0.0, cost: 0, body: '#c9973f', bodyDark: '#7a5620' },
  { name: 'Escudo de Hierro', defense: 0.15, cost: 25, body: '#a9b2ba', bodyDark: '#5b636a' },
  { name: 'Escudo de Plata', defense: 0.30, cost: 60, body: '#dfe6ea', bodyDark: '#8b939a' },
  { name: 'Escudo de Aegis', defense: 0.45, cost: 120, body: '#fff3c4', bodyDark: '#e0b84a' },
];

// Per-warrior visual variation (skin tone, cape shade, crest) so no two
// hoplites in a phalanx look quite identical. Cycled deterministically by
// formation index, not randomized per frame.
const HERO_VARIANTS = [
  { skin: '#c98a54', skinDark: '#8f5c34', cape: '#b8291f', crest: '#f6f1e2' },
  { skin: '#b97b45', skinDark: '#7d5129', cape: '#9c1f17', crest: '#efe2c0' },
  { skin: '#d59a63', skinDark: '#96683c', cape: '#c93a2a', crest: '#fff6e0' },
  { skin: '#a66f3d', skinDark: '#6f4a26', cape: '#7a1712', crest: '#e8dcc0' },
];

// Enemy variety: a power multiplier (effective threat) plus a visual profile
// — a rival dark-caped warband, same Spartan rig, different colors per type.
const ENEMY_TYPES = {
  minimo: {
    power: 0.45, sizeMult: 0.62, label: 'Recluta', metal: '#a0a5a8', metalDark: '#686d70',
    variants: [
      { skin: '#b98a70', skinDark: '#7a5640', cape: '#707070', crest: '#b0b0b0' },
      { skin: '#ac7d64', skinDark: '#6e4c38', cape: '#606060', crest: '#c0c0c0' },
    ],
  },
  debil: {
    power: 0.7, sizeMult: 0.85, label: 'Explorador', metal: '#8a8f93', metalDark: '#52565a',
    variants: [
      { skin: '#9c6a52', skinDark: '#5f3f2c', cape: '#5a5a5a', crest: '#8a8a8a' },
      { skin: '#8f5f49', skinDark: '#553626', cape: '#4a4a4a', crest: '#9a9a9a' },
    ],
  },
  raso: {
    power: 1.0, sizeMult: 1.0, label: 'Soldado', metal: '#6a6a6a', metalDark: '#3a3a3a',
    variants: [
      { skin: '#8a4a3f', skinDark: '#552c24', cape: '#4a2020', crest: '#5a5a5a' },
      { skin: '#7d4136', skinDark: '#4a251e', cape: '#3e1c1c', crest: '#666666' },
    ],
  },
  elite: {
    power: 1.4, sizeMult: 1.18, label: 'Élite', metal: '#4a2424', metalDark: '#2a1212',
    variants: [
      { skin: '#5a2020', skinDark: '#2e0f0f', cape: '#6a1414', crest: '#ff8a2a' },
      { skin: '#4f1d1d', skinDark: '#280d0d', cape: '#5a1818', crest: '#ff9a3a' },
    ],
  },
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
  {
    // The true final boss: Ares himself, arriving as night falls. Same rig,
    // vastly bigger, wreathed in a divine fire that the other bosses don't
    // have (see the `divine` flag, used by drawBoss to add flame + lightning).
    name: 'ARES, DIOS DE LA GUERRA', weapon: 'spear', scale: 1.85, maxHp: 900, divine: true,
    body: '#6e1210', bodyDark: '#2e0705', crest: '#161616', eye: '#ff3300', shield: '#1c0e0c', shieldDark: '#0c0504', metal: '#3a1512',
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
  { z: -600, theme: BOSS_THEMES[2] },
  { z: LEVEL_END_Z, theme: BOSS_THEMES[3] },
];

// ---------- World scenery (static): a marble colonnade flanking the path,
// with temple-facade gateways (columns + architrave + pediment) spanning it
// at intervals.
const scenery = [];

const BANNER_COLORS = ['#b8291f', '#e8b93a', '#2f6fa8'];

function buildWorld() {
  const colXs = [-8.0, 8.0];
  colXs.forEach((baseX, side) => {
    let z = 32;
    let i = 0;
    while (z > LEVEL_END_Z - 40) {
      const broken = i % 5 === 4; // one in five columns stands in ruin
      const height = broken ? (3 + Math.random() * 2.5) : (8.5 + Math.random() * 2.2);
      scenery.push({ type: 'column', x: baseX, z, height, broken });
      if (!broken && i % 3 === 1) {
        scenery.push({ type: 'banner', x: baseX + (side === 0 ? 0.9 : -0.9), z: z - 1, height, color: BANNER_COLORS[i % BANNER_COLORS.length], phase: i * 1.7 });
      }
      z -= 4.2 + Math.random() * 1.3;
      i++;
    }
  });

  // Statues on pedestals, alternating marble/bronze, just outside the
  // colonnade.
  let sz = 12;
  let si = 0;
  while (sz > LEVEL_END_Z - 20) {
    const side = si % 2 === 0 ? -1 : 1;
    scenery.push({ type: 'statue', x: side * 10.4, z: sz, bronze: si % 3 === 0 });
    sz -= 52 + (si % 3) * 6;
    si++;
  }

  // Braziers flanking the path itself, closer in, lighting the way.
  let bz = 18;
  let bi = 0;
  while (bz > LEVEL_END_Z - 20) {
    const side = bi % 2 === 0 ? -1 : 1;
    scenery.push({ type: 'brazier', x: side * 3.7, z: bz, phase: bi * 2.3 });
    bz -= 20 + (bi % 4) * 3;
    bi++;
  }

  // Olive trees and urns dotted just beyond the colonnade for garden life.
  let tz = 24;
  let ti = 0;
  while (tz > LEVEL_END_Z - 20) {
    const side = ti % 2 === 0 ? 1 : -1;
    if (ti % 2 === 0) {
      scenery.push({ type: 'tree', x: side * 9.4, z: tz, seed: ti * 3.1 });
    } else {
      scenery.push({ type: 'urn', x: side * 9.0, z: tz });
    }
    tz -= 34 + (ti % 3) * 8;
    ti++;
  }

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

  if (p.broken) {
    // jagged, crumbled top instead of a neat capital
    const midA = project(p.x - hw * 0.3, p.height + 0.35, p.z);
    const midB = project(p.x + hw * 0.15, p.height + 0.55, p.z);
    if (midA.ok && midB.ok) {
      ctx.fillStyle = COL.cliffC;
      ctx.beginPath();
      ctx.moveTo(topL.sx, topL.sy);
      ctx.lineTo(midA.sx, midA.sy); ctx.lineTo(midB.sx, midB.sy);
      ctx.lineTo(topR.sx, topR.sy);
      ctx.closePath(); ctx.fill();
    }
    // rubble at the base
    ctx.fillStyle = COL.cliffB;
    for (let k = 0; k < 3; k++) {
      const rp = project(p.x - hw + k * hw * 0.7, 0.16, p.z + 0.3 - k * 0.25);
      if (rp.ok) { ctx.beginPath(); ctx.arc(rp.sx, rp.sy, 3.2 * rp.scale * 0.1, 0, Math.PI * 2); ctx.fill(); }
    }
  } else {
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

// A simple standing figure on a pedestal — marble or bronze, static.
function drawStatue(p) {
  const depth = camera.z - p.z;
  if (depth < 0 || depth > FAR_CLIP) return;
  const fog = fogFactor(depth);
  const stone = p.bronze ? COL.gold : '#e8e2d0';
  const stoneDark = p.bronze ? COL.goldDark : '#b8b098';
  ctx.save();
  ctx.globalAlpha = fog;
  const parts = [
    { center: [p.x, 0.5, p.z], half: [0.7, 0.5, 0.7], color: stoneDark }, // pedestal
    { center: [p.x, 1.5, p.z], half: [0.32, 0.5, 0.24], color: stone }, // legs/robe
    { center: [p.x, 2.3, p.z], half: [0.34, 0.32, 0.26], color: stone }, // torso
    { center: [p.x, 2.78, p.z], half: [0.2, 0.2, 0.2], color: stone }, // head
    { center: [p.x + 0.42, 2.35, p.z], half: [0.11, 0.32, 0.11], color: stone, rot: { axis: 'z', angle: -0.9, pivot: [p.x + 0.34, 2.55, p.z] } }, // raised arm
  ];
  drawActor3D({ x: 0, y: 0, z: 0 }, parts);
  ctx.restore();
}

// A bronze brazier with a hand-drawn flicker of flame on top (2D overlay —
// cheap, and shadowBlur glow reads better than a lit 3D face for fire).
function drawBrazier(p) {
  const proj = project(p.x, 1.05, p.z);
  if (!proj.ok || proj.depth < 0 || proj.depth > FAR_CLIP) return;
  const fog = fogFactor(proj.depth);
  ctx.save();
  ctx.globalAlpha = fog;
  const parts = [
    { center: [p.x, 0.55, p.z], half: [0.09, 0.55, 0.09], color: COL.goldDark }, // pole
    { center: [p.x, 1.15, p.z], half: [0.32, 0.16, 0.32], color: COL.gold }, // bowl
  ];
  drawActor3D({ x: 0, y: 0, z: 0 }, parts);

  const t = runCycle * 6 + p.phase;
  const fs = proj.scale;
  const dayT = computeDayT(p.z);
  ctx.translate(proj.sx, proj.sy - 0.16 * fs);
  ctx.fillStyle = `rgba(255,150,40,${0.35 + dayT * 0.3})`;
  ctx.beginPath(); ctx.arc(0, 0, (0.55 + dayT * 0.35) * fs, 0, Math.PI * 2); ctx.fill();
  for (let i = 0; i < 3; i++) {
    const fl = Math.sin(t + i * 2.1) * 0.5 + 0.5;
    const fx = Math.sin(t * 1.7 + i) * 0.12 * fs;
    const fh = (0.32 + fl * 0.22) * fs;
    ctx.fillStyle = i === 1 ? '#ffe066' : '#ff7a2a';
    ctx.shadowColor = '#ff9a2a';
    ctx.shadowBlur = 8 + dayT * 10;
    ctx.beginPath();
    ctx.moveTo(fx - 0.09 * fs, 0);
    ctx.quadraticCurveTo(fx - 0.12 * fs, -fh * 0.6, fx, -fh);
    ctx.quadraticCurveTo(fx + 0.12 * fs, -fh * 0.6, fx + 0.09 * fs, 0);
    ctx.closePath();
    ctx.fill();
  }
  ctx.shadowBlur = 0;
  ctx.restore();
}

// A hanging cloth banner, gently swaying, projected as one flat panel.
function drawBanner(p) {
  const proj = project(p.x, p.height * 0.6, p.z);
  if (!proj.ok || proj.depth < 0 || proj.depth > FAR_CLIP) return;
  const fog = fogFactor(proj.depth);
  const sway = Math.sin(runCycle * 1.3 + p.phase) * 0.18;
  const topY = p.height + 0.3;
  const botY = p.height - 2.1;
  ctx.save();
  ctx.globalAlpha = fog;
  const part = {
    kind: 'panel',
    points: [
      [p.x - 0.5, topY, p.z],
      [p.x + 0.5, topY, p.z],
      [p.x + 0.5 + sway, botY, p.z + 0.15],
      [p.x - 0.5 + sway, botY, p.z + 0.15],
    ],
    color: p.color,
  };
  drawActor3D({ x: 0, y: 0, z: 0 }, [part]);
  ctx.restore();
}

const OLIVE_GREEN = '#7a8f4a', OLIVE_GREEN_DARK = '#5a6a34';
function drawTree(p) {
  const proj = project(p.x, 0, p.z);
  if (!proj.ok || proj.depth < 0 || proj.depth > FAR_CLIP) return;
  ctx.save();
  ctx.globalAlpha = fogFactor(proj.depth);
  const sway = Math.sin(runCycle * 0.4 + p.seed) * 0.04;
  const parts = [
    { center: [p.x, 1.1, p.z], half: [0.16, 1.1, 0.16], color: '#7a6a4a', rot: { axis: 'z', angle: sway, pivot: [p.x, 0, p.z] } },
    { kind: 'disc', center: [p.x - 0.5, 2.3, p.z], normalAxis: [0.3, 0.2, 0.9], radius: 0.85, segments: 8, color: OLIVE_GREEN },
    { kind: 'disc', center: [p.x + 0.4, 2.6, p.z + 0.1], normalAxis: [-0.2, 0.3, 0.9], radius: 0.95, segments: 8, color: OLIVE_GREEN_DARK },
    { kind: 'disc', center: [p.x, 3.1, p.z - 0.1], normalAxis: [0.1, 0.4, 0.85], radius: 0.75, segments: 8, color: OLIVE_GREEN },
  ];
  drawActor3D({ x: 0, y: 0, z: 0 }, parts);
  ctx.restore();
}

function drawUrn(p) {
  const proj = project(p.x, 0, p.z);
  if (!proj.ok || proj.depth < 0 || proj.depth > FAR_CLIP) return;
  ctx.save();
  ctx.globalAlpha = fogFactor(proj.depth);
  const parts = [
    { center: [p.x, 0.22, p.z], half: [0.16, 0.22, 0.16], color: COL.cliffB },
    { center: [p.x, 0.62, p.z], half: [0.32, 0.28, 0.32], color: COL.gold },
    { center: [p.x, 1.0, p.z], half: [0.18, 0.14, 0.18], color: COL.goldDark },
  ];
  drawActor3D({ x: 0, y: 0, z: 0 }, parts);
  ctx.restore();
}

function drawSceneryPiece(p) {
  if (p.type === 'column') drawColumn(p);
  else if (p.type === 'temple') drawTemple(p);
  else if (p.type === 'statue') drawStatue(p);
  else if (p.type === 'brazier') drawBrazier(p);
  else if (p.type === 'banner') drawBanner(p);
  else if (p.type === 'tree') drawTree(p);
  else if (p.type === 'urn') drawUrn(p);
}

let atmosphereT = 0;

function drawMountainLayer(baseY, amp, color, alpha, parallax, seedOffset) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, HORIZON_Y);
  const scroll = camera.x * parallax;
  const peaks = 7;
  for (let i = 0; i <= peaks; i++) {
    const x = (i / peaks) * (W + 120) - 60 - (scroll % (W / peaks));
    const n = Math.sin(i * 12.9 + seedOffset) * 0.5 + Math.sin(i * 5.3 + seedOffset * 1.7) * 0.5;
    const y = baseY - Math.abs(n) * amp;
    ctx.lineTo(x, y);
  }
  ctx.lineTo(W + 60, HORIZON_Y);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawCloud(cx, cy, s, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = '#fffaf0';
  [[-0.5, 0, 0.5], [0, -0.18, 0.62], [0.55, 0.02, 0.45], [-1.0, 0.08, 0.4], [1.05, 0.1, 0.36]].forEach(([dx, dy, r]) => {
    ctx.beginPath();
    ctx.ellipse(cx + dx * s, cy + dy * s, r * s, r * s * 0.62, 0, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.restore();
}

// Fixed star field (screen-fraction positions via a golden-angle spread so
// they never clump), faded in as night falls.
const STAR_POSITIONS = Array.from({ length: 46 }, (_, i) => ({
  x: (i * 137.508) % 100 / 100,
  y: ((i * 71.317) % 100) / 100 * 0.8,
  s: 0.6 + (i % 5) * 0.3,
  phase: i * 1.7,
}));
function drawStars(dayT) {
  if (dayT <= 0.04) return;
  ctx.save();
  for (const st of STAR_POSITIONS) {
    const twinkle = 0.5 + 0.5 * Math.sin(atmosphereT * 2 + st.phase);
    ctx.globalAlpha = dayT * (0.25 + twinkle * 0.55);
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(st.x * W, st.y * HORIZON_Y, st.s, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawBackground() {
  const dayT = computeDayT(player.z);
  const sky1 = lerpColor(COL.sky1, NIGHT.sky1, dayT);
  const sky2 = lerpColor(COL.sky2, NIGHT.sky2, dayT);
  const sky3 = lerpColor(COL.sky3, NIGHT.sky3, dayT);
  const fog = lerpColor(COL.fog, NIGHT.fog, dayT);
  const sand1 = lerpColor(COL.sand1, NIGHT.sand1, dayT);
  const sand2 = lerpColor(COL.sand2, NIGHT.sand2, dayT);
  const mtn1 = lerpColor('#a9c3dd', NIGHT.mtn1, dayT);
  const mtn2 = lerpColor('#8fb3d6', NIGHT.mtn2, dayT);

  // sky
  const skyGrad = ctx.createLinearGradient(0, 0, 0, HORIZON_Y);
  skyGrad.addColorStop(0, sky3);
  skyGrad.addColorStop(0.55, sky2);
  skyGrad.addColorStop(1, sky1);
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, W, HORIZON_Y);

  const sunX = CENTER_X + Math.sin(camera.x * 0.02) * 20;
  const sunY = HORIZON_Y * 0.5;

  drawStars(dayT);

  // drifting clouds, dimmer once night falls
  for (let i = 0; i < 4; i++) {
    const speed = 3.2 + i * 1.1;
    const cx = ((atmosphereT * speed + i * 210 - camera.x * 0.15) % (W + 260)) - 130;
    const cy = HORIZON_Y * (0.16 + (i % 3) * 0.13);
    drawCloud(cx, cy, 34 + (i % 3) * 10, (0.5 - i * 0.06) * (1 - dayT * 0.75));
  }

  // hazy distant mountains, two parallax layers
  drawMountainLayer(HORIZON_Y, HORIZON_Y * 0.22, mtn1, 0.55, 0.01, 4.1);
  drawMountainLayer(HORIZON_Y, HORIZON_Y * 0.14, mtn2, 0.7, 0.025, 11.7);

  // sun by day, moon by night — cross-fades at the same spot in the sky
  if (dayT < 0.97) {
    const glow = ctx.createRadialGradient(sunX, sunY, 4, sunX, sunY, H * 0.5);
    glow.addColorStop(0, `rgba(255,244,210,${0.95 * (1 - dayT)})`);
    glow.addColorStop(0.35, `rgba(255,214,140,${0.35 * (1 - dayT)})`);
    glow.addColorStop(1, 'rgba(255,214,140,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, HORIZON_Y * 1.4);
    ctx.save();
    ctx.globalAlpha = 1 - dayT;
    ctx.fillStyle = '#fff9e8';
    ctx.shadowColor = '#fff3c4';
    ctx.shadowBlur = 30;
    ctx.beginPath(); ctx.arc(sunX, sunY, Math.max(10, H * 0.032), 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  if (dayT > 0.03) {
    const mglow = ctx.createRadialGradient(sunX, sunY, 2, sunX, sunY, H * 0.32);
    mglow.addColorStop(0, `rgba(200,210,255,${0.5 * dayT})`);
    mglow.addColorStop(1, 'rgba(200,210,255,0)');
    ctx.fillStyle = mglow;
    ctx.fillRect(0, 0, W, HORIZON_Y * 1.4);
    ctx.save();
    ctx.globalAlpha = dayT;
    ctx.fillStyle = '#e8ecf6';
    ctx.shadowColor = '#c7d2f0';
    ctx.shadowBlur = 22;
    const mr = Math.max(9, H * 0.028);
    ctx.beginPath(); ctx.arc(sunX, sunY, mr, 0, Math.PI * 2); ctx.fill();
    ctx.globalCompositeOperation = 'destination-out';
    ctx.globalAlpha = 0.5;
    ctx.beginPath(); ctx.arc(sunX + mr * 0.42, sunY - mr * 0.15, mr * 0.85, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  // god rays (soft streaks), warm by day / cool moonlight by night
  ctx.save();
  ctx.globalAlpha = 0.10 * (1 - dayT * 0.5);
  ctx.fillStyle = dayT > 0.5 ? '#c7d2f0' : '#fff6da';
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
  groundGrad.addColorStop(0, fog);
  groundGrad.addColorStop(0.18, sand2);
  groundGrad.addColorStop(1, sand1);
  ctx.fillStyle = groundGrad;
  ctx.fillRect(0, HORIZON_Y, W, H - HORIZON_Y);
}

function drawVignette(dayT) {
  const r = Math.max(W, H) * 0.75;
  const edgeAlpha = 0.38 + (dayT || 0) * 0.16;
  const vg = ctx.createRadialGradient(CENTER_X, H * 0.52, r * 0.45, CENTER_X, H * 0.52, r);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, `rgba(10,6,2,${edgeAlpha})`);
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, W, H);
}

// A translucent night-blue wash over the whole scene — cheaper and more
// convincing than re-deriving every prop/warrior color for darkness.
function drawNightTint(dayT) {
  if (dayT <= 0.01) return;
  ctx.save();
  ctx.globalAlpha = dayT * 0.42;
  ctx.fillStyle = '#0a1030';
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// Slow-drifting dust motes catching the light, for atmosphere.
const dustMotes = [];
function initDustMotes() {
  dustMotes.length = 0;
  for (let i = 0; i < 22; i++) {
    dustMotes.push({
      x: (Math.random() - 0.5) * 14, y: 0.5 + Math.random() * 3.5, z: 0,
      speed: 0.15 + Math.random() * 0.25, drift: (Math.random() - 0.5) * 0.3, phase: Math.random() * 10,
    });
  }
}
initDustMotes();
function drawDustMotes() {
  ctx.save();
  for (const m of dustMotes) {
    const z = camera.z - 4 - ((atmosphereT * m.speed * 6 + m.phase * 3) % 30);
    const x = m.x + Math.sin(atmosphereT * 0.4 + m.phase) * m.drift * 3;
    const proj = project(x, m.y, z);
    if (!proj.ok || proj.depth > 34) continue;
    const flicker = 0.35 + 0.35 * Math.sin(atmosphereT * 2 + m.phase * 5);
    ctx.globalAlpha = Math.max(0, flicker) * fogFactor(proj.depth) * 0.5;
    ctx.fillStyle = '#fff3c4';
    ctx.beginPath();
    ctx.arc(proj.sx, proj.sy, Math.max(0.6, proj.scale * 0.012), 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

// Alternating perspective-correct floor bands between the colonnades — a
// real mosaic tile pattern instead of a flat gradient.
function drawMosaicFloor() {
  const spacing = 3.2;
  const startZ = Math.ceil((camera.z - 1.2) / spacing) * spacing;
  for (let i = 0; i < 16; i++) {
    const zNear = startZ - i * spacing;
    const zFar = zNear - spacing;
    const depth = camera.z - (zNear + zFar) / 2;
    if (depth < 0.6 || depth > 70) continue;
    const nl = project(-3.9, 0.01, zNear), nr = project(3.9, 0.01, zNear);
    const fl = project(-3.9, 0.01, zFar), fr = project(3.9, 0.01, zFar);
    if (!nl.ok || !nr.ok || !fl.ok || !fr.ok) continue;
    const tileIdx = Math.round(zNear / spacing);
    ctx.globalAlpha = fogFactor(depth) * 0.3;
    ctx.fillStyle = tileIdx % 2 === 0 ? 'rgba(196,138,62,0.5)' : 'rgba(230,190,120,0.35)';
    ctx.beginPath();
    ctx.moveTo(nl.sx, nl.sy); ctx.lineTo(nr.sx, nr.sy); ctx.lineTo(fr.sx, fr.sy); ctx.lineTo(fl.sx, fl.sy);
    ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawLaneLines() {
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
  // decorative mosaic border just inside the colonnade
  [-3.9, 3.9].forEach((lx) => {
    const near = project(lx, 0, camera.z - 1.5);
    if (!near.ok) return;
    ctx.strokeStyle = 'rgba(200,140,60,0.4)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(near.sx, near.sy);
    ctx.lineTo(CENTER_X, HORIZON_Y);
    ctx.stroke();
  });
}

// ---------- Soldier / creature sprite drawing ----------
// Sprite sizes are defined in WORLD units and multiplied by `scale` (px per
// world unit, from project()) to get pixel dimensions — never raw pixels.
// ---------- Spartan hoplite rig (real 3D, player + enemy) ----------
// Bare-chested torso, kilt, bronze Corinthian helmet, horsehair crest, a
// shield slung on the back, and a cape that flows on the side the camera
// actually sees (the runners' backs, since the camera trails behind them).
const SPEAR_WOOD = '#6b4a2a', SPEAR_WOOD_DARK = '#3f2c18';

function buildSoldierParts(S, variant, metal, metalDark, bobT) {
  const parts = [];
  const skirtHalf = [0.26 * S, 0.28 * S, 0.22 * S];
  parts.push({ center: [0, 0.28 * S, 0], half: skirtHalf, color: variant.skinDark });

  const torsoHalf = [0.30 * S, 0.32 * S, 0.20 * S];
  const torsoCenterY = 0.56 * S + torsoHalf[1];
  parts.push({ center: [0, torsoCenterY, 0], half: torsoHalf, color: variant.skin });

  // pteruges — a fringe of little leather straps at the waist line, the
  // detail that breaks up a plain box torso when seen from behind
  const waistY = 0.56 * S;
  for (let i = -2; i <= 2; i++) {
    parts.push({
      center: [i * 0.1 * S, waistY - 0.02 * S, torsoHalf[2] * 0.75], half: [0.045 * S, 0.08 * S, 0.03 * S],
      color: i % 2 === 0 ? variant.skinDark : variant.cape,
    });
  }

  const headHalf = [0.17 * S, 0.17 * S, 0.17 * S];
  const headCenterY = torsoCenterY + torsoHalf[1] + headHalf[1] + 0.04 * S;
  parts.push({ center: [0, headCenterY, 0], half: headHalf, color: metal });
  // helmet rim flare at the base — turns the plain cube into a recognizable
  // helmet silhouette from any angle, including from behind
  parts.push({ center: [0, headCenterY - headHalf[1] * 0.82, 0], half: [headHalf[0] * 1.3, headHalf[1] * 0.22, headHalf[2] * 1.3], color: metalDark });
  parts.push({
    center: [0, headCenterY + headHalf[1] + 0.1 * S, 0.02 * S], half: [0.07 * S, 0.13 * S, 0.32 * S], color: variant.crest,
  });

  // shield, slung on the back — mostly facing the camera since that's the
  // visible side of a runner moving away into the level
  const shieldCenter = [-0.05 * S, torsoCenterY + 0.05 * S, torsoHalf[2] + 0.1 * S];
  const shieldNormal = [-0.25, 0.05, 0.95];
  parts.push({
    kind: 'disc', center: shieldCenter, normalAxis: shieldNormal, radius: 0.44 * S, segments: 10, color: metal,
  });

  // a spear slung across the back, its head rising past the shoulder
  const spearBase = [0.32 * S, 0.42 * S, torsoHalf[2] * 0.6];
  const spearRot = { axis: 'x', angle: -0.18, pivot: spearBase };
  parts.push({ center: [spearBase[0], spearBase[1] + 0.75 * S, spearBase[2]], half: [0.035 * S, 0.75 * S, 0.035 * S], color: SPEAR_WOOD, rot: spearRot });
  parts.push({ center: [spearBase[0], spearBase[1] + 1.62 * S, spearBase[2]], half: [0.06 * S, 0.16 * S, 0.03 * S], color: metal, rot: spearRot });
  parts.push({ center: [spearBase[0], spearBase[1] + 0.2 * S, spearBase[2]], half: [0.05 * S, 0.1 * S, 0.05 * S], color: SPEAR_WOOD_DARK, rot: spearRot });

  // cape — flows down the back with a slow cloth-lag sway, independent of
  // the faster running bob
  const sway = Math.sin(bobT * 0.6) * 0.05 * S;
  const billow = 0.22 * S + Math.cos(bobT * 0.6) * 0.05 * S;
  const capeZ = torsoHalf[2] + 0.04 * S;
  const shoulderY = torsoCenterY + torsoHalf[1] * 0.7;
  parts.push({
    kind: 'panel',
    points: [
      [-0.2 * S, shoulderY, capeZ],
      [0.2 * S, shoulderY, capeZ],
      [0.32 * S + sway, 0.04 * S, capeZ + billow],
      [-0.32 * S + sway, 0.04 * S, capeZ + billow],
    ],
    color: variant.cape,
  });

  return { parts, shieldCenter, shieldNormal };
}

function drawSoldierActor(worldX, worldZ, S, variant, metal, metalDark, bobT, emblem) {
  const shadowProj = project(worldX, 0.02, worldZ);
  if (shadowProj.ok) {
    ctx.globalAlpha *= 0.28;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(shadowProj.sx, shadowProj.sy, 0.34 * shadowProj.scale * S, 0.13 * shadowProj.scale * S, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha /= 0.28;
  }
  const bob = Math.abs(Math.sin(bobT)) * 0.05 * S;
  const actor = { x: worldX, y: bob, z: worldZ };
  const rig = buildSoldierParts(S, variant, metal, metalDark, bobT);
  drawActor3D(actor, rig.parts, { outline: true });

  // a shield emblem — cheap 2D overlay projected onto the shield's center,
  // the one detail that instantly reads as "Spartan" rather than "box army"
  if (emblem) {
    const sc = rig.shieldCenter;
    const proj = project(sc[0] + actor.x, sc[1] + actor.y, sc[2] + actor.z);
    if (proj.ok) {
      const s = proj.scale * S;
      ctx.save();
      ctx.translate(proj.sx, proj.sy);
      ctx.strokeStyle = 'rgba(20,14,8,0.55)';
      ctx.lineWidth = Math.max(1, s * 0.045);
      ctx.lineCap = 'round';
      ctx.beginPath();
      if (emblem === 'lambda') {
        ctx.moveTo(0, -0.22 * s); ctx.lineTo(-0.16 * s, 0.22 * s);
        ctx.moveTo(0, -0.22 * s); ctx.lineTo(0.16 * s, 0.22 * s);
      } else { // enemy mark: a jagged scar-like slash
        ctx.moveTo(-0.16 * s, -0.18 * s); ctx.lineTo(0.14 * s, 0.05 * s);
        ctx.moveTo(0.14 * s, 0.05 * s); ctx.lineTo(-0.08 * s, 0.2 * s);
      }
      ctx.stroke();
      ctx.restore();
    }
  }
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
  const spacingX = 0.86, spacingZ = 0.78;
  const offsets = [];
  for (let i = 0; i < n; i++) {
    const row = Math.floor(i / perRow);
    const col = i % perRow;
    const inThisRow = Math.min(perRow, n - row * perRow);
    const startOffset = -(inThisRow - 1) / 2;
    const brick = (row % 2 === 1) ? spacingX * 0.5 : 0; // stagger alternate ranks
    offsets.push({ x: (startOffset + col) * spacingX + brick, z: row * spacingZ });
  }
  return offsets;
}

let runCycle = 0;

// ---------- Screen juice: shake + hit flash ----------
let screenShakeMag = 0;
let flashAlpha = 0, flashColor = '#fff';
function triggerShake(mag) { screenShakeMag = Math.max(screenShakeMag, mag); }
function triggerFlash(color, alpha) { flashColor = color; flashAlpha = Math.max(flashAlpha, alpha); }

let dustTimer = 0;
function updateRunDust(dt) {
  dustTimer -= dt;
  if ((state.mode === 'run') && dustTimer <= 0 && player.count > 0) {
    dustTimer = 0.09;
    for (let k = 0; k < 2; k++) {
      particles.push({
        x: player.x + (Math.random() - 0.5) * 1.6, y: 0.05, z: player.z + 0.5 + Math.random() * 0.3,
        vx: (Math.random() - 0.5) * 1.2, vy: 0.4 + Math.random() * 0.5, vz: 1.2 + Math.random() * 0.8,
        life: 0.35 + Math.random() * 0.15, kind: 'dust', rot: 0, spin: 0,
      });
    }
  }
}

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
    const jitter = 0.94 + ((it.idx * 37) % 13) / 13 * 0.12;
    const variant = HERO_VARIANTS[it.idx % HERO_VARIANTS.length];
    const metalTint = 0.86 + ((it.idx * 53) % 17) / 17 * 0.3;
    ctx.globalAlpha = fogFactor(proj.depth);
    drawSoldierActor(it.wx, it.wz, pop * jitter, variant, shadeColor(armor.body, metalTint), shadeColor(armor.bodyDark, metalTint), it.bobT, 'lambda');
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
    if (p.kind !== 'dust') p.vy -= 16 * dt;
    else p.vy -= 1.2 * dt;
    p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
    p.rot += p.spin * dt;
    if (p.kind !== 'dust' && p.y < 0.15) { p.y = 0.15; p.vy *= -0.4; p.vx *= 0.7; p.vz *= 0.7; }
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
    else if (p.kind === 'dust') {
      ctx.globalAlpha *= 0.4;
      ctx.fillStyle = COL.sand2;
      ctx.beginPath();
      ctx.arc(proj.sx, proj.sy, proj.scale * 0.1 * (1.4 - p.life), 0, Math.PI * 2);
      ctx.fill();
    } else drawDebrisSprite(proj.sx, proj.sy, proj.scale, p.rot, p.color || '#ff6633');
    ctx.globalAlpha = 1;
  }
}

// ---------- Obstacles: gates, enemy squads, coins ----------
const obstacles = [];

function spawnLevel() {
  const defs = [
    // Act 1: start -> boss checkpoint 1 (z -200)
    { type: 'gate', z: -40, op: 'x2' },
    { type: 'enemy', z: -75, lanes: [0], count: 2, etype: 'minimo' },
    { type: 'coins', z: -70, lanes: [2] },
    { type: 'enemy', z: -110, lanes: [1], count: 3, etype: 'raso' },
    { type: 'gate', z: -155, op: 'x3' },
    { type: 'enemy', z: -180, lanes: [2], count: 4, etype: 'debil' },

    // Act 2: boss 1 -> boss checkpoint 2 (z -400)
    { type: 'gate', z: -240, op: '+5' },
    { type: 'enemy', z: -280, lanes: [0, 1], count: 10, etype: 'raso' },
    { type: 'coins', z: -300, lanes: [0, 1, 2] },
    { type: 'gate', z: -330, op: 'x2' },
    { type: 'enemy', z: -365, lanes: [1], count: 14, etype: 'elite' },

    // Act 3: boss 2 -> boss checkpoint 3 (z -600)
    { type: 'gate', z: -440, op: 'x3' },
    { type: 'enemy', z: -470, lanes: [0, 1, 2], count: 20, etype: 'raso' },
    { type: 'coins', z: -490, lanes: [0, 1, 2] },
    { type: 'gate', z: -520, op: '/2' },
    { type: 'enemy', z: -550, lanes: [0, 2], count: 16, etype: 'elite' },
    { type: 'coins', z: -570, lanes: [0, 1, 2] },

    // Act 4: boss 3 (Talos) -> Ares, the god of war (z -800), as night falls
    { type: 'gate', z: -630, op: 'x2' },
    { type: 'enemy', z: -655, lanes: [0, 1, 2], count: 12, etype: 'minimo' },
    { type: 'coins', z: -670, lanes: [0, 1, 2] },
    { type: 'gate', z: -690, op: 'x3' },
    { type: 'enemy', z: -715, lanes: [0, 1], count: 22, etype: 'elite' },
    { type: 'coins', z: -730, lanes: [0, 1, 2] },
    { type: 'gate', z: -745, op: '+5' },
    { type: 'enemy', z: -765, lanes: [0, 1, 2], count: 28, etype: 'elite' },
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
    const jitter = 0.94 + ((it.idx * 37) % 13) / 13 * 0.12;
    const variant = etype.variants[it.idx % etype.variants.length];
    const metalTint = 0.86 + ((it.idx * 53) % 17) / 17 * 0.3;
    ctx.globalAlpha = fogFactor(proj.depth);
    drawSoldierActor(it.wx, it.wz, etype.sizeMult * jitter, variant, shadeColor(etype.metal, metalTint), shadeColor(etype.metalDark, metalTint), runCycle * 8 + it.idx, 'scar');
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
  let weaponFireAt = null; // world-relative (pre-actor-offset) point for a fire/divine flourish
  if (theme.weapon === 'axe') {
    parts.push({ center: [tip[0], tip[1] - 0.35 * S, tip[2]], half: [0.12 * S, 0.35 * S, 0.12 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0] + 0.32 * S, tip[1] - 0.55 * S, tip[2]], half: [0.3 * S, 0.28 * S, 0.06 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0] - 0.32 * S, tip[1] - 0.55 * S, tip[2]], half: [0.3 * S, 0.28 * S, 0.06 * S], color: theme.metal, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 0.55 * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'hammer') {
    parts.push({ center: [tip[0], tip[1] - 0.55 * S, tip[2]], half: [0.4 * S, 0.4 * S, 0.4 * S], color: theme.metal, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 0.55 * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'spear') {
    parts.push({ center: [tip[0], tip[1] - 0.9 * S, tip[2]], half: [0.06 * S, 0.9 * S, 0.06 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 1.75 * S, tip[2]], half: [0.14 * S, 0.28 * S, 0.05 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 1.35 * S, tip[2]], half: [0.2 * S, 0.06 * S, 0.06 * S], color: theme.bodyDark, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 2.0 * S, tip[2]], rot: armRot };
  } else { // sword
    parts.push({ center: [tip[0], tip[1] - 0.55 * S, tip[2]], half: [0.09 * S, 0.55 * S, 0.05 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 0.08 * S, tip[2]], half: [0.26 * S, 0.06 * S, 0.1 * S], color: theme.bodyDark, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 1.05 * S, tip[2]], rot: armRot };
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

  return { parts, torsoCenterY, torsoHalf, headCenterY, weaponFireAt };
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

  // divine fire wreathing the weapon — only Ares (and any future god boss)
  if (theme.divine && rig.weaponFireAt) {
    const { local, rot } = rig.weaponFireAt;
    const rotated = rot ? rotateAroundPivot(local, rot.pivot, rot.axis, rot.angle) : local;
    const fireProj = project(rotated[0] + actor.x, rotated[1] + actor.y, rotated[2] + actor.z);
    if (fireProj.ok) {
      const fs = fireProj.scale * theme.scale;
      const t = runCycle * 8 + boss.shakeT * 3;
      ctx.save();
      ctx.globalAlpha = fog;
      ctx.translate(fireProj.sx, fireProj.sy);
      for (let i = 0; i < 4; i++) {
        const fl = Math.sin(t + i * 1.9) * 0.5 + 0.5;
        const fx = Math.sin(t * 1.6 + i * 2) * 0.1 * fs;
        const fy = -Math.abs(Math.cos(t * 1.3 + i)) * 0.18 * fs;
        const fh = (0.22 + fl * 0.18) * fs;
        ctx.fillStyle = i % 2 === 0 ? '#ff5a1a' : '#ffcf4a';
        ctx.shadowColor = '#ff3300';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(fx - 0.06 * fs, fy);
        ctx.quadraticCurveTo(fx - 0.08 * fs, fy - fh * 0.6, fx, fy - fh);
        ctx.quadraticCurveTo(fx + 0.08 * fs, fy - fh * 0.6, fx + 0.06 * fs, fy);
        ctx.closePath();
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      ctx.restore();
    }
  }

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
  lightningTimer = 1.2;
  els.bossHudWrap.classList.remove('hidden');
  els.bossLabel.textContent = checkpoint.theme.name;
  toast(`¡${checkpoint.theme.name.split(',')[0]}!`);
}

let lightningTimer = 1.5;
function updateBoss(dt) {
  if (!boss || !boss.alive) return;
  boss.spawnT += dt;
  if (boss.spawnT < 0.4) return;
  const weapon = WEAPON_TIERS[save.weaponTier];
  const dps = (14 + player.count * 4) * weapon.power;
  boss.hp -= dps * dt;
  boss.shakeT += dt;
  els.bossHpBar.style.width = Math.max(0, (boss.hp / boss.maxHp) * 100) + '%';

  if (boss.theme.divine) {
    lightningTimer -= dt;
    if (lightningTimer <= 0) {
      lightningTimer = 1.8 + Math.random() * 2.2;
      triggerFlash('#eaf3ff', 0.28);
      triggerShake(0.15);
      AudioFX.laser();
    }
  }

  if (boss.hp <= 0 && boss.alive) {
    boss.alive = false;
    spawnExplosion(boss.x, boss.z, '#ffb347');
    spawnExplosion(boss.x, boss.z, '#ff7a3c');
    spawnCoinBurst(boss.x, boss.z, 50 + bossCheckpointIndex * 20);
    AudioFX.explosion();
    triggerShake(boss.theme.divine ? 1.0 : 0.7);
    triggerFlash(boss.theme.divine ? '#ffffff' : '#ffe066', boss.theme.divine ? 0.75 : 0.5);
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
          triggerShake(0.12 + Math.min(0.25, o.count / 200));
          triggerFlash('#fff3c4', 0.18);
        } else {
          spawnExplosion(player.x, player.z, '#3ad1ff');
          triggerShake(0.45);
          triggerFlash('#ff3b3b', 0.4);
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
  atmosphereT += dt;

  updateLasers(dt);
  updateParticles(dt);
  updateRunDust(dt);
  updateCamera();
  screenShakeMag *= 0.88;
  flashAlpha = Math.max(0, flashAlpha - dt * 2.2);

  // ---- render ----
  ctx.clearRect(0, 0, W, H);
  const shakeX = screenShakeMag > 0.002 ? (Math.random() - 0.5) * screenShakeMag * W * 0.06 : 0;
  const shakeY = screenShakeMag > 0.002 ? (Math.random() - 0.5) * screenShakeMag * H * 0.04 : 0;
  ctx.save();
  ctx.translate(shakeX, shakeY);

  drawBackground();
  drawMosaicFloor();
  drawLaneLines();

  // static scenery: draw far-to-near (scenery sorted ascending by z already; z more negative = farther)
  for (let i = 0; i < scenery.length; i++) drawSceneryPiece(scenery[i]);

  drawDynamicWorld();
  if (state.mode === 'boss' || (boss && boss.alive)) drawBoss();
  drawPlayerSquad();
  drawParticles();
  drawLasers();
  drawDustMotes();

  const dayT = computeDayT(player.z);
  drawNightTint(dayT);

  ctx.restore();

  drawVignette(dayT);
  if (flashAlpha > 0.005) {
    ctx.save();
    ctx.globalAlpha = flashAlpha;
    ctx.fillStyle = flashColor;
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
  }

  updateHud();
}

resize();
updateHud();
updateBankDisplays();
requestAnimationFrame(animate);
})();

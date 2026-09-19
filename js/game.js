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
const LEVEL_END_Z = -1800;
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

// Accepts '#rrggbb' or 'rgb(r,g,b)' — lerpColor's own output feeds back into
// itself when biome blending chains onto an already-blended day/night color.
function hexToRgb(hex) {
  if (hex.charCodeAt(0) !== 35 /* '#' */) {
    const m = hex.match(/[\d.]+/g);
    return [+m[0], +m[1], +m[2]];
  }
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

// 0 = full day, 1 = full night — day holds through the early gods, dusk
// creeps in around Odín, and it's fully dark by the time Zeus appears.
// (Bosses with their own `biome` override this entirely during their fight.)
function computeDayT(z) {
  if (z >= -900) return 0;
  if (z >= -1400) return ((-900 - z) / 500) * 0.5;
  if (z >= -1650) return 0.5 + ((-1400 - z) / 250) * 0.5;
  return 1;
}

// ---------- Progression: weapons, armor, enemy types, boss themes ----------
// Weapon tier: raises effective offense (player.count * power) in combat
// math, and recolors the ranged bolts. `rarity` tints the shop row's accent
// bar so the growing roster reads at a glance (common bronze -> legendary gold).
const WEAPON_TIERS = [
  { name: 'Espada de Bronce', power: 1.0, cost: 0, laser: '#ffe066', rarity: '#c9973f', statText: 'Poder x1.00' },
  { name: 'Lanza de Hierro', power: 1.3, cost: 25, laser: '#cfeaff', rarity: '#9aa4ab', statText: 'Poder x1.30' },
  { name: 'Jabalina de Fuego', power: 1.7, cost: 60, laser: '#ff9a52', rarity: '#ff7a3c', statText: 'Poder x1.70' },
  { name: 'Rayo de Zeus', power: 2.3, cost: 120, laser: '#e0b3ff', rarity: '#b98bff', statText: 'Poder x2.30' },
  { name: 'Tridente de Poseidón', power: 3.0, cost: 220, laser: '#4ad1ff', rarity: '#2fb8e0', statText: 'Poder x3.00' },
  { name: 'Hoz de Cronos', power: 3.9, cost: 380, laser: '#a06bff', rarity: '#5a2e8a', statText: 'Poder x3.90' },
  { name: 'Arco de Apolo', power: 5.0, cost: 620, laser: '#fff3b0', rarity: '#ffd23f', statText: 'Poder x5.00' },
  { name: 'Espada de Aquiles', power: 6.3, cost: 950, laser: '#ff4d4d', rarity: '#e02f2f', statText: 'Poder x6.30' },
  { name: 'Lanza de Atenea', power: 7.8, cost: 1400, laser: '#baffc9', rarity: '#4fae66', statText: 'Poder x7.80' },
  { name: 'Trueno del Olimpo', power: 9.5, cost: 2000, laser: '#fff8e0', rarity: '#ffd700', statText: 'Poder x9.50' },
];
// Armor tier: mitigates enemy effective threat and reduces casualties on a
// win. Spartans fight bare-chested, so this tier instead reskins the shield
// (bronze -> iron -> silver -> the radiant Aegis, and beyond) — a hoplite's
// real pride.
const ARMOR_TIERS = [
  { name: 'Escudo de Bronce', defense: 0.00, cost: 0, body: '#c9973f', bodyDark: '#7a5620', rarity: '#c9973f', statText: 'Defensa 0%' },
  { name: 'Escudo de Hierro', defense: 0.15, cost: 25, body: '#a9b2ba', bodyDark: '#5b636a', rarity: '#9aa4ab', statText: 'Defensa 15%' },
  { name: 'Escudo de Plata', defense: 0.30, cost: 60, body: '#dfe6ea', bodyDark: '#8b939a', rarity: '#c7ccd1', statText: 'Defensa 30%' },
  { name: 'Escudo de Aegis', defense: 0.45, cost: 120, body: '#fff3c4', bodyDark: '#e0b84a', rarity: '#ffd700', statText: 'Defensa 45%' },
  { name: 'Escudo Espartano', defense: 0.55, cost: 220, body: '#8a1f1f', bodyDark: '#4a0f0f', rarity: '#c93a2a', statText: 'Defensa 55%' },
  { name: 'Escudo de Poseidón', defense: 0.63, cost: 380, body: '#2f7d9e', bodyDark: '#164152', rarity: '#4ad1ff', statText: 'Defensa 63%' },
  { name: 'Escudo de Atenea', defense: 0.70, cost: 600, body: '#5a7d4a', bodyDark: '#2e4526', rarity: '#8fce6a', statText: 'Defensa 70%' },
  { name: 'Escudo de Titán', defense: 0.76, cost: 950, body: '#5a4632', bodyDark: '#2e2216', rarity: '#8a6b45', statText: 'Defensa 76%' },
  { name: 'Escudo de Hefesto', defense: 0.82, cost: 1400, body: '#ff8a2a', bodyDark: '#a3480c', rarity: '#ff8a2a', statText: 'Defensa 82%' },
  { name: 'Escudo del Olimpo', defense: 0.90, cost: 2000, body: '#f5f8ff', bodyDark: '#c7d2f0', rarity: '#ffffff', statText: 'Defensa 90%' },
];

// ---------- Favores Divinos ("Divine Favors") — booster system ----------
// A second, independent progression track layered on top of the equipped
// weapon/shield tier: a permanent blessing from a god that multiplies weapon
// power or adds to shield defense. Bought/equipped separately from tiers so
// the player always has two things to save dracmas toward.
const WEAPON_FAVORS = [
  { name: 'Sin Favor', mult: 1.00, cost: 0, rarity: '#8a8478', statText: 'Sin bono' },
  { name: 'Favor de Ares I', mult: 1.10, cost: 150, rarity: '#c93a2a', statText: '+10% Poder' },
  { name: 'Favor de Ares II', mult: 1.22, cost: 420, rarity: '#ff5533', statText: '+22% Poder' },
  { name: 'Favor de Ares III', mult: 1.38, cost: 900, rarity: '#ff3300', statText: '+38% Poder' },
];
const ARMOR_FAVORS = [
  { name: 'Sin Favor', bonus: 0.00, cost: 0, rarity: '#8a8478', statText: 'Sin bono' },
  { name: 'Favor de Atenea I', bonus: 0.05, cost: 150, rarity: '#8fce6a', statText: '+5% Defensa' },
  { name: 'Favor de Atenea II', bonus: 0.11, cost: 420, rarity: '#5fae4a', statText: '+11% Defensa' },
  { name: 'Favor de Atenea III', bonus: 0.18, cost: 900, rarity: '#3f8a30', statText: '+18% Defensa' },
];
function effectiveWeaponPower() {
  return WEAPON_TIERS[save.weaponTier].power * WEAPON_FAVORS[save.weaponFavor].mult;
}
function effectiveArmorDefense() {
  return Math.min(0.95, ARMOR_TIERS[save.armorTier].defense + ARMOR_FAVORS[save.armorFavor].bonus);
}

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

// Boss themes: a pantheon of 9 Greek (and one Norse guest, Odín) gods and
// legends, one per checkpoint. Each reuses the same rig-building pipeline
// but `morph` swaps out whole body parts (snake-hair instead of a helmet,
// a serpent tail instead of legs, a lion pelt, a beard...) so every god
// reads as a genuinely different creature, not just a recolor. `biome`
// and `weather` drive a full environment swap while that boss is up —
// see BIOME_PALETTES / updateWeather — and `divine` (with optional
// `fireColors`/`fireGlow`) drives the elemental flourish wreathing their
// weapon (fire, lightning, sea-spray...).
const BOSS_THEMES = [
  {
    name: 'MEDUSA, LA GORGONA', weapon: 'sword', scale: 1.05, maxHp: 300, morph: 'gorgon',
    biome: 'petrified', weather: null,
    body: '#7a9e6a', bodyDark: '#3f5c34', crest: '#8a9e78', eye: '#ffe066', shield: '#9aa89a', shieldDark: '#5a6a56', metal: '#c9c9c9',
  },
  {
    name: 'CRONOS, TITÁN DEL TIEMPO', weapon: 'scythe', scale: 1.2, maxHp: 380, morph: 'titan',
    biome: 'temporal', weather: 'ash',
    body: '#6a5a4a', bodyDark: '#362c22', crest: '#c9a45a', eye: '#c9a45a', shield: '#5a4a3a', shieldDark: '#2e2418', metal: '#c9a45a',
  },
  {
    name: 'AFRODITA, DIOSA DEL AMOR', weapon: 'scepter', scale: 0.95, maxHp: 300, morph: 'goddess',
    biome: 'blossom', weather: 'petals',
    body: '#ffd9ea', bodyDark: '#e0a8c0', crest: '#fff0c9', eye: '#ff6fae', shield: '#ffe6f2', shieldDark: '#e8b8d0', metal: '#ffd700',
  },
  {
    name: 'HÉRCULES, EL SEMIDIÓS', weapon: 'club', scale: 1.3, maxHp: 460, morph: 'hero',
    biome: 'inferno', weather: 'ash',
    body: '#c98a54', bodyDark: '#8f5c34', crest: '#8a6a3a', eye: '#ff8a2a', shield: '#c98a54', shieldDark: '#8f5c34', metal: '#8a6a3a',
  },
  {
    name: 'ARES, DIOS DE LA GUERRA', weapon: 'spear', scale: 1.5, maxHp: 560, morph: 'warrior', divine: true,
    biome: 'warzone', weather: null,
    body: '#6e1210', bodyDark: '#2e0705', crest: '#161616', eye: '#ff3300', shield: '#1c0e0c', shieldDark: '#0c0504', metal: '#3a1512',
  },
  {
    name: 'ODÍN, EL PADRE DE TODO', weapon: 'spear', scale: 1.35, maxHp: 620, morph: 'allfather',
    biome: 'aurora', weather: 'snow',
    body: '#4a5a68', bodyDark: '#242e38', crest: '#dfe6ea', eye: '#ffe066', shield: '#5a6a78', shieldDark: '#2e3a42', metal: '#c9d2da',
  },
  {
    // The player's own phalanx boards Poseidón's ship for this fight — see
    // drawOceanScene(), swapped in for the usual floor/scenery while
    // biome === 'ocean' — with sirens singing from the wreckage nearby.
    name: 'POSEIDÓN, DIOS DEL MAR', weapon: 'trident', scale: 1.4, maxHp: 680, morph: 'seagod', divine: true,
    fireColors: ['#4ad1ff', '#eaffff'], fireGlow: '#1a6a9e',
    biome: 'ocean', weather: null,
    body: '#2f6a86', bodyDark: '#163a4a', crest: '#4ad1ff', eye: '#baf0ff', shield: '#1a4a5e', shieldDark: '#0c2a36', metal: '#bfe6f2',
  },
  {
    name: 'CRÁTOS, LA FUERZA ETERNA', weapon: 'chain', scale: 1.45, maxHp: 760, morph: 'enforcer',
    biome: 'shadow', weather: null,
    body: '#3a3630', bodyDark: '#1c1a16', crest: '#8a1414', eye: '#ff3300', shield: '#2a2622', shieldDark: '#141210', metal: '#5a5650',
  },
  {
    // The true final boss: Zeus himself, king of Olympus, wreathed in a
    // real thunderstorm — see BIOME_PALETTES.storm / weather 'rain'.
    name: 'ZEUS, REY DEL OLIMPO', weapon: 'bolt', scale: 1.9, maxHp: 950, morph: 'king', divine: true,
    fireColors: ['#dff0ff', '#fff8c0'], fireGlow: '#aee0ff',
    biome: 'storm', weather: 'rain',
    body: '#e8c874', bodyDark: '#9c7a2e', crest: '#fff8e0', eye: '#fff2a0', shield: '#e8c874', shieldDark: '#9c7a2e', metal: '#fff8e0',
  },
];

// Environment palette swap while a themed boss is active — overrides the
// normal day/night sky/ground colors entirely for the duration of the fight.
const BIOME_PALETTES = {
  petrified: { sky1: '#8a8f96', sky2: '#6b6f75', sky3: '#3f4247', fog: '#7a7e84', sand1: '#9a9a92', sand2: '#6e6e66', mtn1: '#5a5d62', mtn2: '#3a3d42' },
  temporal: { sky1: '#4a3a6b', sky2: '#2a1f45', sky3: '#140d24', fog: '#3a2d5c', sand1: '#4a3f5a', sand2: '#2e2640', mtn1: '#3a2e55', mtn2: '#221a38' },
  blossom: { sky1: '#ffd6e8', sky2: '#ffb6d5', sky3: '#ff8fc0', fog: '#ffe0ee', sand1: '#ffe9d6', sand2: '#f2c9a8', mtn1: '#ffc2dd', mtn2: '#ff9fc8' },
  inferno: { sky1: '#ffb066', sky2: '#e2601f', sky3: '#6e1a08', fog: '#c94a1a', sand1: '#8a3a1a', sand2: '#5a2410', mtn1: '#7a2c10', mtn2: '#4a1a0a' },
  warzone: { sky1: '#7a1c1c', sky2: '#4a0f0f', sky3: '#1c0505', fog: '#5a1414', sand1: '#3a1414', sand2: '#220a0a', mtn1: '#3a1010', mtn2: '#1c0808' },
  aurora: { sky1: '#bfe8e0', sky2: '#5fa0b0', sky3: '#1c2c48', fog: '#8fc8c0', sand1: '#c8d8d0', sand2: '#8aa098', mtn1: '#3a5868', mtn2: '#1c2c40' },
  ocean: { sky1: '#bfe0ff', sky2: '#5fa8d8', sky3: '#144a78', fog: '#7fc0e8', sand1: '#1a4a6a', sand2: '#0e2c42', mtn1: '#2a6088', mtn2: '#123650' },
  shadow: { sky1: '#3a3a42', sky2: '#1e1e26', sky3: '#0a0a10', fog: '#2a2a32', sand1: '#2a2a30', sand2: '#161618', mtn1: '#26262e', mtn2: '#121216' },
  storm: { sky1: '#5a6272', sky2: '#333a48', sky3: '#14161e', fog: '#454c5c', sand1: '#3a3e48', sand2: '#22242c', mtn1: '#2e3440', mtn2: '#181c24' },
};

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
        weaponFavor: Math.max(0, Math.min(WEAPON_FAVORS.length - 1, parsed.weaponFavor | 0)),
        armorFavor: Math.max(0, Math.min(ARMOR_FAVORS.length - 1, parsed.armorFavor | 0)),
      };
    }
  } catch (e) { /* localStorage unavailable, fall back to defaults */ }
  return { bank: 0, weaponTier: 0, armorTier: 0, weaponFavor: 0, armorFavor: 0 };
}
function persistSave() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); } catch (e) { /* ignore */ }
}
const save = loadSave();

// Boss checkpoints along the run — one every 200 units, the last (Zeus) at
// the level's end. Each uses a different BOSS_THEMES entry, in escalating
// order of power.
const bossCheckpoints = BOSS_THEMES.map((theme, i) => ({
  z: i === BOSS_THEMES.length - 1 ? LEVEL_END_Z : -200 * (i + 1),
  theme,
}));

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

// Occasional bird flybys: small flocks that cross the sky at random
// intervals, purely decorative (screen-space, not world-space like the 3D
// engine below) — same trick as clouds/stars.
const birds = [];
let birdTimer = 5 + Math.random() * 8;
function spawnBirdFlock() {
  const dir = Math.random() < 0.5 ? 1 : -1;
  const count = 3 + Math.floor(Math.random() * 4);
  const y = HORIZON_Y * (0.1 + Math.random() * 0.28);
  const speed = (24 + Math.random() * 16) * dir;
  const offsets = [];
  for (let i = 0; i < count; i++) {
    offsets.push({
      dx: -i * 15 * dir + (Math.random() * 6 - 3),
      dy: Math.floor((i + 1) / 2) * 6 * (i % 2 === 0 ? -1 : 1) + (Math.random() * 4 - 2),
      phase: Math.random() * Math.PI * 2,
    });
  }
  birds.push({ dir, y, speed, offsets, x: dir > 0 ? -90 : W + 90, life: 0 });
}
function updateBirds(dt) {
  birdTimer -= dt;
  if (birdTimer <= 0) {
    spawnBirdFlock();
    birdTimer = 14 + Math.random() * 18;
  }
  for (let i = birds.length - 1; i >= 0; i--) {
    const f = birds[i];
    f.x += f.speed * dt;
    f.life += dt;
    if ((f.dir > 0 && f.x > W + 100) || (f.dir < 0 && f.x < -100)) birds.splice(i, 1);
  }
}
function drawBirds(dayT) {
  if (!birds.length) return;
  ctx.save();
  ctx.strokeStyle = dayT > 0.55 ? 'rgba(220,226,240,0.7)' : 'rgba(20,16,12,0.6)';
  ctx.lineWidth = 1.6;
  ctx.lineCap = 'round';
  for (const f of birds) {
    ctx.globalAlpha = Math.max(0, Math.min(1, f.life * 2));
    for (const o of f.offsets) {
      const bx = f.x + o.dx;
      const by = f.y + o.dy;
      const flap = 0.35 + 0.65 * Math.abs(Math.sin(atmosphereT * 9 + o.phase));
      const s = 6;
      ctx.beginPath();
      ctx.moveTo(bx - s, by - flap * s * 0.7);
      ctx.quadraticCurveTo(bx - s * 0.35, by - flap * s * 1.2, bx, by);
      ctx.quadraticCurveTo(bx + s * 0.35, by - flap * s * 1.2, bx + s, by - flap * s * 0.7);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function drawBackground() {
  const dayT = computeDayT(player.z);
  let sky1 = lerpColor(COL.sky1, NIGHT.sky1, dayT);
  let sky2 = lerpColor(COL.sky2, NIGHT.sky2, dayT);
  let sky3 = lerpColor(COL.sky3, NIGHT.sky3, dayT);
  let fog = lerpColor(COL.fog, NIGHT.fog, dayT);
  let sand1 = lerpColor(COL.sand1, NIGHT.sand1, dayT);
  let sand2 = lerpColor(COL.sand2, NIGHT.sand2, dayT);
  let mtn1 = lerpColor('#a9c3dd', NIGHT.mtn1, dayT);
  let mtn2 = lerpColor('#8fb3d6', NIGHT.mtn2, dayT);

  // A boss with its own biome (Medusa's petrified grey, Zeus's storm...)
  // overrides the normal day/night palette entirely, blending in fast as
  // the fight starts so the arrival reads as a real environment change.
  const biome = (state.mode === 'boss' && boss && boss.theme.biome) ? BIOME_PALETTES[boss.theme.biome] : null;
  if (biome) {
    const bt = Math.min(1, boss.spawnT / 1.0);
    sky1 = lerpColor(sky1, biome.sky1, bt);
    sky2 = lerpColor(sky2, biome.sky2, bt);
    sky3 = lerpColor(sky3, biome.sky3, bt);
    fog = lerpColor(fog, biome.fog, bt);
    sand1 = lerpColor(sand1, biome.sand1, bt);
    sand2 = lerpColor(sand2, biome.sand2, bt);
    mtn1 = lerpColor(mtn1, biome.mtn1, bt);
    mtn2 = lerpColor(mtn2, biome.mtn2, bt);
  }

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

  drawBirds(dayT);

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

  // legs — a real alternating running stride (not just a static kilt),
  // the single biggest thing that makes a runner look alive
  const hipY = 0.26 * S;
  const legHalf = [0.095 * S, 0.15 * S, 0.1 * S];
  [-1, 1].forEach((side, i) => {
    const phase = i === 0 ? 0 : Math.PI;
    const swing = Math.sin(bobT + phase) * 0.8;
    const hip = [side * 0.14 * S, hipY, 0];
    const legRot = { axis: 'x', angle: swing, pivot: hip };
    parts.push({ center: [hip[0], hipY - legHalf[1], hip[2]], half: legHalf, color: variant.skinDark, rot: legRot });
    // a sandal strap band at the ankle, riding with the leg's own swing
    parts.push({ center: [hip[0], hipY - legHalf[1] * 1.9, hip[2]], half: [legHalf[0] * 1.05, 0.035 * S, legHalf[2] * 1.05], color: metalDark, rot: legRot });
  });

  const kiltHalf = [0.27 * S, 0.16 * S, 0.22 * S];
  parts.push({ center: [0, hipY + kiltHalf[1], 0], half: kiltHalf, color: variant.skinDark });

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

  // shield, slung past the shoulder so it reads as its own round shape
  // instead of hiding directly behind the torso/cape
  const shieldCenter = [-0.46 * S, torsoCenterY + 0.02 * S, torsoHalf[2] * 0.5];
  const shieldNormal = [-0.55, 0.05, 0.83];
  parts.push({
    kind: 'disc', center: shieldCenter, normalAxis: shieldNormal, radius: 0.4 * S, segments: 10, color: metal,
  });

  // a spear slung across the back, its head rising past the shoulder
  const spearBase = [0.32 * S, 0.42 * S, torsoHalf[2] * 0.6];
  const spearRot = { axis: 'x', angle: -0.18, pivot: spearBase };
  parts.push({ center: [spearBase[0], spearBase[1] + 0.75 * S, spearBase[2]], half: [0.035 * S, 0.75 * S, 0.035 * S], color: SPEAR_WOOD, rot: spearRot });
  parts.push({ center: [spearBase[0], spearBase[1] + 1.62 * S, spearBase[2]], half: [0.06 * S, 0.16 * S, 0.03 * S], color: metal, rot: spearRot });
  parts.push({ center: [spearBase[0], spearBase[1] + 0.2 * S, spearBase[2]], half: [0.05 * S, 0.1 * S, 0.05 * S], color: SPEAR_WOOD_DARK, rot: spearRot });

  // a free arm swinging opposite the near-side leg, for a natural running
  // counter-swing (the other arm is busy carrying the spear)
  const shoulderFree = [-0.32 * S, torsoCenterY + 0.22 * S, 0.02 * S];
  const armHalf = [0.075 * S, 0.24 * S, 0.075 * S];
  const armSwing = Math.sin(bobT + Math.PI) * 0.45;
  parts.push({
    center: [shoulderFree[0], shoulderFree[1] - armHalf[1], shoulderFree[2]], half: armHalf, color: variant.skin,
    rot: { axis: 'x', angle: armSwing, pivot: shoulderFree },
  });

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
      [0.26 * S + sway, hipY * 0.7, capeZ + billow],
      [-0.26 * S + sway, hipY * 0.7, capeZ + billow],
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

    // Act 4: boss 3 (Afrodita) -> Hércules (z -800)
    { type: 'gate', z: -630, op: 'x2' },
    { type: 'enemy', z: -655, lanes: [0, 1, 2], count: 12, etype: 'minimo' },
    { type: 'coins', z: -670, lanes: [0, 1, 2] },
    { type: 'gate', z: -690, op: 'x3' },
    { type: 'enemy', z: -715, lanes: [0, 1], count: 22, etype: 'elite' },
    { type: 'coins', z: -730, lanes: [0, 1, 2] },
    { type: 'gate', z: -745, op: '+5' },
    { type: 'enemy', z: -765, lanes: [0, 1, 2], count: 28, etype: 'elite' },
  ];

  // Acts 5-9: boss 4 (Hércules) all the way to Zeus (z -1800), each act
  // scaled up from the act-4 pattern so the run keeps escalating after the
  // hand-authored early acts above.
  const laterBossZs = [-800, -1000, -1200, -1400, -1600];
  const mults = [1.2, 1.4, 1.65, 1.9, 2.2];
  laterBossZs.forEach((baseZ, i) => {
    const m = mults[i];
    defs.push(
      { type: 'gate', z: baseZ - 30, op: 'x2' },
      { type: 'enemy', z: baseZ - 55, lanes: [0, 1, 2], count: Math.round(12 * m), etype: 'minimo' },
      { type: 'coins', z: baseZ - 70, lanes: [0, 1, 2] },
      { type: 'gate', z: baseZ - 90, op: 'x3' },
      { type: 'enemy', z: baseZ - 115, lanes: [0, 1], count: Math.round(22 * m), etype: 'elite' },
      { type: 'coins', z: baseZ - 130, lanes: [0, 1, 2] },
      { type: 'gate', z: baseZ - 145, op: '+5' },
      { type: 'enemy', z: baseZ - 165, lanes: [0, 1, 2], count: Math.round(28 * m), etype: 'elite' },
    );
  });

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
  const morph = theme.morph || 'warrior';
  const parts = [];
  const legTop = 1.5 * S;

  if (morph === 'gorgon') {
    // Medusa: a coiling serpent tail instead of legs, tapering thin at the
    // ground and thick near the torso, swaying independently of any stride.
    const segCount = 4;
    const segFullH = legTop / segCount;
    for (let i = 0; i < segCount; i++) {
      const t = i / (segCount - 1);
      const segHalfH = segFullH / 2;
      const segY = segFullH * i + segHalfH;
      const width = (0.16 + t * 0.2) * S;
      const depth = (0.14 + t * 0.16) * S;
      const sway = Math.sin(shakeT * 2.2 + i * 0.9) * 0.16 * S * (1 - t * 0.5);
      parts.push({ center: [sway, segY, 0], half: [width, segHalfH, depth], color: i % 2 === 0 ? theme.body : theme.bodyDark });
    }
  } else {
    const legHalf = [0.22 * S, 0.75 * S, 0.24 * S];
    const legY = 0.75 * S;
    parts.push({ center: [-0.42 * S, legY, 0], half: legHalf, color: theme.bodyDark });
    parts.push({ center: [0.42 * S, legY, 0], half: legHalf, color: theme.bodyDark });
  }

  let torsoHalf = [1.05 * S, 0.85 * S, 0.55 * S];
  if (morph === 'goddess') torsoHalf = [0.85 * S, 0.8 * S, 0.48 * S];
  else if (morph === 'hero' || morph === 'enforcer') torsoHalf = [1.22 * S, 0.88 * S, 0.6 * S];
  else if (morph === 'king') torsoHalf = [1.15 * S, 0.9 * S, 0.58 * S];
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
  } else if (theme.weapon === 'spear' || theme.weapon === 'trident') {
    parts.push({ center: [tip[0], tip[1] - 0.9 * S, tip[2]], half: [0.06 * S, 0.9 * S, 0.06 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 1.35 * S, tip[2]], half: [0.2 * S, 0.06 * S, 0.06 * S], color: theme.bodyDark, rot: armRot });
    if (theme.weapon === 'trident') {
      parts.push({ center: [tip[0], tip[1] - 2.1 * S, tip[2]], half: [0.05 * S, 0.35 * S, 0.05 * S], color: theme.metal, rot: armRot });
      parts.push({ center: [tip[0] - 0.22 * S, tip[1] - 1.95 * S, tip[2]], half: [0.045 * S, 0.3 * S, 0.045 * S], color: theme.metal, rot: armRot });
      parts.push({ center: [tip[0] + 0.22 * S, tip[1] - 1.95 * S, tip[2]], half: [0.045 * S, 0.3 * S, 0.045 * S], color: theme.metal, rot: armRot });
      weaponFireAt = { local: [tip[0], tip[1] - 2.3 * S, tip[2]], rot: armRot };
    } else {
      parts.push({ center: [tip[0], tip[1] - 1.75 * S, tip[2]], half: [0.14 * S, 0.28 * S, 0.05 * S], color: theme.metal, rot: armRot });
      weaponFireAt = { local: [tip[0], tip[1] - 2.0 * S, tip[2]], rot: armRot };
    }
  } else if (theme.weapon === 'scythe') {
    parts.push({ center: [tip[0], tip[1] - 0.9 * S, tip[2]], half: [0.05 * S, 0.9 * S, 0.05 * S], color: theme.bodyDark, rot: armRot });
    parts.push({ center: [tip[0] + 0.32 * S, tip[1] - 1.85 * S, tip[2]], half: [0.34 * S, 0.16 * S, 0.05 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0] + 0.55 * S, tip[1] - 2.05 * S, tip[2]], half: [0.16 * S, 0.28 * S, 0.05 * S], color: theme.metal, rot: armRot });
    weaponFireAt = { local: [tip[0] + 0.4 * S, tip[1] - 2.0 * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'club') {
    parts.push({ center: [tip[0], tip[1] - 0.4 * S, tip[2]], half: [0.16 * S, 0.4 * S, 0.16 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 0.95 * S, tip[2]], half: [0.32 * S, 0.32 * S, 0.32 * S], color: theme.metal, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 1.1 * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'scepter') {
    parts.push({ center: [tip[0], tip[1] - 0.75 * S, tip[2]], half: [0.045 * S, 0.75 * S, 0.045 * S], color: theme.metal, rot: armRot });
    parts.push({ kind: 'disc', center: [tip[0], tip[1] - 1.55 * S, tip[2]], normalAxis: [0, 0.3, 1], radius: 0.18 * S, segments: 8, color: theme.eye, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 1.7 * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'chain') {
    const linkCount = 5;
    for (let i = 0; i < linkCount; i++) {
      const sway = Math.sin(shakeT * 5 + i * 0.9) * (0.05 + i * 0.03) * S;
      parts.push({ center: [tip[0] + sway, tip[1] - (0.3 + i * 0.32) * S, tip[2]], half: [0.1 * S, 0.14 * S, 0.1 * S], color: i % 2 === 0 ? theme.metal : theme.bodyDark, rot: armRot });
    }
    weaponFireAt = { local: [tip[0], tip[1] - (0.3 + (linkCount - 1) * 0.32) * S, tip[2]], rot: armRot };
  } else if (theme.weapon === 'bolt') {
    const zigs = [0, 0.22, -0.18, 0.24, 0];
    for (let i = 0; i < zigs.length; i++) {
      const segY = tip[1] - (0.35 + i * 0.4) * S;
      parts.push({ center: [tip[0] + zigs[i] * S, segY, tip[2]], half: [0.1 * S, 0.24 * S, 0.08 * S], color: theme.metal, rot: armRot });
    }
    weaponFireAt = { local: [tip[0] + zigs[zigs.length - 1] * S, tip[1] - (0.35 + (zigs.length - 1) * 0.4) * S, tip[2]], rot: armRot };
  } else { // sword
    parts.push({ center: [tip[0], tip[1] - 0.55 * S, tip[2]], half: [0.09 * S, 0.55 * S, 0.05 * S], color: theme.metal, rot: armRot });
    parts.push({ center: [tip[0], tip[1] - 0.08 * S, tip[2]], half: [0.26 * S, 0.06 * S, 0.1 * S], color: theme.bodyDark, rot: armRot });
    weaponFireAt = { local: [tip[0], tip[1] - 1.05 * S, tip[2]], rot: armRot };
  }

  // Torso
  parts.push({ center: [0, torsoCenterY, 0], half: torsoHalf, color: theme.body });

  // Head, with per-morph decorations replacing the default Corinthian
  // helmet crest — snake hair, a titan's hood, a goddess's flowing locks,
  // a lion pelt, Odín's hat/beard/raven, a coral crown, a spiked helm and
  // chains, or a king's lightning-spike crown.
  const headHalf = [0.34 * S, 0.32 * S, 0.34 * S];
  const headCenterY = torsoTop + headHalf[1] + 0.08 * S;
  parts.push({ center: [0, headCenterY, 0], half: headHalf, color: theme.body });

  if (morph === 'gorgon') {
    const n = 7;
    for (let i = 0; i < n; i++) {
      const ang = (i / (n - 1) - 0.5) * 2.6;
      const wave = Math.sin(shakeT * 3 + i * 1.3) * 0.25;
      const len = 0.36 * S;
      const dx = Math.sin(ang) * len * 0.6;
      const dz = Math.cos(ang) * len * 0.5 - headHalf[2] * 0.2;
      parts.push({
        center: [dx, headCenterY + headHalf[1] + 0.05 * S, dz], half: [0.045 * S, len * 0.5, 0.045 * S],
        color: i % 2 === 0 ? '#5a7a3e' : '#3f5c2a',
        rot: { axis: 'x', angle: 1.15 + wave * 0.4, pivot: [dx, headCenterY + headHalf[1], dz] },
      });
    }
  } else if (morph === 'titan') {
    parts.push({ center: [0, headCenterY + headHalf[1] * 0.7, -0.05 * S], half: [0.46 * S, 0.22 * S, 0.5 * S], color: theme.bodyDark });
    parts.push({ kind: 'disc', center: [0, legTop + 0.1 * S, torsoHalf[2] + 0.12 * S], normalAxis: [0, 0.2, 1], radius: 0.22 * S, segments: 8, color: theme.crest, rot: null });
    parts.push({ center: [0, headCenterY - headHalf[1] - 0.14 * S, headHalf[2] * 0.5], half: [0.14 * S, 0.18 * S, 0.1 * S], color: '#9a978a' });
  } else if (morph === 'goddess') {
    parts.push({ center: [0, headCenterY - 0.04 * S, -headHalf[2] * 0.9], half: [0.3 * S, 0.5 * S, 0.22 * S], color: theme.crest });
    parts.push({ kind: 'disc', center: [0, headCenterY + headHalf[1] + 0.3 * S, 0], normalAxis: [0, 1, 0.2], radius: 0.14 * S, segments: 8, color: theme.eye, rot: null });
  } else if (morph === 'hero') {
    parts.push({ center: [0, headCenterY + headHalf[1] * 0.5, -0.08 * S], half: [0.44 * S, 0.34 * S, 0.4 * S], color: theme.crest });
    parts.push({ center: [0, torsoCenterY + 0.1 * S, -torsoHalf[2] - 0.12 * S], half: [0.5 * S, 0.55 * S, 0.14 * S], color: theme.crest });
  } else if (morph === 'allfather') {
    parts.push({ kind: 'disc', center: [0, headCenterY + headHalf[1] + 0.02 * S, 0], normalAxis: [0, 1, 0], radius: 0.5 * S, segments: 10, color: theme.bodyDark, rot: null });
    parts.push({ center: [0, headCenterY - headHalf[1] - 0.16 * S, headHalf[2] * 0.5], half: [0.16 * S, 0.2 * S, 0.12 * S], color: theme.metal });
    parts.push({ center: [-1.0 * S, torsoTop + 0.05 * S, 0.15 * S], half: [0.12 * S, 0.1 * S, 0.18 * S], color: '#1c1c1c' });
  } else if (morph === 'seagod') {
    for (let i = -1; i <= 1; i++) {
      parts.push({ center: [i * 0.16 * S, headCenterY + headHalf[1] + 0.14 * S, 0], half: [0.05 * S, 0.14 * S, 0.05 * S], color: theme.crest });
    }
    parts.push({ center: [0, headCenterY - headHalf[1] - 0.14 * S, headHalf[2] * 0.5], half: [0.16 * S, 0.18 * S, 0.12 * S], color: '#dfe9ec' });
  } else if (morph === 'enforcer') {
    parts.push({ center: [0, headCenterY + headHalf[1] + 0.05 * S, 0], half: [0.3 * S, 0.08 * S, 0.3 * S], color: theme.crest });
    parts.push({ center: [-0.18 * S, headCenterY + headHalf[1] + 0.14 * S, 0], half: [0.04 * S, 0.1 * S, 0.04 * S], color: theme.metal });
    parts.push({ center: [0.18 * S, headCenterY + headHalf[1] + 0.14 * S, 0], half: [0.04 * S, 0.1 * S, 0.04 * S], color: theme.metal });
    parts.push({ center: [0, torsoCenterY, torsoHalf[2] + 0.03 * S], half: [torsoHalf[0] * 0.9, 0.05 * S, 0.03 * S], color: theme.metal, rot: { axis: 'z', angle: 0.5, pivot: [0, torsoCenterY, torsoHalf[2] + 0.03 * S] } });
    parts.push({ center: [0, torsoCenterY, torsoHalf[2] + 0.03 * S], half: [torsoHalf[0] * 0.9, 0.05 * S, 0.03 * S], color: theme.metal, rot: { axis: 'z', angle: -0.5, pivot: [0, torsoCenterY, torsoHalf[2] + 0.03 * S] } });
  } else if (morph === 'king') {
    for (let i = -2; i <= 2; i++) {
      const h = (0.16 - Math.abs(i) * 0.03) * S;
      parts.push({ center: [i * 0.13 * S, headCenterY + headHalf[1] + h * 0.5 + 0.04 * S, 0], half: [0.035 * S, h * 0.5, 0.035 * S], color: theme.crest });
    }
    parts.push({ center: [0, headCenterY - headHalf[1] - 0.14 * S, headHalf[2] * 0.5], half: [0.18 * S, 0.2 * S, 0.13 * S], color: '#f5f0e0' });
  } else {
    // warrior (Ares) / default: the classic Corinthian helmet crest
    parts.push({
      center: [0, headCenterY + headHalf[1] + 0.16 * S, -0.02 * S], half: [0.42 * S, 0.16 * S, 0.58 * S], color: theme.crest,
      rot: { axis: 'x', angle: -0.3, pivot: [0, headCenterY + headHalf[1], 0] },
    });
  }
  if (morph !== 'gorgon') {
    parts.push({ center: [0, headCenterY - 0.02 * S, headHalf[2] * 0.7], half: [0.06 * S, 0.26 * S, 0.05 * S], color: theme.bodyDark });
  }

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

  // divine elemental flourish wreathing the weapon — fire for Ares, electric
  // arcs for Zeus, sea-spray for Poseidón (theme.fireColors/fireGlow pick
  // the palette; default stays the original orange flame).
  if (theme.divine && rig.weaponFireAt) {
    const { local, rot } = rig.weaponFireAt;
    const rotated = rot ? rotateAroundPivot(local, rot.pivot, rot.axis, rot.angle) : local;
    const fireProj = project(rotated[0] + actor.x, rotated[1] + actor.y, rotated[2] + actor.z);
    const fc = theme.fireColors || ['#ff5a1a', '#ffcf4a'];
    const fg = theme.fireGlow || '#ff3300';
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
        ctx.fillStyle = i % 2 === 0 ? fc[0] : fc[1];
        ctx.shadowColor = fg;
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

  // glowing eyes + damage cracks/ichor glow, as a 2D overlay on the head/torso.
  // Odín (allfather) only has one eye — the other is hidden beneath his hat.
  const eyeProj = project(actor.x, rig.headCenterY, actor.z + 0.34 * theme.scale * 0.7);
  if (eyeProj.ok) {
    const es = eyeProj.scale * theme.scale;
    ctx.save();
    ctx.globalAlpha = fog;
    ctx.fillStyle = theme.eye;
    ctx.shadowColor = theme.eye;
    ctx.shadowBlur = 14;
    if (theme.morph === 'allfather') {
      ctx.beginPath(); ctx.ellipse(eyeProj.sx - 0.13 * es, eyeProj.sy, 0.065 * es, 0.05 * es, 0, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.beginPath(); ctx.ellipse(eyeProj.sx - 0.13 * es, eyeProj.sy, 0.055 * es, 0.04 * es, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(eyeProj.sx + 0.13 * es, eyeProj.sy, 0.055 * es, 0.04 * es, 0, 0, Math.PI * 2); ctx.fill();
    }
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
  const rawDps = (14 + player.count * 4) * effectiveWeaponPower();
  // Once the squad hits its 999 cap (a couple of acts in), raw dps would
  // one-shot every later boss — capping it to a ~2.6s-minimum fight means
  // the player actually gets to see each god's morphology/biome before it
  // dies, instead of it vanishing the instant it spawns.
  const dps = Math.min(rawDps, boss.maxHp / 2.6);
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

// ---------- Boss weather: rain/snow/petals/ash tied to the active boss's
// theme.weather, screen-space particles (not world-projected) so they read
// as an atmosphere overlay rather than props in the 3D scene.
const weatherParticles = [];
let weatherSpawnTimer = 0;
function updateWeather(dt) {
  const type = boss && boss.alive && boss.theme.weather;
  if (type) {
    weatherSpawnTimer -= dt;
    if (weatherSpawnTimer <= 0) {
      weatherSpawnTimer = type === 'rain' ? 0.02 : 0.09;
      const fall = type === 'rain' ? 480 + Math.random() * 140 : type === 'snow' ? 35 + Math.random() * 25 : type === 'ash' ? -(45 + Math.random() * 35) : 28 + Math.random() * 22;
      weatherParticles.push({
        type, x: Math.random() * W, y: type === 'ash' ? H * (0.5 + Math.random() * 0.5) : -10 - Math.random() * 30,
        speed: fall, drift: (Math.random() - 0.5) * (type === 'rain' ? 20 : 36),
        size: type === 'snow' ? 1.4 + Math.random() * 2 : type === 'petals' ? 3 + Math.random() * 3 : type === 'ash' ? 1.6 + Math.random() * 2.2 : 0,
        len: type === 'rain' ? 13 + Math.random() * 9 : 0, phase: Math.random() * Math.PI * 2,
      });
    }
  }
  for (let i = weatherParticles.length - 1; i >= 0; i--) {
    const p = weatherParticles[i];
    p.y += p.speed * dt;
    p.x += (p.drift + Math.sin(atmosphereT * 2 + p.phase) * 8) * dt;
    if (p.y > H + 20 || p.y < -60 || p.x < -40 || p.x > W + 40) weatherParticles.splice(i, 1);
  }
}
function drawWeather() {
  if (!weatherParticles.length) return;
  ctx.save();
  for (const p of weatherParticles) {
    if (p.type === 'rain') {
      ctx.strokeStyle = 'rgba(210,225,255,0.55)';
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - p.drift * 0.02, p.y + p.len);
      ctx.stroke();
    } else if (p.type === 'snow') {
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fill();
    } else if (p.type === 'petals') {
      ctx.fillStyle = 'rgba(255,175,205,0.85)';
      ctx.beginPath(); ctx.ellipse(p.x, p.y, p.size, p.size * 0.6, atmosphereT + p.phase, 0, Math.PI * 2); ctx.fill();
    } else if (p.type === 'ash') {
      ctx.fillStyle = 'rgba(255,150,60,0.6)';
      ctx.shadowColor = '#ff5a1a';
      ctx.shadowBlur = 4;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
    }
  }
  ctx.restore();
}

// ---------- Poseidón's ship scene: swapped in for the mosaic floor + temple
// scenery while biome === 'ocean' — a wooden deck, a mast/sail, animated
// wave highlights, and a couple of sirens singing from the wreckage.
function drawWaterWaves() {
  ctx.save();
  ctx.globalAlpha = 0.25;
  ctx.strokeStyle = 'rgba(255,255,255,0.5)';
  ctx.lineWidth = 1.5;
  for (let i = 0; i < 5; i++) {
    const wy = HORIZON_Y + (H - HORIZON_Y) * (0.15 + i * 0.18);
    ctx.beginPath();
    for (let x = 0; x <= W; x += 20) {
      const yy = wy + Math.sin(x * 0.05 + atmosphereT * 2 + i) * 3;
      if (x === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
    }
    ctx.stroke();
  }
  ctx.restore();
}
function drawShipDeck() {
  if (!boss) return;
  const nearZ = Math.min(player.z + 3, boss.z + 18);
  const farZ = boss.z - 3;
  const hw = 6.2;
  const nl = project(-hw, 0.02, nearZ), nr = project(hw, 0.02, nearZ);
  const fl = project(-hw, 0.02, farZ), fr = project(hw, 0.02, farZ);
  if (!nl.ok || !nr.ok || !fl.ok || !fr.ok) return;
  ctx.save();
  const grad = ctx.createLinearGradient(0, fl.sy, 0, nl.sy);
  grad.addColorStop(0, '#6b4a2c');
  grad.addColorStop(1, '#4a3018');
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(nl.sx, nl.sy); ctx.lineTo(fl.sx, fl.sy); ctx.lineTo(fr.sx, fr.sy); ctx.lineTo(nr.sx, nr.sy);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(40,24,10,0.35)';
  ctx.lineWidth = 1;
  for (let k = 1; k < 6; k++) {
    const t = k / 6;
    const a = project(-hw, 0.02, nearZ + (farZ - nearZ) * t);
    const b = project(hw, 0.02, nearZ + (farZ - nearZ) * t);
    if (a.ok && b.ok) { ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke(); }
  }
  ctx.restore();

  const mastZ = farZ - 1;
  const mastBase = project(0, 0.02, mastZ);
  const mastTop = project(0, 9, mastZ);
  if (mastBase.ok && mastTop.ok) {
    ctx.save();
    ctx.strokeStyle = '#3a2814';
    ctx.lineWidth = Math.max(2, mastBase.scale * 0.05);
    ctx.beginPath(); ctx.moveTo(mastBase.sx, mastBase.sy); ctx.lineTo(mastTop.sx, mastTop.sy); ctx.stroke();
    const sailTop = project(0, 8.4, mastZ);
    const sailBotFar = project(1.1, 4.2, mastZ);
    const sailBotNear = project(0, 4.2, mastZ);
    if (sailTop.ok && sailBotFar.ok && sailBotNear.ok) {
      ctx.fillStyle = 'rgba(230,222,200,0.85)';
      ctx.beginPath();
      ctx.moveTo(sailTop.sx, sailTop.sy);
      ctx.lineTo(sailBotFar.sx, sailBotFar.sy);
      ctx.lineTo(sailBotNear.sx, sailBotNear.sy);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
}
function buildSirenParts(seed) {
  const S = 0.85;
  const flick = Math.sin(atmosphereT * 2.4 + seed) * 0.35;
  return [
    { center: [0, 0.22 * S, 0], half: [0.22 * S, 0.22 * S, 0.5 * S], color: '#2f8a7a' },
    { center: [0, 0.22 * S, -0.55 * S], half: [0.16 * S, 0.16 * S, 0.35 * S], color: '#256e60', rot: { axis: 'x', angle: flick, pivot: [0, 0.22 * S, -0.2 * S] } },
    { center: [0, 0.22 * S, -1.0 * S], half: [0.32 * S, 0.05 * S, 0.16 * S], color: '#3fae9a', rot: { axis: 'x', angle: flick, pivot: [0, 0.22 * S, -0.2 * S] } },
    { center: [0, 0.62 * S, 0.15 * S], half: [0.24 * S, 0.32 * S, 0.2 * S], color: '#e8b090' },
    { center: [0, 0.95 * S, 0.05 * S], half: [0.2 * S, 0.22 * S, 0.22 * S], color: '#3a2a1e' },
    { center: [0, 0.98 * S, 0.22 * S], half: [0.15 * S, 0.15 * S, 0.15 * S], color: '#e8b090' },
  ];
}
function drawSirens() {
  if (!boss) return;
  const seeds = [11, 47];
  [-1, 1].forEach((side, i) => {
    const wx = side * 6.2;
    const wz = boss.z + 3.5 + i * 1.5;
    const proj = project(wx, 0, wz);
    if (!proj.ok || proj.depth > FAR_CLIP || proj.depth < 0) return;
    ctx.globalAlpha = fogFactor(proj.depth);
    ctx.fillStyle = '#4a4a48';
    ctx.beginPath(); ctx.ellipse(proj.sx, proj.sy, 0.5 * proj.scale, 0.22 * proj.scale, 0, 0, Math.PI * 2); ctx.fill();
    drawActor3D({ x: wx, y: 0, z: wz }, buildSirenParts(seeds[i]), { outline: true });
    ctx.globalAlpha = 1;
  });
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
  weaponFavorList: document.getElementById('weaponFavorList'),
  armorFavorList: document.getElementById('armorFavorList'),
  armoryTabs: document.getElementById('armoryTabs'),
  armoryPanels: document.getElementById('armoryPanels'),
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

// ---------- Armory (dynamic upgrade shop) ----------
// One generic row renderer shared by weapon tiers, armor tiers, and both
// Favor tracks — each is just "a sequential list you own up to index N".
function renderShopList(container, tiers, currentTierKey, onBuy) {
  container.innerHTML = '';
  const currentTier = save[currentTierKey];
  tiers.forEach((tier, i) => {
    const row = document.createElement('div');
    row.className = 'shopRow';
    row.style.borderLeft = `4px solid ${tier.rarity || 'rgba(230,190,90,0.4)'}`;
    const owned = i <= currentTier;
    const isNext = i === currentTier + 1;
    let actionHtml;
    if (owned) {
      actionHtml = i === currentTier ? '<span class="shopStatus equipped">EQUIPADO</span>' : '<span class="shopStatus">poseído</span>';
    } else if (isNext) {
      const affordable = save.bank >= tier.cost;
      actionHtml = `<button class="shopBuy" data-idx="${i}" ${affordable ? '' : 'disabled'}>${tier.cost} 🪙</button>`;
    } else {
      actionHtml = '<span class="shopStatus locked">🔒</span>';
    }
    row.innerHTML = `<div class="shopInfo"><div class="shopName">${tier.name}</div><div class="shopStat">${tier.statText}</div></div>${actionHtml}`;
    container.appendChild(row);
  });
  container.querySelectorAll('.shopBuy').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx, 10);
      onBuy(idx);
    });
  });
}

function buySequential(tiers, currentTierKey, idx) {
  const tier = tiers[idx];
  if (save.bank < tier.cost || idx !== save[currentTierKey] + 1) return;
  save.bank -= tier.cost;
  save[currentTierKey] = idx;
  persistSave();
  AudioFX.coin();
  renderArmory();
}

function renderArmory() {
  updateBankDisplays();
  renderShopList(els.weaponList, WEAPON_TIERS, 'weaponTier', (idx) => buySequential(WEAPON_TIERS, 'weaponTier', idx));
  renderShopList(els.armorList, ARMOR_TIERS, 'armorTier', (idx) => buySequential(ARMOR_TIERS, 'armorTier', idx));
  renderShopList(els.weaponFavorList, WEAPON_FAVORS, 'weaponFavor', (idx) => buySequential(WEAPON_FAVORS, 'weaponFavor', idx));
  renderShopList(els.armorFavorList, ARMOR_FAVORS, 'armorFavor', (idx) => buySequential(ARMOR_FAVORS, 'armorFavor', idx));
}

// Dynamic menu: three tabs (Armas / Escudos / Favores) share one screen and
// swap which panel is visible instead of stacking every list at once — the
// roster is now 10+10+4+4 rows deep, too much to show all together.
function showArmoryTab(tab) {
  els.armoryTabs.querySelectorAll('.armoryTab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  els.armoryPanels.querySelectorAll('.armoryPanel').forEach(panel => {
    panel.classList.toggle('active', panel.dataset.panel === tab);
  });
}
els.armoryTabs.querySelectorAll('.armoryTab').forEach(btn => {
  btn.addEventListener('click', () => showArmoryTab(btn.dataset.tab));
});

document.getElementById('btnArmory').addEventListener('click', () => {
  renderArmory();
  showArmoryTab('weapons');
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
        const etype = ENEMY_TYPES[o.etype] || ENEMY_TYPES.raso;
        const armorDef = effectiveArmorDefense();
        const effPlayer = player.count * effectiveWeaponPower();
        const effEnemy = o.count * etype.power * (1 - armorDef);
        if (effPlayer > effEnemy) {
          const losses = Math.max(1, Math.round(o.count * (1 - armorDef * 0.5)));
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
  updateBirds(dt);
  updateWeather(dt);
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
  const onShip = state.mode === 'boss' && boss && boss.theme.biome === 'ocean';
  if (onShip) {
    drawWaterWaves();
    drawShipDeck();
    drawSirens();
  } else {
    drawMosaicFloor();
    drawLaneLines();
    // static scenery: draw far-to-near (scenery sorted ascending by z already; z more negative = farther)
    for (let i = 0; i < scenery.length; i++) drawSceneryPiece(scenery[i]);
  }

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
  drawWeather();
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

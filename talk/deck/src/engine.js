/* Motore 3D minimale su Canvas 2D (nessuna libreria: il deck gira offline).
 *
 * "AI Traffic Control": UN solo insieme di frammenti che si trasforma da una
 * formazione all'altra (cabina → biglietto → torre → globo → volano → pista).
 * Il 3D è SEMANTICO: le rotte hanno uno stato (aperta / chiusa, con motivo) e
 * i pacchetti si comportano come le richieste vere — un dato sensibile sbatte
 * contro la pista cloud chiusa e ripiega sul locale, un timeout torna indietro,
 * il RAG entra nel globo, le tracce orbitano nel volano.
 */
'use strict';

const ROUTE_COLOR = { local: '#199e70', cloud: '#d95926', local_rag: '#3987e5', alert: '#d03b3b' };

const Engine = (() => {
  const N = 1400;
  const cv = document.getElementById('stage');
  const ctx = cv.getContext('2d');
  let W = 0, H = 0, DPR = 1;

  // ---------- rng deterministico ----------
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const R = Array.from({ length: N }, rnd);          // un numero stabile per particella
  const R2 = Array.from({ length: N }, rnd);

  // ---------- formazioni: N punti 3D ----------
  const F = {};
  const fill = fn => { const a = new Float32Array(N * 3); for (let i = 0; i < N; i++) { const p = fn(i); a[i * 3] = p[0]; a[i * 3 + 1] = p[1]; a[i * 3 + 2] = p[2]; } return a; };

  // nuvole viste dal finestrino: un tubo di particelle che scorre (animato in step())
  F.cabin = fill(i => { const r = 0.6 + 2.4 * R[i], a = R2[i] * Math.PI * 2; return [Math.cos(a) * r * 1.6, Math.sin(a) * r * 0.55 - 0.2, -6 + 12 * ((i * 0.618) % 1)]; });

  // biglietto: un cartoncino rettangolare di fronte alla camera, con la linea della matrice
  F.pass = fill(i => {
    const w = 3.6, h = 1.45, k = i % 10;
    if (k < 5) {                                                   // bordo
      const t = R[i] * 2 * (w + h);
      return t < w ? [-w / 2 + t, h / 2, 0] : t < w + h ? [w / 2, h / 2 - (t - w), 0]
        : t < 2 * w + h ? [w / 2 - (t - w - h), -h / 2, 0] : [-w / 2, -h / 2 + (t - 2 * w - h), 0];
    }
    if (k < 7) return [w * 0.18, -h / 2 + R[i] * h, 0];             // perforazione della matrice
    return [-w / 2 + R[i] * w, -h / 2 + R2[i] * h, (R[(i + 5) % N] - 0.5) * 0.04];
  });

  // piazzale: griglia a terra + due piste + terminal
  F.airport = fill(i => {
    const k = i % 10;
    if (k < 5) { const gx = (i * 7) % 40, gz = Math.floor(i / 40) % 35; return [(gx - 20) * 0.11, -1, (gz - 17) * 0.11]; }
    if (k < 8) { const t = R[i] * 4.4 - 2.2, side = k === 5 ? -0.35 : k === 6 ? -0.25 : 0.9; return [t, -1, side]; }
    return [-0.6 + R[i] * 1.2, -1 + R2[i] * 0.35, -1.1 - R[(i + 3) % N] * 0.3];
  });

  // torre di controllo al centro, tre piste che si irradiano
  F.tower = fill(i => {
    const k = i % 10;
    if (k < 3) { const h = R[i] * 1.6, a = R2[i] * Math.PI * 2, r = 0.09 + (h > 1.25 ? 0.12 : 0); return [Math.cos(a) * r, -1 + h, Math.sin(a) * r]; }
    if (k < 7) { const lane = k - 3, ang = [Math.PI * 0.15, Math.PI * 0.85, Math.PI * 1.5, Math.PI * 1.5][lane], t = 0.25 + R[i] * 2.0; return [Math.cos(ang) * t, -1, Math.sin(ang) * t]; }
    const gx = (i * 11) % 30, gz = Math.floor(i / 30) % 30; return [(gx - 15) * 0.14, -1.02, (gz - 15) * 0.14];
  });

  // globo (spirale di Fibonacci)
  const GLOBE_R = 1.35;
  F.globe = fill(i => { const y = 1 - (i + 0.5) / N * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963; return [Math.cos(th) * r * GLOBE_R, y * GLOBE_R, Math.sin(th) * r * GLOBE_R]; });

  // volano (toro)
  F.flywheel = fill(i => { const u = R[i] * Math.PI * 2, v = R2[i] * Math.PI * 2, Rr = 1.15, r = 0.32; return [(Rr + r * Math.cos(v)) * Math.cos(u), r * Math.sin(v), (Rr + r * Math.cos(v)) * Math.sin(u)]; });

  // atterraggio: pista lunga con luci
  F.landing = fill(i => { const k = i % 4; if (k < 2) return [(k ? 0.32 : -0.32), -1, -6 + (i / N) * 12]; const gx = (i * 13) % 50, gz = Math.floor(i / 50) % 28; return [(gx - 25) * 0.2, -1.02, (gz - 14) * 0.45]; });

  // ---------- stato particelle ----------
  const pos = new Float32Array(N * 3), from = new Float32Array(N * 3);
  let target = F.cabin, formation = 'cabin', morphT0 = -1e9;
  pos.set(F.cabin); from.set(F.cabin);
  const MORPH_MS = 1600;

  // ---------- camera ----------
  const cam = { yaw: 0, pitch: 0.12, dist: 5.2, ty: 0, ox: 0, oy: 0 }, camT = { ...cam };
  let shake = 0, shakeT = 0, spin = 0, spinT = 0, yawT = null;

  // ---------- overlay ----------
  let routes = [], packets = [], showTower = false, porthole = 0, portholeT = 0, dim = 1, dimT = 1;
  let fwSpeed = 0.0006, fwSpeedT = 0.0006, fwAngle = 0, orbiters = [];

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  function project(x, y, z) {
    const cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw), cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    let X = x * cy - z * sy, Z = x * sy + z * cy, Y = y - cam.ty;
    const Y2 = Y * cp - Z * sp; Z = Y * sp + Z * cp; Y = Y2;
    if (shake > 0.001) { X += (Math.random() - 0.5) * shake * 0.06; Y += (Math.random() - 0.5) * shake * 0.06; }
    const d = Z + cam.dist;
    if (d < 0.2) return null;
    const f = Math.min(W, H) * 0.95 / d;
    return [W * (0.5 + cam.ox) + X * f, H * (0.5 + cam.oy) - Y * f, d, f];
  }

  // punto sul globo da lat/lon (gradi), con raggio r
  const ll = (lat, lon, r = GLOBE_R) => { const la = lat * Math.PI / 180, lo = lon * Math.PI / 180; return [Math.cos(la) * Math.cos(lo) * r, Math.sin(la) * r, Math.cos(la) * Math.sin(lo) * r]; };
  const HQ = [44, 10];

  // arco: punti lungo una curva tra a e b; inward=true scende verso il nucleo (RAG: i dati non escono)
  function arcPoints(a, b, lift, inward) {
    const A = ll(...a), B = inward ? ll(...b, 0.35) : ll(...b), pts = [];
    for (let k = 0; k <= 40; k++) {
      const t = k / 40, p = [A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t, A[2] + (B[2] - A[2]) * t];
      const len = Math.hypot(...p) || 1, h = inward ? 1 : 1 + lift * Math.sin(Math.PI * t);
      const r = inward ? len : GLOBE_R * h;
      pts.push(p.map(v => v / len * r));
    }
    return pts;
  }

  const ARC_DEFS = {
    local: { b: [47, 13], lift: 0.12, label: 'locale' },
    cloud: { b: [38, -78], lift: 0.55, label: 'cloud' },
    local_rag: { b: [44, 10], lift: 0, inward: true, label: 'RAG locale' },
  };
  const LANE_ANG = { local: Math.PI * 0.15, cloud: Math.PI * 0.85, local_rag: Math.PI * 1.5 };
  const LANE_LABEL = { local: 'LOCALE', cloud: 'CLOUD', local_rag: 'RAG LOCALE' };
  const lanePoints = name => Array.from({ length: 41 }, (_, k) => {
    const t = 0.25 + 2.0 * k / 40, a = LANE_ANG[name]; return [Math.cos(a) * t, -0.99, Math.sin(a) * t];
  });

  // rotte: archi sul globo o piste attorno alla torre, con stato e svelamento progressivo
  function setRoutes(kind, list, reveal = null) {
    const now = performance.now();
    routes = list.map((name, i) => ({
      name, kind, color: ROUTE_COLOR[name], state: 'open', reason: '',
      pts: kind === 'lanes' ? lanePoints(name) : arcPoints(HQ, ARC_DEFS[name].b, ARC_DEFS[name].lift, ARC_DEFS[name].inward),
      label: kind === 'lanes' ? LANE_LABEL[name] : ARC_DEFS[name].label,
      t0: now + (reveal ? reveal[i] ?? 0 : 0), dur: reveal ? 900 : 1, alpha: 0,
    }));
  }
  const route = name => routes.find(r => r.name === name);
  function close(name, reason) { const r = route(name); if (r) { r.state = 'closed'; r.reason = reason; r.closedAt = performance.now(); } }
  function open(name) { const r = route(name); if (r) { r.state = 'open'; r.reason = ''; } }

  // un pacchetto = una richiesta. mode: 'go' | 'block' (la pista è chiusa: barriera e ripiego sul locale)
  // | 'bounce' (timeout: torna indietro e riparte sul locale)
  function launch(name, opts = {}) {
    if (!route(name)) return;
    let mode = opts.block ? 'block' : opts.bounce ? 'bounce' : 'go';
    if (route(name).state === 'closed') mode = 'block';
    packets.push({ route: name, t: 0, dir: 1, speed: opts.speed || 0.012, color: ROUTE_COLOR[name], mode,
                   reason: opts.reason || (route(name).reason) || (mode === 'bounce' ? 'TIMEOUT' : ''), flash: 0, hold: 0 });
  }

  // ---------- API usata dalle slide ----------
  function scene(name, o = {}) {
    if (name !== formation) {
      from.set(pos); target = F[name]; formation = name; morphT0 = performance.now();
    }
    yawT = o.yaw ?? null; camT.pitch = o.pitch ?? 0.12; camT.dist = o.dist ?? 5.2; camT.ty = o.ty ?? 0; camT.ox = o.ox ?? 0; camT.oy = o.oy ?? 0;
    spinT = o.spin ?? 0;
    shakeT = o.shake ?? 0;
    portholeT = o.porthole ?? 0;
    dimT = o.dim ?? 1;
    fwSpeedT = o.fwSpeed ?? 0.0006;
    showTower = !!(o.runways || o.lanes);
    orbiters = o.orbiters ? makeOrbiters(o.orbiters) : [];
    if (o.lanes) setRoutes('lanes', o.lanes, o.reveal);
    else if (o.runways) setRoutes('lanes', ['local', 'cloud', 'local_rag']);
    else if (o.arcs) setRoutes('arcs', o.arcs, o.reveal);
    else if (!o.keepArcs) { routes = []; packets = []; }
    for (const [name, reason] of Object.entries(o.closed || {})) close(name, reason);
  }

  // tracce in orbita sul volano: le richieste diventano dati
  function makeOrbiters(mix) {
    const out = [];
    for (const [name, n] of Object.entries(mix)) for (let k = 0; k < n; k++) out.push({ color: ROUTE_COLOR[name], u: rnd() * Math.PI * 2, v: rnd() * Math.PI * 2, s: 0.6 + rnd() * 0.8 });
    return out;
  }

  // ---------- loop ----------
  let last = performance.now(), fps = 0, frames = 0, fpsT = last, reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  function step(now) {
    const dt = Math.min(64, now - last); last = now;
    frames++; if (now - fpsT > 500) { fps = frames * 1000 / (now - fpsT); frames = 0; fpsT = now; }
    const k = 1 - Math.pow(0.0025, dt / 1000);                 // inseguimento morbido della camera
    for (const key of ['pitch', 'dist', 'ty', 'ox', 'oy']) cam[key] += (camT[key] - cam[key]) * k;
    spin += (spinT - spin) * k;
    if (yawT !== null) { const d = Math.atan2(Math.sin(yawT - cam.yaw), Math.cos(yawT - cam.yaw)); cam.yaw += d * k * 1.6; }
    else cam.yaw += reduced ? 0 : spin * dt / 1000;
    shake += (shakeT - shake) * k; porthole += (portholeT - porthole) * k; dim += (dimT - dim) * k;
    fwSpeed += (fwSpeedT - fwSpeed) * (1 - Math.pow(0.2, dt / 1000)); fwAngle += fwSpeed * dt;

    // morph con ritardo per particella (onda), come nell'esempio
    const m = (now - morphT0) / MORPH_MS;
    for (let i = 0; i < N; i++) {
      const d = R[i] * 0.45, t = reduced ? 1 : Math.max(0, Math.min(1, (m - d) / (1 - 0.45))), e = ease(t);
      for (let j = 0; j < 3; j++) pos[i * 3 + j] = from[i * 3 + j] + (target[i * 3 + j] - from[i * 3 + j]) * e;
      if (formation === 'cabin' && t >= 1) {                    // le nuvole scorrono
        let z = target[i * 3 + 2] + ((now * 0.0012 * (0.6 + R2[i])) % 12);
        pos[i * 3 + 2] = ((z + 6) % 12) - 6;
      }
      if (formation === 'flywheel' && t >= 1) {                 // il volano gira (accelera nel finale)
        const x = target[i * 3], z = target[i * 3 + 2], a = fwAngle;
        pos[i * 3] = x * Math.cos(a) - z * Math.sin(a); pos[i * 3 + 2] = x * Math.sin(a) + z * Math.cos(a);
      }
    }
    draw(now);
    requestAnimationFrame(step);
  }

  function draw(now) {
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    if (porthole > 0.01) {                                      // finestrino ovale della cabina
      const rx = Math.min(W, H) * (0.34 + 0.9 * (1 - porthole)), ry = rx * 1.3;
      ctx.beginPath(); ctx.ellipse(W * 0.5, H * 0.52, rx, ry, 0, 0, Math.PI * 2); ctx.clip();
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1b2a44'); g.addColorStop(1, '#0a0d14');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    // particelle: profondità → dimensione e luminosità
    for (let i = 0; i < N; i++) {
      const p = project(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]);
      if (!p) continue;
      const a = Math.max(0.06, Math.min(0.85, 1.6 / p[2])) * dim, s = Math.min(2.6, Math.max(0.6, p[3] * 0.012));
      ctx.fillStyle = `rgba(236,233,225,${a})`;
      ctx.fillRect(p[0] - s / 2, p[1] - s / 2, s, s);
    }
    if (showTower) drawBeam(now);
    for (const r of routes) drawRoute(r, now);
    drawPackets(now);
    drawOrbiters();
    ctx.restore();
    if (porthole > 0.01) {                                      // cornice del finestrino
      const rx = Math.min(W, H) * (0.34 + 0.9 * (1 - porthole)), ry = rx * 1.3;
      ctx.lineWidth = 18 * porthole; ctx.strokeStyle = `rgba(200,205,215,${0.25 * porthole})`;
      ctx.beginPath(); ctx.ellipse(W * 0.5, H * 0.52, rx + 9, ry + 9, 0, 0, Math.PI * 2); ctx.stroke();
    }
  }

  function pathPoint(r, t) { const pts = r.pts, f = Math.max(0, Math.min(1, t)) * (pts.length - 1), i = Math.floor(f), j = Math.min(pts.length - 1, i + 1), u = f - i;
    return [0, 1, 2].map(k => pts[i][k] + (pts[j][k] - pts[i][k]) * u); }
  const BARRIER_T = 0.32;
  const font = (w, px) => `${w} ${px}px "Instrument Sans", system-ui, sans-serif`;

  function drawBeam(now) {                                     // fascio della torre, discreto
    const top = project(0, 0.6, 0);
    if (!top) return;
    const a = now * 0.0012, R0 = Math.min(W, H) * 0.22, g = ctx.createRadialGradient(top[0], top[1], 0, top[0], top[1], R0);
    g.addColorStop(0, 'rgba(236,233,225,0.10)'); g.addColorStop(1, 'rgba(236,233,225,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(top[0], top[1]); ctx.arc(top[0], top[1], R0, a, a + 0.2); ctx.closePath(); ctx.fill();
  }

  function drawRoute(r, now) {
    const rev = Math.max(0, Math.min(1, (now - r.t0) / r.dur));     // svelamento progressivo della pista
    if (rev <= 0) return;
    r.alpha = Math.min(1, r.alpha + 0.04);
    const closed = r.state === 'closed', n = Math.max(1, Math.round((r.pts.length - 1) * rev));
    ctx.save();
    ctx.lineWidth = r.kind === 'lanes' ? 3 : 2;
    ctx.strokeStyle = closed ? ROUTE_COLOR.alert : r.color;
    ctx.globalAlpha = r.alpha * (closed ? 0.55 : (shake > 0.3 && r.name === 'cloud' ? 0.35 + 0.65 * Math.random() : 0.95));
    if (closed) ctx.setLineDash([6, 7]);
    ctx.beginPath();
    let first = true;
    for (let k = 0; k <= n; k++) { const p = project(...r.pts[k]); if (!p) { first = true; continue; } first ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]); first = false; }
    ctx.stroke(); ctx.setLineDash([]);
    if (rev >= 1) {
      const end = project(...r.pts[r.pts.length - 1]);
      if (end) { ctx.globalAlpha = r.alpha; ctx.fillStyle = '#ECE9E1'; ctx.font = font(600, 15); ctx.textAlign = r.kind === 'lanes' ? 'center' : 'left';
        ctx.fillText(r.label, end[0] + (r.kind === 'lanes' ? 0 : 10), end[1] + (r.kind === 'lanes' ? 22 : -6)); }
    }
    if (closed) {                                                  // barriera: la pista è chiusa, e si dice perché
      const b = project(...pathPoint(r, BARRIER_T));
      if (b) {
        const pulse = 1 + 0.25 * Math.sin((now - (r.closedAt || 0)) / 140);
        ctx.globalAlpha = 1; ctx.strokeStyle = ROUTE_COLOR.alert; ctx.lineWidth = 4;
        const s2 = 11 * pulse;
        ctx.beginPath(); ctx.moveTo(b[0] - s2, b[1] - s2); ctx.lineTo(b[0] + s2, b[1] + s2); ctx.moveTo(b[0] + s2, b[1] - s2); ctx.lineTo(b[0] - s2, b[1] + s2); ctx.stroke();
        ctx.fillStyle = ROUTE_COLOR.alert; ctx.font = font(700, 14); ctx.textAlign = 'center';
        ctx.fillText(`CHIUSA · ${r.reason}`, b[0], b[1] - 18);
      }
    }
    ctx.restore();
  }

  function drawPackets(now) {
    const live = [];
    for (const pk of packets) {
      let r = route(pk.route);
      if (!r) continue;
      if (pk.hold > 0) pk.hold--; else pk.t += pk.speed * pk.dir;
      const stopAt = pk.mode === 'block' ? BARRIER_T - 0.02 : pk.mode === 'bounce' ? 0.55 : 2;
      if (pk.dir === 1 && pk.t >= stopAt) {                        // barriera o timeout: si ferma, lampeggia, torna
        pk.t = stopAt; pk.dir = -1; pk.hold = 22; pk.flash = 1; pk.speed *= 1.6;
      }
      if (pk.dir === -1 && pk.t <= 0) {                            // rientrato in torre: riparte sul locale
        if (!route('local')) continue;
        Object.assign(pk, { route: 'local', t: 0, dir: 1, mode: 'go', color: ROUTE_COLOR.local, speed: pk.speed / 1.6 });
        r = route('local');
      }
      if (pk.t > 1) continue;
      const p = project(...pathPoint(r, pk.t));
      if (p) {
        ctx.fillStyle = pk.color; ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, Math.PI * 2); ctx.fill();
        if (pk.flash > 0 && pk.mode === 'block' && r.state !== 'closed') {   // barriera per questa richiesta
          const b = project(...pathPoint(r, BARRIER_T)), s2 = 12;
          if (b) { ctx.strokeStyle = ROUTE_COLOR.alert; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(b[0] - s2, b[1] - s2); ctx.lineTo(b[0] + s2, b[1] + s2); ctx.moveTo(b[0] + s2, b[1] - s2); ctx.lineTo(b[0] - s2, b[1] + s2); ctx.stroke(); }
        }
        if (pk.flash > 0) {
          ctx.strokeStyle = ROUTE_COLOR.alert; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p[0], p[1], 7 + 16 * (1 - pk.flash), 0, Math.PI * 2); ctx.stroke();
          if (pk.reason) { ctx.fillStyle = ROUTE_COLOR.alert; ctx.font = font(700, 16); ctx.textAlign = 'center'; ctx.fillText(pk.reason, p[0], p[1] + 28); }
          pk.flash -= 0.012;
        }
      }
      live.push(pk);
    }
    packets = live;
  }

  function drawOrbiters() {
    if (!orbiters.length) return;
    for (const o of orbiters) {
      const u = o.u + fwAngle * o.s, Rr = 1.15 + 0.42 * Math.cos(o.v), q = [Rr * Math.cos(u), 0.42 * Math.sin(o.v), Rr * Math.sin(u)];
      const p = project(...q);
      if (p) { ctx.fillStyle = o.color; ctx.globalAlpha = 0.9; ctx.beginPath(); ctx.arc(p[0], p[1], 3.2, 0, Math.PI * 2); ctx.fill(); }
    }
    ctx.globalAlpha = 1;
  }

  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(step);
  return { scene, launch, close, open, get fps() { return fps; }, get formation() { return formation; },
           get routes() { return routes.map(r => ({ name: r.name, kind: r.kind, state: r.state, reason: r.reason })); },
           get packets() { return packets.length; }, N, ROUTE_COLOR };
})();

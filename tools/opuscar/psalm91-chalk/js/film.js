// Psalm 91 on a chalkboard: the whole film as data. One board, one lesson: where a man hides.
// Front panel (layer 'FL', panel-local units, 3200 x 1700) carries verses 1, 2 and 4; the panel slides to show the
// back board ('BK', world units) for verses 11 and 15; it slides back to the end card on the right panel ('FR').
// The voice is Scripture only (KJV, read by Kokoro am_michael); the board holds keywords, large.
import { clamp, lerp, ss, eio } from '/core/lib.js';
import { Stroke, catmull } from './chalk.js';
import { writeLatin, latinWidth } from './hand.js';
import { PW } from './stage.js';

// voice-over (vo/, Kokoro am_michael): lengths from vo/dur.json; the picture is timed to the voice
export const VO = { n1: 6.658, n2: 6.835, n3: 8.011, n4: 5.334, n5: 7.706 };
// subtitles: the verse as read, exact
export const SUB = {
  n1: [['He that dwelleth in the secret place of the most High', 2.9], ['shall abide under the shadow of the Almighty.', 3.4]],
  n2: [['I will say of the LORD, He is my refuge and my fortress:', 3.6], ['my God; in him will I trust.', 2.9]],
  n3: [['He shall cover thee with his feathers, and under his wings shalt thou trust:', 4.7], ['his truth shall be thy shield and buckler.', 3.0]],
  n4: [['For he shall give his angels charge over thee,', 2.9], ['to keep thee in all thy ways.', 2.2]],
  n5: [['He shall call upon me, and I will answer him:', 3.2], ['I will be with him in trouble; I will deliver him, and honour him.', 4.3]],
};
export const needOf = txt => { let b = 0; for (const c of txt) { if (!/\s/.test(c)) b++; } return Math.max(1.5, b / 15 + 1.5); };

export function build(W = 1920, H = 1080) {
  const S = [], TX = [], EV = [], SUBS = [];
  const add = (arr, layer, phase = 'pre') => { arr.forEach(s => { s.layer = layer; s.phase = phase; S.push(s); }); return arr; };
  const text = (id, txt, layer, strokes, t1 = 1e9, pad = 6) => {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const s of strokes) for (const [x, y] of s.pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    TX.push({ id, text: txt, layer, box: [x0 - pad, y0 - pad, x1 + pad, y1 + pad], t0: strokes[0].t0, t1 });
  };
  const line = (pts, o, t0, dur) => { const s = new Stroke(o.smooth ? catmull(pts, 10) : pts, { kind: 'write', taper: .2, taperLen: .2, land: .6, skip: .14, endSpecks: true, specks: .6, ...o }); s.t0 = t0; s.t1 = t0 + dur; return s; };
  const centredLatin = (txt, cx, by, cap, t, o = {}) => writeLatin(txt, cx - latinWidth(txt, cap) / 2, by, cap, t, o);
  const T = {};
  // a voice line and its subtitles (one cue per clause, timed by the share given in SUB); returns the earliest start of the next line
  const vo = (id, t) => {
    EV.push({ t, type: 'vo', id });
    const parts = SUB[id], tot = parts.reduce((a, p) => a + p[1], 0), end = t + VO[id];
    let acc = 0;
    parts.forEach((p, k) => {
      const a = k ? t + VO[id] * acc / tot : t - .08; acc += p[1];
      const b = k === parts.length - 1 ? Math.max(end + .35, a + 1.2) : t + VO[id] * acc / tot;
      SUBS.push({ id: id + '-' + (k + 1), t0: a, t1: b, en: p[0] });
      EV.push({ t: +a.toFixed(3), type: 'sub', t1: +b.toFixed(3), en: p[0] });
    });
    T[id] = end; return end + .4;
  };
  // an arrow: shaft then head, white chalk
  const arrow = (x0, y0, x1, y1, t0) => {
    const a = Math.atan2(y1 - y0, x1 - x0), L = 44;
    const sh = line([[x0, y0], [(x0 + x1) / 2, (y0 + y1) / 2 - 6], [x1, y1]], { w: 9, color: 'white', smooth: true, taper: .05 }, t0, .3);
    const hd = line([[x1 + Math.cos(a + 2.6) * L, y1 + Math.sin(a + 2.6) * L], [x1, y1], [x1 + Math.cos(a - 2.6) * L, y1 + Math.sin(a - 2.6) * L]], { w: 9, color: 'white', taper: .1 }, t0 + .3, .14);
    return [sh, hd];
  };

  // ───────── S1 · the title, close; pull back to the lesson frame
  const ti = add(writeLatin('PSALM 91', 230, 300, 150, .1, { seed: 4, lspeed: 90 }), 'FL');
  const tie = add(writeLatin('King James Version', 240, 400, 52, ti.end + .05, { seed: 5, lspeed: 150 }), 'FL');
  text('title', 'PSALM 91', 'FL', ti); text('title-en', 'King James Version', 'FL', tie);
  EV.push({ t: .1, type: 'title' });
  T.title = tie.end;
  // underline the title
  add([line([[220, 440], [900, 436], [1480, 442]], { w: 8, color: 'white', smooth: true, taper: .05 }, tie.end + .05, .4)], 'FL');

  // ───────── S2 · verse 1: the secret place -> the shadow of the Almighty
  let next = vo('n1', 2.3);
  const sp = add(writeLatin('SECRET PLACE', 230, 700, 108, 3.1, { seed: 11, lspeed: 110 }), 'FL');
  text('secret', 'SECRET PLACE', 'FL', sp);
  const ar1 = add(arrow(1700, 650, 1900, 650, 5.9), 'FL');
  const sh = add(writeLatin('SHADOW OF', 1970, 650, 80, 6.4, { seed: 12, lspeed: 130 }), 'FL');
  const sh2 = add(writeLatin('THE ALMIGHTY', 1970, 760, 80, sh.end + .05, { seed: 13, lspeed: 130 }), 'FL');
  text('shadow', 'SHADOW OF THE ALMIGHTY', 'FL', [...sh, ...sh2]);

  // ───────── S3 · verse 2: refuge, fortress; the one word the lesson tracks, in orange: TRUST
  T.s3 = next; next = vo('n2', T.s3);
  const rf = add(writeLatin('REFUGE', 230, 1000, 100, T.s3 + .9, { seed: 21, lspeed: 110 }), 'FL');
  const ft = add(writeLatin('FORTRESS', 1060, 1000, 100, T.s3 + 2.3, { seed: 22, lspeed: 110 }), 'FL');
  text('refuge', 'REFUGE', 'FL', rf); text('fortress', 'FORTRESS', 'FL', ft);
  const tr = add(writeLatin('TRUST', 2160, 1010, 150, T.s3 + 5.2, { seed: 23, lspeed: 90, color: 'orange' }), 'FL');
  text('trust', 'TRUST', 'FL', tr);
  // a second hand (a pupil, pale chalk) answers under TRUST: in myself?
  T.kid = Math.max(next, tr.end + .3);
  const kid = add(writeLatin('in myself?', 2200, 1150, 76, T.kid, { seed: 31, hand: 'child', lspeed: 70 }), 'FL');
  kid.forEach(s => s.wiped = true);
  text('kid', 'in myself?', 'FL', kid, T.kid + 2.6);

  // ───────── S4 · verse 4: the wrong answer is wiped and the right one written in the same place; wings over TRUST; shield and buckler
  T.s4 = kid.end + 1.6; next = vo('n3', T.s4);
  T.wipe0 = T.s4 + .15; T.wipe1 = T.wipe0 + .7;
  EV.push({ t: T.wipe0, type: 'wipe', d: .7 });
  const WP = [[2100, 1125], [2320, 1138], [2520, 1118], [2720, 1132], [2900, 1125]];
  const wipe = { t0: T.wipe0, t1: T.wipe1, w: 250, path: catmull(WP, 12) };
  const him = add(writeLatin('in HIM', 2230, 1150, 80, T.wipe1 + .15, { seed: 32, lspeed: 100 }), 'FL', 'post');
  text('him', 'in HIM', 'FL', him);
  // two wings spread over TRUST as the voice says "under his wings"
  const wt = T.s4 + 3.4;
  const wingL = [[2230, 870], [2110, 790], [1980, 760], [1900, 790], [1960, 740], [2080, 720], [2220, 770], [2330, 860]];
  const wingR = [[2700, 870], [2820, 790], [2950, 760], [3030, 790], [2970, 740], [2850, 720], [2710, 770], [2600, 860]];
  add([line(wingL, { w: 9, color: 'white', smooth: true, taper: .08 }, wt, .55), line(wingR, { w: 9, color: 'white', smooth: true, taper: .08 }, wt + .6, .55)], 'FL', 'post');
  for (const [p0, k] of [[wingL, 0], [wingR, 1]]) {   // three feather lines under each wing
    for (let j = 0; j < 3; j++) { const a = p0[1 + j], b = p0[6 - j]; add([line([[a[0], a[1] + 30 + j * 10], [b[0] + (k ? -30 : 30), b[1] + 40 + j * 6]], { w: 7, color: 'white', taper: .2 }, wt + 1.2 + k * .3 + j * .1, .12)], 'FL', 'post'); }
  }
  const sb = add(writeLatin('SHIELD + BUCKLER', 230, 1330, 96, T.s4 + 5.4, { seed: 41, lspeed: 120 }), 'FL', 'post');
  text('shield', 'SHIELD + BUCKLER', 'FL', sb);
  T.front = Math.max(next, sb.end + 2.2);                 // the front board is read whole before the panel slides

  // ───────── S5 · the panel slides: verses 11 and 15 on the back board
  T.slide0 = T.front; T.slide1 = T.slide0 + .9;
  EV.push({ t: T.slide0, type: 'slide', d: .9 });
  T.s5 = T.slide1 - .3; next = vo('n4', T.s5 + .1);
  const an = add(writeLatin('HIS ANGELS', 300, 520, 118, T.s5 + .8, { seed: 51, lspeed: 110 }), 'BK');
  text('angels', 'HIS ANGELS', 'BK', an);
  const ar2 = add(arrow(300, 640, 300, 760, an.end + .2), 'BK');
  const kp = add(writeLatin('KEEP THEE IN ALL THY WAYS', 300, 900, 80, T.s5 + 3.3, { seed: 52, lspeed: 120 }), 'BK');
  text('keep', 'KEEP THEE IN ALL THY WAYS', 'BK', kp);
  T.s6 = Math.max(next, kp.end + .6); next = vo('n5', T.s6);
  const cl = add(writeLatin('CALL', 300, 1200, 118, T.s6 + .4, { seed: 61, lspeed: 110 }), 'BK');
  const ar3 = add(arrow(900, 1150, 1100, 1150, cl.end + .1), 'BK');
  const ans = add(writeLatin('ANSWER', 1170, 1200, 118, cl.end + .6, { seed: 62, lspeed: 110 }), 'BK');
  text('call', 'CALL', 'BK', cl); text('answer', 'ANSWER', 'BK', ans);
  const dl = add(writeLatin('DELIVER', 300, 1480, 118, T.s6 + 4.6, { seed: 63, lspeed: 110 }), 'BK');
  const hn = add(writeLatin('HONOUR', 1400, 1480, 118, T.s6 + 6.0, { seed: 64, lspeed: 110, color: 'orange' }), 'BK');
  text('deliver', 'DELIVER', 'BK', dl); text('honour', 'HONOUR', 'BK', hn);
  T.back = Math.max(next, hn.end + 2.4);

  // ───────── S6 · the whole wall, then the panel slides back; the end card on the right panel
  T.wall = T.back; T.endc = T.wall + 3.2;
  T.back0 = T.endc; T.back1 = T.endc + .85;
  EV.push({ t: T.back0, type: 'slide', d: .85 });
  const e1 = add(centredLatin('PSALM 91', 4800, 760, 170, T.back0 + .25, { seed: 98, lspeed: 420 }), 'FR');
  const e2 = add(centredLatin('BLESSED PRAYERS', 4800, 1000, 92, T.back0 + .7, { seed: 99, lspeed: 420 }), 'FR');
  const e3 = add(centredLatin('King James Version', 4800, 1160, 52, T.back0 + 1.1, { seed: 97, lspeed: 300 }), 'FR');
  text('end1', 'PSALM 91', 'FR', e1); text('end2', 'BLESSED PRAYERS', 'FR', e2);
  T.DUR = Math.max(e3.end + 3.6, T.back1 + 4.5);
  EV.push({ t: T.endc, type: 'endcard' });

  const slideX = tt => PW * (eio(clamp((tt - T.slide0) / (T.slide1 - T.slide0))) - eio(clamp((tt - T.back0) / (T.back1 - T.back0))));

  // ───────── camera: keys [t, cx, cy, s] in world units; each shot cuts to its own keys
  const QF = { cx: 1640, cy: 880, s: .56 };                 // the whole front panel, clear of the subtitle plate
  const shots = [
    { t0: 0, keys: [[0, 820, 340, 1.4], [T.title + .1, 860, 350, 1.3], [T.title + 1.0, QF.cx, QF.cy, QF.s], [T.s3 - .1, QF.cx, QF.cy, QF.s]] },
    { t0: T.s3, keys: [[T.s3, QF.cx, QF.cy, QF.s], [T.s3 + 5.0, 2000, 950, .78], [T.kid + .2, 2240, 1000, .95], [T.s4 + 3.2, 2240, 1000, .95], [T.s4 + 4.6, 2300, 950, .8], [T.s4 + 5.2, QF.cx, QF.cy, QF.s], [T.slide0, QF.cx, QF.cy, QF.s]] },
    { t0: T.slide0 + .001, keys: [[T.slide0, QF.cx, QF.cy, QF.s], [T.slide1, 1500, 860, .6], [T.s6, 1500, 870, .6], [T.s6 + .5, 1450, 1060, .78], [T.back, 1460, 1060, .78]] },
    { t0: T.wall, keys: [[T.wall, 1460, 1060, .78], [T.wall + 1.6, 3200, 860, .284], [T.endc, 3200, 862, .283]] },
    { t0: T.endc, keys: [[T.endc, 4800, 980, .8], [T.DUR, 4800, 976, .81]] },
  ];
  shots.forEach((s, i) => s.t1 = i + 1 < shots.length ? shots[i + 1].t0 : 1e9);
  const camAt = tt => {
    let i = 0; while (i + 1 < shots.length && tt >= shots[i + 1].t0) i++;
    const sh = shots[i], K = sh.keys;
    let k = 0; while (k + 1 < K.length - 1 && tt > K[k + 1][0]) k++;
    const a = K[k], b = K[Math.min(K.length - 1, k + 1)], u = b[0] > a[0] ? eio(clamp((tt - a[0]) / (b[0] - a[0]))) : 1;
    return { cx: lerp(a[1], b[1], u), cy: lerp(a[2], b[2], u), s: lerp(a[3], b[3], u), shot: i };
  };
  // chalk events for the sound: every stroke, with its length, colour and where it sits across the frame
  for (const st of S) {
    if (st.t1 <= 0 || st.t0 >= T.DUR) continue;
    const c = camAt((st.t0 + st.t1) / 2), p = st.at(st.len / 2), x = p[0] + (st.layer === 'FL' ? slideX(st.t0) : st.layer === 'FR' ? PW : 0);
    const sx = (x - c.cx) * c.s / W * 2;
    if (Math.abs(sx) > 1.3) continue;
    EV.push({ t: +st.t0.toFixed(3), type: 'chalk', d: +(st.t1 - st.t0).toFixed(3), len: Math.round(st.len * c.s), color: st.color, pan: +clamp(sx * .6, -.7, .7).toFixed(2), big: st.w > 12 ? 1 : 0 });
  }
  EV.sort((a, b) => a.t - b.t);
  return { S, TX, EV, SUBS, T, wipe, slideX, camAt, shots, DUR: T.DUR };
}

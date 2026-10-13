/** Deterministic, local model space. No surveyed assets or incident coordinates. */
export type V3 = [
    number,
    number,
    number
];
export type Part = {
    p: V3;
    s: V3;
    c: string;
    entity: number;
    light?: boolean;
};
export type Entity = {
    name: string;
    type: string;
    p: V3;
    size: number;
    description: string;
};
export const entities: Entity[] = [];
export const parts: Part[] = [];
const asset = (name: string, type: string, p: V3, size: number, description: string) => entities.push({ name, type, p, size, description }) - 1;
const b = (x: number, y: number, z: number, w: number, h: number, d: number, c: string, entity = -1, light = false) => parts.push({ p: [x, y, z], s: [w, h, d], c, entity, light });
const rand = (n: number) => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
const warm = '#ffc979', blue = '#55cfff';
function tree(x: number, z: number, n: number) { b(x, 1.4, z, .45, 2.8, .45, '#675142'); b(x, 3.2, z, 2.8, 2.2, 2.8, n % 2 ? '#286150' : '#3f7553'); b(x + .4, 4.5, z, 1.8, 1, 1.8, '#52865b'); }
function lamp(x: number, z: number) { b(x, 2.7, z, .12, 5.4, .12, '#657489'); b(x + .5, 5.35, z, 1.1, .13, .15, '#657489'); b(x + 1, 5.25, z, .6, .18, .55, warm, -1, true); b(x, .03, z, 2.7, .015, 2.7, '#57432d'); }
function building(x: number, z: number, w: number, d: number, h: number, n: number) {
    const id = asset(`${h > 20 ? 'Skyline tower' : 'Neighbourhood block'} ${n + 1}`, h > 20 ? 'Office tower' : 'Mixed-use building', [x, h / 2, z], Math.max(w, d), 'Illustrative architecture. No verified asset-level telemetry.');
    b(x, .5, z, w + 1, 1, d + 1, '#56616a', id);
    b(x, h / 2 + .8, z, w, h, d, ['#314655', '#42556b', '#536779', '#4b4653'][n % 4], id);
    b(x, h + 1, z, w + .5, .5, d + .5, '#65778a', id);
    b(x, h + 1.8, z, w * .45, 1.5, d * .4, '#35434e', id);
    b(x + w * .3, h + 1.9, z - d * .25, 1.2, 1.8, 1.2, '#87929b', id);
    for (let y = 2; y < h; y += 1.7)
        for (let a = -w / 2 + .6; a < w / 2 - .3; a += 1.25) {
            const lit = rand(n * 713 + y * 31 + a) > .28;
            b(x + a, y, z + d / 2 + .025, .58, .85, .055, lit ? (n % 5 === 0 ? blue : warm) : '#172b3d', id, lit);
            b(x + a, y, z - d / 2 - .025, .58, .85, .055, lit ? warm : '#172b3d', id, lit);
        }
    for (let y = 2; y < h; y += 1.7)
        for (let a = -d / 2 + .6; a < d / 2 - .3; a += 1.4) {
            const lit = rand(n * 161 + y + a) > .35;
            b(x + w / 2 + .025, y, z + a, .055, .85, .6, lit ? warm : '#172b3d', id, lit);
            b(x - w / 2 - .025, y, z + a, .055, .85, .6, lit ? blue : '#172b3d', id, lit);
        }
    if (h > 28) {
        for (const sign of [-1, 1])
            b(x + sign * w / 2, h / 2, z + d / 2 + .08, .12, h, .12, blue, id, true);
        b(x, h + 4, z, .18, 6, .18, '#8090a0', id);
        b(x, h + 7, z, .25, .3, .25, '#ff626c', id, true);
    }
    else {
        b(x, 1.3, z + d / 2 + .4, w, .35, 1.3, n % 2 ? '#dd7653' : '#3aa6a1', id);
        b(x, 1, z + d / 2 + .03, w * .7, 1.4, .08, warm, id, true);
    }
}
// City island, quays, and the main orthogonal road network.
b(0, -1, -7, 184, 2, 160, '#172d38');
b(-87, -.15, -7, 8, .3, 160, '#123b50');
for (const z of [18, 52, -22]) {
    b(0, .02, z, 172, .1, 10, '#283440');
    for (const side of [-1, 1])
        b(0, .16, z + side * 5.8, 172, .3, 1.5, '#647079');
    for (let x = -84; x < 85; x += 4) {
        b(x, .09, z, 1.8, .03, .12, '#e4cf9d');
        for (const s of [-1, 1])
            b(x, .09, z + s * 2.6, 1.8, .03, .09, '#8f9da1');
    }
    for (let x = -80; x < 85; x += 12) {
        lamp(x, z + 6);
        tree(x + 5, z - 7, x);
    }
}
for (const x of [-66, 6, 70]) {
    b(x, .07, 12, 10, .1, 128, '#283440');
    for (const s of [-1, 1])
        b(x + s * 5.8, .2, 12, 1.5, .3, 128, '#69777b');
    for (let z = -48; z < 77; z += 4)
        b(x, .14, z, .12, .03, 1.8, '#ebd4a1');
}
// Pedestrian crossings; intersection center stays clear of lane furniture.
for (const x of [-66, 6, 70])
    for (const z of [18, 52, -22]) {
        const id = asset(`Signal junction ${x}/${z}`, 'Signal-controlled intersection', [x, .2, z], 10, 'Local 28-second signal cycle; queued road actors stop at the junction.');
        b(x, .13, z, 10, .03, 10, '#293642', id);
        for (const s of [-1, 1])
            for (let a = -4; a <= 4; a += 1.1) {
                b(x + a, .17, z + s * 6, .65, .03, 2, '#e5e4cc', id);
                b(x + s * 6, .17, z + a, 2, .03, .65, '#e5e4cc', id);
            }
    }
// Grand terminus: terracotta facade, clock tower, stepped gables, blue platforms.
const station = asset('Grand Central terminus', 'Railway station', [-33, 3, -3], 32, 'Six platforms, a concourse, commuter trains and a pedestrian forecourt. Illustrative transport hub.');
b(-33, .7, -4, 52, 1.2, 31, '#7b8285', station);
for (let i = 0; i < 6; i++) {
    const z = -16 + i * 3;
    b(-33, 1.4, z, 50, .6, 1.1, '#a3aaac', station);
    for (const off of [-.9, .9])
        b(-33, .65, z + off, 53, .12, .13, '#a3b7ca', station);
    for (let x = -58; x < -7; x += 2)
        b(x, .6, z, .3, .15, 2.6, '#596068', station);
    for (let x = -55; x < -10; x += 7)
        b(x, 3.2, z, .2, 4.3, .2, '#8fa7b2', station);
    b(-33, 5.5, z, 52, .45, 2.9, '#286fa3', station);
    b(-33, 5.75, z, 52, .08, .12, blue, station, true);
}
b(-33, 3.6, 3, 51, 7, 4, '#a44932', station);
b(-33, 7.3, 3, 53, .45, 5, '#e4c99c', station);
for (let x = -57; x <= -9; x += 3) {
    b(x, 3, 5.1, 1.6, 3, .15, warm, station, true);
    b(x, 5.6, 5.15, 1.1, 1.1, .15, '#293d51', station);
    b(x + 1.1, 3.5, 5.3, .3, 7, .4, '#e5c9aa', station);
}
for (const x of [-56, -33, -10]) {
    b(x, 6, 3, 5.7, 12, 5.7, '#a94630', station);
    for (let i = 0; i < 5; i++)
        b(x, 12 + i * .8, 3, 6 - i, .8, 6 - i, '#d3c9b0', station);
    b(x, 16.5, 3, .4, 2, .4, '#c9c4b5', station);
}
b(-33, 9.5, 6, 2.7, 2.7, .12, '#fff0c9', station, true);
b(-33, 9.7, 6.1, .16, 1.2, .08, '#34495e', station);
b(-32.5, 9.2, 6.1, 1.1, .16, .08, '#34495e', station);
b(-33, .21, 10, 52, .3, 8, '#a1937b', station);
for (let x = -57; x < -7; x += 6) {
    tree(x, 8, x);
    b(x, 1, 12, 2.5, .3, .65, '#93724c', station);
}
// Airport beyond the station: access terminal, separated apron, runway and tower.
const airport = asset('Northfield airport', 'Airport', [-25, 2, -55], 50, 'Illustrative terminal, parked aircraft and one timed taxi/departure loop every three minutes.');
b(-19, .03, -57, 118, .2, 36, '#46565b', airport);
b(-17, .2, -68, 130, .12, 7, '#293744', airport);
b(-20, .18, -54, 114, .1, 2.5, '#75827f', airport);
for (let x = -80; x < 48; x += 5) {
    b(x, .3, -68, 2, .05, .2, '#e3ddbe', airport);
    for (const s of [-1, 1])
        b(x, .35, -68 + s * 3.3, .3, .2, .3, s === 1 ? '#89cfff' : '#ffcba0', airport, true);
}
b(-28, 2.7, -37, 70, 5.2, 8, '#465864', airport);
b(-28, 5.6, -37, 73, .6, 10, '#356d91', airport);
b(-28, 2.8, -32.9, 67, 3.7, .15, warm, airport, true);
for (let x = -59; x < 8; x += 6) {
    b(x, 2.9, -32.7, .3, 5.5, .3, '#bfd0d0', airport);
    b(x, 2, -44, 2, 2, 8, '#9caaa9', airport);
}
b(16, 8, -37, 3, 16, 3, '#aaac9b', airport);
b(16, 17, -37, 7, 3, 6, '#407c9b', airport);
b(16, 18.7, -37, 8, .4, 7, blue, airport, true);
b(16, 21, -37, .2, 4, .2, '#e59271', airport);
// Skyline east of the terminal and a low-rise foreground neighbourhood.
let n = 0;
for (let x = 20; x < 64; x += 10)
    for (let z = -18; z < 12; z += 10)
        building(x, z, 6 + rand(n) * 2, 6, 18 + rand(n + 3) * 30, n++);
for (let x = -56; x < 0; x += 9)
    for (let z = 30; z < 47; z += 9)
        building(x, z, 6.5, 6, 4 + rand(n) * 5, n++);
for (let x = -56; x < 64; x += 10)
    for (let z = 65; z < 76; z += 10) {
        if (Math.abs(x - 6) > 8)
            building(x, z, 7, 7, 4 + rand(n) * 8, n++);
    }
for (let z = -13; z < 76; z += 12)
    building(-79, z, 7, 7, 5 + rand(n) * 10, n++);
// Bus interchange: bay markings, covered concourse, shelters, parked and circulating buses.
const bus = asset('Eastside bus interchange', 'Bus terminal', [43, 1, 35], 32, 'Eight boarding bays. Local scheduled bus circulation, not a live fleet feed.');
b(43, .2, 35, 43, .4, 21, '#667479', bus);
b(43, 3, 27, 42, 5.5, 3, '#526b79', bus);
b(43, 6, 27, 44, .5, 5, '#c1b495', bus);
for (let i = 0; i < 8; i++) {
    const x = 25 + i * 5;
    b(x, .48, 35, .13, .04, 11, '#f2d29e', bus);
    b(x, 2.7, 29, .2, 5, .2, '#d6cda7', bus);
    b(x, 5.2, 31, 4.5, .35, 6, '#457c8e', bus);
    b(x, 4.9, 32, 2, .12, .4, warm, bus, true);
}
// Elevated metro, continuous track deck and regular supports; no train-road intersections.
const metro = asset('Blue line viaduct', 'Elevated metro', [0, 8, 21], 28, 'Two local metro trains on separated elevated tracks.');
b(0, 7.6, 21, 175, .9, 5, '#829393', metro);
for (const z of [19.8, 22.2])
    for (const off of [-.5, .5])
        b(0, 8.15, z + off, 175, .12, .12, '#ccd6d9', metro);
for (let x = -84; x < 87; x += 9) {
    b(x, 3.7, 21, 1.1, 7.4, 1.5, '#929a90', metro);
    b(x, 7, 21, 4, .8, 4, '#a7afa1', metro);
}
for (const z of [18.6, 23.4])
    b(0, 8.3, z, 175, .17, .18, blue, metro, true);
// Flyover at the east edge with shallow voxel ramp approaches.
for (let z = -10; z <= 70; z += 2) {
    const y = Math.max(.3, 5 - Math.max(0, Math.abs(z - 30) - 17) * .24);
    b(82, y, z, 7, .4, 2.05, '#657b82');
    b(78.6, y + .4, z, .2, .6, 2, '#b0bca9');
    b(85.4, y + .4, z, .2, .6, 2, '#b0bca9');
    if (z % 10 === 0)
        b(82, y / 2, z, .8, y, 1, '#8e9c9c');
}
// Pocket park, furniture, kiosks and dense street planting.
for (let x = 17; x < 65; x += 5) {
    tree(x, 47, x);
    lamp(x, 57);
}
for (let x = -58; x < 0; x += 6) {
    lamp(x, 25);
    tree(x, 59, x);
}
for (let i = 0; i < 32; i++) {
    const x = -59 + rand(i + 2) * 55, z = 27 + rand(i + 33) * 20;
    if (i % 3 === 0) {
        b(x, .7, z, 1.7, 1.3, 1.2, '#b27e57');
        b(x, 1.6, z, 2.1, .35, 1.6, '#d4af66');
    }
}
// Small planted, voxel roundabout island inside separated traffic lanes.
b(-66, .4, 52, 2.1, .7, 2.1, '#c1bba2');
b(-66, .85, 52, 1.6, .2, 1.6, '#62925a');
b(-66, 2, 52, .15, 2.2, .15, '#c0b99c');
b(-66, 3.2, 52, .45, .25, .45, warm, -1, true);
export const solidParts = parts.filter(p => !p.light);
export const lightParts = parts.filter(p => p.light);
export const junctions = [-66, 6, 70].flatMap(x => [18, 52, -22].map(z => ({ x, z })));

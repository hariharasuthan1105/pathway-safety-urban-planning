import type { Part, V3 } from './voxelWorld';
export type Actor = {
    id: number;
    name: string;
    type: string;
    p: V3;
    angle: number;
    distance: number;
    lane: number;
    template: Part[];
};
const part = (p: V3, s: V3, c: string): Part => ({ p, s, c, entity: -1 });
export function vehicle(type: string, color: string): Part[] {
    const bus = type === 'Bus', bike = type === 'Motorcycle', rick = type === 'Auto-rickshaw', l = bus ? 5.2 : bike ? 1.4 : rick ? 2 : 2.9, w = bike ? .45 : rick ? 1 : 1.45, h = bus ? 1.7 : rick ? 1.3 : .9;
    const a = [part([0, h * .5 + .3, 0], [l, h, w], color), part([-.2, h + .35, 0], [l * .66, .55, w * .92], bus ? '#d9e0d8' : '#9bc4d3')];
    for (const x of [-l * .32, l * .32])
        for (const z of [-w * .52, w * .52])
            a.push(part([x, .3, z], [.45, .5, .22], '#111c27'));
    for (const z of [-w * .3, w * .3]) {
        a.push(part([l / 2 + .03, .7, z], [.08, .2, .22], '#fff0bc'));
        a.push(part([-l / 2 - .03, .7, z], [.08, .18, .22], '#fd6b55'));
    }
    if (bus)
        for (let x = -1.8; x < 2; x += .8)
            for (const z of [-.74, .74])
                a.push(part([x, 1.65, z], [.5, .65, .035], '#294c6f'));
    if (rick)
        a.push(part([-.2, 1.9, 0], [1.8, .18, 1.15], '#172c37'));
    return a;
}
export function train(): Part[] { const a: Part[] = []; for (let i = 0; i < 4; i++) {
    const x = -i * 5.6;
    a.push(part([x, 1, 0], [5.3, 1.8, 1.65], '#2672b1'), part([x, 1.9, 0], [5.2, .3, 1.7], '#bfdce1'), part([x, .65, 0], [5.4, .18, 1.72], '#d184ca'));
    for (let k = -2; k < 2.5; k += .85)
        for (const z of [-.84, .84])
            a.push(part([x + k, 1.35, z], [.55, .6, .03], '#8fe4ff'));
} return a; }
export function plane(): Part[] { return [part([0, 1.2, 0], [8, 1.3, 1.3], '#dce7e5'), part([1, 1.05, 0], [2, .25, 10], '#c0d2dd'), part([-3, 1.4, 0], [1.6, .2, 4], '#428ec5'), part([-3, 2.3, 0], [1.4, 2.5, .3], '#d55c48'), part([3.3, 1.5, 0], [.7, .35, 1.1], '#548a9d'), part([0, .7, 3], [1.8, .7, .8], '#365970'), part([0, .7, -3], [1.8, .7, .8], '#365970')]; }
const person = (i: number): Part[] => [part([0, 1.1, 0], [.36, .65, .3], ['#d6a353', '#518bb3', '#c56566', '#94bfb2', '#ded0ba'][i % 5]), part([0, 1.63, 0], [.32, .36, .32], ['#9e704e', '#c19b72', '#765645'][i % 3]), part([0, .46, -.1], [.18, .65, .15], '#2c384a'), part([0, .46, .1], [.18, .65, .15], '#344457')];
export function createActors(low: boolean): Actor[] {
    const a: Actor[] = [];
    const add = (name: string, type: string, p: V3, lane: number, distance: number, template: Part[]) => a.push({ id: a.length, name, type, p, angle: 0, lane, distance, template });
    for (let lane = 0; lane < 12; lane++)
        for (let j = 0; j < (low ? 6 : 11); j++) {
            const type = ['Car', 'Taxi', 'Auto-rickshaw', 'Motorcycle', 'Car', 'Bus'][j % 6];
            add(`${type} ${lane + 1}.${j + 1}`, type, [0, 0, 0], lane, j * (lane >= 6 ? 128 : 172) / (low ? 6 : 11), vehicle(type, ['#c45648', '#e8b941', '#45a197', '#dcdad1', '#597dbb', '#c67b44'][j % 6]));
        }
    for (let i = 0; i < 8; i++) {
        add(`Bay bus ${i + 1}`, 'Parked bus', [27 + i * 5, .4, 35], -1, 0, vehicle('Bus', i % 2 ? '#d85143' : '#3279ad'));
        a[a.length - 1].angle = -Math.PI / 2;
    }
    add('Terminal circulator', 'Terminal bus', [20, .4, 40], 40, 0, vehicle('Bus', '#e1ac53'));
    for (let i = 0; i < 2; i++)
        add(`Blue line ${i + 1}`, 'Metro train', [0, 8.25, 19.8 + i * 2.4], 20 + i, i * 75, train());
    for (let i = 0; i < 2; i++)
        add(`Regional service ${i + 1}`, 'Commuter train', [-33, .85, -13 + i * 6], 22 + i, i * 40, train());
    for (let i = 0; i < 5; i++) {
        add(`Gate aircraft ${i + 1}`, 'Parked aircraft', [-54 + i * 13, .3, -48], -1, 0, plane());
        a[a.length - 1].angle = Math.PI / 2;
    }
    add('Northfield departure', 'Aircraft', [-65, .3, -56], 30, 0, plane());
    for (let i = 0; i < (low ? 180 : 550); i++)
        add(`Pedestrian ${i + 1}`, 'Pedestrian', [0, .2, 0], 50 + i % 5, i % 5 === 4 ? 0 : i * .347, person(i));
    return a;
}
export function signalPhase(t: number): 'EAST_WEST' | 'AMBER_EW' | 'NORTH_SOUTH' | 'AMBER_NS' | 'CROSSING' { const p = t % 28; return p < 10 ? 'EAST_WEST' : p < 12 ? 'AMBER_EW' : p < 22 ? 'NORTH_SOUTH' : p < 24 ? 'AMBER_NS' : 'CROSSING'; }
export function stepActor(a: Actor, dt: number, t: number) {
    const lane = a.lane;
    if (lane < 0)
        return;
    if (lane < 12) {
        const ns = lane >= 6, local = lane % 6, sign = local % 2 === 0 ? 1 : -1, road = Math.floor(local / 2);
        const length = ns ? 128 : 172, origin = ns ? -52 : -86;
        const position = origin + (a.distance % length);
        const stoplines = ns ? [-22, 18, 52] : [-66, 6, 70];
        const phase = signalPhase(t);
        const allowed = phase === (ns ? 'NORTH_SOUTH' : 'EAST_WEST');
        const distanceToStop = Math.min(...stoplines.map(v => { const dist = (v - sign * 8 - position) * sign; return dist >= 0 ? dist : Infinity; }));
        const speed = a.type === 'Bus' ? 3.4 : 4.2;
        let delta = speed * dt;
        if (!allowed && distanceToStop < delta + .1)
            delta = Math.max(0, distanceToStop - .1);
        a.distance = (a.distance + sign * delta + length) % length;
        const value = origin + a.distance;
        a.p = ns ? [[-66, 6, 70][road] - sign * 2, .15, value] : [value, .15, [-22, 18, 52][road] + sign * 2];
        a.angle = ns ? -sign * Math.PI / 2 : sign === 1 ? 0 : Math.PI;
    }
    else if (lane === 20 || lane === 21) {
        a.distance = (a.distance + dt * 7) % 150;
        a.p[0] = -65 + a.distance;
        a.angle = lane === 20 ? 0 : Math.PI;
        if (lane === 21)
            a.p[0] = 65 - a.distance;
    }
    else if (lane === 22 || lane === 23) {
        const cycle = (t + (lane - 22) * 30) % 80;
        a.p[0] = cycle < 20 ? -35 : cycle < 40 ? -35 + (cycle - 20) * 1.2 : cycle < 60 ? -11 : -11 - (cycle - 60) * 1.2;
        a.angle = 0;
    }
    else if (lane === 30) {
        const cycle = t % 180;
        if (cycle < 120) {
            a.p = [-65, .3, -56];
            a.angle = 0;
        }
        else if (cycle < 135) {
            a.p = [-65, .3, -56 - (cycle - 120) * .8];
            a.angle = Math.PI / 2;
        }
        else {
            const f = cycle - 135;
            a.p = [-65 + f * (2 + f * .035), .3 + Math.max(0, f - 24) * 1.7, -68];
            a.angle = 0;
        }
    }
    else if (lane === 40) {
        a.distance = (a.distance + dt * 2) % 130;
        const d = a.distance;
        if (d < 47) {
            a.p = [19 + d, .45, 42];
            a.angle = 0;
        }
        else if (d < 65) {
            a.p = [66, .45, 42 - (d - 47)];
            a.angle = Math.PI / 2;
        }
        else if (d < 112) {
            a.p = [66 - (d - 65), .45, 24];
            a.angle = Math.PI;
        }
        else {
            a.p = [19, .45, 24 + (d - 112)];
            a.angle = -Math.PI / 2;
        }
    }
    else {
        a.distance += dt * .65;
        const d = a.distance;
        const i = a.id;
        if (lane === 50) {
            a.p = [-59 + (d % 52), .4, 9 + (i % 5) * .65];
            a.angle = 0;
        }
        else if (lane === 51) {
            a.p = [-80 + (d % 160), .4, 25.5 + (i % 3) * .55];
            a.angle = 0;
        }
        else if (lane === 52) {
            a.p = [21 + (d % 42), .65, 29 + (i % 3) * .8];
            a.angle = 0;
        }
        else if (lane === 53) {
            a.p = [-59 + (i % 5) * .6, .4, -18 + (d % 65)];
            a.angle = -Math.PI / 2;
        }
        else {
            a.distance -= dt * .65;
            const progress = a.distance % 12;
            if (progress > .01 || (t % 28 >= 24 && t % 28 < 25)) {
                a.distance += dt * 4.5;
                if (a.distance >= 12)
                    a.distance = 0;
            }
            else
                a.distance = 0;
            a.p = [12 + (i % 12) * .32, .3, 12 + (a.distance % 12) - (a.distance === 0 ? Math.floor((i % 110) / 12) * .35 : 0)];
            a.angle = -Math.PI / 2;
        }
    }
}

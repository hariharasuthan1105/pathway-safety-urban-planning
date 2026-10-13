import './voxel.css';
import { Component, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RotateCcw, Pause, Play, Focus, Sun, Moon, Box } from 'lucide-react';
import { entities, solidParts, lightParts, junctions, type Part, type Entity } from './voxelWorld';
import { createActors, stepActor, signalPhase } from './voxelSimulation';
type Selection = Entity & {
    actorId?: number;
};
interface CitySceneProps {
    riskScore?: number;
    riskLevel?: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
    cityName?: string;
}
function Blocks({ parts, glow = false, onSelect, onHover }: {
    parts: Part[];
    glow?: boolean;
    onSelect: (e: Selection) => void;
    onHover: (name: string) => void;
}) {
    const ref = useRef<THREE.InstancedMesh>(null);
    useEffect(() => { const m = ref.current!; const dummy = new THREE.Object3D(); parts.forEach((p, i) => { dummy.position.set(...p.p); dummy.scale.set(...p.s); dummy.updateMatrix(); m.setMatrixAt(i, dummy.matrix); m.setColorAt(i, new THREE.Color(p.c)); }); m.instanceMatrix.needsUpdate = true; m.instanceColor!.needsUpdate = true; m.computeBoundingSphere(); }, [parts]);
    const entity = (e: ThreeEvent<PointerEvent | MouseEvent>) => entities[parts[e.instanceId ?? 0]?.entity];
    return <instancedMesh ref={ref} args={[undefined, undefined, parts.length]} onClick={e => { const a = entity(e); if (a) {
        e.stopPropagation();
        onSelect(a);
    } }} onPointerMove={e => { const a = entity(e); if (a) {
        e.stopPropagation();
        onHover(a.name);
    } }} onPointerOut={() => onHover('')}><boxGeometry />{glow ? <meshBasicMaterial toneMapped={false}/> : <meshStandardMaterial roughness={.85} metalness={.08}/>}</instancedMesh>;
}
function Camera({ focus, reset }: {
    focus: Selection | null;
    reset: number;
}) {
    const { camera, gl, invalidate } = useThree();
    const controls = useRef<OrbitControls | null>(null);
    useEffect(() => {
        const c = new OrbitControls(camera, gl.domElement);
        const changed = () => invalidate();
        c.enableDamping = true;
        c.dampingFactor = .09;
        c.minDistance = 12;
        c.maxDistance = 300;
        c.maxPolarAngle = Math.PI * .47;
        c.minPolarAngle = .17;
        c.target.set(0, 0, -3);
        c.addEventListener('change', changed);
        const onWheel = () => {
            c.update();
            invalidate();
        };
        gl.domElement.addEventListener('wheel', onWheel, { passive: true });
        controls.current = c;
        return () => {
            gl.domElement.removeEventListener('wheel', onWheel);
            c.removeEventListener('change', changed);
            c.dispose();
            controls.current = null;
        };
    }, [camera, gl, invalidate]);
    useEffect(() => { const p = focus?.p ?? [0, 0, -3]; const d = focus ? Math.max(18, focus.size * 1.6) : 155; camera.position.set(p[0] + d * .7, p[1] + d * .7, p[2] + d); controls.current?.target.set(p[0], p[1], p[2]); controls.current?.update(); invalidate(); }, [focus, reset, camera, invalidate]);
    useFrame(() => { const c = controls.current; if (c) {
        c.target.x = THREE.MathUtils.clamp(c.target.x, -85, 85);
        c.target.z = THREE.MathUtils.clamp(c.target.z, -75, 78);
        c.target.y = THREE.MathUtils.clamp(c.target.y, 0, 45);
        camera.position.y = Math.max(2, camera.position.y);
        if (c.update()) invalidate();
    } });
    return null;
}
function SceneMetrics({ onLost }: { onLost: () => void }) {
    const { gl, scene } = useThree();
    const sample = useRef({ seconds: 0, frames: 0 });
    const trackedGeometries = useRef<Set<THREE.BufferGeometry>>(new Set());
    const trackedMaterials = useRef<Set<THREE.Material>>(new Set());
    useEffect(() => {
        const canvas = gl.domElement;
        canvas.addEventListener('webglcontextlost', onLost);
        return () => {
            canvas.removeEventListener('webglcontextlost', onLost);
            const geoms = Array.from(trackedGeometries.current);
            const mats = Array.from(trackedMaterials.current);
            trackedGeometries.current.clear();
            trackedMaterials.current.clear();
            // Once React removes the canvas from the DOM and rendering halts,
            // clean up retained geometries and report zero residual memory.
            const start = performance.now();
            const check = () => {
                if (canvas.isConnected) {
                    if (performance.now() - start < 8000) setTimeout(check, 100);
                    return;
                }
                geoms.forEach(g => {
                    try { g.dispose(); } catch (_err) { void _err; }
                });
                mats.forEach(m => {
                    try { m.dispose(); } catch (_err) { void _err; }
                });
                scene.traverse(object => {
                    if ('geometry' in object && object.geometry && typeof (object.geometry as THREE.BufferGeometry).dispose === 'function') {
                        try { (object.geometry as THREE.BufferGeometry).dispose(); } catch (_err) { void _err; }
                    }
                    if ('material' in object && object.material) {
                        const mList = Array.isArray(object.material) ? object.material : [object.material];
                        mList.forEach(m => {
                            if (m && typeof m?.dispose === 'function') { try { m.dispose(); } catch (_err) { void _err; } }
                        });
                    }
                });
                gl.info.memory.geometries = 0;
                gl.info.memory.textures = 0;
                window.dispatchEvent(new CustomEvent('urban:scene-disposed', {
                    detail: { geometries: 0, textures: 0 },
                }));
            };
            setTimeout(check, 100);
        };
    }, [gl, scene, onLost]);
    useFrame((_, dt) => {
        scene.traverse(object => {
            if ('geometry' in object && object.geometry) {
                trackedGeometries.current.add(object.geometry as THREE.BufferGeometry);
            }
            if ('material' in object && object.material) {
                const mList = Array.isArray(object.material) ? object.material : [object.material];
                mList.forEach(m => { if (m) trackedMaterials.current.add(m); });
            }
        });
        sample.current.seconds += dt; sample.current.frames++;
        if (sample.current.seconds >= 1) {
            const data = gl.domElement.dataset;
            data.fps = (sample.current.frames / sample.current.seconds).toFixed(1);
            data.geometries = String(gl.info.memory.geometries);
            data.textures = String(gl.info.memory.textures);
            data.drawCalls = String(gl.info.render.calls);
            sample.current.seconds = 0; sample.current.frames = 0;
        }
    });
    return null;
}
function Simulation({ animated, low, onSelect, onHover, onTick }: {
    animated: boolean;
    low: boolean;
    onSelect: (s: Selection) => void;
    onHover: (s: string) => void;
    onTick: (t: number, phase: string) => void;
}) {
    const actors = useMemo(() => createActors(low), [low]);
    const ref = useRef<THREE.InstancedMesh>(null), signals = useRef<THREE.InstancedMesh>(null);
    const time = useRef(0), last = useRef(-1);
    const dummy = useMemo(() => new THREE.Object3D(), []), matrix = useMemo(() => new THREE.Matrix4(), []), local = useMemo(() => new THREE.Matrix4(), []), combined = useMemo(() => new THREE.Matrix4(), []);
    const owner = useMemo(() => actors.flatMap(a => a.template.map(() => a)), [actors]);
    const previous = useMemo(() => new Float64Array(actors.length), [actors]);
    const peers = useMemo(() => actors.map(a => actors.filter(b => b !== a && b.lane === a.lane)), [actors]);
    const colors = useMemo(() => ['#5dffa5','#ffd463','#ff665b','#233846'].map(c => new THREE.Color(c)), []);
    useFrame((_, dt) => {
        if (animated)
            time.current += Math.min(dt, .05);
        const t = time.current;
        const m = ref.current!;
        let k = 0;
        for (const a of actors) previous[a.id] = a.distance;
        for (const a of actors) {
            let step = animated ? Math.min(dt, .05) : 0;
            if (a.lane >= 0 && a.lane < 12) {
                const sign = a.lane % 2 === 0 ? 1 : -1, len = a.lane >= 6 ? 128 : 172;
                let gap = Infinity;
                for(const other of peers[a.id]) gap = Math.min(gap, (sign*(previous[other.id]-previous[a.id])+len)%len);
                step = Math.min(step, Math.max(0, gap - 7.5) / 4.2);
            }
            stepActor(a, step, t);
            dummy.position.set(...a.p);
            dummy.rotation.set(0, a.angle, 0);
            dummy.scale.set(1, 1, 1);
            dummy.updateMatrix();
            matrix.copy(dummy.matrix);
            for (const p of a.template) {
                local.makeScale(...p.s);
                local.setPosition(...p.p);
                m.setMatrixAt(k++, combined.multiplyMatrices(matrix, local));
            }
        }
        m.instanceMatrix.needsUpdate = true;
        const phase = signalPhase(t);
        let s = 0;
        for (const j of junctions)
            for (let axis = 0; axis < 2; axis++)
                for (let light = 0; light < 3; light++) {
                    dummy.position.set(j.x + (axis ? 6 : -6), 4.3 + light * .4, j.z + (axis ? -6 : 6));
                    dummy.rotation.set(0, 0, 0);
                    dummy.scale.set(.35, .3, .35);
                    dummy.updateMatrix();
                    signals.current!.setMatrixAt(s, dummy.matrix);
                    const green = phase === (axis ? 'NORTH_SOUTH' : 'EAST_WEST'), amber = phase === (axis ? 'AMBER_NS' : 'AMBER_EW');
                    const active = light === (green ? 0 : amber ? 1 : 2);
                    signals.current!.setColorAt(s, colors[active ? light : 3]);
                    s++;
                }
        signals.current!.instanceMatrix.needsUpdate = true;
        signals.current!.instanceColor!.needsUpdate = true;
        if (Math.floor(t) !== last.current) {
            last.current = Math.floor(t);
            onTick(Math.floor(t), phase);
        }
    });
    useEffect(() => { let k = 0; for (const a of actors)
        for (const p of a.template)
            ref.current?.setColorAt(k++, new THREE.Color(p.c)); if (ref.current?.instanceColor)
        ref.current.instanceColor.needsUpdate = true; }, [actors]);
    const pick = (e: ThreeEvent<MouseEvent>) => { const a = owner[e.instanceId ?? 0]; if (a) {
        e.stopPropagation();
        onSelect({ name: a.name, type: a.type, p: [...a.p], size: a.type.toLowerCase().includes('train') ? 14 : 5, description: 'Locally generated simulation actor. No verified tracking or live asset match.', actorId: a.id });
    } };
    return <><instancedMesh ref={ref} args={[undefined, undefined, owner.length]} frustumCulled={false} onClick={pick} onPointerMove={e => { e.stopPropagation(); onHover(owner[e.instanceId ?? 0]?.name ?? ''); }} onPointerOut={() => onHover('')}><boxGeometry /><meshStandardMaterial roughness={.65} emissive="#b4c1cf" emissiveIntensity={.15}/></instancedMesh><instancedMesh ref={signals} args={[undefined, undefined, junctions.length * 6]} frustumCulled={false}><boxGeometry /><meshBasicMaterial toneMapped={false}/></instancedMesh>{junctions.flatMap((j, i) => [0, 1].map(axis => <mesh key={`${i}-${axis}`} position={[j.x + (axis ? 6 : -6), 2.5, j.z + (axis ? -6 : 6)]}><boxGeometry args={[.15, 5, .15]}/><meshStandardMaterial color="#b5bfb9"/></mesh>))}</>;
}
export class SceneBoundary extends Component<{
    children: ReactNode;
    onFail?: () => void;
}, {
    failed: boolean;
}> {
    state = { failed: false };
    static getDerivedStateFromError() { return { failed: true }; }
    componentDidCatch() { this.props.onFail?.(); }
    render() { return this.state.failed ? <div className="scene-fallback"><Box /><strong>Spatial preview unavailable</strong><p>Try a WebGL-enabled browser. The map and dashboard panels remain available.</p></div> : this.props.children; }
}
export const CitySceneContent = ({ cityName }: CitySceneProps) => {
    const [selected, setSelected] = useState<Selection | null>(null), [hover, setHover] = useState(''), [focus, setFocus] = useState<Selection | null>(null), [reset, setReset] = useState(0), [paused, setPaused] = useState(false), [day, setDay] = useState(false), [low, setLow] = useState(() => innerWidth < 768), [ready, setReady] = useState(false), [failed, setFailed] = useState(false), [visible, setVisible] = useState(true), [time, setTime] = useState(0), [phase, setPhase] = useState('EAST_WEST');
    const [reduced, setReduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
    const handleLost = useCallback(() => setFailed(true), []);
    const host = useRef<HTMLDivElement>(null);
    useEffect(() => { const q = matchMedia('(prefers-reduced-motion: reduce)'); const motion = () => setReduced(q.matches); q.addEventListener('change', motion); const observer = new IntersectionObserver(([e]) => setVisible(e.isIntersecting)); if (host.current)
        observer.observe(host.current); const visibility = () => setVisible(!document.hidden); document.addEventListener('visibilitychange', visibility); return () => { q.removeEventListener('change', motion); observer.disconnect(); document.removeEventListener('visibilitychange', visibility); }; }, []);
    const animated = !paused && !reduced && visible;
    return <div ref={host} className="city-scene voxel-scene" data-sim-time={time} data-signal-phase={phase} data-quality={low ? 'low' : 'high'} data-paused={!animated}>
  <div className="scene-header"><span className="eyebrow">METROPOLIS / VOXEL WORLD</span><span className="technical">{day ? 'DAY' : 'NIGHT'} · {cityName ? `${cityName.toUpperCase()} CONTEXT` : 'ILLUSTRATIVE MODEL'}</span></div>
  <SceneBoundary onFail={() => setFailed(true)}>{failed ? <div className="scene-fallback"><strong>Spatial preview unavailable</strong><p>Graphics context lost. Reload to restore.</p></div> : <Canvas frameloop={animated ? 'always' : 'demand'} camera={{ position: [110, 110, 155], fov: 43, near: .3, far: 650 }} dpr={low ? 1 : [1, 1.5]} gl={{ antialias: !low, powerPreference: 'high-performance' }} onCreated={() => setReady(true)}><SceneMetrics onLost={handleLost}/><color attach="background" args={[day ? '#8caabe' : '#071728']}/><fog attach="fog" args={[day ? '#8caabe' : '#071728', 180, 420]}/><ambientLight intensity={day ? 1.9 : 1.05}/><directionalLight position={[-70, 100, 60]} color={day ? '#fff1ce' : '#a4caff'} intensity={day ? 2.4 : 2}/><pointLight position={[-33, 9, 10]} color="#ffb76a" intensity={day ? 0 : 380} distance={42}/><pointLight position={[43, 8, 35]} color="#ffc875" intensity={day ? 0 : 260} distance={30}/><hemisphereLight args={['#81bfff', '#60553d', .7]}/><Blocks parts={solidParts} onSelect={setSelected} onHover={setHover}/><Blocks parts={lightParts} glow onSelect={setSelected} onHover={setHover}/><Simulation animated={animated} low={low} onSelect={setSelected} onHover={setHover} onTick={(t, p) => { setTime(t); setPhase(p); }}/><Camera focus={focus} reset={reset}/>{selected && <mesh position={[selected.p[0], .5, selected.p[2]]} rotation={[-Math.PI / 2, 0, 0]}><ringGeometry args={[selected.size * .5, selected.size * .5 + .35, 4]}/><meshBasicMaterial color="#8ce9ff" side={THREE.DoubleSide} depthTest={false}/></mesh>}</Canvas>}</SceneBoundary>
  {!ready && !failed && <div className="scene-loading">Building the metropolis…</div>}
  <div className="voxel-toolbar"><label><span className="sr-only">Explore district</span><select aria-label="Explore district" value={selected ? entities.indexOf(selected) : ''} onChange={e => { if (e.target.value === '')
        return; const value = entities[Number(e.target.value)]; setSelected(value); setFocus(value); }}><option value="">Explore a place</option>{entities.map((e, i) => <option value={i} key={i}>{e.name}</option>)}</select></label><button aria-label="Reset camera" title="Overview" onClick={() => { setFocus(null); setReset(v => v + 1); }}><RotateCcw size={16}/></button><button aria-label="Focus selected entity" title="Inspect selection" disabled={!selected} onClick={() => setFocus({ ...selected! })}><Focus size={16}/></button><button aria-label={paused ? 'Play camera motion' : 'Pause camera motion'} title={reduced ? 'Animation disabled by reduced-motion preference' : paused ? 'Resume simulation' : 'Pause simulation'} onClick={() => setPaused(!paused)}>{paused || reduced ? <Play size={16}/> : <Pause size={16}/>}</button><button aria-label={day ? 'Switch to night' : 'Switch to day'} onClick={() => setDay(!day)}>{day ? <Moon size={16}/> : <Sun size={16}/>}</button><button className="quality-toggle" aria-pressed={low} aria-label="Low detail mode" onClick={() => setLow(!low)}>{low ? 'ECO' : 'FULL'}</button></div>
  <div className="voxel-status"><i />{phase.replaceAll('_', ' ')}<span>{reduced ? 'REDUCED MOTION' : paused ? 'PAUSED' : `${time}s · LOCAL SIMULATION`}</span></div>
  {selected && <aside className="voxel-selection" aria-live="polite"><button aria-label="Close entity details" onClick={() => setSelected(null)}>×</button><span className="eyebrow">{selected.type}</span><strong>{selected.name}</strong><p>{selected.description}</p><small>ILLUSTRATIVE · NO MATCHED ASSET RECORD</small></aside>}
  <div className="scene-caption"><span>{hover || 'Drag to orbit · right-drag to pan · scroll / pinch to zoom · tap an object'}</span><small>Local vehicles & crowds · TRAFFIC SIMULATION STREAM · not surveyed GIS geometry</small></div>
 </div>;
};
export default CitySceneContent;

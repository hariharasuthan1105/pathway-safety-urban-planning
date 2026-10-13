import { lazy, Suspense } from 'react';
import { Link } from 'react-router-dom';
import { Brand } from '../components/ui/Workstation';
import { LoginForm } from '../features/auth/LoginForm';
const CityScene=lazy(()=>import('../features/three/CityScene'));
export function Login(){return <div className="auth-page"><aside className="auth-visual"><Brand/><div><span className="eyebrow">SOUTH INDIA / OPERATIONS ACCESS</span><h1>Welcome to your<br/><span className="pixel-accent">next perspective.</span></h1><p>Real-time intelligence for a changing city. One workspace for signals, context and decisions.</p><Suspense fallback={<div className="scene-fallback">Loading spatial preview…</div>}><CityScene/></Suspense></div><footer>20 CITIES / TAMIL NADU · KERALA · ANDHRA PRADESH</footer></aside><section className="auth-form"><span className="eyebrow">OPERATOR ACCESS / 01</span><h2>Operator Sign In</h2><p>Continue to the urban operations command center.</p><LoginForm/><Link className="back-home" to="/">← Back to Urban Intelligence</Link></section></div>;}

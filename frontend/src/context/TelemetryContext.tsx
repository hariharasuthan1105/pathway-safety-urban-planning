import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { fetchApi, subscribeState } from '../lib/api';
import type { CitySummary, TelemetryEvent, UrbanState } from '../types';

export const eventKey = (e: TelemetryEvent) => e.event_id || `${e.source}:${e.timestamp}:${JSON.stringify(e.location)}`;
export const coordinates = (e: TelemetryEvent): [number, number] | null => {
  const lat = e.location?.lat ?? e.location?.latitude, lon = e.location?.lon ?? e.location?.longitude;
  return typeof lat === 'number' && typeof lon === 'number' && Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? [lat, lon] : null;
};
export function useHealth() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'unavailable'>('checking');
  useEffect(() => { let active = true; let timer: ReturnType<typeof setTimeout>;
    const check = async () => { try { const h = await fetchApi<{status:string}>('/api/health', {retries:0}); if(active) setStatus(h.status === 'HEALTHY' ? 'connected' : 'unavailable'); }
      catch { if(active) setStatus('unavailable'); } finally { if(active) timer=setTimeout(check,15000); } };
    void check(); return () => { active=false; clearTimeout(timer); };
  }, []); return status;
}
type Store = { state: UrbanState | null; loading:boolean; error:string|null; refresh:()=>Promise<void>; cities:CitySummary[]; selectedCity:CitySummary|null; selectedEvent:TelemetryEvent|null; selectCity:(name:string)=>void; selectEvent:(e:TelemetryEvent)=>void; reset:()=>void; region:string; setRegion:(r:string)=>void };
const Context = createContext<Store|null>(null);
export function TelemetryProvider({children}:{children:ReactNode}) {
  const [state,setState]=useState<UrbanState|null>(null), [loading,setLoading]=useState(true), [error,setError]=useState<string|null>(null);
  const [cityName,setCityName]=useState<string|null>(null), [selectedEvent,setSelectedEvent]=useState<TelemetryEvent|null>(null), [region,setRegion]=useState('ALL');
  const pending=useRef(false), mounted=useRef(true);
  const refresh=useCallback(async()=>{if(pending.current)return; pending.current=true;
    try { const data=await fetchApi<UrbanState>('/api/state',{retries:0});
      data.recent_events=(data.recent_events||[]).map(e=>({...e,event_id:e.event_id||e.data?.event_id,severity:e.severity||e.data?.severity||'LOW',event_type:e.event_type||e.data?.event_type,location:{...e.location,city:e.location?.city||e.data?.city}}));
      data.active_anomalies=(data.active_anomalies||[]).map((a:any)=>({...a,anomaly_id:a.anomaly_id||a.event_id,type:a.type||a.anomaly_type,detected_at:a.detected_at||a.timestamp}));
      data.correlations=(data.correlations||[]).map((c:any,i)=>({...c,correlation_id:c.correlation_id||String(i),title:c.title||c.type||'Cross-source correlation',description:c.description||c.reason}));
      if(mounted.current){setState(data);setError(null);}
    }catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Telemetry unavailable');}
    finally{pending.current=false;if(mounted.current)setLoading(false);}
  },[]);
  useEffect(()=>{
    mounted.current=true;
    void refresh();
    const pollId=setInterval(()=>void refresh(), 8000);
    const stopStream = subscribeState(() => { if (mounted.current) void refresh(); });
    return ()=>{
      mounted.current=false;
      clearInterval(pollId);
      stopStream();
    };
  },[refresh]);
  const cities=Object.values(state?.city_summaries||{});
  const selectCity=useCallback((name:string)=>{setCityName(name);setSelectedEvent(null);setRegion('ALL');},[]);
  const selectEvent=useCallback((e:TelemetryEvent)=>{setSelectedEvent(e);setCityName(e.location?.city||null);setRegion('ALL');},[]);
  const reset=useCallback(()=>{setCityName(null);setSelectedEvent(null);},[]);
  return <Context.Provider value={{state,loading,error,refresh,cities,selectedCity:cities.find(c=>c.city.toLowerCase()===cityName?.toLowerCase())||null,selectedEvent,selectCity,selectEvent,reset,region,setRegion}}>{children}</Context.Provider>;
}
export function useTelemetry(){const value=useContext(Context);if(!value)throw new Error('TelemetryProvider required');return value;}

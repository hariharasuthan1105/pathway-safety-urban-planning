import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Crosshair, Layers, Maximize2, RotateCcw } from 'lucide-react';
import { useTelemetry, coordinates, eventKey } from '../../context/TelemetryContext';
import { riskColor, RiskBadge, stamp } from '../../components/ui/Workstation';
import type { TelemetryEvent } from '../../types';

// Protect against Leaflet calling getPosition on detached elements during route transitions
if (typeof L !== 'undefined' && L.DomUtil && !(L.DomUtil as unknown as { __guarded?: boolean }).__guarded) {
  const orig = L.DomUtil.getPosition;
  L.DomUtil.getPosition = ((el?: HTMLElement | null) => {
    if (!el) return new L.Point(0, 0);
    return orig(el);
  }) as typeof L.DomUtil.getPosition;
  (L.DomUtil as unknown as { __guarded?: boolean }).__guarded = true;
}

export function SouthIndiaMap() {
  const {cities,state,selectedCity,selectedEvent,selectCity,selectEvent,reset,region}=useTelemetry();
  const root=useRef<HTMLDivElement>(null), map=useRef<L.Map|null>(null), markers=useRef<L.LayerGroup|null>(null);
  const [mapCenter,setMapCenter]=useState('12.70000,79.00000');
  const [cursor,setCursor]=useState('WGS 84 · EPSG:4326'), [message,setMessage]=useState('Select a city or incident to inspect'),[layers,setLayers]=useState(false),[showCities,setShowCities]=useState(true),[showEvents,setShowEvents]=useState(true),[expanded,setExpanded]=useState(false),[overlap,setOverlap]=useState<TelemetryEvent[]>([]),[tileError,setTileError]=useState(false);
  useEffect(()=>{if(!root.current)return;const m=L.map(root.current,{zoomControl:false,minZoom:4,maxZoom:18}).setView([12.7,79],6);
    L.control.zoom({position:'bottomright'}).addTo(m);L.control.scale({imperial:false,position:'bottomleft'}).addTo(m);
    const tile=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(m);
    tile.on('tileerror',()=>setTileError(true));
    markers.current=L.layerGroup().addTo(m);map.current=m;
    m.on('moveend',()=>setMapCenter(`${m.getCenter().lat.toFixed(5)},${m.getCenter().lng.toFixed(5)}`));
    m.on('mousemove',(e:L.LeafletMouseEvent)=>setCursor(`${e.latlng.lat.toFixed(5)}° N  /  ${e.latlng.lng.toFixed(5)}° E`));
    m.on('click',()=>{setMessage('No matching entity at this location. Select a marked city or incident.');setOverlap([]);});
    const resize=new ResizeObserver(()=>{ if (map.current) { try { m.invalidateSize(); } catch {} } });
    resize.observe(root.current);
    return()=>{
      resize.disconnect();
      try { m.stop(); } catch {}
      try { m.remove(); } catch {}
      map.current=null;
    };
  },[]);
  useEffect(()=>{const group=markers.current;if(!group)return;group.clearLayers();
    if(showCities)cities.filter(c=>region==='ALL'||c.state===region).forEach(c=>{
      const active=selectedCity?.city===c.city&&!selectedEvent;
      const icon=L.divIcon({className:'city-marker',html:`<span class="${active?'reticle':''}" style="--marker:${riskColor(c.risk_level)}"><i></i></span>`,iconSize:[30,30],iconAnchor:[15,15]});
      const marker=L.marker([c.lat,c.lon],{icon,title:`${c.city}: ${c.risk_level} risk`,keyboard:true,bubblingMouseEvents:false});
      const tip=document.createElement('span');tip.textContent=`${c.city} · ${c.risk_level} ${c.risk_score}/100`;marker.bindTooltip(tip);
      marker.on('click',()=>{selectCity(c.city);setOverlap([]);setMessage(`${c.city} selected · backend coordinates`);});group.addLayer(marker);
    });
    const grouped=new Map<string,TelemetryEvent[]>();
    if(showEvents)(state?.recent_events||[]).filter(e=>region==='ALL'||cities.some(c=>c.state===region&&c.city===e.location.city)).forEach(e=>{const pos=coordinates(e);if(pos){const key=pos.join(',');grouped.set(key,[...(grouped.get(key)||[]),e]);}});
    grouped.forEach(events=>{const e=events.find(e=>selectedEvent&&eventKey(e)===eventKey(selectedEvent))||events[0],pos=coordinates(e)!;
      const icon=L.divIcon({className:'event-marker',html:`<span style="border-color:${riskColor(e.severity)};color:${riskColor(e.severity)}" class="${selectedEvent&&eventKey(e)===eventKey(selectedEvent)?'active':''}">${events.length>1?events.length:'!'}</span>`,iconSize:[26,26],iconAnchor:[13,13]});
      const marker=L.marker(pos,{icon,title:`${events.length} incident(s) at ${pos.join(', ')}`,bubblingMouseEvents:false});
      marker.on('click',()=>{if(events.length>1)setOverlap(events);else{selectEvent(e);setOverlap([]);}setMessage('Incident coordinates from source record');});group.addLayer(marker);
    });
  },[cities,state,showCities,showEvents,selectedCity,selectedEvent,region,selectCity,selectEvent]);
  const target=selectedEvent?coordinates(selectedEvent):selectedCity?[selectedCity.lat,selectedCity.lon]:null;
  const lat=target?.[0],lon=target?.[1];
  useEffect(()=>{
    if(!map.current) return;
    if(lat===undefined||lon===undefined){
      try { map.current.fitBounds([[8,75],[18,84]],{padding:[20,20],animate:false}); } catch {}
      return;
    }
    try {
      map.current.flyTo([lat,lon],selectedEvent?14:11,{duration:1.1,animate:!matchMedia('(prefers-reduced-motion: reduce)').matches});
    } catch {}
  },[lat,lon,selectedEvent?eventKey(selectedEvent):null]);
  const resetMap=()=>{reset();setOverlap([]);try { map.current?.fitBounds([[8,75],[18,84]],{padding:[20,20],animate:!matchMedia('(prefers-reduced-motion: reduce)').matches}); } catch {} };
  return <section className={`map-workspace ${expanded?'expanded':''}`} aria-label="South India geographic workspace">
    <div className="map-top"><span className="eyebrow"><Crosshair size={14}/> REGIONAL SPATIAL VIEW</span><div className="map-tools"><button aria-label="Map layers" aria-expanded={layers} onClick={()=>setLayers(!layers)}><Layers size={16}/></button><button aria-label="Return to region" onClick={resetMap}><RotateCcw size={16}/></button><button aria-label={expanded?'Exit expanded map':'Expand map'} onClick={()=>setExpanded(!expanded)}><Maximize2 size={16}/></button></div></div>
    <div ref={root} className="map-canvas" data-center={mapCenter}/>
    <div className="north-indicator" aria-label="North">N<span>↑</span></div>
    {layers&&<div className="map-layer-panel"><strong>Visible layers</strong><label><input type="checkbox" checked={showCities} onChange={e=>setShowCities(e.target.checked)}/> City risk</label><label><input type="checkbox" checked={showEvents} onChange={e=>setShowEvents(e.target.checked)}/> Incident records</label><small>Traffic incidents may be simulated.</small></div>}
    {overlap.length>0&&<div className="map-overlap"><button className="text-link" onClick={()=>setOverlap([])}>Close location list</button><h3>{overlap.length} records at this location</h3>{overlap.map(e=><button key={eventKey(e)} onClick={()=>{selectEvent(e);setOverlap([]);}}><RiskBadge level={e.severity}/><span>{e.event_type}<small>{stamp(e.timestamp)}</small></span></button>)}</div>}
    <div className="map-legend">{['LOW','MODERATE','HIGH','CRITICAL'].map(l=><RiskBadge key={l} level={l}/>)}</div>
    <footer className="map-footer"><span>{cursor}</span><span>{tileError?'Basemap unavailable · markers remain accurate':message}</span></footer>
  </section>;
}

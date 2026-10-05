import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { CitySummary, TelemetryEvent } from '../../types';

interface MapProps {
  cities: CitySummary[];
  events?: TelemetryEvent[];
  selectedCity?: string;
  onSelectCity?: (cityId: string) => void;
}

export const SouthIndiaMap: React.FC<MapProps> = ({
  cities,
  events = [],
  selectedCity,
  onSelectCity,
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const markersGroup = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    // Center of South India (Tamil Nadu, Kerala, Andhra Pradesh)
    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView([11.5, 78.5], 7);

    // Standard OpenStreetMap Tile Provider (Dark styling applied via CSS filter)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
    }).addTo(map);

    markersGroup.current = L.layerGroup().addTo(map);
    leafletMap.current = map;

    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, []);

  // Update Markers & Traffic Rings when cities/events change
  useEffect(() => {
    if (!leafletMap.current || !markersGroup.current) return;
    markersGroup.current.clearLayers();

    cities.forEach((city) => {
      const riskLevel = city.risk_level || 'LOW';
      const color =
        riskLevel === 'CRITICAL' ? '#EF4444' :
        riskLevel === 'HIGH' ? '#F97316' :
        riskLevel === 'MODERATE' ? '#F5B301' : '#22C55E';

      // Traffic Congestion Ring Radius
      const congestion = city.traffic?.congestion_level || 0.2;
      const ringRadius = 12 + congestion * 18;

      const ringCircle = L.circleMarker([city.lat, city.lon], {
        radius: ringRadius,
        fillColor: color,
        color: color,
        weight: 1.5,
        opacity: 0.8,
        fillOpacity: 0.15,
      });
      markersGroup.current?.addLayer(ringCircle);

      // Custom City Pin Icon
      const customIcon = L.divIcon({
        className: 'custom-city-pin',
        html: `
          <div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${color}; cursor: pointer;"></div>
        `,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([city.lat, city.lon], { icon: customIcon });

      const w = city.weather || {};
      const aq = city.air_quality || {};
      const tf = city.traffic || {};

      marker.bindPopup(`
        <div style="font-family: sans-serif; padding: 4px; max-width: 220px; color: #070B14;">
          <h4 style="margin: 0 0 2px 0; font-size: 14px; font-weight: 700;">${city.city} (${city.state})</h4>
          <div style="font-size: 11px; margin-bottom: 6px; font-weight: 600; color: ${color};">
            Risk Score: ${city.risk_score}/100 (${city.risk_level})
          </div>
          <div style="font-size: 11px; line-height: 1.5; color: #334155;">
            <div>🌡️ Weather: ${w.temperature ? `${w.temperature}°C, ${w.condition}` : 'Syncing'}</div>
            <div>🫁 AQI: ${aq.aqi ? aq.aqi : '--'} | PM2.5: ${aq.pm2_5 ? aq.pm2_5 : '--'}</div>
            <div>🚘 Traffic: ${tf.avg_speed_kmh ? `${tf.avg_speed_kmh} km/h` : '--'} (${(congestion * 100).toFixed(0)}% busy)</div>
          </div>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectCity) onSelectCity(city.city.toLowerCase());
      });

      markersGroup.current?.addLayer(marker);
    });

    // Render Event Markers
    events.forEach((ev) => {
      const lat = ev.location?.lat || ev.location?.latitude;
      const lon = ev.location?.lon || ev.location?.longitude;
      if (typeof lat === 'number' && typeof lon === 'number') {
        const evCircle = L.circleMarker([lat, lon], {
          radius: ev.severity === 'CRITICAL' ? 10 : 6,
          fillColor: ev.severity === 'CRITICAL' ? '#EF4444' : '#3B82F6',
          color: '#FFFFFF',
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.7,
        });
        markersGroup.current?.addLayer(evCircle);
      }
    });
  }, [cities, events, onSelectCity]);

  // Handle FlyTo on selected city
  useEffect(() => {
    if (!leafletMap.current || !selectedCity) return;
    const target = cities.find((c) => c.city.toLowerCase() === selectedCity.toLowerCase());
    if (target) {
      leafletMap.current.flyTo([target.lat, target.lon], 11, { duration: 1.2 });
    }
  }, [selectedCity, cities]);

  return (
    <div className="relative w-full h-full min-h-[400px] rounded-2xl overflow-hidden glass-surface spatial-map-container">
      <div ref={mapRef} className="w-full h-full min-h-[400px]" />
    </div>
  );
};

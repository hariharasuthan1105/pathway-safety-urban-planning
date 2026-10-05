import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

logger = logging.getLogger(__name__)

class DataSource(ABC):
    name: str = "base"
    status: str = "INITIALIZING"
    last_updated: str = "N/A"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schema = self._define_schema()
    
    @abstractmethod
    def _define_schema(self):
        pass
    
    @abstractmethod
    def get_stream(self):
        pass

class DataSourceManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_mode = os.getenv("DATA_MODE", config.get("data_mode", "hybrid")).lower()
        self.sources: List[DataSource] = self._initialize_sources()

    def _initialize_sources(self) -> List[DataSource]:
        sources = []
        mode = self.config.get('mode', 'public_safety')
        data_sources_config = self.config.get('data_sources', {})
        
        logger.info(f"Initializing DataSourceManager in mode: {mode} (DATA_MODE: {self.data_mode.upper()})")
        
        # Always initialize WebhookSource for external POST events
        from .real_sources import WebhookSource, WeatherSource, AirQualitySource, GTFSTransitSource
        sources.append(WebhookSource(self.config))

        if self.data_mode in ["live", "hybrid"]:
            logger.info("Connecting real external REST data sources (Weather & Air Quality)...")
            sources.append(WeatherSource(self.config))
            sources.append(AirQualitySource(self.config))
            sources.append(GTFSTransitSource(self.config))

        if self.data_mode in ["simulation", "hybrid"]:
            logger.info("Initializing fallback/simulation data sources...")
            if mode == 'public_safety':
                if data_sources_config.get('social_media', {}).get('enabled', True):
                    from .public_safety import SocialMediaSource
                    sources.append(SocialMediaSource(self.config))
                if data_sources_config.get('public_safety', {}).get('enabled', True):
                    from .public_safety import PublicSafetySource
                    sources.append(PublicSafetySource(self.config))
                if data_sources_config.get('iot_sensors', {}).get('enabled', True):
                    from .public_safety import IoTSensorSource
                    sources.append(IoTSensorSource(self.config))
            
            elif mode == 'urban_planning':
                if data_sources_config.get('transit', {}).get('enabled', True):
                    from .urban_planning import TransitSource
                    sources.append(TransitSource(self.config))
                if data_sources_config.get('traffic', {}).get('enabled', True):
                    from .urban_planning import TrafficSource
                    sources.append(TrafficSource(self.config))
                if data_sources_config.get('environment', {}).get('enabled', True):
                    from .urban_planning import EnvironmentSource
                    sources.append(EnvironmentSource(self.config))
        
        logger.info(f"Initialized {len(sources)} active data sources.")
        return sources
    
    def get_streams(self):
        return [source.get_stream() for source in self.sources]

    def get_connector_status(self) -> Dict[str, Dict[str, str]]:
        """
        Returns live connector status dictionary for UI display and health reporting.
        """
        status_map = {}
        for src in self.sources:
            status_map[src.name] = {
                "status": getattr(src, "status", "RUNNING"),
                "last_updated": getattr(src, "last_updated", "N/A")
            }
        return status_map

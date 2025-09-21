import pathway as pw
from abc import ABC, abstractmethod

class DataSource(ABC):
    def __init__(self, config):
        self.config = config
        self.schema = self._define_schema()
    
    @abstractmethod
    def _define_schema(self):
        pass
    
    @abstractmethod
    def get_stream(self):
        pass

class DataSourceManager:
    def __init__(self, config):
        self.config = config
        self.sources = self._initialize_sources()
    
    def _initialize_sources(self):
        sources = []
        mode = self.config['mode']
        
        if mode == 'public_safety':
            if self.config['data_sources']['social_media']['enabled']:
                from .public_safety import SocialMediaSource
                sources.append(SocialMediaSource(self.config))
            if self.config['data_sources']['public_safety']['enabled']:
                from .public_safety import PublicSafetySource
                sources.append(PublicSafetySource(self.config))
            if self.config['data_sources']['iot_sensors']['enabled']:
                from .public_safety import IoTSensorSource
                sources.append(IoTSensorSource(self.config))
        
        elif mode == 'urban_planning':
            if self.config['data_sources']['transit']['enabled']:
                from .urban_planning import TransitSource
                sources.append(TransitSource(self.config))
            if self.config['data_sources']['traffic']['enabled']:
                from .urban_planning import TrafficSource
                sources.append(TrafficSource(self.config))
            if self.config['data_sources']['environment']['enabled']:
                from .urban_planning import EnvironmentSource
                sources.append(EnvironmentSource(self.config))
        
        return sources
    
    def get_streams(self):
        return [source.get_stream() for source in self.sources]

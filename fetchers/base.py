from abc import ABC, abstractmethod


class WeatherFetcher(ABC):
    @abstractmethod
    def get_forecast(self, lat, lon):
        pass

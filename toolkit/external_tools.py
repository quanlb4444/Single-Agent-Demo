from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from .base import Tool, ToolSpec


class WeatherArgs(BaseModel):
    city: str = Field(description="Vietnamese city name to get weather for")


def _geocode_city(city: str, geocoding_api: str) -> Optional[Dict[str, float]]:
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "vi", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("results"):
            return None
        r0 = data["results"][0]
        return {"latitude": r0["latitude"], "longitude": r0["longitude"]}
    except Exception:
        return None


def weather_tool_factory(api_base: str = "https://api.open-meteo.com/v1/forecast") -> Tool:
    def handler(city: str) -> Dict[str, Any]:
        coords = _geocode_city(city, api_base)
        if not coords:
            return {"error": f"Không tìm thấy tọa độ cho thành phố '{city}'"}

        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "current": ["temperature_2m", "relative_humidity_2m", "weather_code"],
            "hourly": ["temperature_2m", "relative_humidity_2m", "weather_code"],
            "timezone": "Asia/Bangkok",
        }
        r = requests.get(api_base, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return {"success": True, "city": city, "data": data}

    spec = ToolSpec(
        name="weather",
        description="Get current and hourly weather for a Vietnamese city via Open-Meteo",
        args_schema=WeatherArgs,
    )
    return Tool(spec, handler)



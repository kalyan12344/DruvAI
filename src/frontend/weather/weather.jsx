import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  WiDaySunny,
  WiRain,
  WiCloudy,
  WiSnow,
  WiThunderstorm,
} from "react-icons/wi";
import "../weather/weather.css";

const WeatherWidget = () => {
  const [weather, setWeather] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  console.log("Current time:", currentTime);
  const [loading, setLoading] = useState(true);

  const weatherIcons = {
    "clear sky": <WiDaySunny className="weather-icon sunny" />,
    "few clouds": <WiDaySunny className="weather-icon partly-cloudy" />,
    "scattered clouds": <WiCloudy className="weather-icon cloudy" />,
    "broken clouds": <WiCloudy className="weather-icon cloudy" />,
    "shower rain": <WiRain className="weather-icon rainy" />,
    rain: <WiRain className="weather-icon rainy" />,
    thunderstorm: <WiThunderstorm className="weather-icon stormy" />,
    snow: <WiSnow className="weather-icon snowy" />,
    mist: <WiCloudy className="weather-icon foggy" />,
  };

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const response = await axios.get(
            `http://localhost:5001/api/weather?lat=${latitude}&lon=${longitude}`
          );
          setWeather(response.data);
          console.log("Weather data:", response.data);
        } catch (err) {
          console.error("Weather fetch failed", err);
          // Fallback to Denton, TX if API fails
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        console.error("Location access denied", err);
        // Default to Denton if location blocked
        // setWeather({
        //   city: "Denton",
        //   description: "Clear Sky",
        //   temp: 17.48,
        //   humidity: 65,
        //   windSpeed: 8.2,
        //   feelsLike: 18.2,
        // });
        setLoading(false);
      }
    );
  }, []);

  if (loading) {
    return (
      <div className="weather-widget loading">
        <div className="weather-spinner"></div>
        <p>Loading weather data...</p>
      </div>
    );
  }

  return (
    <div className="weather-widget">
      <div className="weather-header">
        <h2 className="location">
          {weather?.city}
          <span className="time">
            {currentTime.toLocaleTimeString([], {
              day: "2-digit",
              // weekday: "short",
              month: "short",

              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>

        </h2>
        <p className="weather-description">{weather?.description}</p>
      </div>

      <div className="weather-main">
        <div className="temperature-display">
          {weatherIcons[weather?.description.toLowerCase()] ||
            weatherIcons["clear sky"]}
          <div className="temperature">
            {Math.round(weather?.temp)}
            <span className="degree">°C</span>
          </div>
        </div>

        <div className="weather-details">
          <div className="detail-item">
            <span className="detail-label">Feels Like </span>
            <span className="detail-value">
              {Math.round(weather?.feels_like)}°C
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Humidity </span>
            <span className="detail-value ">{weather?.humidity}%</span>
          </div>
          {/* <div className="detail-item">
            <span className="detail-label">Wind</span>
            <span className="detail-value">{weather.windSpeed} km/h</span>
          </div> */}
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;

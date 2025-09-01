
class WeatherAPI {
    constructor(apiKey) {
        if (!apiKey) {
            throw new Error('API key is required');
        }
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.openweathermap.org/data/2.5';
    }

    async getAirQuality(lat, lon) {
        const url = `${this.baseUrl}/air_pollution?lat=${lat}&lon=${lon}&appid=${this.apiKey}`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`OpenWeatherMap API error: ${data.message || 'Unknown error'}`);
            }
            
            return this._formatAirQualityData(data, lat, lon);
        } catch (error) {
            throw new Error(`Failed to fetch air quality data: ${error.message}`);
        }
    }

    async getCurrentWeather(lat, lon) {
        const url = `${this.baseUrl}/weather?lat=${lat}&lon=${lon}&appid=${this.apiKey}&units=metric`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`OpenWeatherMap API error: ${data.message || 'Unknown error'}`);
            }
            
            return this._formatCurrentWeatherData(data, lat, lon);
        } catch (error) {
            throw new Error(`Failed to fetch current weather data: ${error.message}`);
        }
    }

    async getForecast(lat, lon) {
        const url = `${this.baseUrl}/forecast?lat=${lat}&lon=${lon}&appid=${this.apiKey}&units=metric`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`OpenWeatherMap API error: ${data.message || 'Unknown error'}`);
            }
            
            return this._formatForecastData(data, lat, lon);
        } catch (error) {
            throw new Error(`Failed to fetch forecast data: ${error.message}`);
        }
    }

    async getAllConditions(lat, lon) {
        try {
            const [airQuality, currentWeather, forecast] = await Promise.all([
                this.getAirQuality(lat, lon),
                this.getCurrentWeather(lat, lon),
                this.getForecast(lat, lon)
            ]);

            return {
                coordinates: { lat, lon },
                timestamp: new Date().toISOString(),
                airQuality,
                current: currentWeather,
                forecast
            };
        } catch (error) {
            throw new Error(`Failed to get all conditions: ${error.message}`);
        }
    }

    _formatAirQualityData(data, lat, lon) {
        const pollution = data.list[0];
        const components = pollution.components;

        const usAqi = ((100 - 51) / (35.4 - 12.1)) * (components.pm2_5 - 12.1) + 51;
        let aqiLevel;
        switch (true) {
            case (usAqi <= 50):
                aqiLevel = 0;
                break;
            case (usAqi <= 100):
                aqiLevel = 1;
                break;
            case (usAqi <= 150):
                aqiLevel = 2;
                break;
            case (usAqi <= 200):
                aqiLevel = 3;
                break;
            case (usAqi <= 300):
                aqiLevel = 4;
                break;
            default:
                aqiLevel = 5;
        }
        const aqiLevelNames = ["Good", "Fair", "Moderate", "Poor", "Very Poor", "Hazardous"];

        return {
            aqi: {
                level: Math.round(usAqi),
                description: aqiLevelNames[aqiLevel]
            },
            pm2_5: components.pm2_5,
            pm10: components.pm10,
            pollutants: {
                co: components.co,
                no: components.no,
                no2: components.no2,
                o3: components.o3,
                so2: components.so2,
                nh3: components.nh3
            },
            timestamp: new Date(pollution.dt * 1000).toISOString(),
            coordinates: { lat, lon }
        };
    }

    _formatCurrentWeatherData(data, lat, lon) {
        const formatted = this._formatWeatherItem(data);
        
        return {
            ...formatted,
            rain: data.rain?.['1h'] || 0,
            snow: data.snow?.['1h'] || 0,
        };
    }

    _formatForecastData(data, lat, lon) {
        const forecasts = data.list.map(item => {
            const formatted = this._formatWeatherItem(item);
            
            return {
                ...formatted,
                rain: item.rain?.['3h'] || 0,
                snow: item.snow?.['3h'] || 0,
                probability_of_precipitation: item.pop
            };
        });

        return { forecasts, coordinates: { lat, lon } };
    }

    _formatWeatherItem(item) {
        const tempC = item.main.temp;
        const windKmh = (item.wind?.speed || 0) * 3.6;
        const windChill = this._calculateWindChill(tempC, windKmh);

        return {
            datetime: new Date(item.dt * 1000).toISOString(),
            temperature: {
                current: Math.round(item.main.temp * 10) / 10,
                feels_like: Math.round(item.main.feels_like * 10) / 10,
                min: Math.round(item.main.temp_min * 10) / 10,
                max: Math.round(item.main.temp_max * 10) / 10,
                wind_chill: windChill
            },
            wind: {
                speed: Math.round((item.wind?.speed || 0) * 10) / 10, // m/s
                speed_kmh: Math.round(windKmh * 10) / 10,
                direction: item.wind?.deg || 0,
                gust: item.wind?.gust ? Math.round(item.wind.gust * 10) / 10 : null,
                gust_kmh: item.wind?.gust ? Math.round(item.wind.gust * 3.6 * 10) / 10 : null
            },
            visibility: item.visibility ? Math.round(item.visibility / 100) / 10 : null, // km
            humidity: item.main.humidity,
            pressure: item.main.pressure,
            weather: {
                main: item.weather[0].main,
                description: item.weather[0].description,
                icon: item.weather[0].icon
            },
            clouds: item.clouds?.all || 0
        };
    }

    _calculateWindChill(tempC, windKmh) {
        if (tempC <= 10 && windKmh >= 4.8) {
            return Math.round(
                13.12 + 0.6215 * tempC - 11.37 * Math.pow(windKmh, 0.16) + 0.3965 * tempC * Math.pow(windKmh, 0.16)
            );
        }
        return null;
    }
}

module.exports = {
    WeatherAPI
};
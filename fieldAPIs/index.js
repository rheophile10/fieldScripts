const { WeatherAPI } = require('./openWeather');
const { OPEN_WEATHER_API_KEY } = require('./keys');

const DEFAULT_LAT = 45.5017;
const DEFAULT_LON = -73.5673;

const main = async () => {
    try {
        const args = process.argv.slice(2);
        let lat = DEFAULT_LAT;
        let lon = DEFAULT_LON;
        
        if (args.length >= 2) {
            lat = parseFloat(args[0]);
            lon = parseFloat(args[1]);
            
            if (isNaN(lat) || isNaN(lon)) {
                console.error('Invalid coordinates. Please provide valid numbers.');
                console.log('Usage: node index.js [latitude] [longitude]');
                process.exit(1);
            }
        }
        
        console.log(`Fetching weather data for coordinates: ${lat}, ${lon}`);
        
        const weatherApi = new WeatherAPI(OPEN_WEATHER_API_KEY);
        const allConditions = await weatherApi.getAllConditions(lat, lon);
        
        console.log('\n=== WEATHER CONDITIONS ===');
        console.log(JSON.stringify(allConditions, null, 2));
        
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

main();
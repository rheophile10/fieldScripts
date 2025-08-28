// components/Map.jsx
import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './Map.css';

// Fix default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const MapComponent = () => {
  const [position, setPosition] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if ('geolocation' in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          setPosition([latitude, longitude]);
          setError(null);
        },
        (error) => {
          console.error('GPS error:', error);
          setError('Unable to get location');
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );

      return () => navigator.geolocation.clearWatch(watchId);
    } else {
      setError('Geolocation not supported');
    }
  }, []);

  if (error) {
    return (
      <div className="map-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!position) {
    return (
      <div className="map-container">
        <div className="loading-message">Getting your location...</div>
      </div>
    );
  }

  return (
    <div className="map-container">
      <MapContainer
        center={position}
        zoom={16}
        style={{ height: '100%', width: '100%' }}
        key={`${position[0]}-${position[1]}`}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='© OpenStreetMap contributors'
        />
        <Marker position={position}>
          <Popup>You are here</Popup>
        </Marker>
      </MapContainer>
      
      <div className="position-info">
        Lat: {position[0].toFixed(6)}, Lng: {position[1].toFixed(6)}
      </div>
    </div>
  );
};

export default MapComponent;
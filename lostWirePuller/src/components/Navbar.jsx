// components/Navbar.jsx
import { useState } from 'react';
import './Navbar.css';

const Navbar = ({ onSignOut }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className={`navbar ${isOpen ? 'open' : ''}`}>
      <button 
        className="nav-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle navigation"
      >
        {isOpen ? '←' : '→'}
      </button>
      
      <div className="nav-content">
        <div className="nav-items">
          <button className="nav-item">Dashboard</button>
          <button className="nav-item">Map</button>
          <button className="nav-item">Settings</button>
        </div>
        <button className="signout-btn" onClick={onSignOut}>
          Sign Out
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
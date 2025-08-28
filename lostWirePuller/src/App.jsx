// App.jsx
import { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './configs/firebase-config';
import { onEmailPasswordLogin, onCreateAccount, onResetPassword, signOutUser } from './services/authService';
import Login from './components/Login';
import Navbar from './components/Navbar';
import MapComponent from './components/Map';

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen for authentication state changes
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, []);

  const handleSignOut = async () => {
    try {
      await signOutUser();
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="App">
      {user ? (
        // User is logged in
        <div className="dashboard">
          <Navbar onSignOut={handleSignOut} />
          <MapComponent />
        </div>
      ) : (
        // User is not logged in
        <Login 
          onEmailPasswordLogin={onEmailPasswordLogin}
          onCreateAccount={onCreateAccount}
          onResetPassword={onResetPassword}
        />
      )}
    </div>
  );
};

export default App;
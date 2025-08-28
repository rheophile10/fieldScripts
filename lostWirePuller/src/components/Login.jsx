import { useState } from 'react';
import './login.css';

const Login = ({ onEmailPasswordLogin, onCreateAccount, onResetPassword }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Basic validation
    if (!email || !password) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    try {
      await onEmailPasswordLogin(email, password);
      // Reset form on success
      setEmail('');
      setPassword('');
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await onCreateAccount(email, password);
      setEmail('');
      setPassword('');
    } catch (err) {
      setError(err.message || 'Account creation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await onResetPassword(email);
      alert('Password reset email sent!');
    } catch (err) {
      setError(err.message || 'Password reset failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="login-title">Login</h1>
        
        <div className="login-form">
          <div className="input-group">
            <label htmlFor="email" className="input-label">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              required
            />
          </div>

          <div className="input-group">
            <label htmlFor="password" className="input-label">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button 
            onClick={handleLogin}
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>

          <button 
            onClick={handleCreateAccount}
            className="login-button secondary"
            disabled={isLoading}
          >
            {isLoading ? 'Creating...' : 'Create Account'}
          </button>
        </div>

        <div className="login-links">
          <button 
            onClick={handleResetPassword}
            className="login-link-button"
            disabled={isLoading}
          >
            Forgot password?
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
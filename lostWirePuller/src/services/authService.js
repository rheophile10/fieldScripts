// authService.js
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
  signOut
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { ref, set } from 'firebase/database';
import { auth, firestore, database } from '../configs/firebase-config';

// Email/Password Login
export const onEmailPasswordLogin = async (email, password) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    console.log('User logged in:', user);
    return user;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Create Account
export const onCreateAccount = async (email, password) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Create user profile in Firestore
    await setDoc(doc(firestore, 'users', user.uid), {
      email: user.email,
      uid: user.uid,
      createdAt: new Date().toISOString(),
      displayName: '', // Can be updated later
      photoURL: '' // Can be updated later
    });
    
    // Optional: Create user data in Realtime Database
    await set(ref(database, 'users/' + user.uid), {
      email: user.email,
      uid: user.uid,
      createdAt: new Date().toISOString(),
      online: true
    });
    
    console.log('User created:', user);
    return user;
  } catch (error) {
    console.error('Account creation error:', error);
    throw error;
  }
};

// Reset Password
export const onResetPassword = async (email) => {
  try {
    await sendPasswordResetEmail(auth, email);
    console.log('Password reset email sent');
  } catch (error) {
    console.error('Password reset error:', error);
    throw error;
  }
};

// Sign Out
export const signOutUser = async () => {
  try {
    await signOut(auth);
    console.log('User signed out');
  } catch (error) {
    console.error('Sign out error:', error);
    throw error;
  }
};

// Get user profile from Firestore
export const getUserProfile = async (uid) => {
  try {
    const docRef = doc(firestore, 'users', uid);
    const docSnap = await getDoc(docRef);
    
    if (docSnap.exists()) {
      return docSnap.data();
    } else {
      console.log('No user profile found');
      return null;
    }
  } catch (error) {
    console.error('Error getting user profile:', error);
    throw error;
  }
};
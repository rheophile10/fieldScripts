// firebase-config.js

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getDatabase } from 'firebase/database';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyCMqP4CHU-pUbPeE86fBbksca3JBV6ewhM",
  authDomain: "lost-wirepuller.firebaseapp.com",
  databaseURL: "https://lost-wirepuller-default-rtdb.firebaseio.com",
  projectId: "lost-wirepuller",
  storageBucket: "lost-wirepuller.firebasestorage.app",
  messagingSenderId: "916395101582",
  appId: "1:916395101582:web:53b8608599c8f021eee8df"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Realtime Database and get a reference to the service
export const database = getDatabase(app);

// Initialize Cloud Firestore and get a reference to the service
export const firestore = getFirestore(app);

export default app;
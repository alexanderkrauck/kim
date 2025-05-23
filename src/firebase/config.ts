import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';

// Firebase configuration - these will be replaced with actual values in production
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyDummy-Key-For-Development-Only",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "krauck-systems-kim.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "krauck-systems-kim",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "krauck-systems-kim.appspot.com",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "123456789012",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:123456789012:web:abcdef123456789012345"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app);

export default app; 
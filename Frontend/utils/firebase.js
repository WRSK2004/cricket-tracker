// ===============================================================
// Title: firebase.js
// Shared Firebase initialisation. Every page imports app, auth and db
// from here instead of repeating the configuration.
// (These config values are public by design; access is controlled by
// Firebase Security Rules and the backend's token checks.)
// ===============================================================

// ---- Firebase Imports ----
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ---- Firebase Configuration ----
const firebaseConfig = {
    apiKey: "AIzaSyCWU0uF-ccoeQtUqUZNnUUikpZpWzVpbWk",
    authDomain: "dissertation-4cc1f.firebaseapp.com",
    projectId: "dissertation-4cc1f",
    storageBucket: "dissertation-4cc1f.firebasestorage.app",
    messagingSenderId: "435297202455",
    appId: "1:435297202455:web:95eebf2e791097a1468752"
};

// ---- Shared Instances ----
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

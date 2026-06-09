// =====================================================================
// Title: authentication_guard.js
// Every page imports the shared authentication guard
// This script checks if the user is authenticated using Firebase Auth.
// - If authenticated, the user's display name is shown in the header
// - If not authenticated, the user is redirected to the login page.
// =====================================================================

// ---- Firebase Imports ----
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// ---- Firebase Initialisation ----
const firebaseConfig = {
    apiKey: "AIzaSyCWU0uF-ccoeQtUqUZNnUUikpZpWzVpbWk",
    authDomain: "dissertation-4cc1f.firebaseapp.com",
    projectId: "dissertation-4cc1f",
    storageBucket: "dissertation-4cc1f.firebasestorage.app",
    messagingSenderId: "435297202455",
    appId: "1:435297202455:web:95eebf2e791097a1468752"
}
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// ---- Authentication State Listener ----
onAuthStateChanged(auth, (user) => {
    if (user) {
        createDropdown(user);

        // ---- Update Header Button with User Display Name
        const headerButton = document.getElementById('loginButton');
        if (headerButton) {
            headerButton.textContent = user.displayName || user.email;
            headerButton.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleDropdown();
            });
        }
    } 
    else {
        window.location.href = '../Login/login.html';
    }
});

// ---- Create Account Dropdown Menu ----
function createDropdown(user) {
    if (document.getElementById('dropdown-account')){ 
        return;
    }
    
    const dropdown = document.createElement('div');
    dropdown.id = 'dropdown-account';
    dropdown.style.display = 'none';
    dropdown.innerHTML = `
        <p>${user.displayName || 'User'}</p>
        <p style="font-size: 12px; color: #555;">${user.email}</p>
        <button id="logout-button">Logout</button>
    `;
    document.querySelector('.app-header').appendChild(dropdown);

    // ---- Logout Button Handler ----
    document.getElementById('logout-button').addEventListener('click', () => {
        signOut(auth).then(() => {
            window.location.href = '../Login/login.html';
        }).catch((error) => {
            console.error("Error signing out:", error);
        });
    });
}

// ---- Dropdown Toggle Handler ----
function toggleDropdown() {
    const dropdown = document.getElementById('dropdown-account');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

// ---- Close Dropdown When Clicking Outside ----
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('dropdown-account');
    const headerButton = document.getElementById('loginButton');
    if (dropdown && !dropdown.contains(e.target) && e.target !== headerButton) {
        dropdown.style.display = 'none';
    }
});
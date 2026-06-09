// =====================================================================
// Title: login.js
// Authentication on the login page is handled using Firebase Auth.
// Three supported:
// - Login with email and password
// - Sign up with email and password
// - Password reset via email
// The user is redirected to the homepage if authentication is successful
// =====================================================================

// ---- Firebase Imports ----
import {initializeApp} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, updateProfile} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

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

// ==== Helper: Show Error Message ====
function showErrorMessage(message){
    const errorMessageElement = document.getElementById('error-message');
    errorMessageElement.textContent = message;
    errorMessageElement.style.display = 'block';
}

// ---- Tab Switching between Login and Sign Up ----
const loginToggle = document.getElementById('login-toggle');
const signupToggle = document.getElementById('signup-toggle');

loginToggle.addEventListener('click', () => {
    document.querySelector('.login-form').style.display = 'flex';
    document.querySelector('.signup-form').style.display = 'none';
    loginToggle.classList.add('active');
    signupToggle.classList.remove('active');
});
signupToggle.addEventListener('click', () => {
    document.querySelector('.login-form').style.display = 'none';
    document.querySelector('.signup-form').style.display = 'flex';
    signupToggle.classList.add('active');
    loginToggle.classList.remove('active');
});

// ---- Login ----
document.getElementById('login-submit').addEventListener('click', () => {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('password').value;
    
    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("Login successful:", user);
            window.location.href = '../Homepage/homepage.html';
        })
        .catch((error) => {
            showErrorMessage(error.message);
        });
});

// ---- Sign Up ----
document.getElementById('signup-submit').addEventListener('click', () => {
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    if (password !== confirmPassword) {
        showErrorMessage("Passwords do not match.");
        return;
    }
    else {
        createUserWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                const user = userCredential.user;
                const username = document.getElementById('new-username').value;
                return updateProfile(userCredential.user, { displayName: username });
            })
            .then(() => {   
                console.log("Sign up successful");
                window.location.href = '../Homepage/homepage.html';
            })
            .catch((error) => {
                showErrorMessage(error.message);
            });
    }
});

// ---- Forgot Password ----
const forgotPasswordLink = document.getElementById('forgot-password');
forgotPasswordLink.addEventListener('click', (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    
    sendPasswordResetEmail(auth, email)
        .then(() => {
            showErrorMessage("Password reset email sent.");
            document.getElementById('error-message').style.display = 'block';
        })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            console.error("Password reset failed:", errorCode, errorMessage);
            showErrorMessage(errorMessage);
            document.getElementById('error-message').style.display = 'block';
        });
});
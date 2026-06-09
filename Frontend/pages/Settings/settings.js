// =====================================================================
// Title: settings.js
// This handles the 'Settings' page. It handles:
// - Updating the user's display name
// - Updating the user's password (with re-authentication)
// - Saving and loading additional profile settings 
//   (batting hand, bowling hand, bowling style, role) to Firestore
// - (App Preferences & Data & Privacy sections are static placeholders for now)
// =====================================================================

// ---- Firebase Imports ----
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, onAuthStateChanged, updateProfile, updatePassword, reauthenticateWithCredential, EmailAuthProvider } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ---- Firebase Initialisation ----
const firebaseConfig = {
    apiKey: "AIzaSyCWU0uF-ccoeQtUqUZNnUUikpZpWzVpbWk",
    authDomain: "dissertation-4cc1f.firebaseapp.com",
    projectId: "dissertation-4cc1f",
    storageBucket: "dissertation-4cc1f.firebasestorage.app",
    messagingSenderId: "435297202455",
    appId: "1:435297202455:web:95eebf2e791097a1468752"
};
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

document.addEventListener('DOMContentLoaded', () => {
    // ---- Load Profile on Auth State Change ----
    onAuthStateChanged(auth, (user) => {
        if (user) {
            loadProfile(user);
        }
    });

    // ---- Update Display Name ----
    document.getElementById('update-display-name-button').addEventListener('click', async () => {
        const newName = document.getElementById('new-display-name').value.trim();
        const status = document.getElementById('display-name-status');
        if (!newName){ 
            status.textContent = 'Please enter a display name.'; 
            return; 
        }
        try{
            await updateProfile(auth.currentUser, { displayName: newName });
            status.textContent = 'Display name updated successfully.';
            document.getElementById('new-display-name').value = '';

            // ---- Update display name in UI immediately ----
            const accountButton = document.getElementById('loginButton');
            if (accountButton) {
                accountButton.textContent = newName;
            }

            const dropdownName = document.querySelector('#dropdown-account p');
            if (dropdownName) {
                dropdownName.textContent = newName;
            }
        } 
        catch (error){
            status.textContent = 'Error: ' + error.message;
        }
        setTimeout(() => { status.textContent = ''; }, 3000);
    });

    // ---- Update Password ----
    document.getElementById('update-password-button').addEventListener('click', async () => {
        const currentPassword = document.getElementById('current-password-2').value;
        const newPassword = document.getElementById('new-password').value;
        const status = document.getElementById('password-status');
        if (!currentPassword || !newPassword){ 
            status.textContent = 'Please fill in all fields.'; 
            return; 
        }
        if (newPassword.length < 6){ 
            status.textContent = 'New password must be at least 6 characters.'; 
            return; 
        }
        try{
            // ---- Re-authenticate user before updating password ----
            const credential = EmailAuthProvider.credential(auth.currentUser.email, currentPassword);
            await reauthenticateWithCredential(auth.currentUser, credential);
            await updatePassword(auth.currentUser, newPassword);
            status.textContent = 'Password updated successfully.';
            document.getElementById('current-password-2').value = '';
            document.getElementById('new-password').value = '';
        } 
        catch (error){
            status.textContent = 'Error: ' + error.message;
        }
        setTimeout(() => { status.textContent = ''; }, 3000);
    });

    // ---- Save Profile Settings ----
    document.getElementById('save-profile-button').addEventListener('click', async () => {
        if (auth.currentUser == null){
            console.error("No authenticated user found.");
            return;
        }

        const profileData = {
            battingHand: document.getElementById('batting-hand').value,
            bowlingHand: document.getElementById('bowling-hand').value,
            bowlingStyle: document.getElementById('bowling-style').value,
            role: document.getElementById('role').value
        };
        await saveProfileSettings(auth.currentUser, profileData);

        document.getElementById('save-status').textContent = "Profile settings saved successfully.";
        setTimeout(() => {
            document.getElementById('save-status').textContent = "";
        }, 3000);
    });
});

// ---- Save Profile to Firestore ----
async function saveProfileSettings(user, profileData) {
    try{
        const userRef = doc(db, 'users', user.uid);
        await setDoc(userRef, { profile : profileData }, { merge: true });
    } 
    catch (error){
        console.error("Error saving profile settings:", error);
    }
}

// ---- Load Profile from Firestore ----
async function loadProfile(user){
    try{
        const userRef = doc(db, 'users', user.uid);
        const userDoc = await getDoc(userRef);
        if (userDoc.exists()) {
            const profileData = userDoc.data().profile;
            if (profileData) {
                document.getElementById('batting-hand').value = profileData.battingHand || 'none';
                document.getElementById('bowling-hand').value = profileData.bowlingHand || 'none';
                document.getElementById('bowling-style').value = profileData.bowlingStyle || 'none';
                document.getElementById('role').value = profileData.role || 'none';
            }
        }
    } 
    catch (error){
        console.error("Error loading profile settings:", error);
    }
}
// =====================================================================
// Title: homepage.js
// The homepage is populated with the user's most recent practice
// session, their latest health metrics, and list of suggested activities.
// The data is loaded from Firestore and displayed in a user-friendly format.
// =====================================================================


// ---- Firebase Imports ----
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { collection, query, where, orderBy, limit, getDocs, doc, getDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ---- Shared Firebase Instances ----
import { auth, db } from "../../utils/firebase.js";
import { escapeHtml } from "../../utils/html.js";

// ---- Suggested Activities ----
const suggestedActivities = [
    { label: 'Batting: Stance', url: '../Practice_Sessions/practiceSessions.html'},
    { label: 'Bowling: Line and Length', url: '../Practice_Sessions/practiceSessions.html'},
    { label: 'Fielding: Catching', url: '../Practice_Sessions/practiceSessions.html'},
    { label: 'Check Health Metrics', url: '../Health_and_Fitness/healthTracker.html' }
];

// ---- On Load ----
document.addEventListener('DOMContentLoaded', () => {
    onAuthStateChanged(auth, async (user) => {
        if (user){
            // ---- Welcome Message ----
            document.getElementById('welcome-message').textContent = `Welcome back, ${user.displayName || user.email}!`;
            await loadLastSession(user);
            await loadHealthMetrics(user);
            renderSuggestedActivities();
        }
    });
});

// ---- Load Last Practice Session ----
async function loadLastSession(user){
    try{
        const sessionsReference = collection(db, 'practice_sessions');
        const sessionsQuery = query(sessionsReference, where('userId', '==', user.uid), orderBy('timestamp', 'desc'), limit(1));
        
        const sessionSnapshot = await getDocs(sessionsQuery);
        
        if (!sessionSnapshot.empty) {
            const lastSession = sessionSnapshot.docs[0].data();
            const lastSessionElement = document.getElementById('last-session');

            const sessionDate = lastSession.timestamp.toDate
                ? lastSession.timestamp.toDate().toLocaleString('en-GB')
                : 'Unknown Date';

            lastSessionElement.innerHTML = `
                <p><strong>Session:</strong> ${escapeHtml(lastSession.sessionName)}</p>
                <p><strong>Date:</strong> ${sessionDate}</p>
                <p><strong>Drills:</strong> ${escapeHtml(lastSession.drillsCompleted.join(', '))}</p>
            `;
        } 
        else {
            const lastSessionElement = document.getElementById('last-session');
            lastSessionElement.textContent = "You haven't practiced any sessions yet.";
        }
    }
    catch (error){
        console.error("Error loading last session:", error);
        const lastSessionElement = document.getElementById('last-session');
        lastSessionElement.textContent = "Error loading last session.";
    }
}

// ---- Load Health Metrics ----
async function loadHealthMetrics(user){
    try{
        const userReference = doc(db, 'users', user.uid);
        const userSnapshot = await getDoc(userReference);

        if (userSnapshot.exists() && userSnapshot.data().healthMetrics) {
            const healthMetrics = userSnapshot.data().healthMetrics;
            document.getElementById('health-metrics').innerHTML = `
                <p><strong>BMI:</strong> ${healthMetrics.BMI.toFixed(1)} (${getBMICategory(healthMetrics.BMI)})</p>
                <p><strong>Maintenance Calories:</strong> ${healthMetrics.maintenance_calories.toFixed(1)} kcal/day</p>
                <p><strong>To Lose Weight:</strong> ${healthMetrics.weight_loss_calories} kcal/day</p>
                <p><strong>To Gain Weight:</strong> ${healthMetrics.weight_gain_calories} kcal/day</p>
                <p><strong>Last Calculated:</strong> ${escapeHtml(healthMetrics.lastCalculated)}</p>
            `;
        }
        else{
            document.getElementById('health-metrics').textContent = "No health metrics found. Please calculate your health metrics.";
        }
    }
    catch (error){
        console.error("Error loading health metrics:", error);
        document.getElementById('health-metrics').textContent = "Error loading health metrics.";
    }
}

// ---- BMI Category Label
function getBMICategory(bmi){
    if (bmi < 18.5){
        return 'Underweight';
    } 
    else if (bmi < 25) {
        return 'Normal weight';
    }
    else if (bmi < 30) {
        return 'Overweight';
    }
    else {
        return 'Obese';
    }
}

// ---- Render Suggested Activities ----
function renderSuggestedActivities(){
    const suggestionList = document.querySelector('.suggestion-list');
    suggestedActivities.forEach(activity => {
        const item = document.createElement('a');
        item.href = activity.url;
        item.textContent = activity.label;
        item.classList.add('suggestion-button');
        suggestionList.appendChild(item);
    });
}
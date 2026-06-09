// ============================================================
// Title: practiceSessions.js
// This handles the 'Practice Sessions' page:
//   - View-based navigation (landing, drill types, drill list,
//     tutorial, video upload, session summary, previous sessions)
//   - Video submission to Flask /analyse endpoint
//   - Session saving and loading from Firestore
//   - Session deletion from Firestore
//   - Collapsible session cards in Previous Sessions view
// ============================================================

// ---- API Configuration Import ----
import { API_BASE_URL } from "../../utils/config.js";

// --- Firebase Imports ---
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFirestore, collection, addDoc, getDocs, query, where, serverTimestamp, deleteDoc, doc} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// --- Firebase Initialisation ---
const firebaseConfiguration = {
    apiKey: "AIzaSyCWU0uF-ccoeQtUqUZNnUUikpZpWzVpbWk",
    authDomain: "dissertation-4cc1f.firebaseapp.com",
    projectId: "dissertation-4cc1f",
    storageBucket: "dissertation-4cc1f.firebasestorage.app",
    messagingSenderId: "435297202455",
    appId: "1:435297202455:web:95eebf2e791097a1468752"
};
const app = initializeApp(firebaseConfiguration);
const auth = getAuth(app);
const db = getFirestore(app);

// --- Session State ---
const sessionState = {
    currentDrillType: null,
    currentDrill: null,
    drillsCompleted: [],
    videoCount: 0,
    videos: []
};

// --- Available Drills ---
const drills = {
    batting: [
        {
            id: 'batting-stance',
            name: 'Batting Stance',
            available: true,
            instructions: [
                'Stand with your feet shoulder-width apart.',
                'Hold the bat with a relaxed grip.',
                'Bend your knees slightly and keep your back straight.',
                'Ensure your eyes are in line and your head is straight.',
                'Film a 2-3 second video of your stance in landscape (horizontal) mode for best results.'
            ]
        },
        { id: 'front-foot-defense', name: 'Front Foot Defense', available: false },
        { id: 'back-foot-defense', name: 'Back Foot Defense', available: false },
        { id: 'shot-selection', name: 'Shot Selection', available: false }
    ],
    bowling:  [],
    fielding: [],
    fitness:  []
};

// ---- View Navigation ----
function showView(viewId) {
    document.querySelectorAll('[id^="view-"]').forEach(v => v.style.display = 'none');
    document.getElementById(viewId).style.display = 'block';
}

// ---- Drill List ----
function fillDrillList(type) {
    const drillBlock = document.getElementById('drill-list-block');
    drillBlock.innerHTML = '';
    document.getElementById('drill-list-title').textContent =
        type.charAt(0).toUpperCase() + type.slice(1) + ' Drills';

    drills[type].forEach(drill => {
        const card = document.createElement('div');
        card.className = 'drill-card';
        card.innerHTML = `
            <span>${drill.name}</span>
            <span class="${drill.available ? 'available' : 'coming-soon'}">
                ${drill.available ? 'Available' : 'Coming Soon'}
            </span>
            ${drill.available
                ? `<button class="select-button" data-drill-id="${drill.id}" data-drill-name="${drill.name}">Select</button>`
                : ''}
        `;
        drillBlock.appendChild(card);
    });

    // ---- Drill Select Listeners ----
    drillBlock.querySelectorAll('[data-drill-id]').forEach(button => {
        button.addEventListener('click', () => {
            const selected = drills[sessionState.currentDrillType]
                .find(d => d.id === button.getAttribute('data-drill-id'));

            sessionState.currentDrill = {
                id: button.dataset.drillId,
                name: button.dataset.drillName,
                videos: []
            };

            document.getElementById('tutorial-title').textContent =
                button.dataset.drillName + ' - Tutorial';

            const list = document.getElementById('drill-instructions');
            list.innerHTML = '';
            if (selected?.instructions) {
                selected.instructions.forEach(step => {
                    const li = document.createElement('li');
                    li.textContent = step;
                    list.appendChild(li);
                });
            }

            showView('view-tutorial');
        });
    });
}

// ---- Upload View Reset ----
function resetUploadView() {
    sessionState.videoCount = 0;
    sessionState.videos = [];
    document.getElementById('video-count').textContent = 0;
    document.getElementById('video-list').innerHTML = '';
    document.getElementById('submit-video').style.display = '';
    document.getElementById('video-upload').style.display = '';
    document.getElementById('submit-video').disabled = false;
    document.getElementById('submit-video').textContent = 'Submit Video';
    document.getElementById('video-upload').value = '';
    document.getElementById('file-name-display').textContent = 'No file chosen';
    document.getElementById('remove-file-button').style.display = 'none';
}

// ---- Event Listeners ----
document.addEventListener('DOMContentLoaded', () => {

    // ---- Landing ----
    document.getElementById('create-session-button').addEventListener('click', () => {
        sessionState.currentDrillType = null;
        sessionState.currentDrill = null;
        sessionState.drillsCompleted = [];
        resetUploadView();
        showView('view-drill-types');
    });

    document.getElementById('previous-sessions-button').addEventListener('click', () => {
        showView('view-previous-sessions');
        loadPreviousSessions();
    });

    // ---- Back Buttons ----
    document.getElementById('back-to-landing-button').addEventListener('click', () => showView('view-landing'));
    document.getElementById('back-to-landing-from-sessions').addEventListener('click', () => showView('view-landing'));
    document.getElementById('back-to-drill-types-button').addEventListener('click', () => showView('view-drill-types'));
    document.getElementById('back-to-upload').addEventListener('click', () => showView('view-video-upload'));

    document.getElementById('back-to-drill-list').addEventListener('click', () => {
        if (sessionState.currentDrill && sessionState.videoCount > 0) {
            if (!window.confirm('You have uploaded videos for this drill. Going back will reset your progress. Continue?')) return;
            resetUploadView();
            sessionState.currentDrill = null;
        }
        showView('view-drill-list');
    });

    document.getElementById('back-to-tutorial').addEventListener('click', () => {
        if (sessionState.videoCount > 0) {
            if (!window.confirm('You have uploaded videos for this drill. Going back will reset your progress. Continue?')) return;
            resetUploadView();
        } else {
            document.getElementById('video-upload').value = '';
            document.getElementById('file-name-display').textContent = 'No file chosen';
        }

        // ---- Repopulate Tutorial Instructions ----
        const list = document.getElementById('drill-instructions');
        list.innerHTML = '';
        const drillData = drills[sessionState.currentDrillType]
            ?.find(d => d.id === sessionState.currentDrill?.id);
        drillData?.instructions?.forEach(step => {
            const li = document.createElement('li');
            li.textContent = step;
            list.appendChild(li);
        });

        showView('view-tutorial');
    });

    // ---- Drill Type Selection ----
    document.getElementById('batting-drills-button').addEventListener('click', () => {
        sessionState.currentDrillType = 'batting';
        fillDrillList('batting');
        showView('view-drill-list');
    });

    // ---- Start Drill ----
    document.getElementById('start-drill').addEventListener('click', () => {
        if (!sessionState.videos.length) resetUploadView();
        showView('view-video-upload');
    });

    // ---- File Selection ----
    document.getElementById('video-upload').addEventListener('change', () => {
        const file = document.getElementById('video-upload').files[0];
        document.getElementById('file-name-display').textContent = file ? file.name : 'No file chosen';
        document.getElementById('remove-file-button').style.display = file ? '' : 'none';
    });

    document.getElementById('remove-file-button').addEventListener('click', () => {
        document.getElementById('video-upload').value = '';
        document.getElementById('file-name-display').textContent = 'No file chosen';
        document.getElementById('remove-file-button').style.display = 'none';
    });

    // ---- Add Another Drill ----
    document.getElementById('add-another-drill').addEventListener('click', () => {
        if (sessionState.videos.length === 0) {
            alert('Please upload at least one video before adding another drill.');
            return;
        }
        if (sessionState.currentDrill) {
            sessionState.drillsCompleted.push({
                name: sessionState.currentDrill.name,
                videoCount: sessionState.videos.length
            });
            sessionState.currentDrill = null;
        }
        resetUploadView();
        showView('view-drill-types');
    });

    // ---- End Session ----
    document.getElementById('end-session').addEventListener('click', () => {
        if (sessionState.drillsCompleted.length === 0 && sessionState.videos.length === 0) {
            alert('Please add a drill or upload a video before ending the session.');
            return;
        }
        if (sessionState.videos.length === 0) {
            alert('Please upload at least one video before ending the session.');
            return;
        }

        showView('view-session-summary');

        const summaryList = document.getElementById('summary-drill-list');
        summaryList.innerHTML = '';
        const allDrills = sessionState.currentDrill
            ? [...sessionState.drillsCompleted, { name: sessionState.currentDrill.name, videoCount: sessionState.videos.length }]
            : sessionState.drillsCompleted;

        allDrills.forEach(drill => {
            const li = document.createElement('li');
            li.textContent = `${drill.name} - ${drill.videoCount} video(s)`;
            summaryList.appendChild(li);
        });
    });

    // ---- Video Submission ----
    document.getElementById('submit-video').addEventListener('click', async () => {
        const videoInput = document.getElementById('video-upload');
        const file = videoInput.files[0];

        if (!file) {
            alert('Please select a video file to upload.');
            return;
        }
        if (sessionState.videoCount >= 5) {
            alert('You have reached the maximum number of videos for this drill.');
            return;
        }

        const submitButton = document.getElementById('submit-video');
        submitButton.disabled = true;
        submitButton.textContent = 'Uploading & Analysing...';

        const formData = new FormData();
        formData.append('video', file);
        const user = auth.currentUser;

        try {
            // ---- Send Video to Flask ----
            const response = await fetch(`${API_BASE_URL}/analyse`, {
                method: 'POST',
                headers: { 'X-User-Id': user ? user.uid : 'anonymous' },
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to upload and analyse video');
            }

            const result = await response.json();

            // ---- Update Session State ----
            sessionState.videoCount++;
            const videoId = Date.now();
            sessionState.videos.push({
                id: videoId,
                url: result.video_url,
                best_frame_url: result.best_frame_url,
                feedback: result.feedback,
                results: result.results
            });
            document.getElementById('video-count').textContent = sessionState.videoCount;

            // ---- Render Video Card ----
            const videoContainer = document.createElement('div');
            videoContainer.className = 'video-card';
            videoContainer.dataset.index = sessionState.videoCount - 1;
            videoContainer.innerHTML = `
                <div class="video-card-header">
                    <strong>Video ${sessionState.videoCount}:</strong>
                    <button class="delete-video-button session-button" data-index="${sessionState.videoCount - 1}">Delete</button>
                </div>
                <div class="video-media-row">
                    <div class="media-column">
                        <p class="video-label">Anonymised Video:</p>
                        <video width="100%" controls crossorigin="anonymous">
                            <source src="${result.video_url}">
                        </video>
                    </div>
                    ${result.best_frame_url ? `
                        <div class="media-column">
                            <p class="video-label">Best Frame:</p>
                            <img src="${result.best_frame_url}" style="width:100%; border-radius:8px; background-color:#000;">
                        </div>
                    ` : ''}
                </div>
                <div class="video-feedback">
                    <p>${result.feedback || 'No feedback available.'}</p>
                    <div class="video-results">
                        ${Object.values(result.results).map(check => `
                            <div class="result-row">
                                <span class="result-check">${check.check}</span>
                                <span class="result-status status-${check.status.toLowerCase()}">${check.status}</span>
                                <span class="result-message">${check.message}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            document.getElementById('video-list').appendChild(videoContainer);

            // ---- Delete Video Button ----
            videoContainer.querySelector('.delete-video-button').addEventListener('click', () => {
                sessionState.videos = sessionState.videos.filter(v => v.id !== videoId);
                sessionState.videoCount--;
                document.getElementById('video-count').textContent = sessionState.videoCount;
                videoContainer.remove();
                document.getElementById('video-upload').value = '';
                document.getElementById('file-name-display').textContent = 'No file chosen';
                if (sessionState.videoCount < 5) {
                    document.getElementById('submit-video').style.display = '';
                    document.getElementById('video-upload').style.display = '';
                }
            });

        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            if (sessionState.videoCount < 5) {
                submitButton.textContent = 'Submit Video';
                submitButton.disabled = false;
            }
            videoInput.value = '';
        }
    });

    // ---- Save Session ----
    document.getElementById('save-session-button').addEventListener('click', async () => {
        if (sessionState.currentDrill) {
            sessionState.drillsCompleted.push({
                name: sessionState.currentDrill.name,
                videoCount: sessionState.videos.length
            });
            sessionState.currentDrill = null;
        }

        const sessionName = document.getElementById('session-name').value.trim();
        if (!sessionName) {
            alert('Please enter a name for your session.');
            return;
        }
        if (!auth.currentUser) {
            alert('You must be logged in to save a session.');
            return;
        }

        const saveButton = document.getElementById('save-session-button');
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';

        try {
            await addDoc(collection(db, 'practice_sessions'), {
                userId: auth.currentUser.uid,
                sessionName: sessionName,
                drillsCompleted: sessionState.drillsCompleted.map(d => d.name),
                videos: sessionState.videos.filter(v => v.url),
                timestamp: serverTimestamp()
            });

            alert('Session saved successfully!');
            sessionState.drillsCompleted = [];
            sessionState.videoCount = 0;
            sessionState.videos = [];
            document.getElementById('session-name').value = '';
            showView('view-landing');

        } catch (error) {
            alert('Error saving session: ' + error.message);
        } finally {
            saveButton.textContent = 'Save Session';
            saveButton.disabled = false;
        }
    });

});

// ---- Load Previous Sessions ----
async function loadPreviousSessions() {
    const container = document.getElementById('previous-sessions-list');
    container.innerHTML = '<p>Loading sessions...</p>';

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
        unsubscribe();
        if (!user) {
            alert('You must be logged in to view previous sessions.');
            return;
        }

        try {
            const q = query(
                collection(db, 'practice_sessions'),
                where('userId', '==', user.uid)
            );
            const snapshot = await getDocs(q);
            container.innerHTML = '';

            if (snapshot.empty) {
                container.innerHTML = '<p>No previous sessions found.</p>';
                return;
            }

            snapshot.forEach(docSnapshot => {
                const data = docSnapshot.data();
                const card = document.createElement('div');
                card.className = 'session-card';

                const date = data.timestamp?.toDate
                    ? data.timestamp.toDate().toLocaleString('en-GB')
                    : 'Unknown Date';

                // ---- Build Video Cards HTML ----
                const videosHTML = (data.videos || []).map((video, index) => `
                    <div class="video-card">
                        <div class="video-card-header">
                            <strong>Video ${index + 1}:</strong>
                        </div>
                        <div class="video-media-row">
                            <div class="media-column">
                                <p class="video-label">Anonymised Video:</p>
                                <video width="100%" controls crossorigin="anonymous">
                                    <source src="${video.url}">
                                </video>
                            </div>
                            ${video.best_frame_url ? `
                                <div class="media-column">
                                    <p class="video-label">Best Frame:</p>
                                    <img src="${video.best_frame_url}" style="width:100%; border-radius:8px; background-color:#000;">
                                </div>
                            ` : ''}
                        </div>
                        <div class="video-feedback">
                            <p>${video.feedback || 'No feedback available.'}</p>
                            <div class="video-results">
                                ${Object.values(video.results || {}).map(check => `
                                    <div class="result-row">
                                        <span class="result-check">${check.check}</span>
                                        <span class="result-status status-${check.status.toLowerCase()}">${check.status}</span>
                                        <span class="result-message">${check.message}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `).join('');

                // ---- Session Card Template ----
                card.innerHTML = `
                    <div class="session-card-header">
                        <div>
                            <h3 style="margin:0; color:#457a00;">${data.sessionName}</h3>
                            <p style="margin:4px 0 0 0; font-size:13px; color:#555;">
                                <strong>Date:</strong> ${date} &nbsp;|&nbsp;
                                <strong>Drills:</strong> ${data.drillsCompleted.join(', ')}
                            </p>
                        </div>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <button class="delete-session-btn">Delete</button>
                            <button class="session-toggle-btn">▼</button>
                        </div>
                    </div>
                    <div class="session-card-content">
                        ${videosHTML}
                    </div>
                `;

                // ---- Toggle Expand/Collapse ----
                const header = card.querySelector('.session-card-header');
                const content = card.querySelector('.session-card-content');
                const toggleBtn = card.querySelector('.session-toggle-btn');
                header.addEventListener('click', () => {
                    const expanded = content.classList.toggle('expanded');
                    toggleBtn.textContent = expanded ? '▲' : '▼';
                });

                // ---- Delete Session ----
                const deleteBtn = card.querySelector('.delete-session-btn');
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (!window.confirm('Are you sure you want to delete this session? This cannot be undone.')) return;
                    try {
                        await deleteDoc(doc(db, 'practice_sessions', docSnapshot.id));
                        card.remove();
                        if (container.querySelectorAll('.session-card').length === 0) {
                            container.innerHTML = '<p>No previous sessions found.</p>';
                        }
                    } catch (error) {
                        console.error('Error deleting session:', error);
                    }
                });

                container.appendChild(card);
            });

        } catch (error) {
            container.innerHTML = '<p>Error loading sessions: ' + error.message + '</p>';
        }
    });
}

// ---- Page Unload Warning ----
window.addEventListener('beforeunload', (e) => {
    if (sessionState.drillsCompleted.length > 0 || sessionState.videos.length > 0) {
        e.preventDefault();
        e.returnValue = '';
    }
});
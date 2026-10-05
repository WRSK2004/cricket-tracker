// ===============================================================
// Title: api.js
// Calls the backend API with the signed-in user's Firebase ID token,
// so the backend can verify who is making the request.
// Errors from the backend ({"error": "..."}) are thrown as Error objects.
// ===============================================================

import { API_BASE_URL } from "./config.js";
import { auth } from "./firebase.js";

// ---- Authenticated Request ----
export async function apiFetch(path, options = {}) {
    const user = auth.currentUser;
    if (!user) {
        throw new Error("You need to be signed in to do that.");
    }
    const token = await user.getIdToken();

    const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
    // JSON bodies are sent as JSON; FormData sets its own content type
    let body = options.body;
    if (body && !(body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, body });
    } catch {
        throw new Error("Could not reach the server. Please check your connection and try again.");
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || "Something went wrong. Please try again.");
    }
    return data;
}

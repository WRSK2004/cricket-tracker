// ===============================================================
// Title: html.js
// Escapes text before it is inserted with innerHTML, so names,
// AI feedback or other stored text can't inject HTML or scripts.
// ===============================================================

const HTML_ESCAPES = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
};

export function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => HTML_ESCAPES[character]);
}

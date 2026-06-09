// ================================================================
// Title: help.js
// Handles collapsible sections for Getting Started and FAQ
// Each button reveals or hides the corresponding answer when clicked
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    // ---- Collapsible Toggle ----
    document.querySelectorAll('.collapsible-button').forEach(button => {
        button.addEventListener('click', () => {
            const answer = button.nextElementSibling;
            if (answer.style.display === 'none' || answer.style.display === '') {
                answer.style.display = 'block';
            } else {
                answer.style.display = 'none';
            }
        });
    });
});
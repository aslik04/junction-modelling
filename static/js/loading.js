// Automatically redirect to results page once it's ready
const urlParams = new URLSearchParams(window.location.search);
const session_id = urlParams.get('session_id');
const run_id = urlParams.get('run_id');

function checkAndRedirect() {
    window.location.href = `/results?session_id=${session_id}&run_id=${run_id}`;
}

// Wait a few seconds before redirecting
setTimeout(checkAndRedirect, 5000); // Redirect after 5 seconds
// Optional: You can move the player-related JavaScript here if you want to separate concerns
// The code would be the same as in the index.html script tag

// Example of how you might structure it:
async function fetchStreamDetails() {
    try {
        const response = await fetch('/stream-details');
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const streamDetails = await response.json();
        
        // Setup JW Player with fetched details
        setupPlayer(streamDetails);
    } catch (error) {
        console.error('Error fetching stream details:', error);
        document.getElementById('loadingMessage').textContent = 'Failed to load stream. Please check the server.';
    }
}

function setupPlayer(streamDetails) {
    try {
        // Hide loading message
        document.getElementById('loadingMessage').style.display = 'none';

        // Setup JW Player with details from server
        jwplayer("jwplayerDiv").setup({
            file: streamDetails.file || "",
            type: "dash",
            drm: {
                "clearkey": {
                    "keyId": streamDetails.keyId || "",
                    "key": streamDetails.key || ""
                }
            },
            width: "100%",
            height: "500px"
        });
    } catch (error) {
        console.error('Error setting up player:', error);
        document.getElementById('loadingMessage').textContent = 'Failed to initialize player.';
    }
}

// Fetch stream details when page loads
document.addEventListener('DOMContentLoaded', fetchStreamDetails);

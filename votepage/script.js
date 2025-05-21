// Cache DOM elements
const kingSelect = document.getElementById('kingSelect');
const queenSelect = document.getElementById('queenSelect');
const voteBtn = document.getElementById('voteBtn');
const messageDiv = document.getElementById('message');

// Check if already voted (both localStorage and cookies)
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

const hasVoted = localStorage.getItem('hasVoted') || getCookie('vote_status');
if (hasVoted) {
    voteBtn.disabled = true;
    showMessage('You have already voted!', true);
}

// Generate a unique device token
function generateDeviceToken() {
    const existingToken = localStorage.getItem('deviceToken');
    if (existingToken) return existingToken;

    const token = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');

    localStorage.setItem('deviceToken', token);
    return token;
}

// Sample candidates - in a real app, these could be fetched from server
const candidates = {
    kings: ['Candidate 1', 'Candidate 2', 'Candidate 3', 'Candidate 4'],
    queens: ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D']
};

// Populate select options
function populateSelect(select, options) {
    options.forEach(option => {
        const optElement = document.createElement('option');
        optElement.value = option;
        optElement.textContent = option;
        select.appendChild(optElement);
    });
}

// Initialize selects
populateSelect(kingSelect, candidates.kings);
populateSelect(queenSelect, candidates.queens);

// Handle vote submission
async function submitVote() {
    try {
        if (!kingSelect.value && !queenSelect.value) {
            throw new Error('Please select at least one candidate');
        }

        // Prevent multiple submissions
        if (voteBtn.disabled) {
            return;
        }

        // Disable button immediately
        voteBtn.disabled = true;
        
        const vote = {
            pop_king: kingSelect.value || null,
            pop_queen: queenSelect.value || null,
            device_token: generateDeviceToken()
        };

        const response = await fetch('http://localhost:8000/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(vote),
            mode: 'cors', // Add CORS mode explicitly
            cache: 'no-cache',
            credentials: 'same-origin'
        }).catch(error => {
            // Handle network errors specifically
            throw new Error('Server connection failed. Please check if the server is running.');
        });

        if (response.status === 403) {
            throw new Error('You have already voted');
        }

        if (!response.ok) {
            throw new Error(`Vote failed: ${response.statusText}`);
        }

        const result = await response.json();
        showMessage('Vote submitted successfully!', false);
        localStorage.setItem('hasVoted', 'true');
        
        // Reset form
        kingSelect.value = '';
        queenSelect.value = '';
    } catch (error) {
        showMessage(error.message, true);
        console.error('Vote error:', error); // Add error logging
    } finally {
        // Only re-enable button if there was an error
        if (!localStorage.getItem('hasVoted')) {
            voteBtn.disabled = false;
        }
    }
}


// Show message to user
function showMessage(text, isError = false) {
    messageDiv.textContent = text;
    messageDiv.className = 'message' + (isError ? ' error' : '');
    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = 'message';
    }, 3000);
}

// Event listeners
voteBtn.addEventListener('click', submitVote);

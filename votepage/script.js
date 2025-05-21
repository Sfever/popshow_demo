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
        // Disable button to prevent double submission
        voteBtn.disabled = true;
        const vote = {
            pop_king: kingSelect.value || null,
            pop_queen: queenSelect.value || null,
            device_token: generateDeviceToken()
        };

        // Only send votes that have been selected
        const response = await fetch('https://localhost:8000/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(vote)
        }); const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Vote failed');
        }

        // Show success message
        showMessage('Vote submitted successfully!', false);

        // Mark as voted in localStorage
        localStorage.setItem('hasVoted', 'true');

        // Disable the vote button
        voteBtn.disabled = true;

        // Reset form
        kingSelect.value = '';
        queenSelect.value = '';
    } catch (error) {
        showMessage('Failed to submit vote. Please try again.', true);
    } finally {
        voteBtn.disabled = false;
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

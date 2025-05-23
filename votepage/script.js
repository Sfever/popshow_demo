// Cache DOM elements
// Remove hard-coded select references
// const kingSelect = document.getElementById('kingSelect');
// const queenSelect = document.getElementById('queenSelect');
// const voteBtn = document.getElementById('voteBtn');
// const messageDiv = document.getElementById('message');

// Define voting categories and their options
async function fetchCandidates() {
    try {
        const response = await fetch('http://localhost:8000/candidates', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Failed to fetch candidates: ${response.statusText}`);
        return await response.json();
    }
    catch (error) {
        const categories = {
            pop_king: ['Candidate 1', 'Candidate 2', 'Candidate 3', 'Candidate 4'],
            pop_queen: ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D'],
            most_spirited_dance: ['Dance 1', 'Dance 2', 'Dance 3'],
            most_dazzling_dance: ['Dance 4', 'Dance 5', 'Dance 6'],
            most_attractive_dance: ['Dance 7', 'Dance 8', 'Dance 9'],
            meishi_grammy: ['Artist X', 'Artist Y'],
            best_band: ['Band Alpha', 'Band Beta']
        };
        return categories;
    }
}
const categories = await fetchCandidates();


// Cache common elements
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

// Populate select options
function populateSelect(select, options) {
    options.forEach(option => {
        const optElement = document.createElement('option');
        optElement.value = option;
        optElement.textContent = option;
        select.appendChild(optElement);
    });
}

// Populate each select dynamically
Object.entries(categories).forEach(([category, options]) => {
    const select = document.getElementById(`${category}_select`);
    if (!select) return;
    populateSelect(select, options);
});

// Handle vote submission
async function submitVote() {
    try {
        // Ensure every category has a selection
        const emptyCategories = Object.keys(categories).filter(cat => {
            const val = document.getElementById(`${cat}_select`).value;
            return !val; // Return true for empty values
        });
        
        if (emptyCategories.length > 0) {
            throw new Error(`Please select options for all categories`);
        }

        if (voteBtn.disabled) return;
        voteBtn.disabled = true;

        // Build vote payload
        const vote = {};
        Object.keys(categories).forEach(cat => {
            const val = document.getElementById(`${cat}_select`).value;
            vote[cat] = val;
        });
        vote.name=document.getElementById('name_input').value;
        if (!vote.name) {
            throw new Error('Please enter your name');
        }
        vote.grade=document.getElementById('grade_select').value;
        if (!vote.grade) {
            throw new Error('Please select your grade');
        }
        const device_token = generateDeviceToken();

        const response = await fetch('http://localhost:8000/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Device-Token': device_token
            },
            body: JSON.stringify(vote),
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin'
        });

        if (response.status === 403) throw new Error('You have already voted');
        if (!response.ok) throw new Error(`Vote failed: ${response.statusText}`);

        await response.json();
        showMessage('Vote submitted successfully!', false);
        localStorage.setItem('hasVoted', 'true');

        // Reset all selects
        Object.keys(categories).forEach(cat => document.getElementById(`${cat}_select`).value = '');
    } catch (error) {
        showMessage(error.message, true);
        console.error('Vote error:', error);
    } finally {
        if (!localStorage.getItem('hasVoted')) voteBtn.disabled = false;
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

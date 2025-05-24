// Mock data function to simulate getting data from a remote source
function generateMockData(count) {
    return Array.from({ length: count }, (_, i) => ({
        id: i + 1,
        name: `Player ${i + 1}`,
        score: Math.floor(Math.random() * 1000)
    })).sort((a, b) => b.score - a.score);
}

// Store previous rankings to detect changes
const previousRankings = {
    pop_king: new Map(),
    pop_queen: new Map(),
    most_spirited_dance: new Map(),
    most_dazzling_dance: new Map(),
    most_attractive_dance: new Map(),
    meishi_grammy: new Map(),
    best_band: new Map()
};

// Store positions and dimensions for smooth transitions
let rankingPositions = new Map();

function getItemPosition(element) {
    return {
        top: element.offsetTop,
        height: element.offsetHeight
    };
}

function convertVotesToRankingData(votes, category) {
    return Object.entries(votes[category] || {}).map(([name, score], index) => ({
        id: name, // Use name as ID since it's unique
        name: name,
        score: score
    }));
}

function updateRankingList(elementId, data) {
    const container = document.getElementById(elementId);
    const previousRanking = previousRankings[elementId];
    const ITEM_HEIGHT = 48;
    const ITEM_MARGIN = 8;
    const TOTAL_ITEM_HEIGHT = ITEM_HEIGHT + ITEM_MARGIN;

    // Sort data by score
    data.sort((a, b) => b.score - a.score);

    // Track existing items
    const existingItems = new Map();
    Array.from(container.children).forEach(item => {
        existingItems.set(item.dataset.id, item);
    });

    // Update or create items
    data.forEach((item, newIndex) => {
        const itemId = item.id.toString();
        const existingItem = existingItems.get(itemId);
        const newTop = newIndex * TOTAL_ITEM_HEIGHT;

        if (existingItem) {
            // Update existing item
            const prevIndex = previousRanking.get(itemId);
            
            // Update content without removing the element
            existingItem.querySelector('.rank').textContent = `#${newIndex + 1}`;
            existingItem.querySelector('.name').textContent = item.name;
            existingItem.querySelector('.score').textContent = item.score;
            
            // Handle movement
            if (prevIndex !== newIndex) {
                existingItem.style.transition = 'none';
                existingItem.classList.remove('moving-up', 'moving-down');
                
                // Force reflow
                existingItem.offsetHeight;
                existingItem.style.transition = 'top 2s ease-in-out, background-color 0.3s ease';
                existingItem.classList.add(prevIndex > newIndex ? 'moving-up' : 'moving-down');
                existingItem.style.top = `${newTop}px`;

                // Remove movement classes after animation
                setTimeout(() => {
                    existingItem.classList.remove('moving-up', 'moving-down');
                }, 2000);
            }
            
            // Mark as processed
            existingItems.delete(itemId);
        } else {
            // Create new item
            const newItem = document.createElement('div');
            newItem.className = 'ranking-item';
            newItem.dataset.id = itemId;
            newItem.style.opacity = '0';
            newItem.style.top = `${newTop}px`;
            newItem.innerHTML = `
                <span class="rank">#${newIndex + 1}</span>
                <span class="name">${item.name}</span>
                <span class="score">${item.score}</span>
            `;
            container.appendChild(newItem);
            
            // Fade in new item
            requestAnimationFrame(() => {
                newItem.style.transition = 'opacity 0.5s ease-in-out';
                newItem.style.opacity = '1';
            });
        }
        
        // Update previous ranking
        previousRanking.set(itemId, newIndex);
    });
    
    // Remove items that are no longer in the data
    existingItems.forEach(item => {
        item.style.transition = 'all 0.5s ease-in-out';
        item.style.opacity = '0';
        setTimeout(() => item.remove(), 500);
    });
}

async function getRankings() {
    try {
        const response = await fetch('https://popshow.sfever.org/votes');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        
        // Transform the data into the format we need
        return {
            pop_king: convertVotesToRankingData(data, 'pop_king'),
            pop_queen: convertVotesToRankingData(data, 'pop_queen'),
            most_spirited_dance: convertVotesToRankingData(data, 'most_spirited_dance'),
            most_dazzling_dance: convertVotesToRankingData(data, 'most_dazzling_dance'),
            most_attractive_dance: convertVotesToRankingData(data, 'most_attractive_dance'),
            meishi_grammy: convertVotesToRankingData(data, 'meishi_grammy'),
            best_band: convertVotesToRankingData(data, 'best_band')
        };
    } catch (error) {
        console.error('Error fetching rankings:', error);
        // Fallback to mock data in case of error
        return {
            pop_king: generateMockData(15),
            pop_queen: generateMockData(15),
            most_spirited_dance: generateMockData(15),
            most_dazzling_dance: generateMockData(15),
            most_attractive_dance: generateMockData(15),
            meishi_grammy: generateMockData(15),
            best_band: generateMockData(15)
        };
    }
}

// Function to update all rankings with online data
async function updateAllRankingsOnline() {
    try {
        const rankingsData = await getRankings();
        Object.entries(rankingsData).forEach(([elementId, data]) => {
            updateRankingList(elementId, data);
        });
    } catch (error) {
        console.error('Failed to update rankings:', error);
    }
}

// Initialize rankings and start updates
document.addEventListener('DOMContentLoaded', () => {
    // Start with mock data while loading real data
    updateAllRankings();
    // Then immediately try to get real data
    updateAllRankingsOnline();
});

// Update every 3 second
setInterval(updateAllRankingsOnline, 3000);
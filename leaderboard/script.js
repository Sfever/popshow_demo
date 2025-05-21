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
    rankingA: new Map(),
    rankingB: new Map(),
    rankingC: new Map(),
    rankingD: new Map()
};

// Store positions and dimensions for smooth transitions
let rankingPositions = new Map();

function getItemPosition(element) {
    return {
        top: element.offsetTop,
        height: element.offsetHeight
    };
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
            const prevIndex = previousRanking.get(Number(itemId));
            
            // Update content without removing the element
            existingItem.querySelector('.rank').textContent = `#${newIndex + 1}`;
            existingItem.querySelector('.name').textContent = item.name;
            existingItem.querySelector('.score').textContent = item.score;
            
            // Handle movement
            if (prevIndex !== newIndex) {
                existingItem.style.transition = 'none';
                existingItem.classList.remove('moving-up', 'moving-down');
                
                // Force reflow
                existingItem.offsetHeight;                existingItem.style.transition = 'top 2s ease-in-out, background-color 0.3s ease';
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
        previousRanking.set(Number(itemId), newIndex);
    });
    
    // Remove items that are no longer in the data
    existingItems.forEach(item => {
        item.style.transition = 'all 0.5s ease-in-out';
        item.style.opacity = '0';
        setTimeout(() => item.remove(), 500);
    });
}

// Function to update all rankings
function updateAllRankings() {    const rankingsData = {
        rankingA: generateMockData(20),
        rankingB: generateMockData(20),
        rankingC: generateMockData(20),
        rankingD: generateMockData(20)
    };

    Object.entries(rankingsData).forEach(([elementId, data]) => {
        updateRankingList(elementId, data);
    });
}

// Initialize rankings on load
document.addEventListener('DOMContentLoaded', () => {
    updateAllRankings();
});

// Update every 10 seconds
setInterval(updateAllRankings, 10000);

// In a real application, you would replace generateMockData with actual API calls
// Example with fetch:
/*
async function fetchRankings() {
    try {
        const response = await fetch('your-api-endpoint');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching rankings:', error);
        return generateMockData(10); // Fallback to mock data
    }
}
*/

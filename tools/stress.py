import asyncio
import aiohttp
import json
import uuid
import random
from rich.console import Console
from rich.progress import track

console = Console()

CANDIDATES = {
    "pop_king": ["Justin Bieber", "Harry Styles", "The Weeknd", "Ed Sheeran"],
    "pop_queen": ["Taylor Swift", "Ariana Grande", "Lady Gaga", "Beyoncé"]
}

async def submit_vote(session, url):
    try:
        # Generate unique device token for each vote
        device_token = str(uuid.uuid4())
        
        # Create random vote data
        data = {
            "pop_king": random.choice(CANDIDATES["pop_king"]),
            "pop_queen": random.choice(CANDIDATES["pop_queen"])
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Device-Token": device_token
        }
        
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json(), response.status
    except Exception as e:
        return {"error": str(e)}, 500

async def get_votes(session, url):
    try:
        async with session.get(f"{url}/votes") as response:
            return await response.json(), response.status
    except Exception as e:
        return {"error": str(e)}, 500

async def stress_test():
    base_url = "http://localhost:8000"
    # Update the test parameters
    num_votes = 200  # Double the number of votes
    concurrent_requests = 20  # Double concurrent requests
    
    async with aiohttp.ClientSession() as session:
        # Test vote submission
        console.log("[yellow]Starting vote submission stress test...[/yellow]")
        tasks = []
        for _ in range(num_votes):
            task = submit_vote(session, base_url)
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                results = await asyncio.gather(*tasks)
                tasks = []
                
                # Check for server unavailability
                if any(status == 503 for _, status in results):
                    console.log("[red]Server became unavailable, stopping test[/red]")
                    return
        
        if tasks:
            await asyncio.gather(*tasks)
        
        # Test vote retrieval
        console.log("[yellow]Testing vote retrieval...[/yellow]")
        result, status = await get_votes(session, base_url)
        if status == 200:
            console.log("[green]Vote retrieval successful[/green]")
            console.log("Current vote counts:", result)
        else:
            console.log("[red]Vote retrieval failed[/red]")

def main():
    try:
        asyncio.run(stress_test())
    except KeyboardInterrupt:
        console.log("[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.log(f"[red]Test error: {e}[/red]")

if __name__ == "__main__":
    main()
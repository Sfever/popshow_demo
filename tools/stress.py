import asyncio
import aiohttp
import json
import uuid
import random
from rich.console import Console
from rich.progress import Progress, track
import time
import statistics  # Added for statistical analysis of timings

console = Console()

# Global candidates cache
CANDIDATES = {}

async def get_candidates():
    # Use global cache to avoid redundant API calls
        
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://popshow.sfever.org/candidates") as response:
                if response.status == 200:
                    CANDIDATES = await response.json()
                    return CANDIDATES
                else:
                    console.log("[red]Failed to fetch candidates[/red]")
                    return {
                        "pop_king": ["candidate1", "candidate2"],
                        "pop_queen": ["candidate1", "candidate2"],
                        "most_spirited_dance": ["candidate1", "candidate2"],
                        "most_dazzling_dance": ["candidate1", "candidate2"],
                        "most_attractive_dance": ["candidate1", "candidate2"],
                        "meishi_grammy": ["candidate1", "candidate2"],
                        "best_band": ["candidate1", "candidate2"]
                    }
        except Exception as e:
            console.log(f"[red]Error fetching candidates: {e}[/red]")
            return {
                "pop_king": ["candidate1", "candidate2"],
                "pop_queen": ["candidate1", "candidate2"],
                "most_spirited_dance": ["candidate1", "candidate2"],
                "most_dazzling_dance": ["candidate1", "candidate2"],
                "most_attractive_dance": ["candidate1", "candidate2"],
                "meishi_grammy": ["candidate1", "candidate2"],
                "best_band": ["candidate1", "candidate2"]
            }

async def submit_vote(session, url, candidates_source):
    start_time = time.time()
    request_timing = {
        "total": 0,
        "candidates_fetch": 0,
        "request_preparation": 0,
        "network": 0,
        "server_processing": 0
    }
    
    try:
        # Generate unique device token for each vote
        device_token = str(uuid.uuid4())
        
        # Add back the small delay to simulate user behavior
        prep_start = time.time()
        await asyncio.sleep(random.uniform(0.1, 0.2))
        
        # Get fresh candidates for each vote request
        # This simulates real users who would be loading the page each time
        candidates_start = time.time()
        request_timing["request_preparation"] = candidates_start - prep_start
        
        if candidates_source == "api":
            candidates = await get_candidates()
        else:
            candidates = candidates_source
        
        candidates_end = time.time()
        request_timing["candidates_fetch"] = candidates_end - candidates_start
        
        # Create random vote data
        data = {
            "pop_king": random.choice(candidates["pop_king"]),
            "pop_queen": random.choice(candidates["pop_queen"]),
            "most_attractive_dance": random.choice(candidates["most_attractive_dance"]),
            "most_dazzling_dance": random.choice(candidates["most_dazzling_dance"]),
            "most_spirited_dance": random.choice(candidates["most_spirited_dance"]),
            "meishi_grammy": random.choice(candidates["meishi_grammy"]),
            "best_band": random.choice(candidates["best_band"])
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Device-Token": device_token
        }
        
        # Add back a bit of delay before sending the request
        await asyncio.sleep(random.uniform(0.1, 0.3))  # Non-blocking delay
        
        network_start = time.time()
        async with session.post(url, json=data, headers=headers) as response:
            server_start = time.time()
            request_timing["network"] = server_start - network_start
            
            result = await response.json()
            server_end = time.time()
            request_timing["server_processing"] = server_end - server_start
            
            end_time = time.time()
            request_timing["total"] = end_time - start_time
            
            return result, response.status, request_timing
    except aiohttp.ClientError as e:
        console.log(f"[red]Client error: {e}[/red]")
        end_time = time.time()
        request_timing["total"] = end_time - start_time
        return {"error": str(e)}, 0, request_timing
    except Exception as e:
        console.log(f"[red]Unexpected error: {e}[/red]")
        end_time = time.time()
        request_timing["total"] = end_time - start_time
        return {"error": str(e)}, 500, request_timing

async def get_votes(session, url):
    start_time = time.time()
    try:
        async with session.get(f"{url}/votes") as response:
            result = await response.json()
            end_time = time.time()
            timing = {"total": end_time - start_time}
            return result, response.status, timing
    except Exception as e:
        end_time = time.time()
        timing = {"total": end_time - start_time}
        return {"error": str(e)}, 500, timing

def generate_timing_report(timing_stats):
    """Generate a more detailed timing report with percentiles."""
    if not timing_stats["total"]:
        return "No timing data available"
    
    report = []
    report.append("\n[bold]DETAILED TIMING ANALYSIS[/bold]")
    
    # Calculate percentiles for each timing category
    for key in timing_stats:
        if timing_stats[key]:
            data = sorted(timing_stats[key])
            count = len(data)
            
            if count < 1:
                continue
                
            report.append(f"\n[bold cyan]{key.upper()}[/bold cyan]")
            report.append(f"  Sample count: {count}")
            report.append(f"  Min: {min(data):.4f} sec")
            report.append(f"  Max: {max(data):.4f} sec")
            report.append(f"  Avg: {sum(data) / count:.4f} sec")
            
            # Calculate percentiles
            percentiles = [50, 75, 90, 95, 99]
            for p in percentiles:
                idx = int((p/100.0) * count)
                if idx >= count:
                    idx = count - 1
                report.append(f"  {p}th percentile: {data[idx]:.4f} sec")
            
            # Calculate standard deviation if we have enough data
            if count > 1:
                report.append(f"  StdDev: {statistics.stdev(data):.4f}")
    
    # Add section about performance bottlenecks
    report.append("\n[bold]PERFORMANCE ANALYSIS[/bold]")
    
    # Determine bottlenecks
    if timing_stats["total"]:
        avg_total = sum(timing_stats["total"]) / len(timing_stats["total"])
        components = ["candidates_fetch", "request_preparation", "network", "server_processing"]
        component_averages = {}
        
        for comp in components:
            if timing_stats[comp] and len(timing_stats[comp]) > 0:
                component_averages[comp] = sum(timing_stats[comp]) / len(timing_stats[comp])
                percentage = (component_averages[comp] / avg_total) * 100 if avg_total > 0 else 0
                report.append(f"  {comp}: {component_averages[comp]:.4f} sec ({percentage:.1f}% of total)")
        
        # Identify the slowest component
        if component_averages:
            slowest = max(component_averages.items(), key=lambda x: x[1])
            report.append(f"\n[bold red]Primary bottleneck appears to be: {slowest[0]} ({slowest[1]:.4f} sec)[/bold red]")
    
    return "\n".join(report)

async def stress_test():
    base_url = "http://popshow.sfever.org"
    # Update the test parameters
    num_votes = 2000  # Number of votes to simulate
    concurrent_requests = 50  # Concurrency level
    use_api_per_request = True  # Whether to make an API call for candidates on each request
    
    # Get candidates once - will be used if use_api_per_request is False
    candidates = await get_candidates()
    candidates_source = "api"
    
    # Use TCP connector with keep alive and higher limits
    connector = aiohttp.TCPConnector(limit=concurrent_requests, limit_per_host=concurrent_requests, keepalive_timeout=60)
    
    start_time = time.time()
    successes = 0
    failures = 0
    
    # Collect timing statistics
    timing_stats = {
        "total": [],
        "candidates_fetch": [],
        "request_preparation": [],
        "network": [],
        "server_processing": []
    }
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Test vote submission
        console.log(f"[yellow]Starting vote submission stress test with {num_votes} votes and {concurrent_requests} concurrent connections...[/yellow]")
        console.log(f"[yellow]API calls per request: {use_api_per_request}[/yellow]")
        
        # Create all tasks at once for maximum concurrency
        with Progress() as progress:
            task = progress.add_task("[cyan]Submitting votes...", total=num_votes)
            
            # Create batches for better tracking but process them concurrently
            batch_size = 100
            for i in range(0, num_votes, batch_size):
                batch_count = min(batch_size, num_votes - i)
                tasks = [submit_vote(session, base_url, candidates_source) for _ in range(batch_count)]
                results = await asyncio.gather(*tasks)
                
                for result, status, timing in results:
                    if status >= 200 and status < 300:
                        successes += 1
                        # Only include successful requests in timing statistics
                        for key in timing:
                            if key in timing_stats:
                                timing_stats[key].append(timing[key])
                    else:
                        failures += 1
                
                progress.update(task, advance=batch_count)
        
        end_time = time.time()
        duration = end_time - start_time
        rate = num_votes / duration if duration > 0 else 0
        
        console.log(f"[green]Completed {successes} successful votes in {duration:.2f} seconds[/green]")
        console.log(f"[yellow]Failed votes: {failures}[/yellow]")
        console.log(f"[blue]Rate: {rate:.2f} votes/second[/blue]")
        
        # Generate and display detailed timing report
        detailed_report = generate_timing_report(timing_stats)
        console.print(detailed_report)
        
        # Test vote retrieval
        console.log("[yellow]Testing vote retrieval...[/yellow]")
        result, status, timing = await get_votes(session, base_url)
        if status == 200:
            console.log("[green]Vote retrieval successful[/green]")
            console.log(f"[blue]Vote retrieval time: {timing['total']:.4f} seconds[/blue]")
            
            # Count total votes across all categories
            total_votes = 0
            for category, votes in result.items():
                if isinstance(votes, dict):
                    total_votes += sum(votes.values())
            console.log(f"[blue]Total votes recorded on server: {total_votes}[/blue]")
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
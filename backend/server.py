import json
import signal
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from rich.console import Console
import ssl
import sys
import os
import time

console = Console()

class VoteDatabaseWorker():
    def __init__(self):
        self.pop_king = {}
        self.pop_queen = {}
        self.most_spirited_dance = {}
        self.most_dazzling_dance = {}
        self.most_attractive_dance = {}
        self.meishi_grammy = {}
        self.best_band = {}
        self.voted_devices = set()
        self.running = True
        self.lock = threading.Lock()
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.data_dir, "vote_data.json")
        self._load_data()

    def _load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.pop_king = data.get('pop_king', {})
                    self.pop_queen = data.get('pop_queen', {})
                    self.most_spirited_dance = data.get('most_spirited_dance', {})
                    self.most_dazzling_dance = data.get('most_dazzling_dance', {})
                    self.most_attractive_dance = data.get('most_attractive_dance', {})
                    self.meishi_grammy = data.get('meishi_grammy', {})
                    self.best_band = data.get('best_band', {})
                    self.voted_devices = set(data.get('voted_devices', []))
                    console.log(f"[green]Vote data loaded from {self.data_file}[/green]")
            else:
                console.log(f"[yellow]No existing vote data found at {self.data_file}[/yellow]")
        except Exception as e:
            console.log(f"[yellow]Could not load vote data: {e}[/yellow]")

    def _save_data(self):
        try:
            # Write data to a temporary file first
            temp_file = self.data_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump({
                    'pop_king': self.pop_king,
                    'pop_queen': self.pop_queen,
                    'most_spirited_dance': self.most_spirited_dance,
                    'most_dazzling_dance': self.most_dazzling_dance,
                    'most_attractive_dance': self.most_attractive_dance,
                    'meishi_grammy': self.meishi_grammy,
                    'best_band': self.best_band,
                    'voted_devices': list(self.voted_devices)
                }, f, indent=2)
            
            # Replace the old file with the new one
            if os.path.exists(self.data_file):
                os.replace(self.data_file, self.data_file + '.bak')
            os.rename(temp_file, self.data_file)
            
            console.log(f"[green]Vote data saved to {self.data_file}[/green]")
        except Exception as e:
            console.log(f"[red]Failed to save vote data: {e}[/red]")

    def check_if_voted(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        return vote_id in self.voted_devices

    def record_vote(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        self.voted_devices.add(vote_id)
        self._save_data()  # Save after each vote

    def modify_vote(self, pop_king_vote=None, pop_queen_vote=None, most_spirited_dance_vote=None, most_dazzling_dance_vote=None, most_attractive_dance_vote=None, meishi_grammy_vote=None, best_band_vote=None, ip_address=None, device_token=None, bypass=False):
        if not self.running:
            console.log("[yellow]Vote rejected - server is shutting down[/yellow]")
            return False
        
        if not self.lock.acquire(timeout=5):  # Use instance lock with timeout
            console.log("[red]Failed to acquire lock in modify_vote[/red]")
            return False
            
        try:
            # Check if this device has already voted
            if not bypass and self.check_if_voted(ip_address, device_token):
                return False

            if pop_king_vote:
                self.pop_king[pop_king_vote] = self.pop_king.get(pop_king_vote, 0) + 1
            if pop_queen_vote:
                self.pop_queen[pop_queen_vote] = self.pop_queen.get(pop_queen_vote, 0) + 1
            if most_spirited_dance_vote:
                self.most_spirited_dance[most_spirited_dance_vote] = self.most_spirited_dance.get(most_spirited_dance_vote, 0) + 1
            if most_dazzling_dance_vote:
                self.most_dazzling_dance[most_dazzling_dance_vote] = self.most_dazzling_dance.get(most_dazzling_dance_vote, 0) + 1
            if most_attractive_dance_vote:
                self.most_attractive_dance[most_attractive_dance_vote] = self.most_attractive_dance.get(most_attractive_dance_vote, 0) + 1
            if meishi_grammy_vote:
                self.meishi_grammy[meishi_grammy_vote] = self.meishi_grammy.get(meishi_grammy_vote, 0) + 1
            if best_band_vote:
                self.best_band[best_band_vote] = self.best_band.get(best_band_vote, 0) + 1
            
            # Record the vote
            self.record_vote(ip_address, device_token)
            return True
        finally:
            self.lock.release()

    def read_vote(self):
        if not self.lock.acquire(timeout=5):  # Use instance lock with timeout
            console.log("[red]Failed to acquire lock in read_vote[/red]")
            return {
                "pop_king": {}, 
                "pop_queen": {}, 
                "most_spirited_dance": {}, 
                "most_dazzling_dance": {}, 
                "most_attractive_dance": {}, 
                "meishi_grammy": {}, 
                "best_band": {}
            }
            
        try:
            return {
                "pop_king": self.pop_king.copy(), 
                "pop_queen": self.pop_queen.copy(), 
                "most_spirited_dance": self.most_spirited_dance.copy(), 
                "most_dazzling_dance": self.most_dazzling_dance.copy(), 
                "most_attractive_dance": self.most_attractive_dance.copy(), 
                "meishi_grammy": self.meishi_grammy.copy(), 
                "best_band": self.best_band.copy()
            }
        finally:
            self.lock.release()

    def shutdown(self):
        console.log("[yellow]Database worker shutting down...[/yellow]")
        self.running = False
        self._save_data()  # Save data before shutdown
        console.log("[green]Database worker shutdown complete[/green]")

class VotingServer(HTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.vote_db:VoteDatabaseWorker = VoteDatabaseWorker()
        self._running = True
        self._active_requests = 0
        self._requests_lock = threading.Lock()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        console.log("[yellow]Received shutdown signal, stopping server...[/yellow]")
        self._running = False
        
        # Wait for active requests to complete (up to 5 seconds)
        wait_start = time.time()
        while self._active_requests > 0 and (time.time() - wait_start) < 5:
            time.sleep(0.1)
            
        if self._active_requests > 0:
            console.log(f"[yellow]Shutdown proceeding with {self._active_requests} requests still active[/yellow]")
        
        self.vote_db.shutdown()
        
        # Wake up the server by connecting to it
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(self.server_address)
        except:
            pass

    def track_request(self):
        with self._requests_lock:
            self._active_requests += 1

    def complete_request(self):
        with self._requests_lock:
            self._active_requests -= 1

    def serve_forever(self, poll_interval=0.5):
        console.log("[green]Server started and ready to accept connections[/green]")
        while self._running:
            try:
                self.handle_request()
            except Exception as e:
                if self._running:
                    console.log(f"[red]Error handling request: {e}[/red]")
        console.log("[green]Server shutdown complete[/green]")

class VoteHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._send_cors_headers()
        self.send_response(204)
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Device-Token')
        self.send_header('Access-Control-Max-Age', '86400')

    def do_POST(self):
        self.server.track_request()
        try:
            if not self.server._running:
                self.send_error(503, "Service Unavailable - Server is shutting down")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            device_token = self.headers.get('X-Device-Token')
            if not device_token:
                self.send_error(400, "Missing device token")
                return

            success = self.server.vote_db.modify_vote(
                data.get('pop_king'), 
                data.get('pop_queen'),
                self.client_address[0],
                device_token
            )

            self.send_response(200 if success else 403)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': success,
                'message': 'Vote recorded' if success else 'Already voted or server shutting down'
            }).encode())

        except Exception as e:
            console.log(f"[red]Error in do_POST: {str(e)}[/red]")
            self.send_error(500, "Internal Server Error")
        finally:
            self.server.complete_request()

    def do_GET(self):
        self.server.track_request()
        try:
            if not self.server._running:
                self.send_error(503, "Service Unavailable - Server is shutting down")
                return

            if self.path == '/votes':
                votes = self.server.vote_db.read_vote()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(votes).encode())
            else:
                self.send_error(404, "Not Found")

        except Exception as e:
            console.log(f"[red]Error in do_GET: {str(e)}[/red]")
            self.send_error(500, "Internal Server Error")
        finally:
            self.server.complete_request()

def main():
    try:
        server = VotingServer(('0.0.0.0', 8000), VoteHandler)
        console.log("[green]Server started at http://0.0.0.0:8000[/green]")
        server.serve_forever()
    except Exception as e:
        console.log(f"[red]Server error: {e}[/red]")
    finally:
        server._running = False
        server.server_close()
        console.log("[yellow]Server stopped[/yellow]")

if __name__ == '__main__':
    main()

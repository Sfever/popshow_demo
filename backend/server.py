import json
import signal
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from rich.console import Console
import ssl
import sys
import os
import time
import queue

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
        self.pop_king_candidates = {}
        self.pop_queen_candidates = {}
        self.most_spirited_dance_candidates = {}
        self.most_dazzling_dance_candidates = {}
        self.most_attractive_dance_candidates = {}
        self.meishi_grammy_candidates = {}
        self.best_band_candidates = {}
        self.voted_devices = set()
        self.running = True
        self.lock = threading.Lock()
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.data_dir, "vote_data.json")
        self.candidates_file = os.path.join(self.data_dir, "candidates.json")
        self.allowance_file = os.path.join(self.data_dir, "allowance.json")
        self.save_queue = queue.Queue()
        self.save_thread = threading.Thread(target=self._save_worker, daemon=True)
        self.save_thread.start()
        self.test_mode=True
        self.last_save_time = time.time()
        self.save_interval = 5  # Save at most once every 5 seconds
        self.g6_allowed = []
        self.g7_allowed = []
        self.g8_allowed = []
        self.g9_allowed = []
        self.g10_allowed = []
        self.g11_allowed = []
        self.g12_allowed = []
        self.teachers_allowed = []
        self.g6_voted = []
        self.g7_voted = []
        self.g8_voted = []
        self.g9_voted = []
        self.g10_voted = []
        self.g11_voted = []
        self.g12_voted = []
        self.teachers_voted = []
        self._load_data()

    def _load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
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
        try:
            if os.path.exists(self.candidates_file):
                with open(self.candidates_file, 'r', encoding='utf-8') as f:
                    candidates = json.load(f)
                    self.pop_king_candidates = candidates.get('pop_king', {})
                    self.pop_queen_candidates = candidates.get('pop_queen', {})
                    self.most_spirited_dance_candidates = candidates.get('dance', {})
                    self.most_dazzling_dance_candidates = candidates.get('dance', {})
                    self.most_attractive_dance_candidates = candidates.get('dance', {})
                    self.meishi_grammy_candidates = candidates.get('meishi_grammy', {})
                    self.best_band_candidates = candidates.get('best_band', {})
                    console.log(f"[green]Candidates data loaded from {self.candidates_file}[/green]")
            else:
                console.log(f"[yellow]No existing candidates data found at {self.candidates_file}[/yellow]")
        except Exception as e:
            console.log(f"[yellow]Could not load candidates data: {e}[/yellow]")
        try:
            if os.path.exists(self.allowance_file):
                with open(self.allowance_file, 'r', encoding='utf-8') as f:
                    allowance = json.load(f)
                    self.g6_allowed = allowance.get('g6', [])
                    self.g7_allowed = allowance.get('g7', [])
                    self.g8_allowed = allowance.get('g8', [])
                    self.g9_allowed = allowance.get('g9', [])
                    self.g10_allowed = allowance.get('g10', [])
                    self.g11_allowed = allowance.get('g11', [])
                    self.g12_allowed = allowance.get('g12', [])
                    self.teachers_allowed = allowance.get('teachers', [])
                    console.log(f"[green]Allowance data loaded from {self.allowance_file}[/green]")
            else:
                console.log(f"[yellow]No existing allowance data found at {self.allowance_file}[/yellow]")
        except Exception as e:
            console.log(f"[yellow]Could not load allowance data: {e}[/yellow]")

    def _save_data(self):
        if self.test_mode:
            return#bypass the save for testing
        try:
            # Write data to a temporary file first
            temp_file = self.data_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'pop_king': self.pop_king,
                    'pop_queen': self.pop_queen,
                    'most_spirited_dance': self.most_spirited_dance,
                    'most_dazzling_dance': self.most_dazzling_dance,
                    'most_attractive_dance': self.most_attractive_dance,
                    'meishi_grammy': self.meishi_grammy,
                    'best_band': self.best_band,
                    'voted_devices': list(self.voted_devices)
                }, f, ensure_ascii=False, indent=2)
            
            # Replace the old file with the new one
            if os.path.exists(self.data_file):
                os.replace(self.data_file, self.data_file + '.bak')
            os.rename(temp_file, self.data_file)
            
            console.log(f"[green]Vote data saved to {self.data_file}[/green]")
        except Exception as e:
            console.log(f"[red]Failed to save vote data: {e}[/red]")

    def _save_worker(self):
        while self.running:
            try:
                data = self.save_queue.get(timeout=1)
                if time.time() - self.last_save_time >= self.save_interval:
                    self._save_data()
                    self.last_save_time = time.time()
            except queue.Empty:
                continue

    def check_if_voted(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        return vote_id in self.voted_devices

    def record_vote(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        self.voted_devices.add(vote_id)
        self.save_queue.put(True)  # Trigger asynchronous save

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

    def read_candidates(self):
        return {
            "pop_king": self.pop_king_candidates.copy(),
            "pop_queen": self.pop_queen_candidates.copy(),
            "most_spirited_dance": self.most_spirited_dance_candidates.copy(),
            "most_dazzling_dance": self.most_dazzling_dance_candidates.copy(),
            "most_attractive_dance": self.most_attractive_dance_candidates.copy(),
            "meishi_grammy": self.meishi_grammy_candidates.copy(),
            "best_band": self.best_band_candidates.copy()
        }
    
    def check_authorication(self, grade:int, name:str):
        if self.test_mode:
            return True
        name = name.lower()
        if grade == 6 and name in self.g6_allowed and name not in self.g6_voted:
            self.g6_voted.append(name)
            return True
        elif grade == 7 and name in self.g7_allowed and name not in self.g7_voted:
            self.g7_voted.append(name)
            return True
        elif grade == 8 and name in self.g8_allowed and name not in self.g8_voted:
            self.g8_voted.append(name)
            return True
        elif grade == 9 and name in self.g9_allowed and name not in self.g9_voted:
            self.g9_voted.append(name)
            return True
        elif grade == 10 and name in self.g10_allowed and name not in self.g10_voted:
            self.g10_voted.append(name)
            return True
        elif grade == 11 and name in self.g11_allowed and name not in self.g11_voted:
            self.g11_voted.append(name)
            return True
        elif grade == 12 and name in self.g12_allowed and name not in self.g12_voted:
            self.g12_voted.append(name)
            return True
        elif grade == 13 and name in self.teachers_allowed and name not in self.teachers_voted:
            self.teachers_voted.append(name)
            return True



class VotingServer(ThreadingHTTPServer):
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
        self.socket.settimeout(poll_interval)
        while self._running:
            try:
                self.handle_request()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    console.log(f"[red]Error handling request: {e}[/red]")
        console.log("[green]Server shutdown complete[/green]")

class VoteHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
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
            grade = data.get('grade')
            name = data.get('name')
            device_token = self.headers.get('X-Device-Token')
            if not device_token:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Missing device token'
                }, ensure_ascii=False).encode('utf-8'))
                return
            if not self.server.vote_db.check_authorication(grade, name):
                self.send_response(403)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Not authorized to vote'
                }, ensure_ascii=False).encode('utf-8'))
                return
            success = self.server.vote_db.modify_vote(
                    data.get('pop_king'), 
                    data.get('pop_queen'),
                    data.get('most_spirited_dance'),
                    data.get('most_dazzling_dance'),
                    data.get('most_attractive_dance'),
                    data.get('meishi_grammy'),
                    data.get('best_band'),
                    self.client_address[0],
                    device_token
                )

            self.send_response(200 if success else 403)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                    'success': success,
                    'message': 'Vote recorded' if success else 'Already voted or server shutting down'
            }, ensure_ascii=False).encode('utf-8'))
            


        except Exception as e:
            try:
                console.log(f"[red]Error in do_POST: {str(e)}[/red]")
                self.send_error(500, "Internal Server Error")
            except Exception as e:
                pass
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
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(votes, ensure_ascii=False).encode('utf-8'))
            elif self.path == '/candidates':
                votes = self.server.vote_db.read_candidates()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(votes, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            try:
                console.log(f"[red]Error in do_GET: {str(e)}[/red]")
                self.send_error(500, "Internal Server Error")
            except Exception as e:
                pass
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

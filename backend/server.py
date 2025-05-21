import http.server
import json
import urllib.parse
import rich.console
import threading
import ssl
import http.cookies

#Some other votes here
# Create a console object
dict_lock = threading.Lock()#this lock causes the server to stop like fucking 2 minutes before it responds to ctrl-c
# Leave it tommorrow
'''
# Add at the top with other imports
import signal

# ...existing code...

class VoteDatabaseWorker():
    def __init__(self):
        # ...existing code...
        self.running = True  # Add this flag

    def modify_vote(self, pop_king_vote=None, pop_queen_vote=None, ip_address=None, device_token=None, bypass=False):
        if not self.running:  # Check if server is shutting down
            return False
            
        with dict_lock:
            try:
                timeout = 5  # 5 seconds timeout
                while self.vote_read and timeout > 0 and self.running:
                    time.sleep(0.1)
                    timeout -= 0.1
                
                if timeout <= 0 or not self.running:
                    return False
                    
                # ...rest of existing code...
                
            except Exception as e:
                console.log(f"[red]Error in modify_vote: {e}[/red]")
                return False

    def shutdown(self):
        self.running = False

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, VoteDataServer)
    database = VoteDatabaseWorker()

    def shutdown_handler(signum, frame):
        console.log("[yellow]Shutting down server...[/yellow]")
        database.shutdown()  # Signal threads to stop
        httpd.shutdown()     # Stop the server
        httpd.server_close() # Close the socket
        console.log("[red]Server stopped.[/red]")
        sys.exit(0)

    # Register the signal handler
    signal.signal(signal.SIGINT, shutdown_handler)
    
    # ...existing SSL context code...

    console.log("[green]Starting server on port 8000...[/green]")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        shutdown_handler(None, None)
    except Exception as e:
        console.print_exception()
        shutdown_handler(None, None)
Copilot gives this, hope it works
'''
console = rich.console.Console()
class VoteDatabaseWorker():
    global dict_lock
    def __init__(self):
        self.pop_king = {}
        self.pop_queen = {}
        self.vote_read = False
        self.voted_devices = set()  # Store voted devices

    def check_if_voted(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        return vote_id in self.voted_devices

    def record_vote(self, ip_address, device_token):
        vote_id = f"{ip_address}_{device_token}"
        self.voted_devices.add(vote_id)

    def modify_vote(self, pop_king_vote=None, pop_queen_vote=None, ip_address=None, device_token=None, bypass=False):
        with dict_lock:
            while self.vote_read:
                pass
            
            # Check if this device has already voted
            if self.check_if_voted(ip_address, device_token) and not bypass:
                return False

            if pop_king_vote:
                if pop_king_vote in self.pop_king:
                    self.pop_king[pop_king_vote] += 1
                else:
                    self.pop_king[pop_king_vote] = 1
            if pop_queen_vote:
                if pop_queen_vote in self.pop_queen:
                    self.pop_queen[pop_queen_vote] += 1
                else:
                    self.pop_queen[pop_queen_vote] = 1
            
            # Record the vote
            self.record_vote(ip_address, device_token)
            return True

    def read_vote(self):
        self.vote_read = True
        with dict_lock:
            value={"pop_king":self.pop_king,"pop_queen":self.pop_queen}
            self.vote_read = False
            return value

database=VoteDatabaseWorker()
class VoteDataServer(http.server.BaseHTTPRequestHandler):
    global database

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        # Add CORS headers to all responses
        self.send_cors_headers()
        url = urllib.parse.urlparse(self.path)
        if url.path == '/vote':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Get client IP and device token
            client_ip = self.client_address[0]
            device_token = data.get('device_token')
            
            # Check if already voted
            if database.check_if_voted(client_ip, device_token):
                self.send_response(403)
                response = {'status': 'error', 'message': 'Already voted'}
            else:
                pop_king_vote = data.get('pop_king')
                pop_queen_vote = data.get('pop_queen')
                
                # Record vote
                vote_success = database.modify_vote(pop_king_vote, pop_queen_vote, client_ip, device_token)
                
                if vote_success:
                    # Set simple cookie
                    cookie = http.cookies.SimpleCookie()
                    cookie['vote_status'] = 'voted'
                    cookie['vote_status']['httponly'] = True
                    cookie['vote_status']['secure'] = True
                    cookie['vote_status']['samesite'] = 'Strict'
                    cookie['vote_status']['max-age'] = 31536000  # 1 year
                    
                    self.send_response(200)
                    self.send_header('Set-Cookie', cookie['vote_status'].OutputString())
                    response = {'status': 'success'}
                else:
                    self.send_response(403)
                    response = {'status': 'error', 'message': 'Vote failed'}
            
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif url.path == '/test/vote':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Get client IP and device token
            client_ip = self.client_address[0]
            device_token = data.get('device_token')
            
            # Check if already voted
            if False:
                # Not the best way to bypass, but good enough for now
                self.send_response(403)
                response = {'status': 'error', 'message': 'Already voted'}
            else:
                pop_king_vote = data.get('pop_king')
                pop_queen_vote = data.get('pop_queen')
                
                # Record vote
                vote_success = database.modify_vote(pop_king_vote, pop_queen_vote, client_ip, device_token, bypass=True)
                
                if vote_success:
                    # Set simple cookie
                    cookie = http.cookies.SimpleCookie()
                    cookie['vote_status'] = 'voted'
                    cookie['vote_status']['httponly'] = True
                    cookie['vote_status']['secure'] = True
                    cookie['vote_status']['samesite'] = 'Strict'
                    cookie['vote_status']['max-age'] = 31536000  # 1 year
                    
                    self.send_response(200)
                    self.send_header('Set-Cookie', cookie['vote_status'].OutputString())
                    response = {'status': 'success'}
                else:
                    self.send_response(403)
                    response = {'status': 'error', 'message': 'Vote failed'}
            
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    def do_GET(self):
        # Add CORS headers to all responses
        self.send_cors_headers()
        url = urllib.parse.urlparse(self.path)
        if url.path == '/vote':
            console.log("Received vote read request")
            data = database.read_vote()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, VoteDataServer)
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    try:
        ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
        console.log("[green]SSL certificate loaded successfully.[/green]")
    except Exception as e:
        console.print_exception()
        console.log("[red]Failed to load SSL certificate. Make sure cert.pem and key.pem are in the same directory.[/red]")
        console.log("[red]Running without SSL.[/red]")
    

    console.log("Starting server on port 8000...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        console.log("Server stopped.")
        
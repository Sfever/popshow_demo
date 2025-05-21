import http.server
import json
import urllib.parse
import rich.console
import threading
import ssl

#Some other votes here
# Create a console object
dict_lock = threading.Lock()
console = rich.console.Console()
class VoteDatabaseWorker():
    global dict_lock
    def __init__(self):
        self.pop_king = {}
        self.pop_queen = {}
        self.vote_read = False

    def modify_vote(self, pop_king_vote=None, pop_queen_vote=None):
        with dict_lock:
            while self.vote_read:
                pass
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
            
    def read_vote(self):
        self.vote_read = True
        with dict_lock:
            value={"pop_king":self.pop_king,"pop_queen":self.pop_queen}
            self.vote_read = False
            return value

database=VoteDatabaseWorker()
class VoteDataServer(http.server.BaseHTTPRequestHandler):
    global database
    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/vote':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            pop_king_vote = data.get('pop_king')
            pop_queen_vote = data.get('pop_queen')
            console.log(f"Received vote: {pop_king_vote}, {pop_queen_vote}")
            database.modify_vote(pop_king_vote, pop_queen_vote)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not Found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    def do_GET(self):
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

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, VoteDataServer)
    httpd.socket=ssl.wrap_socket(httpd.socket, certfile='server.pem', server_side=True, keyfile='key.pem',ssl_version=ssl.PROTOCOL_TLS)
    
    console.log("Starting server on port 8000...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        console.log("Server stopped.")
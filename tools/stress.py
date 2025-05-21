import requests
import time
import json
import random
import threading
import rich.console
con=rich.console.Console
def send_stress_requessts(url):
    data={'pop_king':'aaaaaa','pop_queen':'bbbbbb','device_token':'1234567890'}
    headers = {'Content-Type': 'application/json'}
    delay=random.uniform(0.1,10)
    time.sleep(delay)
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("Request sent successfully")
        else:
            print(f"Failed to send request: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
def main():
    url = 'http://127.0.0.1:8000/test/vote'
    threads = []
    for i in range(1000):
        t = threading.Thread(target=send_stress_requessts, args=(url,))
        threads.append(t)
        t.start()
    for i in threads:
        i.join()
if __name__ == "__main__":
    main()
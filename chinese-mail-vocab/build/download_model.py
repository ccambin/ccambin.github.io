import os
import time

import requests

URL = 'https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf'
DEST = os.path.join(os.path.dirname(__file__), '..', 'models', 'qwen2.5-1.5b-instruct-q4_k_m.gguf')
DEST = os.path.abspath(DEST)


def download():
    for attempt in range(30):
        existing = os.path.getsize(DEST) if os.path.exists(DEST) else 0
        headers = {'Range': 'bytes={}-'.format(existing)} if existing else {}
        try:
            with requests.get(URL, headers=headers, stream=True, timeout=30) as r:
                if r.status_code not in (200, 206):
                    print('unexpected status', r.status_code)
                    time.sleep(5)
                    continue
                mode = 'ab' if r.status_code == 206 else 'wb'
                with open(DEST, mode) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                print('done, size =', os.path.getsize(DEST))
                return True
        except requests.exceptions.RequestException as e:
            print('attempt', attempt, 'error:', type(e).__name__, e)
            time.sleep(5)
    return False


if __name__ == '__main__':
    ok = download()
    print('SUCCESS' if ok else 'FAILED')

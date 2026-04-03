#!/bin/sh

set -e

PORT=8080

SCRIPT_DIR=$(dirname $0)
cd $SCRIPT_DIR/site

test -f upcoming-banded.csv || echo "error: missing site/upcoming-banded.csv file, please run 2-build-csv.py"

echo "http://127.0.0.1:$PORT/"

PORT=$PORT python3 - <<'EOF'
import http.server
import time
import os

PORT = int(os.environ.get('PORT', 8080))
THROTTLING_ENABLED = False
BYTES_PER_SECOND = 35

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upcoming-banded.csv':
            if THROTTLING_ENABLED:
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv')
                self.end_headers()
                with open('upcoming-banded.csv', 'rb') as f:
                    while True:
                        chunk = f.read(BYTES_PER_SECOND)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        time.sleep(1)
            else:
                super().do_GET()
        else:
            super().do_GET()

http.server.HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
EOF

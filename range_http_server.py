import http.server
import os
import re
from http import HTTPStatus
import argparse

class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with HTTP Range support."""
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        fs = os.fstat(f.fileno())
        size = fs.st_size
        start = 0
        end = size - 1
        if 'Range' in self.headers:
            m = re.match(r'bytes=(\d+)-(\d+)?', self.headers['Range'])
            if m:
                start = int(m.group(1))
                if m.group(2):
                    end = int(m.group(2))
                    if end >= size:
                        end = size - 1
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            else:
                self.send_response(HTTPStatus.OK)
        else:
            self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', ctype)
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        self.range = (start, end)
        return f

    def copyfile(self, source, outputfile):
        if hasattr(self, 'range'):
            start, end = self.range
            source.seek(start)
            remaining = end - start + 1
            bufsize = 64 * 1024
            while remaining > 0:
                chunk = source.read(min(bufsize, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        else:
            super().copyfile(source, outputfile)


def run_server(port, directory):
    os.chdir(directory)
    with http.server.ThreadingHTTPServer(('', port), RangeRequestHandler) as httpd:
        print(f"Serving HTTP on 0.0.0.0 port {port} (http://0.0.0.0:{port}/) ...")
        httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Static file server with HTTP Range support')
    parser.add_argument('port', nargs='?', default=8000, type=int, help='Port number')
    parser.add_argument('-d', '--directory', default=os.getcwd(), help='Directory to serve')
    args = parser.parse_args()
    run_server(args.port, args.directory)

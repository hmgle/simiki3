import socket
import urllib.request

from simiki3.serve import PreviewServer


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_preview_server_serves_directory(tmp_path):
    html = tmp_path / "index.html"
    html.write_text("<h1>Hello</h1>", encoding="utf-8")

    port = _get_free_port()
    server = PreviewServer(directory=tmp_path, host="127.0.0.1", port=port)
    server.start()
    try:
        response = urllib.request.urlopen(f"http://{server.serve_host}:{server.serve_port}/index.html")
        body = response.read().decode("utf-8")
        assert "Hello" in body
    finally:
        server.stop()

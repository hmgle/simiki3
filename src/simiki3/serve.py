"""Local preview server for Simiki3."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Optional

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class PreviewServer:
    """Serve the generated site directory using the standard library HTTP server."""

    directory: Path
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        handler = partial(SimpleHTTPRequestHandler, directory=str(self.directory))
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._stopped = threading.Event()

    @property
    def serve_host(self) -> str:
        return self._httpd.server_address[0]

    @property
    def serve_port(self) -> int:
        return self._httpd.server_address[1]

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._httpd.shutdown()
        self._thread.join()
        self._stopped.set()

    def wait(self, poll_interval: float = 0.5) -> None:
        try:
            while self._thread.is_alive():
                self._thread.join(poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def run_preview(directory: Path, host: str, port: int) -> PreviewServer:
    """Convenience helper to start a PreviewServer."""
    server = PreviewServer(directory=directory, host=host, port=port)
    server.start()
    return server

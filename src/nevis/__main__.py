"""Entry point for running the Nevis FastAPI application."""
import logging
import sys

import uvicorn

from nevis.api import app

if __name__ == "__main__":
    fmt = f'%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO, stream=sys.stdout)
    logging.captureWarnings(True)
    logging.getLogger(__name__).info("Starting Nevis server...")

    uvicorn.run(
        app,
        log_config=None,
        host="0.0.0.0",
        port=8000,
    )

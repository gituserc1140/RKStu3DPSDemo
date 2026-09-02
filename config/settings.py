"""Configuration settings for the concept art generator app.

The optional Pollinations.ai API key is entered by the end user directly in the
Streamlit UI for each session. It is never read from server-side environment
variables or persisted. The environment variables below only configure trial/demo
defaults such as base URLs and timeouts.
"""

import os

# Pollinations.ai (text-to-image concept art)
API_BASE_URL = os.getenv("API_BASE_URL", "https://image.pollinations.ai")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))

# Meshy.ai (image-to-3d, free trial API)
MESHY_API_BASE_URL = os.getenv("MESHY_API_BASE_URL", "https://api.meshy.ai/openapi/v1")

# Polling behaviour for the Meshy.ai 3D generation job.
JOB_POLL_INTERVAL_SECONDS = float(os.getenv("JOB_POLL_INTERVAL_SECONDS", "2"))
JOB_POLL_TIMEOUT_SECONDS = float(os.getenv("JOB_POLL_TIMEOUT_SECONDS", "180"))

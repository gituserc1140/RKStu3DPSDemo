# 3D Print Concept Studio

This repository contains a Streamlit app for generating polished 3D print concept images. It calls the
Pollinations.ai Image endpoint for text-to-image concept art and links to **Meshy.ai** for optional 3D modeling.

All API keys/tokens are entered by the end user directly in the browser (frontend) sidebar — the app never
reads or stores API keys server-side, and keys only live in the current Streamlit session.

## Folder structure

- `app.py` — Streamlit entry point
- `api_client.py` — Pollinations.ai and Meshy.ai API integrations
- `ui/` — Streamlit UI helpers and layout
- `static/` — CSS styling for the app
- `config/` — app configuration settings
- `tests/` — unit tests for the API client
- `requirements.txt` — Python dependencies

## Requirements

- Python 3.10+
- Streamlit
- Requests

## Install

```bash
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run app.py
```

## How to use

1. Open the app in your browser.
2. (Optional) In the sidebar, enter your Pollinations.ai API key (get one at `enter.pollinations.ai`) to
   raise rate limits or remove the watermark. The endpoint also works anonymously without a key.
3. (Optional) Open Meshy.ai from the sidebar to convert the generated concept art into a 3D model.
4. Choose a model (`flux` or `turbo`), image size, and any of the enhance/watermark/private/seed options.
5. Enter a prompt such as `a low-poly dragon figurine` describing the object you want to 3D print.
6. Click `Generate concept art`. Preview the generated concept-art image and download it as a reference.
7. Download your concept art or open Meshy.ai from the sidebar to continue modeling.

## Notes

- The app calls `GET https://image.pollinations.ai/prompt/{prompt}`, passing `model`, `width`, `height`,
  `seed`, and optionally `enhance`, `nologo`, and `private` as query parameters.
- Prompts are automatically appended with concept-art styling keywords (3D render, product concept art,
  studio lighting, orthographic view) to bias results toward usable 3D print references.
- The Pollinations.ai API key is optional and is never persisted server-side.
- Meshy.ai is an external web app; its availability and terms are managed by Meshy.ai.
- Errors are handled gracefully and surfaced in the Streamlit UI.

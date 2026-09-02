import base64
import random
import time
from urllib.parse import quote

import requests

from config.settings import (
    API_BASE_URL,
    JOB_POLL_INTERVAL_SECONDS,
    JOB_POLL_TIMEOUT_SECONDS,
    MESHY_API_BASE_URL,
)

IMAGE_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

CONCEPT_ART_SUFFIX = (
    "3D render, product concept art for 3D printing, studio lighting, orthographic view, "
    "clean background, high detail"
)


def fetch_data(
    prompt: str,
    api_key: str | None = None,
    model: str = "flux",
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None,
    enhance: bool = False,
    nologo: bool = False,
    private: bool = False,
):
    """Generate a 3D print art concept image from the Pollinations.ai Image API.

    Args:
        prompt: The text prompt describing the desired 3D print art concept.
        api_key: Optional Pollinations.ai API key supplied by the end user.
            When provided, it is sent as an authenticated token in the
            Authorization header. This is not required for basic image
            generation but can raise rate limits and unlock features such as
            removing the watermark.
        model: The image generation model to use (defaults to "flux").
        width: Requested image width in pixels.
        height: Requested image height in pixels.
        seed: Optional seed for reproducible generations. A random seed is
            used when not supplied.
        enhance: When True, lets the API improve the prompt for better
            results.
        nologo: When True, removes the Pollinations watermark (requires an
            account/API key).
        private: When True, hides the image from public feeds.

    Returns:
        A dict containing the raw image bytes (under "content"), its
        "content_type", and a suggested "filename", or a dict with an
        "error" key on failure.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("A non-empty text prompt is required.")

    full_prompt = f"{prompt.strip()}, {CONCEPT_ART_SUFFIX}"
    safe_prompt = quote(full_prompt, safe="")
    url = f"{API_BASE_URL}/prompt/{safe_prompt}"

    headers = {}
    if api_key and api_key.strip():
        headers["Authorization"] = "Bearer " + api_key.strip()

    params = {
        "model": model,
        "width": width,
        "height": height,
        "seed": seed if seed is not None else random.randint(0, 2**31 - 1),
    }
    if enhance:
        params["enhance"] = "true"
    if nologo:
        params["nologo"] = "true"
    if private:
        params["private"] = "true"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=180)

        if response.status_code == 403:
            body = response.text.strip()
            detail = f" Response: {body[:300]}" if body else ""
            return {
                "error": (
                    "Pollinations.ai rejected the request with 403 Forbidden. "
                    "This usually means the key isn't valid for direct generation calls: "
                    "App Keys (pk_... registered with redirect URIs) are OAuth client IDs used to "
                    "obtain a scoped sk_ token, not a bearer credential themselves. Use a secret key "
                    "(sk_...), or complete the OAuth/BYOP flow to obtain a scoped sk_ token, then use "
                    f"that as your API key, or leave the API key blank to use the endpoint anonymously.{detail}"
                )
            }

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if content_type.split(";")[0].strip().lower().startswith("application/json"):
            try:
                return response.json()
            except ValueError:
                content = response.text.strip()
                if not content:
                    return response.url
                return content

        extension = IMAGE_CONTENT_TYPE_EXTENSIONS.get(content_type.split(";")[0].strip().lower(), ".jpg")
        filename = f"{prompt.strip()[:40] or 'concept'}{extension}"
        return {
            "content": response.content,
            "content_type": content_type or "image/jpeg",
            "filename": filename,
        }
    except requests.HTTPError as exc:
        body = exc.response.text.strip() if exc.response is not None else ""
        detail = f" Response: {body[:300]}" if body else ""
        return {"error": f"Failed to contact Pollinations.ai: {exc}.{detail}"}
    except requests.RequestException as exc:
        return {"error": f"Failed to contact Pollinations.ai: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {"error": f"Unexpected error generating the image: {exc}"}


def image_bytes_to_data_uri(content: bytes, content_type: str = "image/jpeg") -> str:
    """Encode raw image bytes as a base64 data URI suitable for image-to-3D APIs."""
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type or 'image/jpeg'};base64,{encoded}"


def fetch_meshy_model(image_url: str, api_key: str, ai_model: str = "meshy-4") -> dict:
    """Generate a 3D model from an image using the Meshy.ai free trial Image-to-3D API.

    Args:
        image_url: A publicly reachable image URL, or a base64 data URI (see
            ``image_bytes_to_data_uri``), of the concept art to convert to 3D.
        api_key: The end user's Meshy.ai API key. Required; sent as a bearer
            token in the Authorization header and never persisted server-side.
        ai_model: The Meshy image-to-3d model version to request.

    Returns:
        A dict with "model_urls" (e.g. glb/fbx/obj/usdz download links) and
        "thumbnail_url" on success, or a dict with an "error" key on failure.
    """
    if not api_key or not api_key.strip():
        return {"error": "A Meshy.ai API key is required to generate a 3D model."}
    if not image_url:
        return {"error": "An image is required before generating a 3D model."}

    headers = {"Authorization": "Bearer " + api_key.strip()}

    try:
        create_response = requests.post(
            f"{MESHY_API_BASE_URL}/image-to-3d",
            headers=headers,
            json={"image_url": image_url, "ai_model": ai_model, "enable_pbr": False},
            timeout=60,
        )
        create_response.raise_for_status()
        task_id = create_response.json().get("result")
        if not task_id:
            return {"error": "Meshy.ai did not return a task id for the 3D generation job."}

        deadline = time.monotonic() + JOB_POLL_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            status_response = requests.get(
                f"{MESHY_API_BASE_URL}/image-to-3d/{task_id}",
                headers=headers,
                timeout=60,
            )
            status_response.raise_for_status()
            data = status_response.json()
            status = data.get("status")

            if status == "SUCCEEDED":
                return {
                    "task_id": task_id,
                    "model_urls": data.get("model_urls", {}),
                    "thumbnail_url": data.get("thumbnail_url"),
                }
            if status == "FAILED":
                task_error = data.get("task_error", {}) or {}
                return {"error": task_error.get("message") or "Meshy.ai failed to generate the 3D model."}

            time.sleep(JOB_POLL_INTERVAL_SECONDS)

        return {"error": "Timed out waiting for Meshy.ai to generate the 3D model. Please try again."}
    except requests.HTTPError as exc:
        body = exc.response.text.strip() if exc.response is not None else ""
        detail = f" Response: {body[:300]}" if body else ""
        return {"error": f"Failed to contact Meshy.ai: {exc}.{detail}"}
    except requests.RequestException as exc:
        return {"error": f"Failed to contact Meshy.ai: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {"error": f"Unexpected error generating the Meshy.ai 3D model: {exc}"}

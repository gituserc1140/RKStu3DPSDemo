import base64
import unittest
from unittest.mock import MagicMock, patch

from api_client import (
    fetch_meshy_model,
    image_bytes_to_data_uri,
)


class ImageBytesToDataUriTests(unittest.TestCase):
    def test_encodes_bytes_as_data_uri(self):
        content = b"fake-image-bytes"
        data_uri = image_bytes_to_data_uri(content, "image/png")
        expected_b64 = base64.b64encode(content).decode("ascii")
        self.assertEqual(data_uri, f"data:image/png;base64,{expected_b64}")

    def test_defaults_to_jpeg_when_content_type_missing(self):
        data_uri = image_bytes_to_data_uri(b"abc", "")
        self.assertTrue(data_uri.startswith("data:image/jpeg;base64,"))


class FetchMeshyModelTests(unittest.TestCase):
    def test_requires_api_key(self):
        result = fetch_meshy_model("https://example.com/image.png", "")
        self.assertIn("error", result)

    def test_requires_image_url(self):
        result = fetch_meshy_model("", "sk_test")
        self.assertIn("error", result)

    @patch("api_client.requests.get")
    @patch("api_client.requests.post")
    def test_returns_model_urls_on_success(self, mock_post, mock_get):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result": "task-123"},
            raise_for_status=lambda: None,
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "status": "SUCCEEDED",
                "model_urls": {"glb": "https://cdn.meshy.ai/model.glb"},
                "thumbnail_url": "https://cdn.meshy.ai/thumb.png",
            },
            raise_for_status=lambda: None,
        )

        result = fetch_meshy_model("https://example.com/image.png", "sk_test")

        self.assertEqual(result["model_urls"]["glb"], "https://cdn.meshy.ai/model.glb")
        self.assertEqual(result["thumbnail_url"], "https://cdn.meshy.ai/thumb.png")
        mock_post.assert_called_once()
        expected_auth = "Bearer " + "sk_test"
        self.assertEqual(mock_post.call_args.kwargs["headers"]["Authorization"], expected_auth)

    @patch("api_client.requests.get")
    @patch("api_client.requests.post")
    def test_returns_error_on_failed_status(self, mock_post, mock_get):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result": "task-123"},
            raise_for_status=lambda: None,
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "FAILED", "task_error": {"message": "boom"}},
            raise_for_status=lambda: None,
        )

        result = fetch_meshy_model("https://example.com/image.png", "sk_test")

        self.assertEqual(result["error"], "boom")


if __name__ == "__main__":
    unittest.main()

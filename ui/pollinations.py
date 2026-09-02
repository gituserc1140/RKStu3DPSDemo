from __future__ import annotations

from typing import Any

import streamlit as st


def render_home() -> None:
    st.title("🎨 3D Print Concept Studio")
    st.subheader("Create polished 3D-print references from a single prompt")
    st.markdown(
        """
        Describe the object, scene, or character you want to print. Pollinations.ai creates a detailed concept
        image to guide your design, ready to download or continue in **Meshy.ai**.
        """
    )

    info_col, features_col = st.columns(2)
    with info_col:
        st.info(
            "Add a Pollinations.ai API key in the sidebar for higher limits or watermark removal. Your key stays "
            "in this browser session and is never stored. Meshy.ai opens in its own web app."
        )
    with features_col:
        st.success("Prompt → concept image → download or refine in Meshy.ai")


def render_result(result: Any) -> None:
    st.markdown("---")
    st.subheader("Generated result")

    if isinstance(result, dict):
        if "error" in result:
            st.error(result["error"])
            return

        if "content" in result and isinstance(result["content"], (bytes, bytearray)):
            render_image_asset(
                result["content"],
                content_type=result.get("content_type", "image/jpeg"),
                filename=result.get("filename", "concept.jpg"),
            )
            return

        if any(key in result for key in ("url", "image_url")):
            url = result.get("url") or result.get("image_url")
            if url:
                st.image(url, caption="Generated preview", use_container_width=True)
                return

        st.json(result)
        return

    if isinstance(result, str):
        if result.startswith("http://") or result.startswith("https://"):
            st.image(result, caption="Generated preview", use_container_width=True)
            return
        st.code(result, language="text")
        return

    st.write(result)


def render_image_asset(content: bytes, content_type: str, filename: str) -> None:
    st.image(content, caption="Generated preview", use_container_width=True)
    st.download_button(
        "Download generated concept art",
        data=content,
        file_name=filename,
        mime=content_type,
    )

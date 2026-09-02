from pathlib import Path

import streamlit as st

from api_client import fetch_data
from ui import render_home, render_result


def load_css() -> None:
    css_path = Path(__file__).resolve().parent / "static" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="3D Print Art Concept Generator", page_icon="🎨", layout="wide")
    load_css()
    render_home()

    with st.sidebar:
        st.subheader("Pollinations.ai API key (optional)")
        api_key = st.text_input(
            "API key",
            value=st.session_state.get("pollinations_api_key", ""),
            type="password",
            placeholder="Enter your Pollinations.ai API key",
            help="Optional. Your key is only kept in this browser session and is sent directly to "
            "Pollinations.ai when generating an image. Leave blank to use the endpoint anonymously.",
        )
        st.session_state["pollinations_api_key"] = api_key
        st.caption("Need a key? Get one at enter.pollinations.ai.")

        st.markdown("---")
        st.subheader("Meshy.ai (for 3D model trial)")
        st.caption("Turn your concept art into a 3D model in Meshy's web app.")
        st.link_button("Open Meshy.ai", "https://www.meshy.ai/", use_container_width=True)

        st.markdown("---")

        model = st.selectbox(
            "Model",
            options=["flux", "turbo"],
            index=0,
            help="The image generation model to use.",
        )

        size_presets = {
            "Square (1024x1024)": (1024, 1024),
            "Portrait (832x1216)": (832, 1216),
            "Landscape (1216x832)": (1216, 832),
        }
        size_label = st.selectbox(
            "Image size",
            options=list(size_presets.keys()),
            index=0,
            help="Choose a resolution/aspect ratio suited for concept art reference.",
        )
        width, height = size_presets[size_label]

        enhance = st.checkbox(
            "Enhance prompt",
            value=False,
            help="Let the AI improve your prompt for better results.",
        )
        nologo = st.checkbox(
            "Remove watermark (requires API key)",
            value=False,
            help="Removes the Pollinations watermark. Requires an account/API key.",
        )
        if nologo and not api_key.strip():
            st.warning("Removing the watermark requires an API key. Add one above or this option will be ignored.")
        private = st.checkbox(
            "Private (hide from public feed)",
            value=False,
        )

        use_random_seed = st.checkbox("Use a random seed", value=True)
        seed = None
        if not use_random_seed:
            seed = st.number_input(
                "Seed",
                min_value=-(2**53 - 1),
                max_value=2**53 - 1,
                value=0,
                step=1,
                help="Provide a fixed seed for reproducible generations.",
            )

    prompt = st.text_input(
        "Describe the 3D print art concept you want to generate",
        value="",
        placeholder="A futuristic dragon figurine, low-poly robot bust, sci-fi castle miniature...",
        help="Use descriptive words that the Pollinations image generator can turn into 3D print concept art.",
    )

    generate_clicked = st.button("Generate concept art", type="primary", use_container_width=True)

    if generate_clicked:
        if not prompt.strip():
            st.warning("Please enter a prompt before generating concept art.")
        else:
            with st.spinner("Generating your 3D print concept art from Pollinations.ai..."):
                try:
                    result = fetch_data(
                        prompt.strip(),
                        api_key=api_key.strip() or None,
                        model=model,
                        width=width,
                        height=height,
                        seed=int(seed) if seed is not None else None,
                        enhance=enhance,
                        nologo=nologo,
                        private=private,
                    )
                except Exception as exc:  # pragma: no cover - defensive UI path
                    st.error(f"Unable to generate the image: {exc}")
                    result = None

            if result is not None:
                if isinstance(result, dict) and "error" not in result:
                    st.session_state["last_image_result"] = result
                else:
                    st.session_state.pop("last_image_result", None)

                render_result(result)

if __name__ == "__main__":
    main()

import streamlit as st
from agents.search import search_person
from utils.ranking import rank_results
from agents.profile_generator import generate_profile
from services.image_service import get_wikipedia_image
from render_profile import normalize_list_fields, render_profile, html_to_png
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="AI Profile Builder", page_icon="📄", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,600&family=Inter:wght@400;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at top, #241B16 0%, #14100D 100%);
        color: #F5E8DE;
    }

    .block-container {
        max-width: 700px;
        padding-top: 2rem;
    }

    .hero {
        text-align: center;
        padding: 30px 20px 5px 20px;
    }

    .hero h1 {
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        font-size: 42px;
        background: linear-gradient(120deg, #FFCBA4, #D96C3F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }

    .hero .sub {
        color: #B99A85;
        font-size: 14px;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 600;
    }

    .tagline {
        font-size: 15px;
        color: #C9AF9F;
        text-align: center;
        max-width: 560px;
        margin: 14px auto 24px auto;
        line-height: 1.6;
    }

    .pipeline {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 35px;
    }

    .pipeline-step {
        background: #1F1712;
        border: 1px solid #3A2E27;
        color: #E8A87C;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 20px;
    }

    .pipeline-arrow {
        color: #6B5548;
        font-size: 14px;
    }

    .stTextInput>div>div>input {
        background-color: #2A211C;
        color: #F5E8DE;
        border: 1px solid #4A3A30;
        border-radius: 10px;
        padding: 14px;
    }

    .stTextInput>div>div>input:focus {
        border: 1px solid #D96C3F;
        box-shadow: 0 0 0 2px rgba(217,108,63,0.2);
    }

    .stTextInput>label {
        color: #E8A87C !important;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #D96C3F, #E8734A);
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: 700;
        padding: 14px 30px;
        margin-top: 10px;
        font-size: 15px;
        letter-spacing: 0.5px;
    }

    .stButton>button:hover {
        background: linear-gradient(120deg, #A54A28, #D96C3F);
    }

    [data-testid="stExpander"] {
        background-color: #1F1712;
        border-radius: 12px;
        border: 1px solid #3A2E27;
    }

    .footer-note {
        text-align: center;
        color: #6B5548;
        font-size: 12px;
        margin-top: 50px;
        letter-spacing: 0.5px;
    }
</style>

<div class="hero">
    <div class="sub">AI-Powered</div>
    <h1>Profile Builder</h1>
</div>

<div class="tagline">
Generates trustworthy public profiles from multiple sources with references and 
transparent handling of missing or conflicting information.
</div>

<div class="pipeline">
    <span class="pipeline-step">Tavily Search</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">TF-IDF Ranking</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">Groq Extraction</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">Structured Profile</span>
</div>
""", unsafe_allow_html=True)

with st.container(border=True):
    with st.form("profile_form"):
        name = st.text_input("Full Name", placeholder="e.g. Satya Nadella")
        context = st.text_input("Context", placeholder="e.g. CEO of Microsoft")
        submitted = st.form_submit_button("Generate Profile")

if submitted:
    if not name or not context:
        st.error("Please enter both name and context.")
    else:
        status = st.status("Running pipeline...", expanded=True)

        status.write("Searching public sources...")
        results = search_person(name, context)

        if not results:
            status.update(label="No results found", state="error")
            st.error("No search results found. Try a different name/context.")
        else:
            status.write(f"{len(results)} sources retrieved.")

            status.write("Ranking documents by relevance...")
            ranked = rank_results(results, f"{name} {context} net worth biography residence")
            status.write(f"Top {len(ranked)} sources selected.")

            status.write("Generating structured profile with Groq...")
            profile = generate_profile(name, context, ranked)

            if not profile:
                status.update(label="Profile generation failed", state="error")
                st.error("Profile generation failed. Check logs/app.log for details.")
            else:
                status.write("Profile structured successfully.")
                profile = normalize_list_fields(profile)

                status.write("Fetching profile photo...")
                image_data = get_wikipedia_image(name)
                image_url = image_data["image_url"] if image_data else None

                status.write("Rendering final profile...")
                html_path = render_profile(profile, image_url)
                png_path = html_to_png(html_path)

                status.update(label="Profile ready", state="complete")

                st.image(png_path, use_container_width=True)

                with open(png_path, "rb") as f:
                    st.download_button(
                        "Download Profile as PNG",
                        f,
                        file_name=f"{name.replace(' ', '_')}_profile.png",
                        mime="image/png"
                    )

                with st.expander("View Raw JSON"):
                    st.json(profile)

st.markdown("""
<div class="footer-note">
Powered by Tavily · Groq · Streamlit
</div>
""", unsafe_allow_html=True)
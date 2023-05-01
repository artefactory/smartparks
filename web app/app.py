import streamlit as st

# set page layout
st.set_page_config(layout="wide")

# Custom imports
from multipage import MultiPage
from panels import (
    map,
    configuration,
    cloudvision,
    videointelligence,
)  # import your pages here

# Create an instance of the app
app = MultiPage()

# Title of the main page
st.title("Artefact 🤝 Smart Parks")


# Add all your applications (pages) here

app.add_page("📸 Images", cloudvision.app)
app.add_page("🎥 Videos", videointelligence.app)

# app.add_page("🎥 Videos", videos.app)
app.add_page("🌍 Map", map.app)
app.add_page("⚙️ Configuration", configuration.app)

# The main app
app.run()

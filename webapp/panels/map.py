import yaml
import streamlit as st
import geemap.foliumap as geemap
from utils import get_metadata

# load config file
with open("config.yml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# constants
BUCKET_NAME = config["BUCKET_NAME"]
OUTPUT_BUCKET_NAME = config["OUTPUT_BUCKET_NAME"]
CAMERAS_METADATA_FILE = config["CAMERAS_METADATA_FILE"]


def app():

    # set title
    st.markdown("### 🌍 Satellite view")

    # define the Map object
    m = geemap.Map(
        basemap="HYBRID",
        plugin_Draw=False,
        Draw_export=False,
        locate_control=True,
        plugin_LatLngPopup=False,
    )

    # set the initial view of the map
    m.set_center(25.6866, -15.2948, zoom=6)

    # get the metadata of the cameras
    df = get_metadata(OUTPUT_BUCKET_NAME, CAMERAS_METADATA_FILE)

    # add the cameras to the map
    m.add_points_from_xy(df, max_width=250)

    # display the map on the streamlit page
    m.to_streamlit(height=800)

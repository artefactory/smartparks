import yaml
import streamlit as st
import pandas as pd
from utils import get_metadata, update_metadata


# load config file
with open("config.yml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# constants
BUCKET_NAME = config["BUCKET_NAME"]
OUTPUT_BUCKET_NAME = config["OUTPUT_BUCKET_NAME"]
CAMERA_NAMES = config["CAMERA_NAMES"]
USE_CASES = config["USE_CASES"]
CAMERAS_METADATA_FILE = config["CAMERAS_METADATA_FILE"]


def app():

    # set title
    st.markdown("### ⚙️ Configuration settings")

    # get the metadata of the cameras
    df = get_metadata(OUTPUT_BUCKET_NAME, CAMERAS_METADATA_FILE)

    # define a container to store the cameras details
    camera_traps_container = st.container()

    # define a container to store the buttons
    buttons_container = st.container()

    # for each camera, display the details
    with camera_traps_container:
        for i, camera_trap in enumerate(df["name"].values):
            single_camera_contaier = st.container()

            # create 4 columns to display the metadata of the camera trap
            col1, col2, col3, col4 = single_camera_contaier.columns(4)

            col1.text_input("Camera name", camera_trap, key=f"name_{i}")
            col2.text_input(
                "Camera streaming URL",
                df[df["name"] == camera_trap]["url"].values[0],
                key=f"url_{i}",
            )
            col3.text_input(
                "Longitude",
                df[df["name"] == camera_trap]["longitude"].values[0],
                key=f"lon_{i}",
            )
            col4.text_input(
                "Latitude",
                df[df["name"] == camera_trap]["latitude"].values[0],
                key=f"lat_{i}",
            )

    with buttons_container:
        button1, button2, _ = st.columns([10, 10, 150])

        # button to add a blank row to the camera traps table
        add = button1.button("add")

        # button to save the changes
        save = button2.button("save")

    # add a boolean session variable to store the state of the button
    if "new_row" not in st.session_state:
        st.session_state.new_row = False

    # if the button is clicked, add a blank row to the camera traps table, reset the button state
    if add:
        st.session_state.new_row = True

    if st.session_state.new_row:
        name = col1.text_input("Camera name")
        url = col2.text_input("Camera streaming URL")
        longitude = col3.text_input("Longitude")
        latitude = col4.text_input("Latitude")

    # if the save button is clicked, update the metadata file
    if save:
        st.write("New camera trap added! 🎉")
        for i, camera_trap in enumerate(df["name"].values):
            df.at[i, "name"] = st.session_state[f"name_{i}"]
            df.at[i, "url"] = st.session_state[f"url_{i}"]
            df.at[i, "longitude"] = st.session_state[f"lon_{i}"]
            df.at[i, "latitude"] = st.session_state[f"lat_{i}"]

        # add a new row to the dataframe
        if st.session_state.new_row:
            d = {
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "url": url,
                "last_detection": "",
                "last_activation": "",
            }
            new_row = pd.DataFrame(data=d, index=[0])
            df = df.append(new_row, ignore_index=True)

        update_metadata(OUTPUT_BUCKET_NAME, CAMERAS_METADATA_FILE, df)
        del st.session_state.new_row
        st.experimental_rerun()

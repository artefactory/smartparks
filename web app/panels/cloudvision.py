import json
import yaml
import pytz
import streamlit as st
from datetime import datetime, time
from utils import (
    run_query,
    filter_dataframe_by_date_time_range,
    read_media,
    get_labels,
    get_face_annotations,
    read_media,
)

# load config file
with open("config.yml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# constants
BUCKET_NAME = config["BUCKET_NAME"]
OUTPUT_BUCKET_NAME = config["OUTPUT_BUCKET_NAME"]
CAMERA_NAMES = config["CAMERA_NAMES"]
PROJECT = config["PROJECT"]
TIME_ZONE = config["TIME_ZONE"]
USE_CASES = config["USE_CASES"]


def app():

    # set title
    st.markdown("### 📸 Cloud Vision")

    # create 2 columns to display the camera trap and date selectors alongside
    col1, col2 = st.columns(2)

    # select box to select the camera trap
    selected_camera_trap = col1.selectbox("Camera trap", CAMERA_NAMES)

    # date selector
    selected_date = col2.date_input(
        "Date",
        (
            datetime.now(pytz.timezone(TIME_ZONE)),
            datetime.now(pytz.timezone(TIME_ZONE)),
        ),
    )

    # time selector
    selected_time = st.slider("Time:", value=(time(8, 30), time(23, 59)))

    # leave one blank space
    st.markdown("#")

    if len(selected_date) == 2:

        df = run_query(
            f"SELECT * FROM `{PROJECT}.images.{selected_camera_trap}`"
        )

        df = filter_dataframe_by_date_time_range(df, selected_date, selected_time)

        for index, row in df.iterrows():

            image = row["uri"].replace(f"gs://{BUCKET_NAME}/", "")

            # create a streamlit container to contin both the video and the predictions elements
            container = st.container()

            # add a caption above the video displaying its datetime
            container.subheader(row["timestamp"].strftime("%d/%m/%Y | %H:%M:%S"))

            # create 2 columns to display the video and the predictions alongside
            img_col, col2 = container.columns([2, 1])

            # get image
            # source_img = read_media(BUCKET_NAME, image)

            annotated_img = read_media(OUTPUT_BUCKET_NAME, image)
            img_col.image(annotated_img)

            # get labels
            labels = get_labels(json.loads(row["response"]))

            # display labels
            for label in labels:
                col2.text(label + ": " + str(round(labels[label] * 100, 2)) + "%")
                col2.progress(labels[label])

            # get annotations
            face_annotations = get_face_annotations(json.loads(row["response"]))

            # display annotations
            if face_annotations is not None:
                for annotation in face_annotations:
                    col2.text(f"{face_annotations[annotation]} {annotation} detected")


            # if selected_use_case == "label detection":
            #     # display image
            #     img_col.image(source_img, use_column_width=True)

            #     # get labels
            #     labels = get_labels(json.loads(row["response"]), selected_use_case)

            #     # display labels
            #     for label in labels:
            #         col2.text(label + ": " + str(round(labels[label] * 100, 2)) + "%")
            #         col2.progress(labels[label])

            # elif selected_use_case == "object detection":

            #     # # get bounding boxes
            #     # bounding_boxes = get_bounding_boxes(json.loads(row["response"]))

            #     # # display image
            #     # bounding_boxes_img = draw_bounding_boxes(
            #     #     BUCKET_NAME, image, bounding_boxes
            #     # )
            #     # img_col.image(bounding_boxes_img, use_column_width=True)

            #     annotated_img = read_media(OUTPUT_BUCKET_NAME, image)
            #     img_col.image(annotated_img)

            #     # get labels
            #     labels = get_labels(json.loads(row["response"]), selected_use_case)

            #     # display labels
            #     for label in labels:
            #         col2.text(label + ": " + str(round(labels[label] * 100, 2)) + "%")
            #         col2.progress(labels[label])

            # elif selected_use_case == "people detection":
            #     # display image
            #     img_col.image(source_img, use_column_width=True)

            #     # get annotations
            #     face_annotations = get_face_annotations(json.loads(row["response"]))

            #     # display annotations
            #     for annotation in face_annotations:
            #         col2.text(f"{face_annotations[annotation]} {annotation} detected")

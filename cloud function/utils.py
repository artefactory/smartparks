# Imports
import os
import base64
import json
import cv2
import requests

import pandas as pd

import moviepy.editor as moviepy

from datetime import datetime
from google.cloud import storage
from google.cloud import bigquery

from config import OUTPUT_BUCKET_NAME, INPUT_BUCKET_NAME, CAMERA_TRAPS_METADATA_PATH

from google.cloud import vision, videointelligence

from google.cloud.vision import AnnotateImageResponse
from google.cloud.videointelligence import AnnotateVideoResponse

from PIL import Image, ImageDraw
from io import BytesIO

from typing import Tuple, List


# Construct a BigQuery client object.
bigquery_client = bigquery.Client()

# Construct a Cloud Storage client object.
storage_client = storage.Client()

OUTPUT_BUCKET = storage_client.get_bucket(OUTPUT_BUCKET_NAME)
INPUT_BUCKET = storage_client.get_bucket(INPUT_BUCKET_NAME)


def get_camera_trap_metadata(camera_trap_name: str) -> Tuple[float, float]:
    """
    This function retrieves the metadata for a given camera trap.

    Args:
      camera_trap_name (str): The name of the camera trap for which to retrieve metadata.

    Returns:
      Tuple[float, float]: A tuple of longitude, and latitude.
    """

    # Get the dataframe of metadata information for all camera traps
    df = pd.read_csv(CAMERA_TRAPS_METADATA_PATH)

    # Get the values of the longitude, and latitude for the camera trap
    longitude = df.loc[df["name"] == camera_trap_name, "longitude"]
    latitude = df.loc[df["name"] == camera_trap_name, "latitude"]

    # Return the metadata as a tuple
    return longitude, latitude


def update_metadata(camera_trap_name: str, last_detection: str, last_activation: str):

    """
    Update the camera traps metadata.

    Returns:
        None: updates the metadata
    """

    # Get the dataframe of metadata information for all camera traps
    df = pd.read_csv(CAMERA_TRAPS_METADATA_PATH)

    df.loc[df["name"] == camera_trap_name, "last_detection"] = last_detection
    df.loc[df["name"] == camera_trap_name, "last_activation"] = last_activation

    OUTPUT_BUCKET.blob("metadata.csv").upload_from_string(
        df.to_csv(index=None), content_type="text/csv"
    )


def send_to_node_red(metadata: dict) -> None:
    """
    Sends metadata to Node-RED API

    Args:
      metadata (dict): metadata to be sent

    Returns:
      None
    """
    # node-red API url
    url = "https://nodered-xgwild.smartparks.org/artefact"
    response = requests.post(url, metadata)

    print(response.status_code)


def bigquery_insert(
    project: str,
    dataset: str,
    camera_trap_name: str,
    timestamp: datetime,
    uri: str,
    response: json,
):
    """
    Inserts a new row into a BigQuery table.

    Args:
        project (str): The ID of the project containing the BigQuery table.
        dataset (str): The ID of the dataset containing the BigQuery table.
        camera_trap_name (str): The ID of the table to insert the row into.
        timestamp (datetime): The timestamp for the new row.
        uri (str): The URI for the new row.
        response (json): The response for the new row.

    Returns:
        None: The function does not return a value.

    Raises:
        google.api_core.exceptions.GoogleAPIError: If an error occurs while inserting the row.
    """

    # Set the ID of the table to insert the row into
    table_id = f"{project}.{dataset}.{camera_trap_name}"

    # Create a list containing a dictionary with the new row's values
    row_to_insert = [
        {
            "timestamp": timestamp,
            "uri": uri,
            "response": response,
        }
    ]

    # Call the BigQuery client's insert_rows_json() method to insert the new row
    errors = bigquery_client.insert_rows_json(table_id, row_to_insert)

    # Check if there were any errors while inserting the row
    if errors == []:
        print("New rows have been added.")
    else:
        # Print any errors to the console
        print("Encountered errors while inserting rows: {}".format(errors))


def draw_bounding_boxes(
    file_name: str, vertices_list: List[dict], display_text: str = ""
) -> bytes:
    """
    This function downloads an image from a Google Cloud Storage bucket,
    draws bounding boxes around specified regions in the image and returns
    the image as a base64 encoded string.

    Parameters:
    file_name (str): The uri of the image file in the Google Cloud Storage bucket.
    vertices_list (list of dicts): List of dictionaries containing the vertices of the bounding boxes.
    display_text (str, optional): Text to display on the image. Default is "".

    Returns:
    encoded_image (bytes): Base64 encoded image with the bounding boxes drawn.
    """

    # Download the image from the Google Cloud Storage bucket
    blob = INPUT_BUCKET.get_blob(file_name)
    encoded_image = BytesIO(blob.download_as_string())

    # Open the image using Pillow library
    pillow_img = Image.open(encoded_image)

    # Create a draw object to draw on the image
    draw = ImageDraw.Draw(pillow_img)

    # Get the width and height of the image
    width, height = pillow_img.size

    # Draw the bounding boxes on the image
    for vertices in vertices_list:
        # Calculate the start and end points of the rectangle
        rect_start = (vertices[0]["x"] * width, vertices[0]["y"] * height)
        rect_end = (vertices[2]["x"] * width, vertices[2]["y"] * height)
        draw.rectangle((rect_start, rect_end), outline="green", width=2)

    # Save the image with the bounding boxes
    buffered = BytesIO()
    pillow_img.save(buffered, format="JPEG")

    OUTPUT_BUCKET.blob(f"{file_name}").upload_from_string(
        buffered.getvalue(), content_type="image/jpeg"
    )

    # Encode the image as a base64 string
    encoded_image = base64.b64encode(buffered.getvalue())

    return encoded_image


########################################################################## IMAGES ##########################################################################


def get_image_response(gcs_uri: str, features: List[str]):
    """
    This function uses the Google Cloud Vision API to extract image features and annotate an image located in a Google Cloud Storage bucket.

    Parameters:
    gcs_uri (str): The URI of the image in the Google Cloud Storage bucket.
    features (List[str]): The features to extract from the image. Can be one of: 'FACE_DETECTION', 'LANDMARK_DETECTION', 'LOGO_DETECTION', 'LABEL_DETECTION', 'DOCUMENT_TEXT_DETECTION', 'SAFE_SEARCH_DETECTION', 'IMAGE_PROPERTIES', or 'CROP_HINTS'.

    Returns:
    response: A response object from the Google Cloud Vision API.
    """

    # Initialize the client for the Google Cloud Vision API
    client = vision.ImageAnnotatorClient()

    # Set the source for the image
    source = {"image_uri": gcs_uri}
    image = {"source": source}

    # Specify the feature type to extract
    requests = {
        "image": image,
        "features": [{"type_": feature} for feature in features],
    }

    # Use the API to annotate the image
    response = client.annotate_image(requests)

    return response


def get_image_outputs(response: str) -> dict:
    """
    Get image response from given response and use case.

    This function takes a response in the form of a json string. The function performs the relevant annotations, computes relevant statistics and summarizes the results.

    Args:
    response (str): The response to be processed in the form of a json string.

    Returns:
    dict: A dictionary containing the predictions, prediction count, summary and additional information depending on the use case.
    """

    response = json.loads(AnnotateImageResponse.to_json(response))
    result = {}

    labels = response["localizedObjectAnnotations"]
    labels = sorted(labels, key=lambda x: x["score"], reverse=True)

    best_detection = labels[0]["name"]

    result["predictions"] = labels
    result["predictions_count"] = len(labels)

    summary = str(len(labels)) + " objects detected: "
    bounding_boxes = []
    for label in labels:
        summary += f"{label['name']} {round(label['score']*100, 2)}%     "
        bounding_boxes.append(label["boundingPoly"]["normalizedVertices"])

    result["bounding_boxes"] = bounding_boxes

    labels = response["faceAnnotations"]

    joy_detected = 0
    sorrow_detected = 0
    anger_detected = 0
    surprise_detected = 0
    headwear_detected = 0

    summary += str(len(labels)) + " people detected: "
    for label in labels:
        if label["joyLikelihood"] >= 3:
            joy_detected += 1
        if label["sorrowLikelihood"] >= 3:
            sorrow_detected += 1
        if label["angerLikelihood"] >= 3:
            anger_detected += 1
        if label["surpriseLikelihood"] >= 3:
            surprise_detected += 1
        if label["headwearLikelihood"] >= 3:
            headwear_detected += 1

    summary += f"{joy_detected} joy, {sorrow_detected} sorrow, {anger_detected} anger, {surprise_detected} surprise, {headwear_detected} headwear"
    result["summary"] = summary

    return best_detection, result


########################################################################## VIDEOS ##########################################################################


def get_video_response(gcs_uri: str, features: List[str]):
    """
    This function analyzes a video stored in a Google Cloud Storage (GCS) bucket using Google's Video Intelligence API and returns the API's response.

    Args:
      gcs_uri (str): The URI of the video file in the GCS bucket.
      features (List[str]): The types of analysis to be performed on the video, such as "LABEL_DETECTION".

    Returns:
      response: The response from the Video Intelligence API, containing the results of the video analysis.
    """

    # Create a client for the Video Intelligence API
    client = videointelligence.VideoIntelligenceServiceClient()

    # Analyze the video using the specified feature
    response = client.annotate_video(
        request={"features": features, "input_uri": gcs_uri}
    )

    # Return the result of the video analysis, with a timeout of 500 seconds
    return response.result(timeout=500)


def get_video_outputs(response):
    """
    Extracts object and person detection annotations from a Google Cloud Video Intelligence API response.

    Args:
      response (AnnotateVideoResponse object): The response object returned by the Google Cloud Video Intelligence API.

    Returns:
      best_detection (str): The label of the most confidently detected object.
      summary (str): A summary of the object and person detection annotations in the response.
                     The summary includes the number of objects detected and their average confidence, as well as the number of people detected.
    """
    # Convert AnnotateVideoResponse to a dictionary and extract the first annotation result
    response = json.loads(AnnotateVideoResponse.to_json(response))["annotationResults"][
        0
    ]

    # Extract object annotations
    labels = response["objectAnnotations"]

    # initialize the dictionary
    average_dict = {}

    for item in labels:
        # if the item is not in the dictionary, initialize its sum and count
        label = item["entity"]["description"]
        if label not in average_dict:
            average_dict[label] = {"sum": 0, "count": 0}
        # add the item value to the sum and increment the count
        average_dict[label]["sum"] += item["confidence"]
        average_dict[label]["count"] += 1

    # Create summary string
    summary = str(len(average_dict)) + " objects detected: "

    best_detection = list(average_dict.keys())[0]

    # calculate the average and update the summary
    for item, item_info in average_dict.items():
        average = item_info["sum"] / item_info["count"]
        summary += f"{item} {round(average*100, 2)}%     "

    # Extract person detection annotations
    labels = response["personDetectionAnnotations"]

    # Create summary string
    if len(labels) != 1:
        summary += str(len(labels)) + " people detected"
    else:
        summary += str(len(labels)) + " person detected"

    return best_detection, summary


def annotate_video(response, file_name):
    """
    This function takes an `AnnotateVideoResponse` object containing video annotations and the name of the video file as input.
    It saves the video file to the `/tmp` directory, opens the video file using OpenCV, loops over the frames of the video,
    and draws bounding boxes around detected objects in each frame. It then saves the annotated video file to the `/tmp` directory,
    converts the annotated video file to the MP4 format, and uploads the annotated video file to a GCS bucket.

    Args:
       response (AnnotateVideoResponse): An `AnnotateVideoResponse` object containing video annotations.
       file_name (str): The name of the video file.

    Returns:
      annotated_frame (str): The annotated frame in base64 format.
    """

    data = json.loads(AnnotateVideoResponse.to_json(response))["annotationResults"][0][
        "objectAnnotations"
    ]

    # Get the video file from the GCS bucket
    blob = INPUT_BUCKET.get_blob(file_name)

    # Save the video to the /tmp directory
    blob.download_to_filename("/tmp/video.mp4")

    # Open the video file
    cap = cv2.VideoCapture("/tmp/video.mp4")

    # Get the video dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec for the output video file
    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    # Get the video frame rate
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))

    # Create the VideoWriter object
    out = cv2.VideoWriter(
        "/tmp/annotated_video.avi", fourcc, frame_rate, (width, height)
    )

    if not out.isOpened():
        print("Failed to open output video file")

    delta = 0.05

    frame_count = 0

    # Loop over the frames of the video
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        video_time = frame_count / frame_rate

        for annotation in data:
            if annotation["confidence"] > 0.6:

                # Loop over the object annotations in the JSON file
                for frame_data in annotation["frames"]:

                    frame_time = float(frame_data["timeOffset"].split("s")[0])

                    if video_time - delta <= frame_time <= video_time + delta:
                        box = frame_data["normalizedBoundingBox"]

                        # Get the normalized bounding box coordinates and convert them to pixel coordinates
                        left = int(box["left"] * width)
                        top = int(box["top"] * height)
                        right = int(box["right"] * width)
                        bottom = int(box["bottom"] * height)

                        # Draw the bounding box on the frame
                        cv2.rectangle(
                            frame, (left, top), (right, bottom), (0, 255, 0), 2
                        )

        # Convert an annotated frame to base64
        if frame_count == 60:
            _, buffer = cv2.imencode(".jpg", frame)
            annotated_frame = base64.b64encode(buffer)

        # Write the annotated frame to the output video file
        out.write(frame)

        frame_count += 1

    # Release the video capture and video writer objects, and destroy the OpenCV windows
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Convert the video to mp4
    mp4_video = moviepy.VideoFileClip("/tmp/annotated_video.avi")
    mp4_video.write_videofile("/tmp/annotated_video.mp4")

    # Save the video in Cloud Storage
    OUTPUT_BUCKET.blob(file_name).upload_from_filename("/tmp/annotated_video.mp4")

    # Delete the temporary video files
    os.remove("/tmp/video.mp4")
    os.remove("/tmp/annotated_video.avi")
    os.remove("/tmp/annotated_video.mp4")

    return annotated_frame

import os
import base64
import json
import cv2
import requests

import pandas as pd
import streamlit as st

from pathlib import Path
from datetime import datetime
from google.cloud import storage
from config import OUTPUT_BUCKET_NAME, INPUT_BUCKET_NAME, CAMERA_TRAPS_METADATA_PATH
from google.oauth2 import service_account

from google.cloud import vision, videointelligence

from google.cloud.vision import AnnotateImageResponse
from google.cloud.videointelligence import AnnotateVideoResponse

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from typing import Tuple, List

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= '.streamlit/smart-parks-cameras-65ce9e1412c5.json'
storage_client = storage.Client(credentials=credentials)
OUTPUT_BUCKET = storage_client.get_bucket(OUTPUT_BUCKET_NAME)
INPUT_BUCKET = storage_client.get_bucket(INPUT_BUCKET_NAME)


def save_as_csv(
    df: pd.DataFrame, destination_path: str, timestamp: bool = True
) -> None:

    """
    Save DataFrame as a CSV file to specified destination path.

    This function saves a given pandas DataFrame as a CSV file to a specified destination path in a Google Cloud Storage bucket. If the "timestamp" argument is set to True, the file will be saved with a timestamp in its name. Otherwise, the file will be saved with the name "master.csv".

    Args:
    df (pd.DataFrame): The DataFrame to be saved as a CSV file.
    destination_path (str): The path to the destination folder in the Google Cloud Storage bucket.
    timestamp (bool, optional): If True, the file will be saved with a timestamp in its name. Defaults to True.

    Returns:
    None
    """

    if timestamp:
        OUTPUT_BUCKET.blob(
            f"{destination_path}/{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        ).upload_from_string(df.to_csv(index=False), "text/csv")
    else:
        OUTPUT_BUCKET.blob(f"{destination_path}/master.csv").upload_from_string(
            df.to_csv(index=False), "text/csv"
        )


def get_master_file(master_file_path: str) -> pd.DataFrame:
    """
    Get the master file as a pandas DataFrame.

    This function retrieves the master file at the specified path in a Google Cloud Storage bucket and returns it as a pandas DataFrame.
    If the file does not exist or cannot be read, an empty DataFrame is returned.

    Args:
    master_file_path (str): The path to the master file in the Google Cloud Storage bucket.

    Returns:
    pd.DataFrame: The master file as a pandas DataFrame. If the file does not exist or cannot be read, an empty DataFrame is returned.
    """

    try:
        df = pd.read_csv(f"gs://{OUTPUT_BUCKET_NAME}/{master_file_path}")
    except:
        df = pd.DataFrame()
    return df


def update_master_file(df: pd.DataFrame, destination_path: str) -> None:
    """
    Update the master file by concatenating a DataFrame with it.

    This function retrieves the current master file from a Google Cloud Storage bucket, concatenates the input DataFrame with it, and saves the result as the updated master file in the same bucket.

    Args:
    df (pd.DataFrame): The DataFrame to be concatenated with the master file.
    destination_path (str): The path to the destination folder in the Google Cloud Storage bucket where the master file is located.

    Returns:
    None
    """

    master_df = get_master_file(f"{destination_path}/master.csv")
    master_df = pd.concat([master_df, df], ignore_index=True)
    save_as_csv(master_df, destination_path, timestamp=False)


def create_json(json_object, filename: str) -> None:
    """
    Save a JSON object to a file in a Google Cloud Storage bucket.

    This function creates a new file in the specified Google Cloud Storage bucket and saves the JSON object to it.

    Args:
    json_object: The JSON object to be saved.
    filename (str): The name of the file to be created.

    Returns:
    None
    """

    # create a blob
    blob = OUTPUT_BUCKET.blob(filename)
    # upload the blob
    blob.upload_from_string(data=json_object, content_type="application/json")


def get_camera_trap_metadata(camera_trap_name: str) -> Tuple[str, float, float]:
    """
    This function retrieves the metadata for a given camera trap.

    Args:
    camera_trap_name (str): The name of the camera trap for which to retrieve metadata.

    Returns:
    Tuple[str, float, float]: A tuple of preferred model name, longitude, and latitude.
    """

    # Get the dataframe of metadata information for all camera traps
    df = pd.read_csv(CAMERA_TRAPS_METADATA_PATH)

    # Filter the dataframe to include only the information for the given camera trap
    df = df[df.name == camera_trap_name]

    # Get the values of the preferred model, longitude, and latitude for the camera trap
    preferred_model = df.preferred_model.values[0]
    longitude = df.longitude.values[0]
    latitude = df.latitude.values[0]

    # Return the metadata as a tuple
    return preferred_model, longitude, latitude


def send_to_node_red(metadata: dict) -> None:
    """
    Sends metadata to Node-RED API

    Parameters:
    metadata (dict): metadata to be sent

    Returns:
    None
    """
    # node-red API url
    url = "https://nodered-xgwild.smartparks.org/artefact"
    response = requests.post(url, metadata)

    print(response.status_code)


def draw_bounding_boxes(
    gcs_uri: str, vertices_list: List[dict], display_text: str = ""
) -> bytes:
    """
    This function downloads an image from a Google Cloud Storage bucket,
    draws bounding boxes around specified regions in the image and returns
    the image as a base64 encoded string.

    Parameters:
    gcs_uri (str): The uri of the image file in the Google Cloud Storage bucket.
    vertices_list (list of dicts): List of dictionaries containing the vertices of the bounding boxes.
    display_text (str, optional): Text to display on the image. Default is "".

    Returns:
    encoded_image (bytes): Base64 encoded image with the bounding boxes drawn.
    """

    # Download the image from the Google Cloud Storage bucket
    blob = INPUT_BUCKET.get_blob(gcs_uri)
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
        draw.rectangle((rect_start, rect_end), outline="green", width=3)

    # Save the image with the bounding boxes
    buffered = BytesIO()
    pillow_img.save(buffered, format="JPEG")

    # Encode the image as a base64 string
    encoded_image = base64.b64encode(buffered.getvalue())

    return encoded_image


########################################################################## IMAGES ##########################################################################


def get_image_response(gcs_uri: str, file_name: str, feature: str):
    """
    This function uses the Google Cloud Vision API to extract image features and annotate an image located in a Google Cloud Storage bucket.

    Parameters:
    gcs_uri (str): The URI of the image in the Google Cloud Storage bucket.
    file_name (str): The name of the file that will be used to save the annotated image.
    feature (str): The feature type to extract from the image. Can be one of: 'FACE_DETECTION', 'LANDMARK_DETECTION', 'LOGO_DETECTION', 'LABEL_DETECTION', 'DOCUMENT_TEXT_DETECTION', 'SAFE_SEARCH_DETECTION', 'IMAGE_PROPERTIES', or 'CROP_HINTS'.

    Returns:
    response: A response object from the Google Cloud Vision API.
    """

    # Initialize the client for the Google Cloud Vision API
    client = vision.ImageAnnotatorClient()

    # Set the source for the image
    source = {"image_uri": gcs_uri}
    image = {"source": source}

    # Specify the feature type to extract
    requests = {"image": image, "features": [{"type_": feature}]}

    # Use the API to annotate the image
    response = client.annotate_image(requests)

    # Convert the response to JSON format and save it
    response_json = AnnotateImageResponse.to_json(response)
    create_json(response_json, file_name)

    return response


def get_image_content(gcs_uri: str) -> str:
    """
    This function retrieves an image from a Google Cloud Storage (GCS) bucket and returns its contents as a base64 encoded string.

    Args:
    gcs_uri (str): The URI of the image file in the GCS bucket.

    Returns:
    str: The base64 encoded contents of the image.

    """

    # Get the image file from the GCS bucket
    blob = INPUT_BUCKET.get_blob(gcs_uri)
    
    #parse image 

    # Encode the image contents as a base64 string
    encoded_image = base64.b64encode(blob.download_as_bytes())

    return encoded_image


def get_image_outputs(response: str, use_case: str) -> dict:
    """
    Get image response from given response and use case.

    This function takes a response in the form of a json string, and a use case string, which specifies the type of annotations required on the image. Based on the use case, the function performs the relevant annotations, computes relevant statistics and summarizes the results.

    The function returns a dictionary containing the predictions, prediction count, summary and additional information (such as bounding boxes) depending on the use case.

    Args:
    response (str): The response to be processed in the form of a json string.
    use_case (str): The type of annotations required on the image, one of "label_detection", "object_detection", "face_detection".

    Returns:
    dict: A dictionary containing the predictions, prediction count, summary and additional information depending on the use case.
    """

    # response = json.loads(AnnotateImageResponse.to_json(response))
    result = {}

    if use_case == "label_detection":
        labels = response["labelAnnotations"]
        result["predictions"] = labels
        result["predictions_count"] = len(labels)

        summary = str(len(labels)) + " labels detected: "
        for label in labels:
            summary += f"{label['description']} {round(label['score']*100, 2)}%     "
        result["summary"] = summary

    elif use_case == "object_detection":
        labels = response["localizedObjectAnnotations"]
        result["predictions"] = labels
        result["predictions_count"] = len(labels)

        summary = str(len(labels)) + " objects detected: "
        bounding_boxes = []
        for label in labels:
            summary += f"{label['name']} {round(label['score']*100, 2)}%     "
            bounding_boxes.append(label["boundingPoly"]["normalizedVertices"])
        result["summary"] = summary
        result["bounding_boxes"] = bounding_boxes

    else:
        labels = response["faceAnnotations"]
        result["predictions"] = labels
        result["predictions_count"] = len(labels)

        joy_detected = 0
        sorrow_detected = 0
        anger_detected = 0
        surprise_detected = 0
        headwear_detected = 0

        summary = str(len(labels)) + " people detected: "
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

    return result


########################################################################## VIDEOS ##########################################################################


def get_first_frame_content(gcs_uri: str) -> dict:
    """
    This function retrieves a video from a Google Cloud Storage (GCS) bucket, extracts its first frame, and returns the frame's contents as a jpg encoded string.

    Args:
    gcs_uri (str): The URI of the video file in the GCS bucket.

    Returns:
    dict: A dictionary containing the contents of the first frame of the video, encoded as a jpg image.
          The key is "file" and the value is the encoded image. If the video cannot be read or the first frame cannot be extracted, returns None.

    """

    # Get the video file from the GCS bucket
    blob = INPUT_BUCKET.get_blob(gcs_uri)

    filepath = f"media/{gcs_uri}"
    fd = os.open(filepath, os.O_WRONLY)
    # Save the video to the /tmp directory
    blob.download_to_filename(filepath)

    # Read the first frame of the video
    vidcap = cv2.VideoCapture(filepath)
    success, image = vidcap.read()

    # Encode the first frame as a jpg image
    if success:
        success, encoded_image = cv2.imencode(".jpg", image)
        # Return the encoded image
        if success:
            os.close(filepath)
            os.remove(filepath)
            return base64.b64encode(encoded_image.tobytes())
        else:
            os.close(filepath)
            os.remove(filepath)
            print("Impossible to read uploaded video")


def get_video_response(gcs_uri: str, output_uri: str, feature: str):
    """
    This function analyzes a video stored in a Google Cloud Storage (GCS) bucket using Google's Video Intelligence API and returns the API's response.

    Args:
    gcs_uri (str): The URI of the video file in the GCS bucket.
    output_uri (str): The URI where the API's output will be stored in the GCS bucket.
    feature (str): The type of analysis to be performed on the video, such as "LABEL_DETECTION".

    Returns:
    response: The response from the Video Intelligence API, containing the results of the video analysis.

    """

    # Create a client for the Video Intelligence API
    client = videointelligence.VideoIntelligenceServiceClient()

    # Analyze the video using the specified feature
    response = client.annotate_video(
        request={"features": [feature], "input_uri": gcs_uri, "output_uri": output_uri}
    )

    # Return the result of the video analysis, with a timeout of 500 seconds
    return response.result(timeout=500)


def get_video_outputs(response, use_case):
    """
    Given a video annotation response and a use case, this function returns a dictionary containing the following:
        - predictions: list of annotations based on the given use case
        - predictions_count: count of annotations in the predictions list
        - summary: string summarizing the predictions

    :param response: AnnotateVideoResponse object from Google Cloud Video Intelligence API
    :type response: AnnotateVideoResponse
    :param use_case: string specifying the desired output type ("label_detection", "object_detection", or "person_detection")
    :type use_case: str
    :return: dictionary containing predictions, predictions_count, and summary
    :rtype: dict
    """

    # Convert AnnotateVideoResponse to a dictionary and extract the first annotation result
    # response = json.loads(AnnotateVideoResponse.to_json(response))["annotationResults"][0]
    response =  response["annotation_results"][0]
    result = {}

    if use_case == "label_detection":
        # Extract label annotations
        labels = response["segment_label_annotations"]
        result["predictions"] = labels
        result["predictions_count"] = len(labels)

        # Create summary string
        summary = str(len(labels)) + " labels detected: "

        for label in labels:
            summary += f"{label['entity']['description']} {round(label['segments'][0]['confidence']*100, 2)}%     "

        result["summary"] = summary

    elif use_case == "object_detection":
        # Extract object annotations
        labels = response["object_annotations"]
        result["predictions"] = labels

        # initialize the dictionary
        average_dict = {}

        for item in labels:
            # if the item is not in the dictionary, initialize its sum and count
            label = item['entity']['description']
            if label not in average_dict:
                average_dict[label] = {'sum': 0, 'count': 0}
            # add the item value to the sum and increment the count
            average_dict[label]['sum'] += item['confidence']
            average_dict[label]['count'] += 1

        result["predictions_count"] = len(average_dict)

        # Create summary string
        summary = str(len(average_dict)) + " objects detected: "

        # calculate the average and update the summary
        for item, item_info in average_dict.items():
            average = item_info['sum'] / item_info['count']
            summary += f"{item} {round(average*100, 2)}%     "

        result["summary"] = summary

    else:
        # Extract person detection annotations
        labels =  response["person_detection_annotations"]
        result["predictions"] = labels
        result["predictions_count"] = len(labels)

        # Create summary string
        if len(labels) != 1:
            summary = str(len(labels)) + " people detected: "
        else:
            summary = str(len(labels)) + " person detected: "

        result["summary"] = summary

    return result



def filter_video_response(response, use_case):
    response = response["annotation_results"][0]
    # animals_list = pd.read_pickle("gs://smartparks-inputs/animals_lower_list.pickle")
    # result = []

    # if use_case == "label_detection":
    #     labels = response["segmentLabelAnnotations"]
    #     for i, label in enumerate(labels):
    #         if label["entity"]["description"] in animals_list:
    #             label["description"] = label["entity"]["description"]
    #             label["confidence"] = label["segments"][0]["confidence"]
    #             label.pop("entity")
    #             label.pop("segments")
    #             label.pop("categoryEntities")
    #             label.pop("frames")
    #             label.pop("version")
    #             result.append(label)

    # elif use_case == "object_detection":
    #     labels = response["objectAnnotations"]
    #     for i, label in enumerate(labels):
    #         if label["entity"]["description"] in animals_list:
    #             label["description"] = label["entity"]["description"]
    #             label.pop("entity")
    #             label.pop("segment")
    #             label.pop("version")
    #         result.append(label)

    # else:
    #     labels =  response["personDetectionAnnotations"]
    #     for i, label in enumerate(labels):
    #         label["segment"] = label["tracks"][0]["segment"]
    #         label["confidence"] = label["tracks"][0]["confidence"]
    #         label.pop("tracks")
    #         label.pop("version")
    #         result.append(label)

    # return result

    return response

# Imports
from pathlib import Path

from datetime import datetime

from google.cloud.vision import AnnotateImageResponse
from google.cloud.videointelligence import AnnotateVideoResponse

from config import (
    PROJECT,
    IMAGE_USE_CASES,
    VIDEO_USE_CASES,
    INPUT_BUCKET_NAME,
    OUTPUT_BUCKET_NAME,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

from utils import (
    get_image_response,
    get_video_response,
    get_camera_trap_metadata,
    send_to_node_red,
    get_image_outputs,
    get_video_outputs,
    draw_bounding_boxes,
    bigquery_insert,
    annotate_video,
    update_metadata,
)


def get_predictions(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    # Get the name of the image/video file to annotate
    media_name = event["name"]
    print(f"Processing: {media_name}.")

    # Get the camera_trap_name
    camera_trap_name = media_name.split("/")[0]
    print(camera_trap_name)
    
    # Get camera trap's coordinates
    longitude, latitude = get_camera_trap_metadata(camera_trap_name)

    gcs_uri = "gs://" + f"{INPUT_BUCKET_NAME}/" + media_name

    extension = Path(media_name).suffix.lower()

    timestamp = datetime.now()

    metadata = {
        "camera_trap_name": camera_trap_name,
        "longitude": longitude,
        "latitude": latitude,
        "timestamp": timestamp,
        "media_name": media_name.split("/")[1],
        "type": event["contentType"],
        "size": event["size"],
        "input_url": gcs_uri,
    }

    if extension in IMAGE_EXTENSIONS:
        response = get_image_response(
            gcs_uri, IMAGE_USE_CASES.values()
        )

        bigquery_insert(PROJECT, "images", camera_trap_name, timestamp.strftime("%Y-%m-%d %H:%M:%S"), gcs_uri, AnnotateImageResponse.to_json(response))
    
        best_detection, image_response =  get_image_outputs(response)

        annotated_image = draw_bounding_boxes(media_name, image_response["bounding_boxes"])

        metadata["summary"] = image_response["summary"]
        metadata["image"] = annotated_image

        update_metadata(camera_trap_name, best_detection, timestamp)

        send_to_node_red(metadata)

    elif extension in VIDEO_EXTENSIONS:

        response = get_video_response(
                gcs_uri, VIDEO_USE_CASES.values()
        )

        bigquery_insert(PROJECT, "videos", camera_trap_name, timestamp.strftime("%Y-%m-%d %H:%M:%S"), gcs_uri, AnnotateVideoResponse.to_json(response))

        best_detection, video_response =  get_video_outputs(response)

        annotated_first_frame = annotate_video(response, media_name)

        metadata["summary"] = video_response["summary"]
        metadata["image"] = annotated_first_frame

        update_metadata(camera_trap_name, best_detection, timestamp)
        
        send_to_node_red(metadata)

    else:
        print(f"File extension {extension} not supported")

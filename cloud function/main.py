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
    """
    Triggered by a change to a Cloud Storage bucket.

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
    
    # Create a GCS URI for the input file
    gcs_uri = "gs://" + f"{INPUT_BUCKET_NAME}/" + media_name
    
    # Get the current timestamp
    timestamp = datetime.now()
    
    # Create a metadata dictionary
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
    
    # Get the file extension
    extension = Path(media_name).suffix.lower()
    
    # If the file is an image, process it
    if extension in IMAGE_EXTENSIONS:
        
        # Call the Vision API
        response = get_image_response(gcs_uri, IMAGE_USE_CASES.values())
        
        # Insert the API response into BigQuery
        bigquery_insert(PROJECT, "images", camera_trap_name, timestamp.strftime("%Y-%m-%d %H:%M:%S"), gcs_uri, AnnotateImageResponse.to_json(response))
        
        # Get the best detection and image outputs
        best_detection, image_outputs = get_image_outputs(response)
        
        # Draw bounding boxes on the image
        annotated_image = draw_bounding_boxes(media_name, image_outputs["bounding_boxes"])
        
        # Add the summary and annotated image to the metadata dictionary
        metadata["summary"] = image_outputs["summary"]
        metadata["image"] = annotated_image
        
        # Update the camera trap metadata with the best detection and timestamp
        update_metadata(camera_trap_name, best_detection, timestamp)
        
        # Send the metadata to Node-RED
        send_to_node_red(metadata)
    
    # If the file is a video, process it
    elif extension in VIDEO_EXTENSIONS:
        
        # Call the Video Intelligence API 
        response = get_video_response(gcs_uri, VIDEO_USE_CASES.values())
        
        # Insert the API response into BigQuery
        bigquery_insert(PROJECT, "videos", camera_trap_name, timestamp.strftime("%Y-%m-%d %H:%M:%S"), gcs_uri, AnnotateVideoResponse.to_json(response))
        
        # Get the best detection and video response
        best_detection, summary= get_video_outputs(response)
        
        # Annotate the first frame of the video with bounding boxes
        annotated_first_frame = annotate_video(response, media_name)
        
        # Add the summary and annotated image to the metadata dictionary
        metadata["summary"] = summary
        metadata["image"] = annotated_first_frame
        
        # Update the camera trap metadata with the best detection and timestamp
        update_metadata(camera_trap_name, best_detection, timestamp)
        
        # Send the metadata to Node-RED
        send_to_node_red(metadata)
    
    # If the file is not an image or video, print an error message
    else:
        print(f"File extension {extension} not supported")

from google.cloud import vision, videointelligence

PROJECT = "smart-parks-cameras"

INPUT_BUCKET_NAME = "camera-traps-media"
OUTPUT_BUCKET_NAME = "models-outputs"

IMAGE_EXTENSIONS = [".jpeg", ".jpg", ".png", ".gif", ".raw", ".bmp", ".pdf", ".webp", ".ico", ".tiff"]
VIDEO_EXTENSIONS = [".mov", ".mpeg4", ".mp4", ".avi"]

IMAGE_FEATURES = [vision.Feature.Type.OBJECT_LOCALIZATION , vision.Feature.Type.LABEL_DETECTION , vision.Feature.Type.FACE_DETECTION]

IMAGE_USE_CASES = {
    "object_detection": vision.Feature.Type.OBJECT_LOCALIZATION,
    "label_detection": vision.Feature.Type.LABEL_DETECTION,
    "people_detection": vision.Feature.Type.FACE_DETECTION
}

VIDEO_FEATURES = [videointelligence.Feature.OBJECT_TRACKING, videointelligence.Feature.LABEL_DETECTION, videointelligence.Feature.PERSON_DETECTION]

VIDEO_USE_CASES = {
    "object_detection": videointelligence.Feature.OBJECT_TRACKING,
    "label_detection": videointelligence.Feature.LABEL_DETECTION,
    "people_detection": videointelligence.Feature.PERSON_DETECTION
}

CAMERA_TRAPS_METADATA_PATH = f"gs://{OUTPUT_BUCKET_NAME}/metadata.csv"

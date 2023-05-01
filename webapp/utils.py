import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from google.cloud import storage
import yaml
import json


# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

client = storage.Client(credentials=credentials)

# load config file
with open("config.yml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Perform query.
@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    """
    Executes the given query and return the result as pandas dataframe
    Args:
        query (str): SQL query to be executed
    Returns:
        pd.Dataframe: The dataframe resulting from the query
    """
    df = pd.read_gbq(query, credentials=credentials)
    return df


def filter_dataframe_by_date_time_range(df, date_range, time_range):
    """
    Filter a pandas DataFrame based on a given date range and time range.

    Args:
        df (pandas DataFrame): The DataFrame to filter
        date_range (tuple): A tuple containing the start and end date (as datetime.date objects)
        time_range (tuple): A tuple containing the start and end time (as datetime.time objects)

    Returns:
        pandas DataFrame: The filtered DataFrame
    """
    # Convert date range to datetime objects
    start_date = date_range[0]
    end_date = date_range[1]

    # Convert time range to timezone-aware datetime objects
    start_time = time_range[0]
    end_time = time_range[1]

    # Filter the DataFrame by date and time range
    mask = (df["timestamp"].dt.date >= start_date) & (
        df["timestamp"].dt.date <= end_date
    )
    filtered_df = df.loc[mask]
    filtered_df = filtered_df.loc[
        filtered_df["timestamp"].apply(lambda x: start_time <= x.time() <= end_time)
    ]

    return filtered_df


def get_labels(response):
    """
    Extracts object labels and their scores from the given response dictionary and returns them in a sorted dictionary.
    
    Args:
        response (dict): A dictionary containing localized object annotations.
        
    Returns:
        dict: A sorted dictionary containing the object labels as keys and their scores as values.
    """
    
    result = {}

    # labels = response["labelAnnotations"]

    # for label in labels:
    #     result[label["description"]] = label["score"]

    # Extract labels and their scores from the response dictionary
    labels = response["localizedObjectAnnotations"]
    for label in labels:
        result[label["name"]] = label["score"]

    # Sort the labels and their scores in descending order of score
    sorted_dict = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))

    return sorted_dict


def get_video_labels(response):
    """
    Extracts object labels and their average confidence scores from the given response dictionary and returns them in a sorted dictionary.
    
    Args:
        response (dict): A dictionary containing video annotation results.
        
    Returns:
        dict: A sorted dictionary containing the object labels as keys and their average confidence scores as values.
    """
    
    result = {}

    # labels = response["annotationResults"][0]["segmentLabelAnnotations"]

    # for label in labels:
    #     result[label["entity"]["description"]] = label["segments"][0]["confidence"]
    
    # Extract labels and their confidence scores from the response dictionary
    labels = response["annotationResults"][0]["objectAnnotations"]
    average_dict = {}
    for item in labels:
        label = item["entity"]["description"]
        if label not in average_dict:
            # if the item is not in the dictionary, initialize its sum and count
            average_dict[label] = {"sum": 0, "count": 0}
        # add the item value to the sum and increment the count
        average_dict[label]["sum"] += item["confidence"]
        average_dict[label]["count"] += 1
    
    # Calculate the average and update the summary
    for item, item_info in average_dict.items():
        average = item_info["sum"] / item_info["count"]
        result[item] = average

    # Sort the labels and their scores in descending order of average score
    sorted_dict = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))

    return sorted_dict



def get_face_annotations(response):
    """
    Extracts the number of faces that express each of the specified emotions (joy, sorrow, anger, surprise) and the presence of headwear in the given response dictionary and returns them in a dictionary.
    
    Args:
        response (dict): A dictionary containing face annotations.
        
    Returns:
        dict: A dictionary containing the number of faces that express each of the specified emotions (joy, sorrow, anger, surprise) and the presence of headwear.
        If none of the emotions or headwear are detected, returns None.
    """
    
    annotations_dict = {"joy": 0, "sorrow": 0, "anger": 0, "surprise": 0, "headwear": 0}
    
    # Extract face annotations from the response dictionary
    labels = response["faceAnnotations"]
    
    # Update the annotations dictionary with the number of faces expressing each emotion and the presence of headwear
    for label in labels:
        if label["joyLikelihood"] >= 3:
            annotations_dict["joy"] += 1

        if label["sorrowLikelihood"] >= 3:
            annotations_dict["sorrow"] += 1

        if label["angerLikelihood"] >= 3:
            annotations_dict["anger"] += 1

        if label["surpriseLikelihood"] >= 3:
            annotations_dict["surprise"] += 1

        if label["headwearLikelihood"] >= 3:
            annotations_dict["headwear"] += 1
    
    # Check if none of the emotions or headwear are detected
    if all(value == 0 for value in annotations_dict.values()):
        return None
    else:
        return annotations_dict



def get_number_of_people(response):
    """
    Extracts the number of people detected in a video using the person detection annotations in the given response.
    
    Args:
        response (dict): The response from the Google Cloud Video Intelligence API.
    
    Returns:
        str or None: If people are detected, returns a string with the number of people detected (e.g., "1 person detected", 
        "2 people detected"). Otherwise, returns None.
    """
    
    # Extract person detection annotations
    labels = response["annotationResults"][0]["personDetectionAnnotations"]

    if len(labels) == 0:
        return None
    elif len(labels) == 1:
        return "1 person detected"
    else:
        return str(len(labels)) + " people detected"



# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def list_videos(bucket_name, folder_name):
    """Retrieve the list of videos present in the given folder.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket whre the videos are saved
        folder_name (string): Name of the folder in the GCP Cloud storage bucket whre the videos are saved

    Returns:
        List: list of the videos' names present in the given folder
    """
    files = client.list_blobs(bucket_name, prefix=folder_name)
    fileList = [file.name for file in files if ".mp4" in file.name]
    fileList.reverse()
    return fileList


@st.cache_data(ttl=600)
def list_media(bucket_name, folder_name, media_type="video"):
    """Retrieve the list of videos present in the given folder.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket whre the videos are saved
        folder_name (string): Name of the folder in the GCP Cloud storage bucket whre the videos are saved

    Returns:
        List: list of the videos' names present in the given folder
    """
    files = client.list_blobs(bucket_name, prefix=folder_name)
    fileList = [file.name for file in files if type_of_media(file.name) == media_type]
    fileList.reverse()
    return fileList


def list_json_blobs(bucket_name, folder_name):
    """
    Lists the names of all the JSON blobs in a specified folder in a Google Cloud Storage bucket.
    
    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket.
        folder_name (str): The name of the folder to search in the bucket.
    
    Returns:
        list: A list of the names of all the JSON blobs in the specified folder, in reverse order.
    """
    files = client.list_blobs(bucket_name, prefix=folder_name)
    fileList = [file.name for file in files if ".json" in file.name]
    fileList.reverse()
    return fileList


# Retrieve video contents.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def read_media(bucket_name, file_name):
    """Retrieve the video contents.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket whre the videos are saved
        file_name (string): Name of the video in the GCP Cloud storage bucket whre the videos are saved

    Returns:
        String: video contents
    """
    bucket = client.bucket(bucket_name)
    data = bucket.blob(file_name).download_as_bytes()
    return data


def read_json_from_bucket(bucket_name, filename):
    """
    Reads a JSON file from a specified bucket in Google Cloud Storage.

    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket.
        filename (str): The name of the JSON file to read from the bucket.

    Returns:
        dict: A dictionary containing the data from the JSON file.
    """
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(filename)

    # Download the contents of the blob as a string and then parse it using json.loads() method
    data = json.loads(blob.download_as_string(client=None))
    return data



# Retrieve video predictions.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_predictions(bucket_name, folder_name, model_name):
    """Retrieve the video predictions.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket where the videos are saved
        folder_name (string): Name of the folder in the GCP Cloud storage bucket where the videos are saved
        model_name (string): Name of the model used to predict the video

    Returns:
        pandas.Dataframe: Pandas dataframe of the predictions
    """
    master_path = (
        folder_name + "/predictions/" + model_name + "/zamba_predictions_master.csv"
    )
    bucket = client.bucket(bucket_name)
    data = io.StringIO(bucket.blob(master_path).download_as_text(encoding="utf-8"))
    df = pd.read_csv(data)
    return df


# Retrieve file contents.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_video_predictions(video_name, df, threshold=0.5):
    """Retrieve the video predictions.

    Args:
        video_name (string): Name of the video
        df (pandas.Dataframe): Pandas dataframe of the predictions
        threshold (float): Threshold used to filter the predictions

    Returns:
        pandas.Dataframe: Pandas dataframe of the predictions of just the given video
    """
    df = df[df["filepath"].str.contains(video_name)]
    df = df.drop("filepath", axis=1)
    df = df[[i for i in df.columns if (df[i] > threshold).any()]]
    df = df.reset_index(drop=True)
    df = df.sort_values(by=0, ascending=False, axis=1)
    return df


# Retrieve file contents.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def print_summary(
    camera_name,
    start_date,
    end_date,
    start_time,
    end_time,
    model_name,
    number_of_videos,
    detected_animals,
):
    """Retrieve the video metadata.

    Args:
        camera_name (string): Name of the camera trap
        start_date (string): Slected start date
        end_date (string): Selected end date
        start_time (string): Slected start time
        end_time (string): Selected end time
        model_name (string): Name of the model used to get the predictions
        number_of_videos (int): Number of videos retrieved
        detected_animals (int): Number of animals retrieved

    Returns:
        String: query result summary
    """
    summary = f"The camera trap *{camera_name}*  was triggerd *{number_of_videos} times*,\
         between the *{start_date}* and the *{end_date}*\
         and during the *{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}* time range.\n"

    if len(detected_animals) != 0:
        summary += (
            f"The *{model_name}* model predicted the presence of these animals:\n"
        )
        for animal in detected_animals:
            summary += "- " + animal + "\n"

    return summary


def get_metadata(bucket_name, file_name):
    """Retrieve the video metadata.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket where the metadata are saved
        file_name (string): Name of the csv file in the GCP Cloud storage bucket where the metadata are saved

    Returns:
        pandas.Dataframe: Pandas dataframe of the metadata
    """
    bucket = client.bucket(bucket_name)
    data = io.StringIO(bucket.blob(file_name).download_as_text(encoding="utf-8"))
    df = pd.read_csv(data)
    return df


def update_metadata(bucket_name, file_name, df):
    """
    Update the camera traps metadata.

    Args:
        bucket_name (string): Name of the GCP Cloud storage bucket where the metadata are saved
        file_name (string): Name of the csv file in the GCP Cloud storage bucket where the metadata are saved
        df (pandas.Dataframe): Pandas dataframe of the metadata

    Returns:
        None: updates the metadata
    """
    bucket = client.bucket(bucket_name)
    bucket.blob(file_name).upload_from_string(
        df.to_csv(index=None), content_type="text/csv"
    )

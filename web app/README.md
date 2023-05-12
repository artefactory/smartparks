
## Where the magic happens 🪄

![The workflow’s core](https://cdn-images-1.medium.com/max/9412/1*J7b1S0xGdxO0lCloSdmWSA.png)

Google Cloud Functions are like little bits of code that you can write and upload to Google’s servers. They’re called “serverless” because you don’t need to worry about managing any servers or infrastructure. Instead, you can focus on writing code that responds to events, in our case a file upload in a Google Cloud Storage bucket.

You can write your code in a bunch of different programming languages, like JavaScript, Python, or Go, and then deploy it to Google Cloud. Once your code is deployed, it will automatically run whenever the specified event occurs. And the cool thing is, you only pay for the time that your code is actually running, so it’s a really cost-effective way to build applications that need event-driven functionality.

For all these reasons we choose to use a cloud function as the core of our workflow. It allows us to focus on the problem we want to solve in an easy, scalable, and cost-effective way.

To recreate the Cloud Function we used you just need to follow these steps:

![1. In the console, click the Navigation menu -> Cloud Functions -> CREATE FUNCTION](https://cdn-images-1.medium.com/max/8644/1*uKcELfz9TB00vYu6hs-xsw.png)

![2. Name your function, choose Cloud Storage on creating file as trigger, and select the bucket you want to use](https://cdn-images-1.medium.com/max/8450/1*KoVeIWWLE0cjevYRgvLnaA.png)

![3. Change the Memory allocated and Timeout settings (we chose this config even if even a more strict one would have been enough)](https://cdn-images-1.medium.com/max/2000/1*-ODnwsrgP2aOa2QYkQ0pSA.png)

![4. Choose Python as Runtime (we choose Python 3.8)](https://cdn-images-1.medium.com/max/2000/1*tzTmylizBAGtCypqG3xHeg.png)

Done that you should be in the situation shown in the image below:

![Default Python Cloud Function structure ](https://cdn-images-1.medium.com/max/2284/1*eiT51ZmfqEy7znsSPiRnuA.png)

Overall, the structure of a Python Cloud Function is quite simple. You just need a *main.py* file that contains the function you want to run (the Entry point), and optionally a *requirements.txt* file if you have any dependencies.

As our code is not so trivial we decided to structure it a bit more by adding a *utils.py* file where we defined all the useful functions used by the main script and a *config.py *to store all the project global variables.

![Our Cloud Function code structure](https://cdn-images-1.medium.com/max/2042/1*9krwLbwcODomQ7A_6hue8Q.png)

You can find the complete code [here](https://github.com/artefactory/smartparks/tree/main/cloud%20function).

### How does it work?

get_predictionsis the cloud function entry point, so it’s the function that will be executed every time the cloud function is triggered. Let’s see together what it does.

    # main.py
    
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

First of all, we get from the event payload the media name, and from it, we extract the name of the camera trap that captured it. Why is the camera trap name in front of the media name? 

Folders in Google Cloud Storage Buckets are virtual constructs, which means that they do not actually exist as physical directories on disk. Instead, they are represented as part of the object’s name. For example, if an object’s name is *“folder1/folder2/object.txt”*, then it is stored in a bucket with the name “bucket-name” as *“bucket-name/folder1/folder2/object.txt”*.

Inside our ingestion bucket, we have a folder for each camera trap so every time a media is uploaded the Cloud Function receives as event name a string like *camera_trap_name/media_name*.

After that we get the camera trap coordinates using the get_camera_tra_metadata **function defined in utils.py.

    # utils.py
    
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
        longitude = df.loc[df['name'] == camera_trap_name, 'longitude']
        latitude = df.loc[df['name'] == camera_trap_name, 'latitude']
    
        # Return the metadata as a tuple
        return longitude, latitude

The function reads from a CSV file stored in another Cloud Storage bucket that stores a bunch of metadata for each camera trap like name, longitude, latitude, last activation timestamp, last detection, and the URL of the camera trap folder in the Cloud Storage ingestion bucket.

Going on with the code of the get_predictions **function you can see that we start populating a metadata dictionary:

    # main.py
    
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

This dictionary will later be sent to Node-RED, where we developed a flow that will use it to generate an alert for the park rangers on the [*Earth Ranger](https://www.earthranger.com/)* website.

As you can see immediately after we start distinguishing between images and videos based on the media extension. The steps involved are basically the same but both the implementation of the utils functions and the Google APIs used are different. From now on we’ll dig into the video case scenario since it’s the most challenging one.

 1. **Call the Video Intelligence API**

    # main.py
    
    # Call the Video Intelligence API 
    response = get_video_response(gcs_uri, VIDEO_USE_CASES.values())

    # utils.py
    
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

The first step is calling the [Cloud Video Intelligence API](https://cloud.google.com/video-intelligence), a tool provided by Google Cloud that uses machine learning to analyze videos and extract valuable information such as object detection, shot and scene detection, label detection, explicit content detection, and speech transcription. 

To do so we defined the get_video_response function that takes as arguments:

* *gcs_uri*: The URI of the video file in the GCS bucket

* *features*: The types of analysis to be performed on the video, such as “LABEL_DETECTION”

and returns the API response containing the results of the video analysis.

**2. Insert the API response into BigQuery**

    # main.py
    
    # Insert the API response into BigQuery
    bigquery_insert(PROJECT, "videos", camera_trap_name, timestamp.strftime("%Y-%m-%d %H:%M:%S"), gcs_uri, AnnotateVideoResponse.to_json(response))

    # utils.py
    
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

Google Cloud Storage is a highly scalable and durable object storage service that can be used to store a wide range of data types, including the responses generated by the Google Cloud Vision API. However, there are several reasons why using Google BigQuery to store the API responses may be a better option:

 1. Querying capabilities: BigQuery provides advanced querying capabilities, such as the ability to use SQL to query JSON data, which can be useful for analyzing and generating insights from the API responses. 

 2. Cost-effectiveness: While both services offer affordable storage options, BigQuery’s pricing model is based on the amount of data processed rather than the amount of data stored. This means that using BigQuery can be more cost-effective in situations where you need to frequently query and analyze the data.

 3. Real-time analysis: BigQuery allows for real-time analysis of data as it is being ingested, which can be useful for generating real-time insights from the API responses.

That’s why we chose to store the API responses in BigQuery rather than in Cloud Storage. We defined the bigquery_insert **function to insert a new row (timestamp, media guri, API response) into a given BigQuery table. We organized our data into two datasets within BigQuery: one for images and the other for videos. Each dataset contains tables for individual camera traps.

![BigQuery project structure](https://cdn-images-1.medium.com/max/2634/1*u3xoUoQkYU6X73TITocatQ.png)

To create a dataset in BigQuery open the BigQuery page in the Google Cloud console, in the Explorer panel, select the project where you want to create the dataset, expand the 3 dots option menu and click Create dataset.

On the Create Dataset page:

* For Dataset ID, enter a unique dataset name.

* For Location type, choose a geographic location for the dataset. After a dataset is created, the location can’t be changed.

* For Default table expiration, choose one of the following options:
- *Never:* (Default) Tables created in the dataset are never automatically deleted. You must delete them manually.
- *Number of days after table creation:* This value determines when a newly created table in the dataset is deleted. 

Finally, click Create Dataset.

![Create dataset page](https://cdn-images-1.medium.com/max/3814/1*Jjgyc1FHg4lU26GEOSbOAQ.png)

Once you have your dataset to create a table go to the Dataset info section, click the + button, and then Create table.
In the Create table panel, specify the following details:

* In the Source section, select Empty table in the Create table list

* In the Destination section, specify the following details:
– In the Table field, enter the name of the table that you want to create
– Verify that the Table type field is set to Native table

* In the Schema section, enter the schema definition by specifying each field’s Name, Type, and Mode

![Create empty table](https://cdn-images-1.medium.com/max/3776/1*Vu40lcybThVLJJKGi5T4LA.png)

**3. Get the best detection and create a response summary **

    # main.py
    
    # Get the best detection and video response
    best_detection, video_response = get_video_outputs(response)

    # utils.py
    
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

From the API response, we want to create a human-readable summary of it and extract the best detection, so the annotation with the highest confidence score. We will send these data to Node-RED altogether with the previously built metadata dictionary. The get_video_outputs serve exactly this purpose.

**4. Annotate the media with bounding boxes**

    # main.py
    
    # Annotate the video with bounding boxes and return the first frame
    annotated_first_frame = annotate_video(response, media_name)

    # utils.py
    
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
    
        data = json.loads(AnnotateVideoResponse.to_json(response))["annotationResults"][0]["objectAnnotations"]
    
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
        out = cv2.VideoWriter("/tmp/annotated_video.avi", fourcc, frame_rate, (width, height))
    
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
                _, buffer = cv2.imencode('.jpg', frame)
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

As the API response includes the bounding boxes of the detected objects, it would be beneficial to display them in the output. However, implementing this requires a somewhat cumbersome process of reading the video frame by frame, drawing the bounding boxes on each frame, and finally combining all the annotated frames to produce a video. Nevertheless, the resulting video is definitely worth the effort.

To annotate a video, the annotate_video function requires the response object containing the annotations and the video file's name as inputs. The function saves the video file to the '/tmp' directory and opens it using OpenCV. It then loops through the video's frames, draws bounding boxes around the detected objects in each frame, and saves the annotated video file to the '/tmp' directory. Finally, it converts the annotated video file to MP4 format and uploads it to a GCS bucket, and returns one of the annotated frames.

**5. Add the summary and annotated image to the metadata dictionary**

    # main.py
    
    # Add the summary and annotated image to the metadata dictionary
    metadata["summary"] = summary
    metadata["image"] = annotated_first_frame

We can now add the API response summary and the annotated frame with the bounding boxes to the metadata dictionary, which will be sent to Node-RED in step 7.

**6. Update the camera trap metadata**

    # main.py
    
    # Update the camera trap metadata with the best detection and timestamp
    update_metadata(camera_trap_name, best_detection, timestamp)

    # utils.py
    
    def update_metadata(camera_trap_name: str, last_detection: str, last_activation: str):
    
        """
        Update the camera traps metadata.
    
        Returns:
            None: updates the metadata
        """
        
        # Get the dataframe of metadata information for all camera traps
        df = pd.read_csv(CAMERA_TRAPS_METADATA_PATH)
    
        df.loc[df['name'] == camera_trap_name, 'last_detection'] = last_detection
        df.loc[df['name'] == camera_trap_name, 'last_activation'] = last_activation
    
        OUTPUT_BUCKET.blob("metadata.csv").upload_from_string(
            df.to_csv(index=None), content_type="text/csv"
        )

To keep the camera traps metadata up to date, we created the update_metadatafunction. This function updates the last detection and last activation values for a given camera trap.

**7. Send the metadata to Node-RED**

    # main.py
    
    # Send the metadata to Node-RED
    send_to_node_red(metadata)

    # utils.py
    
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

Finally, using the send_to_node_red function, we send everything to Node-RED, where we have a flow that receives the metadata dictionary and uses it to generate an event on the Earth Ranger website.

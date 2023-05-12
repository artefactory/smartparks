
## Automated Pipeline and Web App for Efficient Camera Trap Management

![](https://cdn-images-1.medium.com/max/2000/1*ATBmDGwBH_l0vM823b6gwA.jpeg)

## Introduction

Hey there! Thanks for tuning in to our article series. In our last article, we talked about how we built a fully automated scalable pipeline on Google Cloud able to extract insights from camera traps media using Google computer vision APIs.

Today, we want to dive deeper into it and show how we connected our architecture to camera traps and the cool web app we built to manage it all.

Camera traps are becoming increasingly popular for wildlife conservation, monitoring livestock, and even security purposes. However, they generate an enormous amount of data, which can be overwhelming for manual processing. But with our pipeline, we can quickly and efficiently process all that data and extract valuable insights.

We believe that the web app we built can significantly improve the management of camera traps. It’s designed to simplify their management and provide users with a user-friendly interface for visualizing data. You can see everything at a glance and know what’s happening in real time.

We think this is a super exciting development for anyone interested in camera traps, machine learning, and data management. So let’s waste no more time and get started!

## The Workflow 

Since the previous article the workflow has changed a bit, here is the updated and improved version

![Project workflow](https://cdn-images-1.medium.com/max/14844/1*mjB7Xmc6ey2G5PYdRmbarQ.png)

As you can see everything starts when an image or a video is taken by a camera trap. The device sends an email to a dedicated mailbox. A Node-RED flow is then used to check if there are any new emails if so, it uploads their attachments to a Google Cloud Bucket. The upload triggers the rest of the pipeline. The Cloud Function is executed, it calls Google Cloud Vision APIs and:

* Saves the responses in BigQuery

* Saves the annotated images/videos in another bucket in Cloud Storage

* Sends the responses to a Node-RED flow 

Finally, from Node-RED the responses are sent to Earth Ranger, a real-time software solution that aids protected area managers, ecologists, and wildlife biologists in making more informed operational decisions for wildlife conservation. 

In addition, we developed a simple web app that reads from Cloud Storage and BigQuery and allows the users to manage and monitor the camera traps.

In the following sections, we’ll dive into each of the workflow steps, this time providing all the necessary information to reproduce what we have done including code snippets.

## From the bushes🌿to GCP 💻

So now how can we get the media taken from the camera traps in GCP in order to trigger the rest of the pipeline? Easy, to do so we used Google-developed GCP nodes to extend Node-RED and interact with GCP functions.

![Camera traps — GCP connection](https://cdn-images-1.medium.com/max/6946/1*N0BvcOD9Ue-vOwfYcMvuSA.png)

Node-RED is an open-source flow-based programming tool used for creating event-driven applications. In Node-RED, the user creates pipelines by connecting nodes together to represent the flow of data. Each node performs a specific action, such as reading data from a sensor, manipulating the data, or sending the data to an output device. The nodes are created using a visual editor, which makes it easy to create and modify flows without having to write any code. 

One of the key reasons that Node-RED has become as popular as now is the ease with which developers can build additional nodes that encapsulate rich sets functions. Once written, these add-on nodes can be used by flow writers without having to know the complexities of their underlying operation. One just drags a new node onto the canvas and uses it. 

One of these extensions is indeed the [*node-red-contrib-google-cloud](https://flows.nodered.org/node/node-red-contrib-google-cloud)* project. To install these nodes, navigate to the Node-RED system menu and select *Manage Palette*. Switch to the *Palette *tab and then switch to the *Install *tab within Palette. Search for the node set called *“node-red-contrib-google-cloud” *and then click *install*. Once installed, scroll down through the list of available palette nodes and you’ll find a GCP section containing the currently available GCP building blocks.

![How to install extension nodes](https://cdn-images-1.medium.com/max/8648/1*h2d4Io8Ez5MbjxmegVC4Ag.png)

### Media upload flow

The image below shows the full Node-RED flow used to upload the media to Cloud Storage. The first node is just an ingestion node that triggers the flow every 5 seconds, after that we have an email node. This node is used to repeatedly get emails from POP3 or IMAP servers and forward them on as a msg if not already seen. The email node is not a default node so to use it make sure to install the *node-red-node-email *package following the same steps shown before for the Google package.

![Node-RED flow used to upload camera traps media to Cloud Storage](https://cdn-images-1.medium.com/max/2960/1*Hhodeqz7JUpVwErF9iXjfQ.png)

The output is transformed to match the expected input of the GCP write input node. The message payload should contain the content of the attachments, and the message filename property should specify the name of the Cloud Storage bucket where the media will be uploaded.

To create a bucket, go to the Cloud Storage Buckets page in the Google Cloud console, go to Buckets, and click Create bucket. On the Create a bucket page, enter your bucket information like name, location, class and click Create.

![Create Bucket page](https://cdn-images-1.medium.com/max/2000/1*QV9BzChSMLqzDNXqqUPnEA.png)

Finally, we have 2 debug nodes, in dark green, to debug respectively the read email and the output of the gcp write node. The nodes in pink, instead, are used to display the attachments. Note that also these ones are additional nodes. They are part of the *node-red-contrib-image-tools *package and they work only with images. If you try to display a video an error message will be displayed as in the picture above.

### The final touch

Oh great now we are ready to go! Nah, don’t run so fast there is still the most important piece of the puzzle to set up. The flow as it is now will not work, we miss something. If we check the properties of the gcp write node we see that we have a property called credentials, yes credentials that’s what we miss! Of course to allow Node-RED to access our GCP project and write the media taken by the camera traps we need to give the correct permissions to it. 

The best way to do so is to create a service account, give it permission to write to Cloud Storage, and then generate a JSON key to authenticate the service account in Node-RED. Here are the steps to do so:

![1. Create a service account](https://cdn-images-1.medium.com/max/2000/1*KJOQWfXIpRHo-1Exxs3RtQ.png)

![2. Grant Editor permissions](https://cdn-images-1.medium.com/max/2052/1*aiWOwWfIoNh8-Igq04zCNw.png)

![3. Create a new private  JSON key](https://cdn-images-1.medium.com/max/2494/1*rp0GkO8bWT3ZwkfFSWPcRw.png)

![4. Add Google Cloud credentials to Node-RED](https://cdn-images-1.medium.com/max/5176/1*Sn6jtng5Jb2MDKqhkY0qFw.png)

That’s it, now you are really ready to go! 

Another cool feature of Node-RED is that you can share flows in JSON format. This means that by importing [this](https://github.com/artefactory/smartparks/blob/main/node%20red%20flows/write_to_gcp.json) JSON file you can recreate and test the just described flow. 

![How to import Node-RED nodes](https://cdn-images-1.medium.com/max/7096/1*5T8EU3GpooTyRSWbHQED1g.png)

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

### The last piece of the puzzle

The very final step of our pipeline is to create an event on the Earth Ranger website that includes all the data necessary for park rangers to understand why the camera trap was triggered, and to use this information to take appropriate actions.

![Node-RED flow to create an event in the Earth Ranger website](https://cdn-images-1.medium.com/max/2872/1*PD83mLRhMfdLxaKoxB_gnw.png)

The flow begins with an *Http in* node that serves as the endpoint where the metadata dictionary sent by the Cloud Function is received. The metadata is then processed through a series of transformations and *Http POST* to generate an event in Earth Ranger. Since it’s not currently possible to create an event with attachments using a single request, three requests are needed. The first request creates an empty event in Earth Ranger, while the other two attach the media captured by the camera traps and add the detection summary.

The other nodes consist of dark green debug nodes, while the pink nodes display the annotated image from the metadata dictionary sent by the Cloud Function in Node-RED.

The created Earth Ranger event looks like the one below:

![Created Earth Ranger event](https://cdn-images-1.medium.com/max/2914/1*2f31YDMm-uq_4OT_sFHFYA.png)

As you can see it presents an attachment, that is the camera trap image (or in the case of videos one of its frames) annotated with bounding boxes and a note that consists in the summary, in natural language, of the response of the Google Cloud Vision API used.

## The Web App 

To complete the project we developed a Web App to manage and monitor the camera traps. As for the rest of the project we chose the approach able to provide the best result with the lowest effort, that’s why we designed our solution around [Streamlit ](https://streamlit.io/)and [Cloud Run](https://cloud.google.com/run). 

* Streamlit is an open-source Python library that enables data scientists and developers to quickly create interactive web applications. Streamlit includes a simple and easy-to-use API that enables users to quickly prototype and deploy their web applications, without requiring expertise in web development or UI design. It is commonly used in data science, machine learning, and AI projects to build interactive dashboards and visualizations.

* Cloud Run is a serverless computing platform provided by Google Cloud that enables users to run stateless containers in a fully managed environment. With Cloud Run, users can easily deploy and scale their applications, without needing to manage the underlying infrastructure or worry about server capacity. Compared to [App Engine](https://cloud.google.com/appengine), Cloud Run provides more flexibility and control over the environment in which the applications run. 

### Streamlit project structure

We designed the code in order to be able to make it scalable, easy to understand, and modify. 

    .
    └── Smartparks/
        ├── panels/
        │   ├── __init__.py
        │   ├── cloudvision.py
        │   ├── videointelligence.py
        │   ├── map.py
        │   └── configuration.py
        ├── .streamlit/
        │   └── secrets.toml
        ├── app.py
        ├── multipage.py
        ├── utils.py
        ├── config.yml
        ├── Dockerfile
        ├── requirements.txt
        ├── .dockerignore
        └── .gitignore

The project structure is organized in a way that separates its functionality into various directories and files. Here is a brief description of what each directory and file does:

* **Smartparks/** — This is the main directory for the project.

* **panels/** — This directory contains Python scripts that define different pages of the web app. Specifically, *cloudvision.py* creates a page for displaying images captured by camera traps. Similarly, *videointelligence.py* creates a page for displaying videos captured by camera traps. *map.py* allows users to view the locations of camera traps on a map, while *configuration.py* enables users to update metadata or add new cameras to the system.

* **.streamlit/** — This directory contains configuration files for Streamlit. The *secrets.toml* file is used for storing secrets such as API keys and authentication keys.

* **app.py **— This is the main Python script that runs the Smart Parks application.

* **multipage.py** — This Python script defines the framework for generating multiple Streamlit applications through an object-oriented framework.

* **utils.py **— This Python script contains utility functions used throughout the web app.

* **config.yml** — This is a YAML configuration file used to store various configuration options for the Smart Parks application.

* **Dockerfile **— This is a Docker configuration file used to create the Docker image of the project.

* **requirements.txt** — This file lists the dependencies required by the application.

* **.dockerignore **— This file specifies files and directories that should be ignored when creating the Docker image.

* **.gitignore** — This file specifies files and directories that should be ignored when pushing the code to a Git repository.

This design allows to easily add new pages to the web app, let’s see how.

The most important piece is the MultiPage class defined in the multipage.py file. This class is used to manage the multiple apps in our program. 

It has 2 methods:

* add_page: that takes the title of the page which we want to add to the list of apps and a Python function to render this page in Streamlit.

* run: That creates the sidebar and runs the app function

    # multipage.py
    
    # Define the multipage class to manage the multiple apps in our program
    class MultiPage:
        """Framework for combining multiple streamlit applications."""
    
        def __init__(self) -> None:
            """Constructor class to generate a list which will store all our applications as an instance variable."""
            self.pages = []
    
        def add_page(self, title, func) -> None:
            """Class Method to Add pages to the project
    
            Args:
                title (string): The title of page which we are adding to the list of apps
    
                func: Python function to render this page in Streamlit
            """
    
            self.pages.append({"title": title, "function": func})
    
        def run(self):
    
            # Render the spartparks logo on top of the sidebar
            st.sidebar.image("https://jasperspronk.nl/wp-content/uploads/2020/11/Smart_parks_logo.png", use_column_width=True)
    
            # Drodown to select the page to run
            page = st.sidebar.selectbox(
                "App Navigation", self.pages, format_func=lambda page: page["title"]
            )
    
            # run the app function
            page["function"]()

In the app.py python file you just have to import all the pages you want to use from the panels' folder, create an instance of the app, and use the add_pagemethod to add the imported pages. That’s it, nothing else must be done.

    # app.py
    
    from multipage import MultiPage
    from panels import (
        map,
        configuration,
        cloudvision,
        videointelligence,
    )  # import your pages here
    
    # Create an instance of the app
    app = MultiPage()
    
    # Title of the main page
    st.title("Artefact 🤝 Smart Parks")
    
    # Add all your applications (pages) here
    app.add_page("📸 Images", cloudvision.app)
    app.add_page("🎥 Videos", videointelligence.app)
    app.add_page("🌍 Map", map.app)
    app.add_page("⚙️ Configuration", configuration.app)
    
    # The main app
    app.run()

The only thing left to highlight is that in the panels' files like cloudvison.py you have to define all the code inside a function, we always defined it as app. This function has no arguments and does not return anything.

    # cloudvision.py
    
    def app():
    
        # set title
        st.markdown("### 📸 Cloud Vision")
    
        # create 2 columns to display the camera trap and date selectors alongside
        col1, col2 = st.columns(2)
    
        # select box to select the camera trap
        selected_camera_trap = col1.selectbox("Camera trap", CAMERA_NAMES)
    
        ...

### Connect Streamlit to Google Cloud

Now let’s see how to connect our streamlit web app to Google Cloud. We need to do it since to display the images/videos we have to read them from Cloud Storage. At the same time, we also want to read from BigQuery the full API response and other info like the timestamp. 

The steps required are more or less the same as we followed to connect Node-RED to GCP. 

 1. Create a service account

 2. Assign the *Viewer *role to the service account to allow read-only access

 3. Create a JSON key file

 4. Add the key to your local app secrets

As you can see the only different point is the last one. The Streamlit app will read secrets from the .streamlit/secrets.toml file in the app’s root directory. The file looks like this:

    # .streamlit/secrets.toml
    
    [connections.gcs]
    type = "service_account"
    project_id = "xxx"
    private_key_id = "xxx"
    private_key = "xxx"
    client_email = "xxx"
    client_id = "xxx"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "xxx"

You just have to insert the missing data by copying those values from the JSON key file you just created.

We defined 2 utils functions to read respectively from Cloud Storage and from BigQuery. The first one is run_query that executes the SQL query given as an argument and returns the result as pandas dataframe.

    # utils.py
    
    # Create API client.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    
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

The other one is read_media that retrieves the media content given its name and the name of the GCP Cloud storage bucket where the media is saved.

    # utils.py
    
    # Retrieve media content.
    # Uses st.cache_data to only rerun when the query changes or after 10 min.
    @st.cache_data(ttl=600)
    def read_media(bucket_name, file_name):
        """Retrieve the media content.
    
        Args:
            bucket_name (string): Name of the GCP Cloud storage bucket where the media is saved
            file_name (string): Name of the media
    
        Returns:
            String: media content
        """
        bucket = client.bucket(bucket_name)
        data = bucket.blob(file_name).download_as_bytes()
        return data

Both the functions make use of the st.cache_datadecorator to only rerun the function when the query changes or after ttl seconds.

### How it looks like 

Let’s see how the web app looks page by page. 

On the image page, you will find the page selector situated just below the Smart Parks logo on the left-hand side. Beneath the title, there are three filters: the camera trap filter, the date filter, and the time filter. The page displays all pictures taken by the selected camera trap within the specified DateTime range, along with bounding boxes, predictions, and their corresponding confidence scores.

![Images page](https://cdn-images-1.medium.com/max/8456/1*FyzlOiHP_mKPPkXByF2s2w.png)

The videos page looks basically the same but instead of images shows the videos taken by the camera trap. 

![Videos page](https://cdn-images-1.medium.com/max/3826/1*A0WajCQ4us6Wc02Ms-F0xg.png)

The Map page displays the locations of the camera traps. Clicking on the tags on the map will reveal the cameras metadata including the last activation timestamp and detection.

![Map page](https://cdn-images-1.medium.com/max/3830/1*ArKV4hCQ_Fewg1Rb2fhKvg.png)

Finally, the Configuration page allows for modifying camera trap locations and adding new cameras.

![Configuration page](https://cdn-images-1.medium.com/max/3826/1*YYhcod4HJDHYOBHS1I6MtA.png)

### Deployment

The very final step is to deploy the app to make it accessible from the internet and only from our localhost.

Both [Cloud Run](https://cloud.google.com/run) and [App Engine](https://cloud.google.com/appengine) are suitable options for deploying a Streamlit web app, but there are some differences to consider when deciding which one to use.

Google App Engine is a platform-as-a-service (PaaS) offering that allows developers to build and deploy web applications without worrying about the underlying infrastructure. App Engine provides a managed environment that automatically scales to meet demand, and supports multiple programming languages.

On the other hand, Google Cloud Run is a serverless container platform that allows developers to deploy stateless containers that automatically scale up and down in response to incoming traffic. With Cloud Run, developers can deploy applications in any language or framework that can be run in a container.

Compared to App Engine, Cloud Run provides more flexibility and control over the environment in which the applications run so it also has more control over the costs. That’s why we choose to deploy using Cloud Run instead of App Engine.

Deploying a web app in Cloud Run is very easy. Here are the steps:

* **Containerize your web app:** To deploy a web app in Cloud Run, you will need to first containerize your app. This involves packaging your code and its dependencies into a Docker container. 

* **Upload your container to a container registry: **Once your container is created, you will need to upload it to a container registry. Cloud Run supports a variety of container registries, including Google Container Registry (GCR), Docker Hub, and others. You can use the gcloud command-line tool or the Cloud Console to push your container to the registry.

For these first 2 points, you just need to run this command

    gcloud builds submit --tag gcr.io/GOOGLE_PROJECT_NAME/CONTAINER_NAME 

The gcloud builds submit command is used to *build and submit* a Docker container to the Google Container Registry.

* **Create a Cloud Run service: **After your container is uploaded to the registry, you can create a new Cloud Run service using the Cloud Console or the gcloud command-line tool. You will need to specify the container image and the desired settings for your service, such as the amount of memory and CPU resources to allocate, the maximum number of instances to run, and the network settings.

![Create a Cloud Run service](https://cdn-images-1.medium.com/max/5490/1*XDp8qlFiiXzflO2JyrcXXQ.png)

![Choose the container image to use](https://cdn-images-1.medium.com/max/8800/1*dZLELQ3ej6auDDoYy86oNw.png)

![Important setting to check to save money and manage access](https://cdn-images-1.medium.com/max/2904/1*cl-5tjke_9OaLSzYzctJMA.png)

* **Test and deploy your service:** Once your Cloud Run service is created, you can test it by accessing its URL in a web browser or using a tool like curl or wget. 

* **Configure access and security:** Finally, you will need to configure access and security for your Cloud Run service. You can set up authentication and authorization using tools like Cloud Identity and Access Management (IAM) and Cloud Identity-Aware Proxy (IAP). You can also configure HTTPS and SSL/TLS encryption to secure communications with your service.

## Conclusion

In this article series, we’ve explored how our automated pipeline on Google Cloud uses computer vision APIs to extract insights from camera trap data. Today, we went deeper and revealed how we connected our pipeline to the camera traps themselves, and the web app we built to manage it all.

Camera traps have become increasingly popular for wildlife conservation, livestock monitoring, and security purposes. However, managing the enormous amount of data generated by camera traps can be overwhelming. That’s where our pipeline and web app comes in — we can quickly and efficiently process camera trap data and provide users with an easy-to-use interface for managing the traps and visualizing the data in real-time.

Our work is a great starting point for anyone interested in camera traps, machine learning, and data management. By leveraging cutting-edge technology and data management techniques, we’ve made it possible to extract valuable insights from camera trap data that were previously difficult to obtain. We hope our work inspires others to explore the exciting possibilities of camera traps, machine learning, and data management, and we can’t wait to see what the future holds!

*Big shout out to Maël Deschamps for reviewing this post’s content and to Tim van Dam from Smart Parks for being our go-to guy during the project. You guys are awesome! Thanks a lot again for your help!*

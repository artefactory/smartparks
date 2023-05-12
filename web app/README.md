# The Web App 

To complete the project we developed a Web App to manage and monitor the camera traps. As for the rest of the project we chose the approach able to provide the best result with the lowest effort, that’s why we designed our solution around [Streamlit ](https://streamlit.io/)and [Cloud Run](https://cloud.google.com/run). 

* Streamlit is an open-source Python library that enables data scientists and developers to quickly create interactive web applications. Streamlit includes a simple and easy-to-use API that enables users to quickly prototype and deploy their web applications, without requiring expertise in web development or UI design. It is commonly used in data science, machine learning, and AI projects to build interactive dashboards and visualizations.

* Cloud Run is a serverless computing platform provided by Google Cloud that enables users to run stateless containers in a fully managed environment. With Cloud Run, users can easily deploy and scale their applications, without needing to manage the underlying infrastructure or worry about server capacity. Compared to [App Engine](https://cloud.google.com/appengine), Cloud Run provides more flexibility and control over the environment in which the applications run. 

## Streamlit project structure

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

* **app.py**— This is the main Python script that runs the Smart Parks application.

* **multipage.py** — This Python script defines the framework for generating multiple Streamlit applications through an object-oriented framework.

* **utils.py**— This Python script contains utility functions used throughout the web app.

* **config.yml** — This is a YAML configuration file used to store various configuration options for the Smart Parks application.

* **Dockerfile**— This is a Docker configuration file used to create the Docker image of the project.

* **requirements.txt** — This file lists the dependencies required by the application.

* **.dockerignore**— This file specifies files and directories that should be ignored when creating the Docker image.

* **.gitignore** — This file specifies files and directories that should be ignored when pushing the code to a Git repository.

This design allows to easily add new pages to the web app, let’s see how.

The most important piece is the MultiPage class defined in the multipage.py file. This class is used to manage the multiple apps in our program. 

It has 2 methods:

* add_page: that takes the title of the page which we want to add to the list of apps and a Python function to render this page in Streamlit.

* run: That creates the sidebar and runs the app function

In the `app.py` python file you just have to import all the pages you want to use from the panels' folder, create an instance of the app, and use the `add_page` method to add the imported pages. That’s it, nothing else must be done.

The only thing left to highlight is that in the panels' files like `cloudvison.py` you have to define all the code inside a function (we always defined it as app). This function has no arguments and does not return anything.

## Connect Streamlit to Google Cloud

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

## How it looks like 

Let’s see how the web app looks page by page. 

On the image page, you will find the page selector situated just below the Smart Parks logo on the left-hand side. Beneath the title, there are three filters: the camera trap filter, the date filter, and the time filter. The page displays all pictures taken by the selected camera trap within the specified DateTime range, along with bounding boxes, predictions, and their corresponding confidence scores.

![Images page](https://cdn-images-1.medium.com/max/8456/1*FyzlOiHP_mKPPkXByF2s2w.png)

The videos page looks basically the same but instead of images shows the videos taken by the camera trap. 

![Videos page](https://cdn-images-1.medium.com/max/3826/1*A0WajCQ4us6Wc02Ms-F0xg.png)

The Map page displays the locations of the camera traps. Clicking on the tags on the map will reveal the cameras metadata including the last activation timestamp and detection.

![Map page](https://cdn-images-1.medium.com/max/3830/1*ArKV4hCQ_Fewg1Rb2fhKvg.png)

Finally, the Configuration page allows for modifying camera trap locations and adding new cameras.

![Configuration page](https://cdn-images-1.medium.com/max/3826/1*YYhcod4HJDHYOBHS1I6MtA.png)

## Deployment

The very final step is to deploy the app to make it accessible from the internet and not only from our localhost.

Both [Cloud Run](https://cloud.google.com/run) and [App Engine](https://cloud.google.com/appengine) are suitable options for deploying a Streamlit web app, but there are some differences to consider when deciding which one to use.

Google App Engine is a platform-as-a-service (PaaS) offering that allows developers to build and deploy web applications without worrying about the underlying infrastructure. App Engine provides a managed environment that automatically scales to meet demand, and supports multiple programming languages.

On the other hand, Google Cloud Run is a serverless container platform that allows developers to deploy stateless containers that automatically scale up and down in response to incoming traffic. With Cloud Run, developers can deploy applications in any language or framework that can be run in a container.

Compared to App Engine, Cloud Run provides more flexibility and control over the environment in which the applications run so it also has more control over the costs. That’s why we choose to deploy using Cloud Run instead of App Engine.

Deploying a web app in Cloud Run is very easy. Here are the steps:

* **Containerize your web app:** To deploy a web app in Cloud Run, you will need to first containerize your app. This involves packaging your code and its dependencies into a Docker container. 

* **Upload your container to a container registry:** Once your container is created, you will need to upload it to a container registry. Cloud Run supports a variety of container registries, including Google Container Registry (GCR), Docker Hub, and others. You can use the gcloud command-line tool or the Cloud Console to push your container to the registry.

For these first 2 points, you just need to run this command

    gcloud builds submit --tag gcr.io/GOOGLE_PROJECT_NAME/CONTAINER_NAME 

The gcloud builds submit command is used to *build and submit* a Docker container to the Google Container Registry.

* **Create a Cloud Run service:** After your container is uploaded to the registry, you can create a new Cloud Run service using the Cloud Console or the gcloud command-line tool. You will need to specify the container image and the desired settings for your service, such as the amount of memory and CPU resources to allocate, the maximum number of instances to run, and the network settings.

![Create a Cloud Run service](https://cdn-images-1.medium.com/max/5490/1*XDp8qlFiiXzflO2JyrcXXQ.png)

![Choose the container image to use](https://cdn-images-1.medium.com/max/8800/1*dZLELQ3ej6auDDoYy86oNw.png)

![Important setting to check to save money and manage access](https://cdn-images-1.medium.com/max/2904/1*cl-5tjke_9OaLSzYzctJMA.png)

* **Test and deploy your service:** Once your Cloud Run service is created, you can test it by accessing its URL in a web browser or using a tool like curl or wget. 

* **Configure access and security:** Finally, you will need to configure access and security for your Cloud Run service. You can set up authentication and authorization using tools like Cloud Identity and Access Management (IAM) and Cloud Identity-Aware Proxy (IAP). You can also configure HTTPS and SSL/TLS encryption to secure communications with your service.

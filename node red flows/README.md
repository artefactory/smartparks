# From the bushes🌿to GCP 💻

So now how can we get the media taken from the camera traps in GCP in order to trigger the rest of the pipeline? Easy, to do so we used Google-developed GCP nodes to extend Node-RED and interact with GCP functions.

![Camera traps — GCP connection](https://cdn-images-1.medium.com/max/6946/1*N0BvcOD9Ue-vOwfYcMvuSA.png)

Node-RED is an open-source flow-based programming tool used for creating event-driven applications. In Node-RED, the user creates pipelines by connecting nodes together to represent the flow of data. Each node performs a specific action, such as reading data from a sensor, manipulating the data, or sending the data to an output device. The nodes are created using a visual editor, which makes it easy to create and modify flows without having to write any code. 

One of the key reasons that Node-RED has become as popular as now is the ease with which developers can build additional nodes that encapsulate rich sets functions. Once written, these add-on nodes can be used by flow writers without having to know the complexities of their underlying operation. One just drags a new node onto the canvas and uses it. 

One of these extensions is indeed the [*node-red-contrib-google-cloud](https://flows.nodered.org/node/node-red-contrib-google-cloud)* project. To install these nodes, navigate to the Node-RED system menu and select *Manage Palette*. Switch to the *Palette *tab and then switch to the *Install *tab within Palette. Search for the node set called *“node-red-contrib-google-cloud” *and then click *install*. Once installed, scroll down through the list of available palette nodes and you’ll find a GCP section containing the currently available GCP building blocks.

![How to install extension nodes](https://cdn-images-1.medium.com/max/8648/1*h2d4Io8Ez5MbjxmegVC4Ag.png)

## Media upload flow

The image below shows the full Node-RED flow used to upload the media to Cloud Storage. The first node is just an ingestion node that triggers the flow every 5 seconds, after that we have an email node. This node is used to repeatedly get emails from POP3 or IMAP servers and forward them on as a msg if not already seen. The email node is not a default node so to use it make sure to install the *node-red-node-email *package following the same steps shown before for the Google package.

![Node-RED flow used to upload camera traps media to Cloud Storage](https://cdn-images-1.medium.com/max/2960/1*Hhodeqz7JUpVwErF9iXjfQ.png)

The output is transformed to match the expected input of the GCP write input node. The message payload should contain the content of the attachments, and the message filename property should specify the name of the Cloud Storage bucket where the media will be uploaded.

To create a bucket, go to the Cloud Storage Buckets page in the Google Cloud console, go to Buckets, and click Create bucket. On the Create a bucket page, enter your bucket information like name, location, class and click Create.

![Create Bucket page](https://cdn-images-1.medium.com/max/2000/1*QV9BzChSMLqzDNXqqUPnEA.png)

Finally, we have 2 debug nodes, in dark green, to debug respectively the read email and the output of the gcp write node. The nodes in pink, instead, are used to display the attachments. Note that also these ones are additional nodes. They are part of the *node-red-contrib-image-tools *package and they work only with images. If you try to display a video an error message will be displayed as in the picture above.

## The final touch

Oh great now we are ready to go! Nah, don’t run so fast there is still the most important piece of the puzzle to set up. The flow as it is now will not work, we miss something. If we check the properties of the gcp write node we see that we have a property called credentials, yes credentials that’s what we miss! Of course to allow Node-RED to access our GCP project and write the media taken by the camera traps we need to give the correct permissions to it. 

The best way to do so is to create a service account, give it permission to write to Cloud Storage, and then generate a JSON key to authenticate the service account in Node-RED. Here are the steps to do so:

![1. Create a service account](https://cdn-images-1.medium.com/max/2000/1*KJOQWfXIpRHo-1Exxs3RtQ.png)

![2. Grant Editor permissions](https://cdn-images-1.medium.com/max/2052/1*aiWOwWfIoNh8-Igq04zCNw.png)

![3. Create a new private  JSON key](https://cdn-images-1.medium.com/max/2494/1*rp0GkO8bWT3ZwkfFSWPcRw.png)

![4. Add Google Cloud credentials to Node-RED](https://cdn-images-1.medium.com/max/5176/1*Sn6jtng5Jb2MDKqhkY0qFw.png)

That’s it, now you are really ready to go! 

Another cool feature of Node-RED is that you can share flows in JSON format. This means that by importing [this](https://github.com/artefactory/smartparks/blob/main/node%20red%20flows/write_to_gcp.json) JSON file you can recreate and test the just described flow. 

![How to import Node-RED nodes](https://cdn-images-1.medium.com/max/7096/1*5T8EU3GpooTyRSWbHQED1g.png)

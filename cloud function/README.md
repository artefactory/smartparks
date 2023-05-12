
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

Overall, the structure of a Python Cloud Function is quite simple. You just need a `main.py` file that contains the function you want to run (the Entry point), and optionally a `requirements.txt` file if you have any dependencies.

As our code is not so trivial we decided to structure it a bit more by adding a `utils.py` file where we defined all the useful functions used by the main script and a `config.py` to store all the project global variables.

![Our Cloud Function code structure](https://cdn-images-1.medium.com/max/2042/1*9krwLbwcODomQ7A_6hue8Q.png)

You can find the complete code here in this folder

# speedtest-docker
Docker Container for automated internet speedtests via speedtest.net API

My ISP sent out a mail claiming it had the best internet on the world. I do not believe them, this short script should help prove them wrong.

Check out 'config.yaml' for configurations (timeout, test intervals, ...)

## Docker
To build the image run: 
`docker build -t speedtest .`

To start it run:
`docker run -d speedtest`

You might want to create a local directory */data* and mount bind this to the container to get the measurements.

## Manual Install
Install dependencies:
`pip install speedtest-cli`
`pip install pyyaml`
To start it run:
`python main.py`


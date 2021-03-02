#!/usr/bin/env python

import os
import speedtest
import signal
import time
from datetime import datetime, timezone, timedelta
import yaml
import csv

config_file = os.path.dirname(os.path.realpath(__file__)) + "/config.yaml"


def read_config():
    global config_file
    config = yaml.load(open(config_file,"r"), Loader=yaml.SafeLoader)
    # add notes key
    config["output-keys"].append("notes")
    return config

def print_config(config):
    print(f"### Running automatic Internet Speedtest Measurements. \n" + \
          f"### Using speedtest.net as provider \n" +
          f"##    Interval: {config['interval']}s \n" +
          f"##    Timeout: {config['timeout']}s \n" +
          f"##    Output: {config['output']} \n")

# Main function for measuring speedtest
def perform_speedtest(threads=None, servers=[]):
    s = speedtest.Speedtest ()
    s.get_servers(servers)
    s.get_best_server()
    s.download(threads=threads)
    s.upload(threads=threads)
    s.results.share()

    return s.results.dict()

# convert timestamp to readable local time
def convert_timestamp(timestamp):
    timestamp = timestamp[:timestamp.index(".")]
    timestamp = timestamp.replace("T"," ")
    d = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    d=d.replace(tzinfo=timezone.utc) #Convert it to an aware datetime object in UTC time.
    d=d.astimezone() #Convert it to your local timezone (still aware)
    return str(d.strftime("%Y-%m-%d %H:%M:%S"))

# Parse results to csv compatible format
def parse_to_csv(results, keys):
    output = []
    for key in keys:
        if key=="notes":
            continue
        if not isinstance(key, str):
            output.append(results[key[0]][key[1]])
        else:
            value = results[key]
            if key == "timestamp":
                value = convert_timestamp(value)
            elif key in ("upload", "download"):
                value = "%0.2f" % (float(value) / 1000.0 / 1000.0)
            output.append(value)
    return output

# Check if header in file agrees, else append new header
def setup_file(file_path, output_keys):
    units = {"upload":"Mbit/s", "download":"Mbit/s","ping":"s"}
    header = [key if isinstance(key, str) else "_".join(key) for key in output_keys]

    # add units to header
    header = [f"{key} [{units[key]}]" if key in units.keys() else key for key in header]
    write_header = False
    if os.path.exists(file_path):
        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            try:
                first_line = next(reader)
            except StopIteration:
                write_header = True
    else:
        write_header = True
    if write_header:
        with open(file_path, "a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

# Write line
def write_line(file_path, line):
    with open(file_path, "a") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(line)

# Write timeout line
def write_timeout(file_path, output_keys, exception_string):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = ["n/a"] * len(output_keys)
    line[output_keys.index("timestamp")] = timestamp
    # Add exception string to notes output
    line[-1] = exception_string
    write_line(file_path, line)

# Timeout handler
def handler(signum, frame):
    raise TimeoutError("Speedtest timeout!")

def main(config):
    # Stats
    start = time.time()
    measurements = 0

    # Register signal function handler
    signal.signal(signal.SIGALRM, handler)

    # Setup file
    setup_file(config["output"], config["output-keys"])

    download_idx = config["output-keys"].index("download")
    upload_idx = config["output-keys"].index("upload")

    print(f"Current: down={0} up={0} ping={-1} ## Runtime={timedelta(seconds=int(time.time()-start))} Measurements={measurements}", end="\r")
    # Main loop
    while (True):
        # Start timeout
        signal.alarm(config["timeout"])
        measurements += 1

        try:
            results = perform_speedtest()
            # Reset timeout
            signal.alarm(0)
            # Parse output
            line = parse_to_csv(results, config["output-keys"])
            # Write to file
            write_line(config["output"], line)

            print(f"Current: down={line[download_idx]}Mbit/s up={line[upload_idx]}Mbit/s ping={results['ping']}s ## Runtime={timedelta(seconds=int(time.time()-start))} Measurements={measurements}", end="\r")

        except (TimeoutError, speedtest.SpeedtestException) as e:
            write_timeout(config["output"], config["output-keys"], str(e))
            # Reset timeout
            signal.alarm(0)

        # Sleep
        time.sleep(config["interval"])


if __name__ == "__main__":
    config = read_config()
    print_config(config)
    main(config)

FROM python:3
COPY main.py .
COPY config.yaml .

RUN pip install speedtest-cli
RUN pip install pyyaml

CMD [ "python", "-u", "main.py" ]

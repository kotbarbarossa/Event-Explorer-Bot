FROM python:3.10-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt --no-cache-dir
COPY event_explorer_bot/ /app
WORKDIR /app
CMD ["python3", "main.py"]
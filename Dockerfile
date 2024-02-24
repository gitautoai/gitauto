# Use Lambda base image
FROM python:3.10-bullseye

# RUN yum install -y git

ENV PYTHONUNBUFFERED 1 
EXPOSE 8000
WORKDIR /app 
# Copy requirements from host, to docker container in /app 
COPY . .

RUN pip install -r requirements.txt 
# Run the application in the port 8000
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "main:app"]

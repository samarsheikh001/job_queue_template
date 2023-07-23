# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# # Create a non-root user and switch to it
# RUN adduser --disabled-password --gecos '' myuser
# USER myuserwh

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /home/myuser
COPY . .

# Install any needed packages specified in requirements.txt

# Install Gunicorn
RUN pip install -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the WSGI server when the container launches
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8000"]
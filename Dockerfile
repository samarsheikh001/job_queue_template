# Use an official Python runtime as a parent image
FROM python:3.7-slim-buster

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' myuser
USER myuser

# Set the working directory in the container to the non-root user home directory
WORKDIR /home/myuser

# Copy the current directory contents into the container at /home/myuser
COPY ./flask-app /home/myuser

# Install any needed packages specified in requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install gunicorn

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the WSGI server when the container launches
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8000"]
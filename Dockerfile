# Use the official Python image as the base image
FROM python:3.9.12

# Set the working directory
WORKDIR /src

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that your Flask app listens on
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
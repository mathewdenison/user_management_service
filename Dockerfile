# Use a Python base image
FROM python:3.8

# Create a working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project code into /app
COPY . /app

# Copy the entrypoint script into the container
COPY entrypoint.sh /app/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint to our script
ENTRYPOINT ["/app/entrypoint.sh"]

# The command to run the Django app after migrations
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.10-slim

# Create a non-root user (Hugging Face Spaces requires this for security)
RUN useradd -m -u 1000 user

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY ai_attendance_system/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY ai_attendance_system/ /app/

# Give ownership of the app directory to the user
RUN chown -R user:user /app

# Switch to the non-root user
USER user

# Set home environment variables so DeepFace can download weights
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Hugging Face Spaces routes web traffic to port 7860 by default
EXPOSE 7860

# Run the gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "run:app"]

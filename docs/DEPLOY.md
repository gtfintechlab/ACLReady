# ACLReady Deployment Guide

This guide provides step-by-step instructions to deploy the ACLReady application using Docker.

## Prerequisites

Ensure you have the following installed on your system:

- Docker

## Deployment Steps

1. **Clone the Repository**

    First, clone the repository and navigate to the project directory:

    ```bash
    git clone git@github.com:gtfintechlab/ACL_SystemDemonstrationChecklist.git
    cd ACL_SystemDemonstrationChecklist
    ```

2. **Create `.env` File**

    Add your LLM inference provider API keys to a `.env` file inside the `server` directory.

    ```ini
    TOGETHERAI_API_KEY=your_together_ai_key_here
    OPENAI_API_KEY=your_openai_key_here
    ```

3. **Create Dockerfile**

    Create a file named `Dockerfile` in the root of the project directory and add the following content:

    ```Dockerfile
    # Use an official Python runtime as a parent image
    FROM python:3.11-slim

    # Set the working directory in the container
    WORKDIR /app

    # Copy the current directory contents into the container at /app
    COPY . /app

    # Install system dependencies
    RUN apt-get update && apt-get install -y \
        curl \
        && rm -rf /var/lib/apt/lists/*

    # Install Conda
    RUN curl -o ~/miniconda.sh -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
        chmod +x ~/miniconda.sh && \
        ~/miniconda.sh -b -p ~/miniconda && \
        rm ~/miniconda.sh

    ENV PATH="/root/miniconda/bin:${PATH}"

    # Create conda environment and install dependencies
    COPY environment.yml .
    RUN conda env create -f environment.yml
    RUN echo "source activate aclready_env" > ~/.bashrc
    ENV PATH /root/miniconda/envs/aclready_env/bin:$PATH

    # Install npm
    RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
    RUN apt-get install -y nodejs

    # Install npm dependencies
    WORKDIR /app/aclready
    RUN npm install

    # Expose the port the app runs on
    EXPOSE 8080

    # Set the environment variable for Flask
    ENV FAST_APP=server/app.py

    # Define environment variable for API keys
    ENV TOGETHERAI_API_KEY=your_together_ai_key_here
    ENV OPENAI_API_KEY=your_openai_key_here

    # Run the Flask server and the web interface
    CMD ["bash", "-c", "cd /app/server && python main.py & cd /app/aclready && npm start"]
    ```

4. **Build the Docker Image**

    Build the Docker image using the following command:

    ```bash
    docker build -t aclready:latest .
    ```

5. **Run the Docker Container**

    Run the Docker container using the following command:

    ```bash
    docker run -p 8080:8080 aclready:latest
    ```

6. **Access the Application**

    The application will be accessible at `http://localhost:8080`.

## Dockerfile

Here is the complete Dockerfile for easy reference and copy-pasting:

```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Conda
RUN curl -o ~/miniconda.sh -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    chmod +x ~/miniconda.sh && \
    ~/miniconda.sh -b -p ~/miniconda && \
    rm ~/miniconda.sh

ENV PATH="/root/miniconda/bin:${PATH}"

# Create conda environment and install dependencies
COPY environment.yml .
RUN conda env create -f environment.yml
RUN echo "source activate aclready_env" > ~/.bashrc
ENV PATH /root/miniconda/envs/aclready_env/bin:$PATH

# Install npm
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs

# Install npm dependencies
WORKDIR /app/aclready
RUN npm install

# Expose the port the app runs on
EXPOSE 8080

# Set the environment variable for Flask
ENV FAST_APP=server/app.py

# Define environment variable for API keys
ENV TOGETHERAI_API_KEY=your_together_ai_key_here
ENV OPENAI_API_KEY=your_openai_key_here

# Run the Flask server and the web interface
CMD ["bash", "-c", "cd /app/server && python main.py & cd /app/aclready && npm start"]
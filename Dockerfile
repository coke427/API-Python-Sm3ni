# Use the official Python image as the base image
FROM python:3.8.3

# Set the working directory
WORKDIR /app

# Copy the Conda environment file
COPY requirements.yml .

# Install Conda
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    /opt/conda/bin/conda init && \
    /opt/conda/bin/conda env create -f requirements.yml && \
    /opt/conda/bin/conda clean -afy

# Install libgl1-mesa-glx
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Activate the Conda environment
ENV PATH /opt/conda/envs/venv/bin:$PATH
RUN echo "source activate venv" > ~/.bashrc

# Copy the application code
COPY . .

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the necessary port
EXPOSE 8080

# Command to run your application
CMD ["python", "app.py"]

FROM vastai/pytorch:2.1.2-cuda-12.1-py3.12

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y \
    git-lfs \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

WORKDIR /workspace

# Install Python dependencies (cache-friendly layer ordering)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

CMD ["bash"]

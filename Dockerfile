FROM nvcr.io/nvidia/pytorch:26.02-py3

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System tools
RUN apt-get update && apt-get install -y \
    git-lfs \
    sqlite3 \
    rclone \
    tmux \
    htop \
    nvtop \
    jq \
    ripgrep \
    rsync \
    curl \
    wget \
    openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Node.js + Claude Code + GitHub CLI
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code \
    && (curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg) \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Common ML Python packages (shared across projects)
RUN pip install --no-cache-dir \
    numpy \
    scipy \
    pandas \
    scikit-learn \
    transformers \
    accelerate \
    tokenizers \
    sentencepiece \
    datasets \
    evaluate \
    peft \
    safetensors \
    einops \
    wandb \
    bitsandbytes \
    nltk \
    tqdm \
    matplotlib \
    seaborn \
    plotly \
    pytest \
    hypothesis \
    b2 \
    torchrl \
    tensordict \
    gymnasium

WORKDIR /workspace

CMD ["bash"]

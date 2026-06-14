FROM node:22-bookworm

# System packages: git, build tools for dasm, Python.
# (The document weaves to HTML via weave_html.py; the LaTeX/texlive
# pipeline has been retired, so no TeX packages are needed.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    unzip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies: absl-py for weave.py, Pillow for graphics renderers,
# mistune for the HTML weaver (weave_html.py) Markdown rendering
RUN pip3 install --break-system-packages absl-py Pillow mistune

# Build dasm from source
RUN git clone https://github.com/dasm-assembler/dasm.git /tmp/dasm \
    && cd /tmp/dasm \
    && make \
    && cp /tmp/dasm/bin/dasm /usr/local/bin/dasm \
    && rm -rf /tmp/dasm

# Install uv (Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Create non-root user for Claude Code --dangerously-skip-permissions
RUN useradd -m -s /bin/bash agent \
    && mkdir -p /home/agent/.claude \
    && chown -R agent:agent /home/agent/.claude \
    && echo 'alias yolo="claude --dangerously-skip-permissions"' >> /home/agent/.bashrc

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER agent

# Point npm's global prefix at the agent's home so claude-code can be
# upgraded at runtime (npm install -g @anthropic-ai/claude-code) without
# hitting EACCES on /usr/local/lib/node_modules.
ENV NPM_CONFIG_PREFIX=/home/agent/.npm-global
ENV PATH=/home/agent/.npm-global/bin:$PATH

# Install Claude Code CLI. ADD of the npm registry's "latest" metadata
# invalidates this layer whenever a new version of claude-code is published,
# so the install below always picks up the newest release.
ADD https://registry.npmjs.org/@anthropic-ai/claude-code/latest /tmp/claude-code-latest.json
RUN mkdir -p "$NPM_CONFIG_PREFIX" \
    && npm install -g @anthropic-ai/claude-code

# Trust the bind-mounted project repo so git works inside the container
# (host/container UID mismatch trips git's dubious-ownership check).
RUN git config --global --add safe.directory /project/repo

WORKDIR /project/repo

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["bash"]

FROM public.ecr.aws/docker/library/debian:bookworm-slim

LABEL org.opencontainers.image.title="JNCIE-SP AUTO1" \
      org.opencontainers.image.description="Resource-conscious Junos automation workstation"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl git iputils-ping openssh-client python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
COPY requirements.txt verify_stack.py /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && python /tmp/verify_stack.py \
    && useradd --create-home --uid 1000 automation \
    && mkdir -p /workspace/jncie-sp-master \
    && chown -R automation:automation /workspace

WORKDIR /workspace/jncie-sp-master
USER automation
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD python /tmp/verify_stack.py || exit 1
CMD ["sleep", "infinity"]

FROM python:3.11-alpine

LABEL org.opencontainers.image.title="Decentralised Discovery Gateway"
LABEL org.opencontainers.image.description="Decentralised Discovery Gateway for proxying requests in a decentralised network in a discovery context."
LABEL org.opencontainers.image.authors="wangyunze16@gmail.com"
LABEL org.opencontainers.image.url="https://github.com/Firefox2100/dedi-gateway"
LABEL org.opencontainers.image.documentation="https://decentralised-discovery-gateway.readthedocs.io/en/latest/"
LABEL org.opencontainers.image.source="https://github.com/Firefox2100/dedi-gateway"
LABEL org.opencontainers.image.vendor="uk.co.firefox2100"
LABEL org.opencontainers.image.licenses="MIT"

RUN apk --no-cache add curl bash gcc musl-dev linux-headers
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

ENV PYTHONUNBUFFERED=1
ENV DG_APPLICATION_NAME=dedi-gateway
ENV DG_ACCESS_URL=http://localhost:5321
ENV DG_SERVICE_NAME="Example Service"
ENV DG_SERVICE_DESCRIPTION="This is an example service for the Decentralised Discovery Gateway."
ENV DG_LOGGING_LEVEL=INFO
ENV DG_EMA_FACTOR=0.3
ENV DG_CHALLENGE_DIFFICULTY=22
ENV DG_DATABASE_DRIVER=mongo
ENV DG_MONGODB_HOST=mongodb
ENV DG_MONGODB_PORT=27017
ENV DG_MONGODB_DB_NAME=dedi-gateway
ENV DG_CACHE_DRIVER=redis
ENV DG_REDIS_HOST=redis
ENV DG_REDIS_PORT=6379
ENV DG_KMS_DRIVER=vault
ENV DG_VAULT_URL=http://vault:8200
ENV DG_VAULT_KV_ENGINE=kv
ENV DG_VAULT_KV_PATH=dedi-gateway
ENV DG_VAULT_TRANSIT_ENGINE=transit

WORKDIR /app
COPY ./src/dedi_gateway /app/src/dedi_gateway
COPY ./pyproject.toml /app/pyproject.toml
COPY ./conf/example.env /app/conf/.env
COPY ./LICENSE* /app/
COPY ./README.md /app/README.md

RUN pip install .[hypercorn,redis,mongo,hvac]
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5321

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:5321/health || exit 1

ENTRYPOINT ["python", "-m", "hypercorn"]
CMD ["--bind", "0.0.0.0:5321", "dedi_gateway.asgi:application"]

#!/bin/zsh

docker buildx build \
  --builder=timshee_builder \
  --platform linux/amd64,linux/arm64 \
  -t pavelbeard/cita_catcher:latest \
  -f Dockerfile . \
  --push;

# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=3.11
ARG VARIANT=

# build stage
FROM python:${PYTHON_IMAGE}${VARIANT} AS build-stage

RUN pip install pipx

COPY . /project/

WORKDIR /project

RUN mkdir __pypackages__ && \
  python -m pipx run --no-cache pdm sync --prod --no-editable

# run stage
FROM python:${PYTHON_IMAGE}${VARIANT}

ARG PYTHON_IMAGE

ENV PYTHONPATH=/opt/nb-cli/pkgs

COPY --from=build-stage /project/__pypackages__/${PYTHON_IMAGE}/lib /opt/nb-cli/pkgs
COPY --from=build-stage /project/__pypackages__/${PYTHON_IMAGE}/bin/* /bin/

WORKDIR /workspaces

ENTRYPOINT ["nb"]

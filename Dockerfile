# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM python:3.12 as build-image
ARG FUNCTION_DIR

COPY requirements.txt ${FUNCTION_DIR}/

# Install the function's dependencies
RUN python -m venv ${FUNCTION_DIR}/venv \
 && ${FUNCTION_DIR}/venv/bin/pip --no-cache-dir install -U setuptools pip \
 && ${FUNCTION_DIR}/venv/bin/pip --no-cache-dir install awslambdaric \
 && ${FUNCTION_DIR}/venv/bin/pip --no-cache-dir install -r ${FUNCTION_DIR}/requirements.txt

COPY . ${FUNCTION_DIR}/mosbot
RUN ${FUNCTION_DIR}/venv/bin/pip --no-cache-dir install ${FUNCTION_DIR}/mosbot

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.12-slim
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ENTRYPOINT [ "venv/bin/python", "-m", "awslambdaric" ]
CMD [ "mosbot.bin.scrape_player.handler" ]

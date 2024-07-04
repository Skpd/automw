FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY . ${LAMBDA_TASK_ROOT}/mosbot
RUN pip install ${LAMBDA_TASK_ROOT}/mosbot

CMD [ "mosbot.bin.scrape_player.handler" ]
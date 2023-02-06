FROM python:3-alpine
COPY . /app
WORKDIR /app
RUN apk add redis libgcc gcompat && \
	pip install -r requirements.txt
CMD redis-server --loadmodule ./librejson.so & ./app.py

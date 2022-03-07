FROM python:3.10-bullseye
COPY . /app
WORKDIR /app
RUN pip install -U pip
RUN pip install -r requirements.txt
RUN chmod 755 ./engine
CMD ["python", "bot/main.py"]

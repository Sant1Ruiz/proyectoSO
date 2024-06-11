# imagen base
FROM python:3
WORKDIR /usr/src/app
COPY ./src/ .
COPY ./sync_files/ sync_files/
RUN pip3 install -r requirements.txt
EXPOSE 80
CMD ["python3", "app.py"]
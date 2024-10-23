FROM python:3.12

COPY requirements.txt .

RUN pip install -r requirements.txt

ADD weather.py .

EXPOSE 5000

COPY . .

CMD python ./weather.py
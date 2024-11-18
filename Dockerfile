FROM python:3.9

RUN apt-get update && apt-get install -y nginx sqlite3 fonts-dejavu-core 
RUN echo "deb http://deb.debian.org/debian bookworm contrib non-free" > /etc/apt/sources.list.d/contrib.list
RUN apt update && apt install -y ttf-mscorefonts-installer
 

COPY html /usr/share/nginx
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 80 8000

CMD ["/bin/bash", "-c", "nginx && python weather_station.py"]


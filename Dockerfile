FROM python:3.9

RUN echo "deb http://deb.debian.org/debian bookworm contrib non-free" > /etc/apt/sources.list.d/contrib.list
RUN apt update && apt install -y ttf-mscorefonts-installer
RUN apt install -y nginx sqlite3 fonts-dejavu-core 

COPY nginx.conf /etc/nginx/sites-available/default
COPY html /usr/share/nginx/html
COPY romeo.png /home/pi/weather/weather.png 
COPY romeo.png /usr/share/nginx/weather.png 
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 80

#CMD ["/bin/bash", "-c", "nginx && python weather_station.py"]
#CMD ["/bin/bash", "-c", "lsof -i :80; while (true); do echo 'sleeping'; sleep 100; done"]
CMD ["nginx", "-g", "daemon off;"]

FROM nginx:latest
RUN apt-get update && apt-get install -y procps

# Apache2-utils are needed for the http password
RUN apt-get install --no-install-recommends -y apache2-utils
RUN mkdir -p /home/app/staticfiles

# For creating the user and password
RUN mkdir -p /etc/pwd
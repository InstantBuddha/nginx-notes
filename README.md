# nginx-notes

- [nginx-notes](#nginx-notes)
  - [The basics](#the-basics)
  - [My Nginx security rules notes](#my-nginx-security-rules-notes)
  - [My Nginx mastery course notes](#my-nginx-mastery-course-notes)
  - [Reload nginx](#reload-nginx)
  - [Curl to check nginx](#curl-to-check-nginx)
  - [Trailing slash !important](#trailing-slash-important)
  - [Changing nginx.conf](#changing-nginxconf)
  - [Nginx Caching](#nginx-caching)
    - [Proxy caching](#proxy-caching)
    - [Client side browser caching](#client-side-browser-caching)
    - [Browser caching](#browser-caching)


## The basics

Basic rules and definitions can be found [in this file](basics.md)

## My Nginx security rules notes

Far from perfect. My solutions can be found [in this file](Nginx-security-notes.md)

## My Nginx mastery course notes

My notes can be found [here](Nginx-mastery-notes.md)

## Reload nginx

Although docker compose down and up swwm to work better to restart nginx and load the new config file, but this can be used too:

```sh
docker exec nginx-practice nginx -s reload
```

## Curl to check nginx

```bash
curl -I localhost:80/
```
## Trailing slash !important

Based on [this comment](https://stackoverflow.com/questions/10631933/nginx-static-file-serving-confusion-with-root-alias)

There is no definitive guideline about whether a trailing slash is mandatory per Nginx documentation, but a common observation by people here and elsewhere seems to indicate that it is.

## Changing nginx.conf

It might be edited. This caused the duplicate mime.types earlier. 

It needs to be edited to enable proxy caching.

In the docker-compose.yml I added the following:
```yml
# Nginx Service
  webserver:
    image: nginx:1.26.0-alpine
    container_name: webserver
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      #- ./:/var/www
      #- ./public:/var/www/public #this is probably for Laravel's frontend
      - ./filozofiahu:/filozofiahu:ro #make it read only for added security
      - ./nginx-config/conf.d:/etc/nginx/conf.d/:ro #directory of default.conf
      - ./nginx-config/nginx.conf:/etc/nginx/nginx.conf:ro  # Bind only nginx.conf FILE!
      - ./certbot/www:/var/www/certbot/:ro
      - ./certbot/conf/:/etc/nginx/ssl/:ro
      - nginx-cache:/var/lib/nginx/cache  # Mount volume for cache
    networks:
      - filo-app-network
    # other things
volumes:
    db-data:
    nginx-cache:
```

For this setup inside the nginx
The folder structure for this is:

nginx-config
├── conf.d
│   └── default.conf
└── nginx.conf

For this I copied the original nginx.conf from the container.

## Nginx Caching

See previous point for yml setup and folder structure.

### Proxy caching
Inside nginx.conf
```conf
http {
    # Proxy cache path configuration at the http level
    proxy_cache_path /var/lib/nginx/cache levels=1 keys_zone=frontend_cache:120m max_size=1024m;

}
```

Inside default.conf
```conf
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    # ...
    # for proxy caching it would work:
        #proxy_cache frontend_cache;
}
```

### Client side browser caching
Might be unnecessary

in default.conf
```conf
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
# ...
    location / {
        root /filozofiahu/build;
        try_files $uri /index.html;        
    }
 
    location ~* \.(jpg|JPG|jpeg|png|gif)$ {
        root /filozofiahu/build;
        expires 1M;  # Cache images for 1 month (adjust as needed)
        access_log off;  # Optional: Enable access logging if desired
        add_header Cache-Control "public, max-age=2629746";  # Cache for 1 month
    }

    location ~* \.(?:css|js)$ {
        root /filozofiahu/build;
        expires 1M;
        access_log off;
        add_header Cache-Control "public, max-age=2629746";
    }
}
```

### Browser caching

Might not be needed

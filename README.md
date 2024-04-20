# nginx-notes

Based on [this video](https://www.youtube.com/watch?app=desktop&v=9t9Mp0BGnyI)

## Reload nginx

Although docker compose down and up swwm to work better to restart nginx and load the new config file, but this can be used too:

```sh
docker exec nginx-practice nginx -s reload
```

## Terminology

Directives: like key-walue pairs

Contexts: like blocks of code with key value pairs inside

## Trailing slash !important

Based on [this comment](https://stackoverflow.com/questions/10631933/nginx-static-file-serving-confusion-with-root-alias)

There is no definitive guideline about whether a trailing slash is mandatory per Nginx documentation, but a common observation by people here and elsewhere seems to indicate that it is.

## Most basic example

In the tutorial they included:

```conf
http {
    server {
        listen 8080;
        root /home/dan/NEW_PROGRAMMING/nginx-notes/html-files/;
    }
}

events {}
```

Because of restrictions, I needed to change it to:

```conf
server {
    listen 80;
    root /html-files/;
}
```

## Mime types

The tutorial goes on:

Instead of adding all the types separately like this:

```conf
http {
    types {
        text/css    css;
        text/html   html;
    }

    server {
        listen 8080;
        root /Users/Dan/Desktop/mysite;
    }
}

events {}
```

We can just add:

```conf
http {

    include mime.types;

    server {
        listen 8080;
        root /Users/Dan/Desktop/mysite/;
    }
}

events {}
```

I needed to add it like this:

```conf
include mime.types;

server {
    listen 80;
    root /html-files/;
}
```

## The location block or location context

for the /fruits we can add a location
First, we add a fruits subdirectory and there an index.html

```conf
include mime.types;

server {
    listen 80;
    server_name example.com;    # necessary to avoid a warning
    root /html-files/;

    location /fruits/ {
        root /html-files/;# surprisingly we don't need to add /fruits/ to the end as it adds it automatically, it's enough to add the same root as earlier
    }

    #it is possible to add the same index.html (inside the fruits folder) for a different url /carbs/
    location /carbs/ {
        alias /html-files/fruits/;
    }

    # Handling favicon.ico request to prevent errors
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
}
```

## try_files

Explanation in the comment:

```conf
include mime.types;

server {
    listen 80;
    server_name example.com;    # necessary to avoid a warning
    root /html-files/;

    location /fruits/ {
        root /html-files/;# surprisingly we don't need to add /fruits/ to the end as it adds it automatically, it's enough to add the same root as earlier
    }

    #it is possible to add the same index.html (inside the fruits folder) for a different url /carbs/
    location /carbs/ {
        alias /html-files/fruits/;
    }

    location /vegetables/ {
        root /html-files/;
        #if there is no index.html, we can use try_files
        # Here first it will try /vegetables/veggies.html than /index.html (in root) and in the end 404
        try_files /vegetables/veggies.html /index.html =404;
    }

    # Handling favicon.ico request to prevent errors
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
}
```

## Regular expressions

```conf
# Using regular expressions
    # ~* means it is going to be a regular expression
    # so this url: http://localhost/count/2/ will take us to /index.html

    location ~* /count/[0-9]{
        root /html-files/;
        try_files /index.html =404;
    }
```

**Explanation:**

**`location ~* /count/[0-9]`**:
  - The `location` directive is used to specify how nginx should respond to requests based on the URL pattern.
  - `~*` indicates that the following pattern is a case-insensitive regular expression. If you use just `~`, it denotes a case-sensitive match. 
  - `/count/[0-9]` is a regular expression pattern that matches URLs starting with `/count/` followed by a single digit (0-9).


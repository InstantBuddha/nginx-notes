# Nginx basics

Based on [this video](https://www.youtube.com/watch?app=desktop&v=9t9Mp0BGnyI)

- [Nginx basics](#nginx-basics)
  - [Terminology](#terminology)
  - [Most basic example](#most-basic-example)
  - [Mime types](#mime-types)
  - [The location block or location context](#the-location-block-or-location-context)
  - [Aliases](#aliases)
  - [try\_files](#try_files)
  - [Regular expressions](#regular-expressions)
  - [Redirects](#redirects)
  - [Rewrites](#rewrites)
  - [Load balancing](#load-balancing)


## Terminology

Directives: like key-walue pairs

Contexts: like blocks of code with key value pairs inside

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
## Aliases

The `alias` directive in nginx is used to map a location to a different directory on the server's file system. It is commonly used to serve static files from a different root directory while preserving the original URL path.

**Example:**
```conf
location /static {
    alias /var/www/static-files/;
}
```

In this example, requests to `/static/` are served from `/var/www/static-files/`, with the URL path preserved.

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

## Redirects

Simple redirection from one url to an other.

```conf
# Redirection

    location /crops/ {
        # 307 is http code for redirecting the user, after that we add where to go
        return 307 /fruits/;
    }
```    

There are two ways of doing it: 307 and 301:
- 301 Moved Permanently: Indicates that the requested resource has permanently moved to a new location.
- 307 Temporary Redirect: indicates that the requested resource has temporarily moved to a new location.
  
**Key Differences:**

- **Caching**: `301` is cached by browsers (permanent), while `307` is not cached (temporary).
- **Client Behavior**: Browsers and clients treat `301` as a permanent redirect and `307` as a temporary redirect.
- **SEO Impact**: `301` affects search engine indexing more significantly than `307`.
- **Future Requests**: `301` redirects future requests to the new location automatically without contacting the server again, whereas `307` requires the client to check with the server for each subsequent request.


## Rewrites

Similar to redirects as it shows the html of something else, but the url stays as the user wrote it in.

**Rewrites (`rewrite` Directive):**

The `rewrite` directive in nginx is used to internally rewrite or modify the URL before processing the request. **It changes the URL internally within nginx without informing the client's browser.** The syntax for `rewrite` is as follows:

```conf
rewrite regex replacement [flag];
```

- **`regex`**: Regular expression pattern to match part of the request URL.
- **`replacement`**: Replacement string or URL to which the request should be rewritten.
- **`flag`** (optional): Modifiers like `last`, `break`, `redirect`, etc., to control the behavior of the rewrite.

**Example:**
```nginx
server {
    location /old {
        rewrite ^/old/(.*)$ /new/$1 last;
    }
}
```

In this example, requests to `/old/` are internally rewritten to `/new/` using a regular expression pattern (`^/old/(.*)$`) to capture and reuse part of the URL (`$1`).

**Using `rewrite` with `redirect` Flag**:
  ```nginx
  location /redirect-me {
      rewrite ^/redirect-me$ https://example.com/new-url redirect;
  }
  ```
**The tutorial example explained:**

Let's break down the `rewrite` directive you provided from the `default.conf` file:

```nginx
rewrite ^/number/(\w+) /count/$1;
```

- **`rewrite`**: The `rewrite` directive in nginx is used to modify or transform the requested URL before processing the request further.

- **`^/number/(\w+)`**:
  - `^/number/`: This part is a regular expression pattern that matches URLs starting with `/number/`.
  - `(\w+)`: This is a capturing group (`\w+`) that matches one or more word characters (letters, digits, or underscores). The parentheses `()` capture this part of the URL for reuse.

- **`/count/$1`**:
  - `/count/`: This is the replacement string for the matched part of the URL.
  - `$1`: This refers to the first captured group (`(\w+)`) from the regex pattern. It is used to insert the value captured by `(\w+)` into the replacement string.

**Breakdown:
**
- **Regex Pattern (`^/number/(\w+)`)**:
  - `^`: Anchors the regex pattern to the start of the URL.
  - `/number/`: Matches the literal string `/number/`.
  - `(\w+)`: Captures one or more word characters (letters, digits, or underscores).

- **Replacement String (`/count/$1`)**:
  - `/count/`: Specifies the replacement string where the URL will be rewritten.
  - `$1`: Inserts the value captured by `(\w+)` from the original URL into the replacement string.

**Example:**

- **Original URL**: `http://example.com/number/123`
- **After Rewrite**: `http://example.com/count/123`

## Load balancing

For several servers.

The beginning of my modified default.conf

```conf
include mime.types;

# for backend:

    upstream backendserver {
        server 127.0.0.1:1111;
        server 127.0.0.1:2222;
    }

server {
    listen 80;
    server_name localhost;    # necessary to avoid a warning
    root /html-files/;

    # for backend:
    location / {
        proxy_pass http://backendserver/;
    }
    # ...
}
```    
** Explanation:**

1. **`upstream backendserver { ... }`**:
   - The `upstream` directive defines a group of backend servers (`backendserver`) that nginx will load balance requests across.
   - In this example, `backendserver` is configured with two backend servers:
     - `server 127.0.0.1:1111;`: Specifies the first backend server listening on `127.0.0.1` (localhost) on port `1111`.
     - `server 127.0.0.1:2222;`: Specifies the second backend server listening on `127.0.0.1` (localhost) on port `2222`.
   - Requests will be distributed between these backend servers based on the load balancing method configured (e.g., round-robin by default).

2. **`server { ... }`**: unimportant

3. **`location / { ... }`**:
   - The `location / { ... }` block specifies how nginx handles requests that match the `/` location (all requests not matched by other `location` blocks).
   - **`proxy_pass http://backendserver/;`**:
     - The `proxy_pass` directive is used to forward requests to the specified upstream group (`backendserver` in this case).
     - When a request matches the `/` location, nginx will proxy (or forward) the request to one of the servers defined in the `backendserver` group.
     - Requests will be load balanced between the servers (`127.0.0.1:1111` and `127.0.0.1:2222`) based on the load balancing method configured in the `upstream` block (`backendserver`).

**Summary:**

- **`upstream` Directive**:
  - Defines a group of backend servers (`backendserver`) for load balancing.
  - Specifies the list of servers (`server <address>:<port>;`) within the group.

- **`proxy_pass` Directive**:
  - Forwards requests to an upstream group (`http://backendserver/`).
  - Proxies requests to one of the servers defined in the `backendserver` group for load balancing.

With this configuration, nginx will act as a reverse proxy and load balancer, distributing incoming requests across multiple backend servers (`127.0.0.1:1111` and `127.0.0.1:2222`). This setup improves scalability, reliability, and performance by distributing the request load across multiple servers.


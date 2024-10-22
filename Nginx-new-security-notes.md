# Nginx new security notes

- [Nginx new security notes](#nginx-new-security-notes)
  - [server\_tokens and proxy\_hide\_header](#server_tokens-and-proxy_hide_header)


## server_tokens and proxy_hide_header

The proxy_hide_header directive is typically used to hide or remove certain headers from the response that comes from the upstream server (like Django or another application) before Nginx passes the response to the client.

In nginx.conf (global settings): If you want the proxy_hide_header directive to apply globally across all virtual hosts, you would place it inside nginx.conf. Typically, nginx.conf contains global settings, so it makes sense to include security-related directives there if they should apply to every site/server managed by Nginx.

So, in nginx.conf we can add:
```conf
proxy_hide_header X-Powered-By; # Mainly to hide backend server information
add_header X-Frame-Options SAMEORIGIN; #Needed to add along the previous oprion

```

The added measures can be tested with the command:

```bash
curl -I http://localhost
```

The output before and after implementing proxy_hide_header:
```bash
$ curl -I http://localhost
HTTP/1.1 200 OK
Server: nginx
Date: Fri, 18 Oct 2024 08:02:53 GMT
Content-Type: text/html
Content-Length: 921
Last-Modified: Wed, 16 Oct 2024 09:13:22 GMT
Connection: keep-alive
ETag: "670f83b2-399"
Accept-Ranges: bytes

$ curl -I http://localhost
HTTP/1.1 404 Not Found
Server: nginx
Date: Fri, 18 Oct 2024 08:08:08 GMT
Content-Type: text/html
Content-Length: 146
Connection: keep-alive
```

## Other security header options

If you don’t enable the `proxy_hide_header` option in Nginx, your system may expose sensitive or unnecessary information to clients, which can increase the risk of attacks. Here are some scenarios where leaving headers exposed might lead to security vulnerabilities:

### 1. **Information Disclosure (Server Header)**
- **Risk**: By default, Nginx sends the `Server` header in HTTP responses, which includes the web server version (e.g., `Server: nginx/1.20.1`). Attackers can use this information to target known vulnerabilities in specific versions of Nginx or any upstream servers you are proxying requests to.
  
  **Exploit Scenario**: An attacker can scan for outdated server versions using tools like `nmap` and look for exploits corresponding to that version, leading to remote code execution, denial of service, or other attacks.

- **Solution**: Hide the `Server` header:
  ```nginx
  server_tokens off;
  proxy_hide_header Server;
  ```

### 2. **Leaking Backend Technology (X-Powered-By Header)**
- **Risk**: Some backend frameworks or technologies add an `X-Powered-By` header to the HTTP response, such as `X-Powered-By: Django` or `X-Powered-By: PHP/7.4.0`. This reveals what language or framework your application is running on.

  **Exploit Scenario**: An attacker who knows you're using a specific backend (e.g., an outdated version of Django or PHP) can try to exploit well-known vulnerabilities in those frameworks, such as SQL injection, code execution, or file upload vulnerabilities.

- **Solution**: Hide the `X-Powered-By` header:
  ```nginx
  proxy_hide_header X-Powered-By;
  ```

### 3. **Upstream Load Balancer or Application Information (Via Header)**
- **Risk**: The `Via` header can reveal information about your proxy setup. For example, it can expose details about the upstream load balancer or intermediary proxies between Nginx and the application server, which can help attackers understand your architecture and find weak points.

  **Exploit Scenario**: Attackers can map out your infrastructure, identifying potential entry points like misconfigured load balancers or intermediate proxies, which could be vulnerable to attacks such as session hijacking or misrouting traffic.

- **Solution**: Hide the `Via` header:
  ```nginx
  proxy_hide_header Via;
  ```

### 4. **Exposing Authentication Methods (WWW-Authenticate Header)**
- **Risk**: The `WWW-Authenticate` header is used when authentication is required. In some cases, it may reveal the authentication method (e.g., Basic or Digest authentication) that you are using.

  **Exploit Scenario**: If you're using Basic Authentication without secure transport (e.g., over HTTP instead of HTTPS), an attacker can attempt brute force or dictionary attacks on your authentication mechanism.

- **Solution**: Ensure secure transport for sensitive headers, and if needed, hide or manage the `WWW-Authenticate` header:
  ```nginx
  proxy_hide_header WWW-Authenticate;
  ```

### 5. **Exposing Web Application Firewall (X-Frame-Options, X-Content-Type-Options)**
- **Risk**: Some upstream servers or proxies may pass security-related headers like `X-Frame-Options` and `X-Content-Type-Options`. If these headers are misconfigured or outdated, it can allow clickjacking or MIME-type attacks.

  **Exploit Scenario**: If `X-Frame-Options` is not set or incorrectly configured, attackers could embed your web pages in iframes (clickjacking), tricking users into performing unintended actions. Similarly, missing `X-Content-Type-Options` could lead to MIME-type attacks where an attacker tricks the browser into interpreting the content as a different type.

- **Solution**: You should correctly configure or hide these headers depending on your security policy:
  ```nginx
  proxy_hide_header X-Frame-Options;
  proxy_hide_header X-Content-Type-Options;
  ```

## Nginx OWASP/ModSecurity-crs

This is the docker-compose.yml with which I could make it run initially:
```yml
services:
  nginx-modsecurity:
    image: owasp/modsecurity-crs:4.7.0-nginx-202410090410
    ports:
      - "80:80"
    volumes:
      - ./html-files:/html-files
      #- ./nginx-config/conf.d:/etc/nginx/conf.d/ # The read only was removed :ro #directory of default.conf
      #- ./nginx-config/nginx.conf:/etc/nginx/nginx.conf #:ro The read only was removed  # Bind only nginx.conf FILE!
    command: nginx -g "daemon off;"
```
In the original package the original default.conf looked like this:

```conf
# Nginx configuration for both HTTP and SSL

server_tokens off;

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 8080 default_server;

    server_name localhost;
    set $upstream http://localhost:80;
    set $always_redirect off;

    

    location / {
        client_max_body_size 0;

        if ($always_redirect = on) {
            return 301 https://$host$request_uri;
        }

        include includes/proxy_backend.conf;

        index index.html index.htm;
        root /usr/share/nginx/html;
    }

    include includes/location_common.conf;

}

server {
    listen 8443 ssl;

    server_name localhost;
    set $upstream http://localhost:80;

    ssl_certificate /etc/nginx/conf/server.crt;
    ssl_certificate_key /etc/nginx/conf/server.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets off;

    ssl_dhparam /etc/ssl/certs/dhparam-2048.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    ssl_stapling on;
    ssl_stapling_verify on;

    ssl_verify_client off;
    ssl_verify_depth 1;

    

    location / {
        client_max_body_size 0;

        include includes/proxy_backend.conf;

        index index.html index.htm;
        root /usr/share/nginx/html;
    }

    include includes/location_common.conf;
}
```

And the original nginx.conf looked like this:

```conf
load_module modules/ngx_http_modsecurity_module.so;

worker_processes auto;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    keepalive_timeout 60s;
    sendfile on;

    resolver 127.0.0.11 valid=5s;
    include /etc/nginx/conf.d/*.conf;
}
```


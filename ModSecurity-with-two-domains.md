# ModSecurity with two domains

- [ModSecurity with two domains](#modsecurity-with-two-domains)
  - [For the persistent logs setting permissions might be necessary:](#for-the-persistent-logs-setting-permissions-might-be-necessary)
  - [Creating the ssl certificates](#creating-the-ssl-certificates)
    - [Update Your Hosts File to trick the system believing the domains are the ones served by Docker](#update-your-hosts-file-to-trick-the-system-believing-the-domains-are-the-ones-served-by-docker)

To create a dockerized instance of OWASP ModSecurity+Nginx that serves example.com and anotherdomain.com on your local computer with ssl, mimicking certbot.

## For the persistent logs setting permissions might be necessary:
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

## Creating the ssl certificates
Run the commands in their subfolders (inside certbot/conf/live/example.com for example) to create SSL keys and certificates for `example.com` and `anotherdomain.com`:

**For example.com:**
1. create the files
```bash
openssl req -x509 -out example.com.crt -keyout example.com.key \
  -newkey rsa:2048 -nodes -sha256 \
  -subj '/CN=example.com' -extensions EXT -config <( \
   printf "[dn]\nCN=example.com\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:example.com\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
```
2. rename the files
```bash
mv example.com.key privkey.pem
mv example.com.crt fullchain.pem 
```
3. Then, set the permissions right:
   
```bash
chmod 644 ./certbot/conf/live/example.com/privkey.pem
chmod -R 755 ./certbot/conf/live/example.com/
```

**For anotherdomain.com:**
1. create the files
```bash
openssl req -x509 -out anotherdomain.com.crt -keyout anotherdomain.com.key \
  -newkey rsa:2048 -nodes -sha256 \
  -subj '/CN=anotherdomain.com' -extensions EXT -config <( \
   printf "[dn]\nCN=anotherdomain.com\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:anotherdomain.com\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
```
2. rename the files
```bash
mv anotherdomain.com.key privkey.pem
mv anotherdomain.com.crt fullchain.pem 
```
3. Then, set the permissions right:
   
```bash
chmod 644 ./certbot/conf/live/anotherdomain.com/privkey.pem
chmod -R 755 ./certbot/conf/live/anotherdomain.com/
```

### Update Your Hosts File to trick the system believing the domains are the ones served by Docker
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

# nginx-notes

- [nginx-notes](#nginx-notes)
  - [The basics](#the-basics)
  - [My Nginx mastery course notes](#my-nginx-mastery-course-notes)
  - [My new Nginx security notes](#my-new-nginx-security-notes)
  - [Host Headers and Shared ip addresses](#host-headers-and-shared-ip-addresses)
  - [Host Headers and Shared ip addresses with the OWASP ModSecurity+Nginx setup](#host-headers-and-shared-ip-addresses-with-the-owasp-modsecuritynginx-setup)
  - [My Nginx old security rules notes](#my-nginx-old-security-rules-notes)
  - [Reload nginx](#reload-nginx)
  - [Curl to check nginx](#curl-to-check-nginx)
  - [Trailing slash !important](#trailing-slash-important)


## The basics

Basic rules and definitions can be found [in this file](basics.md)

## My Nginx mastery course notes

My notes can be found [here](Nginx-mastery-notes.md)

## My new Nginx security notes

My new, more organized security notes are collected [in this file](Nginx-new-security-notes.md)

## Host Headers and Shared ip addresses

[My notes on Host Headers and shared ip addresses with Nginx](Host-headers-and-shared-ip-addresses.md)

## Host Headers and Shared ip addresses with the OWASP ModSecurity+Nginx setup

[My notes on how to set up two domain names on the same ip address and forward traffic using the OWASP ModSecurity+Nginx container to do that. ](ModSecurity-with-two-domains.md) In this case the HTML files are served by the two additional Dockerized Nginx instances.

## My Nginx old security rules notes

Far from perfect. My solutions can be found [in this file](Nginx-security-notes-old.md)

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

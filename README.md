# nginx-notes

Based on [this video](https://www.youtube.com/watch?app=desktop&v=9t9Mp0BGnyI)

## Terminology

Directives: like key-walue pairs

Contexts: like blocks of code with key value pairs inside

## Most basic example

```conf
http {
    server {
        listen 8080;
        root /home/dan/NEW_PROGRAMMING/nginx-notes/html-files;
    }
}

events {}
```

## Mime types

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
        root /Users/Dan/Desktop/mysite;
    }
}

events {}
```

## The location block or location context

for the /fruits we can add a location
First, we add a fruits subdirectory and there an index.html

```conf
http {

    include mime.types;

    server {
        listen 8080;
        root /Users/Dan/Desktop/mysite;

        location /fruits {
            root /Users/Dan/Desktop/mysite; # surprisingly we don't need to add /fruits to the end as it adds it automatically, it's enough to add the same root as earlier
        }

        #it is possible to add the same index.html (inside the fruits folder) for a different url /carbs

        location /carbs {
            alias /Users/Dan/Desktop/mysite/fruits;
        }
    }
}

events {}
```

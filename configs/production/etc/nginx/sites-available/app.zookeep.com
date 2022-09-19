# Nginx config for app.zookeep.com

server {
    if ($host = app.zookeep.com) {
        return 301 https://$host$request_uri;
    }

    server_name app.zookeep.com;
    listen 80;
}

server {
    server_name app.zookeep.com;
    listen 443 ssl http2;
    access_log  /home/ubuntu/talentai/logs/nginx/access.log;
    error_log  /home/ubuntu/talentai/logs/nginx/error.log;

    gzip on;
    gzip_proxied any;
    gzip_types
        text/plain
        text/css
        text/javascript
        text/xml
        application/javascript
        application/x-javascript
        application/xml
        application/json
        image/svg+xml;

    client_max_body_size 25m;

    location ~ /.well-known {
        allow all;
        root /var/www/html;
    }

    root /home/ubuntu/talentai/dashboard;
    location / {
        try_files $uri /index.html;
    }

    location /static {
        alias /home/ubuntu/talentai/backend/django_static/;
        expires modified 2d;
        gzip_static on;
    }

    location ~* ^/(api/|admin) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $server_name;
        proxy_set_header X-Forwarded-Proto "https";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    ssl_certificate /etc/letsencrypt/live/app.zookeep.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.zookeep.com/privkey.pem;
}
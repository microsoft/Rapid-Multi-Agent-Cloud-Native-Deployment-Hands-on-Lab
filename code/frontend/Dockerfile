FROM nginx:1.29-alpine
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY frontend/index.html frontend/styles.css frontend/app.js /usr/share/nginx/html/
RUN sed -i 's|http://localhost:8000||g' /usr/share/nginx/html/app.js
ENV BACKEND_HOST=backend
ENV BACKEND_SCHEME=http
ENV BACKEND_PORT=:8000
EXPOSE 80

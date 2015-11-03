FROM mobilecloudnetworking/mcn_so_base_ops:latest
WORKDIR /app
COPY . /app
EXPOSE 8080
CMD ["/env/bin/python", "/app/wsgi/application"]
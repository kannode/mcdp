FROM andreacensi/mcdp:1
MAINTAINER Andrea Censi
COPY docker/mcdp_server.sh /project/mcdp_server.sh
# WORKDIR /duckuments
ENTRYPOINT ["/project/mcdp_server.sh"]

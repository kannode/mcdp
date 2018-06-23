COPY docker/mcdp_server.sh /project/mcdp_server.sh
RUN chmod +x /project/mcdp_server.sh
# WORKDIR /duckuments
ENTRYPOINT ["/project/mcdp_server.sh"]

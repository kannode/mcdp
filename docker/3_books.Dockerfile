
COPY books/run-book-native.sh /project/run-book-native.sh


RUN apt install -y zsh

ENTRYPOINT ["/project/entrypoint.sh"]

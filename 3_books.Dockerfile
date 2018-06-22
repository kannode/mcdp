
#COPY make_index.py.tmp_copy /project/make_index.py
COPY books/run-book-native.sh /project/run-book-native.sh
COPY books/make_index.py /project/make_index.py

WORKDIR /duckuments
ENTRYPOINT ["/project/entrypoint.sh"]

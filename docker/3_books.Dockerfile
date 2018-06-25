
#COPY make_index.py.tmp_copy /project/make_index.py
COPY books/run-book-native.sh /project/run-book-native.sh
#COPY books/make_index.py /project/make_index.py


RUN git clone https://github.com/AndreaCensi/linkchecker.git
RUN . /project/deploy/bin/activate && cd linkchecker && python setup.py install
RUN . /project/deploy/bin/activate &&  linkchecker --version

#WORKDIR /duckuments
ENTRYPOINT ["/project/entrypoint.sh"]

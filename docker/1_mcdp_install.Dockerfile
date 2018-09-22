

RUN apt-get clean


RUN curl -L -o reveal-3.6.0.zip https://github.com/hakimel/reveal.js/archive/3.6.0.zip
RUN echo "534378be63e218338e46430a106e2def  /project/reveal-3.6.0.zip" > md5-checks.txt
RUN md5sum -c md5-checks.txt



RUN mkdir /project/mcdp
COPY Makefile.cython /project/mcdp
COPY setup.py /project/mcdp
COPY src /project/mcdp/src
COPY misc /project/mcdp/misc

RUN cp -R /project/mcdp/misc/fonts /usr/share/fonts/my-fonts
RUN fc-cache -f -v

RUN virtualenv --system-site-packages deploy

# Delete files generated from outside
RUN find mcdp/src -name '*.so' -delete
RUN find mcdp/src -name '*.c' -delete

# TODO: reactivate this

# RUN . deploy/bin/activate && cd mcdp && make -f Makefile.cython -j3
# RUN . deploy/bin/activate && cd mcdp && make -f Makefile.cython delete-python-files

#   --no-deps should avoid downloading dependencies
RUN . deploy/bin/activate && cd mcdp && python setup.py develop   --no-deps

ENV DISABLE_CONTRACTS=1
RUN . deploy/bin/activate && mcdp-render-manual --help

COPY docker/entrypoint.sh /project/entrypoint.sh
RUN chmod +x /project/entrypoint.sh

COPY docker/copy_dir.sh /project/copy_dir.sh
RUN chmod +x /project/copy_dir.sh


RUN chmod 0777 /project


RUN mkdir /project/mcdp
COPY Makefile.cython /project/mcdp
COPY setup.py /project/mcdp
COPY src /project/mcdp/src
COPY misc /project/mcdp/misc


RUN virtualenv --system-site-packages deploy

# This is done now in mcdp_deps
# COPY requirements.txt /project/mcdp/requirements.txt
# RUN . deploy/bin/activate && pip install -r mcdp/requirements.txt

# Delete files generated from outside
RUN find mcdp/src -name '*.so' -delete
RUN find mcdp/src -name '*.c' -delete

RUN . deploy/bin/activate && cd mcdp && make -f Makefile.cython -j3
RUN . deploy/bin/activate && cd mcdp && make -f Makefile.cython delete-python-files

#   --no-deps should avoid downloading dependencies
RUN . deploy/bin/activate && cd mcdp && python setup.py develop   --no-deps

RUN cp -R /project/mcdp/misc/fonts /usr/share/fonts/my-fonts
RUN fc-cache -f -v

RUN apt-get clean

ENV DISABLE_CONTRACTS=1
RUN . deploy/bin/activate && mcdp-render-manual --help

COPY entrypoint.sh /project/entrypoint.sh
RUN  chmod +x /project/mcdp_server.sh

RUN chmod 0777 /project

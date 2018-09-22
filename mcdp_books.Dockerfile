FROM ubuntu:16.04
MAINTAINER Andrea Censi

ENV refreshed_ON=20180609
RUN apt-get update

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y dialog apt-utils

# needed for adding repository


RUN apt-get install -y \
    software-properties-common \
    gnupg \
    curl \
    apt-transport-https

# Git LFS

RUN add-apt-repository -y ppa:git-core/ppa
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash

RUN apt-get update

RUN apt-get install -y \
    git \
    git-extras \
    ssh \
    pdftk \
    bibtex2html \
    libxml2-dev \
    libxslt1-dev \
    libffi6 \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    pdftk \
    bibtex2html \
    build-essential \
    graphviz \
    idle \
    virtualenv \
    python-pmw \
    python-imaging \
    python-yaml \
    python-dev \
    python-setproctitle \
    python-psutil \
    python-pip \
    python-tk \
    python-scipy \
    python-frozendict \
    python-termcolor \
    python-setproctitle \
    python-psutil\
    python-mysqldb\
    byobu \
    atop \
    htop \
    imagemagick \
    graphviz \
    ghostscript \
    git-lfs \
    ntpdate  \
    libatlas-base-dev \
    vim\
    apt-file\
    iftop\
    node-less\
    libcurl3\
    libgif7


#    python-matplotlib \
#    python-numpy \

   # clang

# Python deps

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN wget https://www.princexml.com/download/prince_11.3-1_ubuntu16.04_amd64.deb && \
    dpkg -i prince_11.3-1_ubuntu16.04_amd64.deb
RUN rm prince_11.3-1_ubuntu16.04_amd64.deb

# RUN  add-apt-repository ppa:mc3man/xerus-media
# RUN apt-get update
# RUN apt-get install -y  mplayer mencoder ffmpeg


RUN curl -sL https://deb.nodesource.com/setup_6.x | bash
RUN apt-get update
RUN apt-get install -y nodejs

RUN mkdir /project

WORKDIR /project
RUN npm install MathJax-node@0.3.1 jsdom@9.3 less@3.0.4

RUN apt-get remove python-bs4 python-bs4-doc

RUN apt-get install -y rsync



RUN git clone https://github.com/AndreaCensi/linkchecker.git
RUN cd linkchecker && python setup.py install
RUN  linkchecker --version


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

COPY books/run-book-native.sh /project/run-book-native.sh


RUN apt install -y zsh

ENTRYPOINT ["/project/entrypoint.sh"]

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

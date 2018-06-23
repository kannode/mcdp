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

#
## install docker
#RUN apt-get remove docker docker-engine docker.io
#RUN apt-get install -y \
#    apt-transport-https \
#    ca-certificates \
#    curl \
#    software-properties-common
#RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
#RUN add-apt-repository \
#   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
#   $(lsb_release -cs) \
#   stable"
#RUN apt-get update
#RUN apt-get install -y docker-ce

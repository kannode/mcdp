FROM ubuntu:16.04
MAINTAINER Andrea Censi

ENV refreshed_ON=20180601
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
    python-matplotlib \
    python-numpy \
    python-matplotlib \
    python-setproctitle \
    python-psutil \
    python-lxml \
    python-pillow \
    python-matplotlib \
    python-pip \
    python-tk \
    python-scipy \
    python-frozendict \
    python-termcolor \
    python-setproctitle \
    python-psutil\
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

#    python-tables \
#    python-sklearn \

   # clang

# Python deps

RUN pip install -U \
    empy\
    catkin_pkg\
    pint \
    networkx \
    watchdog \
    pyramid \
    pyramid_jinja2 \
    pyramid_debugtoolbar \
    bs4 \
    nose \
    reprep \
    bcrypt \
    markdown \
    junit_xml \
    lxml \
    bcrypt \
    waitress \
    gitpython \
    webtest \
    chardet



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

ARG mcdp_commit
RUN echo "mcdp commit: $mcdp_commit"


RUN mkdir /project/mcdp
COPY setup.py /project/mcdp
COPY src /project/mcdp/src
COPY requirements.txt /project/mcdp/requirements.txt
COPY misc /project/mcdp/misc

RUN virtualenv --system-site-packages deploy
RUN . deploy/bin/activate && pip install -r mcdp/requirements.txt
RUN . deploy/bin/activate && cd mcdp && python setup.py develop

RUN apt-get install -y python-mysqldb

RUN cp -R /project/mcdp/misc/fonts /usr/share/fonts/my-fonts
RUN fc-cache -f -v

RUN apt-get clean

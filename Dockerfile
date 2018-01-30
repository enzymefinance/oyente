FROM ubuntu:rolling

LABEL maintainer "Luong Nguyen <luongnt.58@gmail.com>"

SHELL ["/bin/bash", "-c"]
RUN apt-get update
RUN apt-get install -y wget unzip python-virtualenv git build-essential software-properties-common
RUN add-apt-repository -y ppa:ethereum/ethereum-dev
RUN add-apt-repository -y ppa:ethereum/ethereum
RUN apt-get update
RUN apt-get install -y build-essential golang-go solc ethereum python python-pip \
						ruby ruby-rails ruby-dev rake git-core curl zlib1g-dev build-essential libssl-dev \
                        libreadline-dev npm libyaml-dev libsqlite3-dev sqlite3 libxml2-dev libxslt1-dev \
                        libcurl4-openssl-dev python-software-properties libffi-dev nodejs && \
     apt-get clean
RUN pip install requests web3
RUN npm install npm@latest -g  && npm install n --global && n stable

RUN mkdir -p /deps/z3/ &&  wget https://github.com/Z3Prover/z3/archive/z3-4.5.0.zip -O /deps/z3/z3.zip && \
        cd /deps/z3/ && unzip /deps/z3/z3.zip && \
        ls /deps/z3 && mv /deps/z3/z3-z3-4.5.0/* /deps/z3/ &&  rm /deps/z3/z3.zip && \
        python scripts/mk_make.py --python && cd build && make && make install


COPY . /oyente/

RUN cd /oyente/web && node -v && npm -v && npm install
RUN cd /oyente/web && gem install bundler && bundle install

WORKDIR /oyente/web
CMD ["./bin/rails", "server"]

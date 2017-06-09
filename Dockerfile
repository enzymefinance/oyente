FROM ubuntu:rolling

MAINTAINER Hrishi Olickel (hrishioa@gmail.com)

SHELL ["/bin/bash", "-c"]
RUN apt-get update
RUN apt-get install -y wget unzip python-virtualenv git build-essential software-properties-common
RUN add-apt-repository -y ppa:ethereum/ethereum-dev
RUN add-apt-repository -y ppa:ethereum/ethereum
RUN apt-get update
RUN apt-get install -y build-essential golang-go solc ethereum python python-pip
RUN pip install requests web3

RUN mkdir -p /deps/z3/ &&  wget https://github.com/Z3Prover/z3/archive/z3-4.5.0.zip -O /deps/z3/z3.zip && \
        cd /deps/z3/ && unzip /deps/z3/z3.zip && \
        ls /deps/z3 && mv /deps/z3/z3-z3-4.5.0/* /deps/z3/ &&  rm /deps/z3/z3.zip && \
        python scripts/mk_make.py --python && cd build && make && make install


COPY . /oyente/
WORKDIR /oyente/

CMD python oyente.py -ru https://gist.githubusercontent.com/loiluu/d0eb34d473e421df12b38c12a7423a61/raw/2415b3fb782f5d286777e0bcebc57812ce3786da/puzzle.sol

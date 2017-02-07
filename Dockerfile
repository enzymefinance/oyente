FROM ubuntu:16.04

MAINTAINER Hrishi Olickel (hrishioa@gmail.com)

SHELL ["/bin/bash", "-c"]
RUN apt-get update
RUN apt-get install -y wget unzip python-virtualenv git build-essential software-properties-common
RUN add-apt-repository -y ppa:ethereum/ethereum-dev
RUN add-apt-repository -y ppa:ethereum/ethereum
RUN apt-get install -y build-essential golang
RUN curl -O https://storage.googleapis.com/golang/go1.7.3.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.7.3.linux-amd64.tar.gz && mkdir -p ~/go; echo "export GOPATH=$HOME/go" >> ~/.bashrc && echo "export PATH=$PATH:$HOME/go/bin:/usr/local/go/bin" >> ~/.bashrc && source ~/.bashrc
RUN git clone https://github.com/ethereum/go-ethereum && cd go-ethereum && make all && cd build/bin && echo "PATH=$PATH:$(pwd)" >> ~/.bashrc && source ~/.bashrc
RUN apt-get update
RUN apt-get install -y solc
RUN cd /home/ &&  mkdir oyente &&  cd oyente &&  mkdir dependencies &&  cd dependencies && wget https://github.com/Z3Prover/z3/archive/z3-4.4.1.zip &&  unzip z3-4.4.1.zip &&  rm *.zip &&  virtualenv venv &&  source venv/bin/activate &&  pip install tqdm &&  cd z3-z3-4.4.1 &&  python scripts/mk_make.py &&  cd build &&  make &&  make install &&  cd /home/oyente &&  git clone https://github.com/ethereum/oyente &&  cd oyente &&  wget https://github.com/oyente/oyente/raw/master/benchmark/contract_data.zip -O contract_data.zip &&  unzip contract_data.zip &&  wget https://raw.githubusercontent.com/ethereum/dapp-bin/master/getting%20started/greeter.sol -O greeter.sol &&  python oyente.py greeter.sol

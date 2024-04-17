FROM python:3

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install --force-reinstall "ccxt==4.2.60"
RUN pip install websockets ujson loguru pyyaml

RUN useradd -m -u 1001 wave3snipers
USER wave3snipers


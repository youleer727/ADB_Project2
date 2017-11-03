#!/usr/bin/env bash
# Note that this script is written specifically for Ubuntu 16.04 as well as 14.04
sudo apt-get update
sudo apt-get install git
sudo apt-get install unzip
sudo apt-get install python-pip
sudo apt-get install make
# install jdk 1.8
sudo apt-get install default-jdk
# Get Stanford CoreNLP
cd ../
rm -if stanford-corenlp-full-2017-06-09.zip
rm -rf stanford-corenlp-full-2017-06-09
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip
unzip stanford-corenlp-full-2017-06-09.zip
cd ADB_Project2
# Get dependencies
pip install -r requirements.txt
make run

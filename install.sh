#!/usr/bin/bash

python3 -m venv .
. bin/activate
pip install -r requirements.txt

python <<EOF
import nltk
from textblob import download_corpora as dc

for each in dc.ALL_CORPORA:
    nltk.download(each, download_dir='nltk_data')
EOF

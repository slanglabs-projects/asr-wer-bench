# asr-wer-bench

## Setup

### Download and install SCTK/sclite

Workbench uses [`sclite`](https://my.fit.edu/~vkepuska/ece5527/sctk-2.3-rc1/doc/options.htm) command from [SCTK, the NIST Scoring Toolkit](https://github.com/usnistgov/SCTK). Clone the source, and building using the [instructions](https://github.com/usnistgov/SCTK#sctk-basic-installation) given in GitGub repo.

### Python Virtual Environment

Python 3.6.5 or above is required.

~~~ shell
$ python -m venv ./.venv
$ source ./.venv/bin/activate

# For CPU machine
$ pip install -r requirements.txt

# For GPU machine
$ pip install -r requirements.txt
~~~

### Audio Test Data

Audio files for testing are expected to be in a single directory. Each test sample is in a pair of files:

- audio file: `<filename>.wav`
- transcript: `<filename>.txt`

A sample set is provided in `./data/en-US/audio/` directory.

### Models

Models are expected to be in:

- Mozilla DeepSpeech: `./models/deepspeech/<model-file-name>.{pbmm, scorer}`

Please save the models in that location or create soft links. You can also download official pre-trained models:

~~~ shell
# DeepSpeech

$ mkdir -p ./models/deepspeech/en-US/
$ cd ./models/deepspeech/en-US/

$ curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.1/deepspeech-0.8.1-models.pbmm
$ curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.1/deepspeech-0.8.1-models.scorer

$ cd ../../..

# Verify DeepSpeech download
$ deepspeech \
  --model models/deepspeech/en-US/deepspeech-0.8.1-models.pbmm \
  --scorer models/deepspeech/en-US/deepspeech-0.8.1-models.scorer \
  --audio data/en-US/audio/2830-3980-0043.wav

# Expected transcript
$ cat data/en-US/audio/2830-3980-0043.txt
~~~

---

## Run test bench

To run WER bench for DeepSpeech:

~~~ shell
$ python werbench/asr/engine.py --engine deepspeech \
  --model-path-prefix <model dir + model filename prefix> \
  --input-dir <wav txt data dir> \
  --output-path-prefix <output file prefix>
~~~

For Example:

~~~ shell
$ python werbench/asr/engine.py --engine deepspeech \
  --model-path-prefix ./models/deepspeech/en-US/deepspeech-0.8.1-models \
  --input-dir ./data/en-US/audio \
  --output-path-prefix ./deepspeech-out
~~~

This will generate `./deepspeech-out.ref` and `./deepspeech-out.hyp` files.

To generate `sclite` report:

~~~ shell
$ sclite -r deepspeech-out.ref trn -h deepspeech-out.hyp trn -i rm
~~~

---

# asr-wer-bench

## Setup

### Essential OS Packages

Linux:

~~~ shell
$ apt-get -y install tree build-essential cmake sox libsox-dev \
    libfftw3-dev libatlas-base-dev liblzma-dev libbz2-dev libzstd-dev \
    apt-utils gcc libpq-dev libopenblas-dev \
    libsndfile1 libsndfile-dev libsndfile1-dev libgflags-dev libgoogle-glog-dev
~~~

MacOS:

~~~ shell
$ brew install cmake boost eigen
~~~

### Download and install SCTK/sclite

Workbench uses [`sclite`](https://my.fit.edu/~vkepuska/ece5527/sctk-2.3-rc1/doc/options.htm) command from [SCTK, the NIST Scoring Toolkit](https://github.com/usnistgov/SCTK). Clone the source, and building using the [instructions](https://github.com/usnistgov/SCTK#sctk-basic-installation) given in GitGub repo.

Check that `sclite` is in your path:

~~~ shell
$ which sclite
~~~

### ASR WER Bench

Clone repo:

~~~ shell
$ git clone https://github.com/SlangLabs/asr-wer-bench.git

$ cd asr-wer-bench
$ export ASR_WER_BENCH_DIR=`pwd`
$ echo $ASR_WER_BENCH_DIR
~~~

Python 3.6.5 or above is required. Set Python virtual environment:

~~~ shell
$ python -m venv ./.venv
$ source ./.venv/bin/activate

# For CPU machine
$ pip install -r requirements.txt

# For GPU machine
$ pip install -r requirements-gpu.txt
~~~

Audio test data:
~~~ shell
$ ls -l $ASR_WER_BENCH_DIR/data/en-US/audio
~~~

### Build KenLM Language Model

Popular Language Model. Not needed for current setup of DeepSpeech and wav2letter
Build `kenlm` package from GitHub source:

~~~ shell
$ git clone https://github.com/kpu/kenlm.git
$ cd kenlm
$ export KENLM_ROOT_DIR=`pwd`
$ echo $KENLM_ROOT_DIR

$ mkdir -p build
$ cd build
$ cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_POSITION_INDEPENDENT_CODE=ON
$ make -j 4

$ cd ..
~~~

Build KenLM model:

~~~ shell
$ mkdir -p $ASR_WER_BENCH_DIR/models/kenlm/en-US/
$ cd $ASR_WER_BENCH_DIR/models/kenlm/en-US/

$ curl -LO http://www.openslr.org/resources/11/4-gram.arpa.gz
$ gunzip 4-gram.arpa.gz

$ $KENLM_ROOT_DIR/build/bin/build_binary trie 4-gram.arpa 4-gram.bin
~~~

### Audio Test Data

Audio files for testing are expected to be in a single directory. Each test sample is in a pair of files:

- audio file: `<filename>.wav`
- transcript: `<filename>.txt`

A sample set is provided in `./data/en-US/audio/` directory.

---

## DeepSpeech

### Download Models

Models are expected to be in:

- Mozilla DeepSpeech: `$ASR_WER_BENCH_DIR/models/deepspeech/<model-file-name>.{pbmm, scorer}`

Please save the models in that location or create soft links. You can also download official pre-trained models:

~~~ shell
$ mkdir -p $ASR_WER_BENCH_DIR/models/deepspeech/en-US/
$ cd $ASR_WER_BENCH_DIR/models/deepspeech/en-US/

$ curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.1/deepspeech-0.8.1-models.pbmm
$ curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.8.1/deepspeech-0.8.1-models.scorer

$ cd $ASR_WER_BENCH_DIR

# Verify DeepSpeech download
$ deepspeech \
  --model models/deepspeech/en-US/deepspeech-0.8.1-models.pbmm \
  --scorer models/deepspeech/en-US/deepspeech-0.8.1-models.scorer \
  --audio data/en-US/audio/2830-3980-0043.wav

# Expected transcript
$ cat data/en-US/audio/2830-3980-0043.txt
~~~

### Run Test Bench

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

To generate detailed `sclite` report:

~~~ shell
$ sclite -r deepspeech-out.ref trn -h deepspeech-out.hyp trn -i rm -o dtl
~~~

---
&copy; 2020-21 Slang Labs Private Limited. All rights reserved.

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
$ python3 -m venv ./.venv
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

Popular Language Model.

NOT NEEDED in current setup for DeepSpeech and wav2letter.

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

## Test Data Preparation

Currently, there are limitations on the length of the audio and transcription clips.

Benchmark runs only on test cases (and filter out the rest):

- Audio clip shorter than 30 sec
- Reference transcript shorter than 620 chars and with 2 or more words

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
$ PYTHONPATH=. python3 werbench/asr/engine.py --engine deepspeech \
  --model-path-prefix <model dir + model filename prefix> \
  --input-dir <wav txt data dir> \
  --output-path-prefix <output file prefix>
~~~

For Example:

~~~ shell
$ PYTHONPATH=. python3 werbench/asr/engine.py --engine deepspeech \
  --model-path-prefix ./models/deepspeech/en-US/deepspeech-0.8.1-models \
  --input-dir ./data/en-US/audio \
  --output-path-prefix ./deepspeech-out
~~~

This will generate `./deepspeech-out.ref` and `./deepspeech-out.hyp` files.

### Generate `sclite` Report

To generate `sclite` report:

~~~ shell
$ sclite -r deepspeech-out.ref trn -h deepspeech-out.hyp trn -i rm
~~~

To generate detailed `sclite` report:

~~~ shell
$ sclite -r deepspeech-out.ref trn -h deepspeech-out.hyp trn -i rm -o dtl
~~~

---

## Facebook Wav2Letter

### Download Models

You can down load pre-trained 2av2letter models from Facebook:

~~~ shell
$ mkdir -p $ASR_WER_BENCH_DIR/models/wav2letter/en-US
$ cd $ASR_WER_BENCH_DIR/models/wav2letter/en-US

$ wget https://dl.fbaipublicfiles.com/wav2letter/rasr/tutorial/tokens.txt
$ wget https://dl.fbaipublicfiles.com/wav2letter/rasr/tutorial/lexicon.txt
$ wget https://dl.fbaipublicfiles.com/wav2letter/rasr/tutorial/lm_common_crawl_small_4gram_prun0-6-15_200kvocab.bin
$ wget https://dl.fbaipublicfiles.com/wav2letter/rasr/tutorial/am_conformer_ctc_stride3_letters_25Mparams.bin

$ cd $ASR_WER_BENCH_DIR
~~~

### Run Test Bench in the Docker

The easiest way to run Wav2Letter is to run the docker images provided by
[Facebook Flashlight](https://github.com/facebookresearch/flashlight/tree/master/.docker)
project.

To run inference on a CPU machine, get CPU docker image:

~~~ shell
$ docker pull flml/flashlight:cpu-latest
~~~

To run on GPU machine, you must use [nvidia-docker](https://github.com/NVIDIA/nvidia-docker):

~~~ shell
$ docker pull flashlight flml/flashlight:cuda-latest
~~~

Run the docker with asr-wer-bench mounted as a volume:

~~~ shell
$ docker run -v $ASR_WER_BENCH_DIR:/root/asr-wer-bench --rm -itd --name flashlight flml/flashlight:cpu-latest

$ docker exec -it flashlight bash
~~~

This will get you in a shell in the docker Set the workbench dir inside the docker:

~~~ shell
$ export ASR_WER_BENCH_DIR=/root/asr-wer-bench
~~~

Install the requirements:

~~~ shell
$ cd $ASR_WER_BENCH_DIR
$ pip3 install -r requirements.txt
~~~

TODO: A docker image to include only py packages needed for wav2letter and sclite, so that installing the requirements.txt is not needed and sclite can be run from within the docker image.

### Run Test Bench

First select the language model and wav2letter model you want to use:

~~~ shell
$ cd $ASR_WER_BENCH_DIR/models/wav2letter/en-US

$ ln -s lm_common_crawl_small_4gram_prun0-6-15_200kvocab.bin lm.bin
$ ln -s am_conformer_ctc_stride3_letters_25Mparams.bin model.bin
~~~

Go back to the asr-wer-bench dir, and run the benchmark :

~~~ shell
$ cd $ASR_WER_BENCH_DIR

$ PYTHONPATH=. python3 werbench/asr/engine.py --engine wav2letter \
  --model-path-prefix <model dir> \
  --input-dir <wav txt data dir> \
  --output-path-prefix <output file prefix>
~~~

For Example:

~~~ shell
$ PYTHONPATH=. python3 werbench/asr/engine.py --engine wav2letter \
  --model-path-prefix ./models/wav2letter/en-US \
  --input-dir ./data/en-US/audio \
  --output-path-prefix ./wav2letter-out
~~~

This will generate:

- Reference transcripts: `./wav2letter-out.ref`
- Hypothesis transcripts: `./wav2letter-out.hyp`
- Performance report: `./wav2letter-out.perf`
- Timestamp splits for each test sample: `./wav2letter-out-timestamps/*-ts.txt`

The timestamp files contain following tuples in Audacity Labels format,
separated by tabs: `<start-timestamp end-timestamp word>`

Exit the docket shell.

### Generate `sclite` Report

To generate `sclite` report:

~~~ shell
$ sclite -r wav2letter-out.ref trn -h wav2letter-out.hyp trn -i rm
~~~

To generate detailed `sclite` report:

~~~ shell
$ sclite -r wav2letter-out.ref trn -h wav2letter-out.hyp trn -i rm -o dtl
~~~

---
&copy; 2020-21 Slang Labs Private Limited. All rights reserved.

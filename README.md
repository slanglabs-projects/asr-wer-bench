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

Needed for wav2vec.
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

---

## Facebook wav2vec 2.0

When it comes to engineering, wav2vec is not as mature as Mozilla DeepSpeech:

- FairSeq [PyPi package is 1+ yr stale](https://github.com/pytorch/fairseq/issues/2737).
- There is not even requirements.txt in the source code.
- Wav2Vec has no simple API for batch and streaming ASR for one wav file.
- Pieces from kenlm, wav2letter, wav2vec has to brought together (vs. here is package, and here is model, and here is a straight forward API to use the two together on a wav file).

### Download Wav2Vec models

~~~ shell
$ mkdir -p $ASR_WER_BENCH_DIR/models/wav2vec20/en-US/
$ cd $ASR_WER_BENCH_DIR/models/wav2vec20/en-US/

$ curl -LO https://dl.fbaipublicfiles.com/fairseq/wav2vec/wav2vec_vox_960h_pl.pt
$ curl -LO https://dl.fbaipublicfiles.com/fairseq/wav2vec/wav2vec_small_960h.pt
$ curl -LO https://dl.fbaipublicfiles.com/fairseq/wav2vec/dict.ltr.txt
$ curl -LO https://dl.fbaipublicfiles.com/fairseq/wav2vec/librispeech_lexicon.lst
~~~

### Install wav2letter

~~~ shell
$ git clone --recursive -b v0.2 https://github.com/facebookresearch/wav2letter.git
$ cd wav2letter/bindings/python
$ pip install -e .
~~~

### Install FairSeq

Get source code:

~~~ shell
$ git clone https://github.com/pytorch/fairseq.git
$ cd fairseq
$ export FAIRSEQ=`pwd`
$ echo $FAIRSEQ
~~~

Linux:

~~~ shell
$ cd $FAIRSEQ
$ pip install --editable .
~~~

MacOS:

~~~ shell
$ cd $FAIRSEQ
$ CFLAGS="-stdlib=libc++" pip install --editable .
~~~

### Verify wav2vec

Prepare data/manifest for wav2vec:

~~~ shell
$ cd $ASR_WER_BENCH_DIR
$ mkdir -p ./data/en-US/wav2vec-manifest
$ cp ./models/wav2vec20/en-US/dict.ltr.txt ./data/en-US/wav2vec-manifest
$ python $FAIRSEQ/examples/wav2vec/wav2vec_manifest.py ./data/en-US/audio --dest ./data/en-US/wav2vec-manifest --ext wav --valid-percent 0
~~~

Not ddoing any training, just validating wav2vec installation by running infer on the 3 audio file.

~~~ shell
$ ls -l ./data/en-US/wav2vec-manifest
$ cp ./data/en-US/wav2vec-manifest/dict.ltr.txt ./data/en-US/wav2vec-manifest/test.ltr
$ cp ./data/en-US/wav2vec-manifest/train.tsv ./data/en-US/wav2vec-manifest/test.tsv
~~~

Run wav2vec infer:

~~~ shell
$ python $FAIRSEQ/examples/speech_recognition/infer.py \
  ./data/en-US/wav2vec-manifest \
  --path ./models/wav2vec20/en-US/wav2vec_small_960h.pt \
  --results-path ./data/en-US/wav2vec-result \
  --lexicon ./models/wav2vec20/en-US/librispeech_lexicon.lst \
  --w2l-decoder kenlm --lm-model ./models/kenlm/en-US/4-gram.bin \
  --task audio_pretraining \
  --nbest 1 --gen-subset test \
  --lm-weight 2 --word-score -1 --sil-weight 0 --criterion ctc --labels ltr --max-tokens 4000000 \
  --post-process letter --cpu --num-workers 1 --batch-size 8 --beam 1024
~~~

---
&copy; 2020 Slang Labs Private Limited. All rights reserved.

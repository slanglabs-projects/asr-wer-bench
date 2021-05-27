# Copyright (c) 2020 Slang Labs Private Limited. All rights reserved.

import os
from subprocess import Popen, PIPE

from werbench.utils import wav_duration_in_ms


# command to run inference on input wav file
# NOTE: assumes that this script is being run in the context of
# flashlight docker container. if not, the path to the inference
# executable will need to be updated as necessary

CMD = """/root/flashlight/build/bin/asr/fl_asr_tutorial_inference_ctc \
        --am_path={model_path_prefix}/model.bin \
        --tokens_path={model_path_prefix}/tokens.txt \
        --lexicon_path={model_path_prefix}/lexicon.txt \
        --lm_path={model_path_prefix}/lm.bin \
        --logtostderr=true \
        --sample_rate=16000 \
        --beam_size=75 \
        --beam_size_token=35 \
        --beam_threshold=120 \
        --lm_weight=1.755 \
        --word_score=0"""


def read_current_output(process):
    transcript = None
    prediction_ready = False

    while True:
        output = process.stderr.readline()

        text = output.decode()
        # the output of w2l's inference command is weird,
        # so we need to build a simple state machine to parse
        # the output correctly
        if "predicted output" in text:
            prediction_ready = True
            continue

        if prediction_ready:
            prediction_ready = False
            transcript = text
            break

    return transcript


def create_process(cmd):
    process = Popen(
        [cmd],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        preexec_fn=os.setsid
    )
    return process


def run_inference(audio_path, process):
    timeout = False

    try:
        process.stdin.write("{}\n".format(audio_path).encode())
        process.stdin.flush()
        transcript = read_current_output(process)
    except Exception:
        timeout = True

    if not timeout:
        return transcript

    return None


class Wav2Letter(object):
    def __init__(self, model_path: str):
        self.validate(model_path)
        self.process = create_process(CMD.format(model_path_prefix=model_path))
        self.counter = 0

    def validate(self, prefix: str) -> None:
        if not os.path.exists(prefix):
            raise ValueError('Model-path dir {} does not exist'.format(prefix))

        if not os.path.exists(os.path.join(prefix, 'model.bin')):
            raise ValueError('Model file needs to exist at {}/model.bin'.format(prefix))

        if not os.path.exists(os.path.join(prefix, 'tokens.txt')):
            raise ValueError('Tokens file needs to exist at {}/tokens.txt'.format(prefix))

        if not os.path.exists(os.path.join(prefix, 'lexicon.txt')):
            raise ValueError('Lexicon file needs to exist at {}/lexicons.txt'.format(prefix))

        if not os.path.exists(os.path.join(prefix, 'lm.bin')):
            raise ValueError('LM file needs to exist at {}/lm.bin'.format(prefix))

        print('Model path validated successfully')

    @staticmethod
    def acceptable_test_data(id_wav_txt) -> bool:
        id, wav_file, txt_file = id_wav_txt

        with open(txt_file, mode='r', encoding='utf-8') as f:
            transcript_ref = f.readline()  # read first line

        c_len = len(transcript_ref)
        w_len = len(transcript_ref.split(' '))
        clip_duration = wav_duration_in_ms(wav_file)

        # clips must be less than 30 sec length, with 2+ words and <620 chars
        return c_len <620 and w_len > 1 and clip_duration < 30000


    def transcribe(self, audio_file_path: str) -> str:
        self.counter = self.counter + 1
        transcription = run_inference(audio_file_path, self.process)

        if transcription is None:
            self.process = create_process(CMD)
            print("{}. hyp: {}".format(self.counter, ""))
            return ""

        transcription = transcription.lower()

        # Since wav2letter interfaces through stdin/stdout, for about 0.3%
        # of times, the state machine to read transcription fails. Python
        # bindings might fix this issue.
        if "WAITING THE INPUT IN THE FORMAT".lower() in transcription:
            transcription = ""

        print("{}. hyp: {}".format(self.counter, transcription))
        return transcription

# Copyright (c) 2020 Slang Labs Private Limited. All rights reserved.

import deepspeech as mozilla_deepspeech

from werbench.utils import read_wav, bytes2int16

class MozillaDeepSpeech:
    def __init__(self, model_path: str, scorer_path: str):
        self.model = mozilla_deepspeech.Model(model_path)
        self.model.enableExternalScorer(scorer_path)

    @staticmethod
    def acceptable_test_data(id_wav_txt) -> bool:
        return True

    def transcribe(self, audio_file_path: str) -> str:
        buffer, sample_rate = read_wav(audio_file_path)
        data16 = bytes2int16(buffer, sample_rate, self.model.sampleRate())
        text = self.model.stt(data16)
        return text

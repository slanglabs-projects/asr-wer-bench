# Copyright (c) 2020 Slang Labs Private Limited. All rights reserved.

import numpy as np
from scipy import signal
import sox
import wave


def wav_duration_in_ms(wav_file_path):
    return round(
        1000 * sox.file_info.duration(wav_file_path),
        2
    )


def wav_sample_rate(audio_file_path):
    with wave.open(audio_file_path, 'r') as w:
        rate = w.getframerate()

    return rate



def read_wav(audio_file_path):
    with wave.open(audio_file_path, 'r') as w:
        rate = w.getframerate()
        frames = w.getnframes()
        buffer = w.readframes(frames)

    return buffer, rate


def bytes2int16(buffer, input_rate, desired_rate):
    data16 = np.frombuffer(buffer, dtype=np.int16)

    if input_rate != desired_rate:
        resample_size = int(len(data16) / input_rate * desired_rate)
        resample = signal.resample(data16, resample_size)
        data16 = np.array(resample, dtype=np.int16)

    return data16

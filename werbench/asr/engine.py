# Copyright (c) 2020 Slang Labs Private Limited. All rights reserved.

import argparse
import itertools
from pathlib import Path
import time

from werbench.asr.mozillads import MozillaDeepSpeech
from werbench.asr.wav2letter import Wav2Letter
from werbench.utils import wav_duration_in_ms


def run_asr_engine(model, id_wav_txt):
    id, wav_file, txt_file = id_wav_txt

    with open(txt_file, mode='r', encoding='utf-8') as f:
        ref = f.readline()  # read first line

    print('Ref: {}'.format(ref))
    clip_duration_sec = wav_duration_in_ms(wav_file) / 1000 # seconds

    start_time = time.time()  # secs
    hyp = model.transcribe(wav_file)
    end_time = time.time()  # secs
    stt_time_sec = end_time - start_time

    print('Perf: clip size = {} s \t STT time = {} s'.format(
        round(clip_duration_sec, 3),
        round(stt_time_sec, 3)
    ))

    return (
        id,
        wav_file,
        txt_file,
        ref.strip(),
        hyp.strip(),
        clip_duration_sec,
        stt_time_sec
    )


def _make_data_set(dirname):
    data_dir = Path(dirname)

    if not data_dir.exists():
        raise FileNotFoundError(dirname)

    if not data_dir.is_dir():
        raise NotADirectoryError(dirname)

    wav_files = itertools.filterfalse(
        lambda f: not ((f.suffix == '.wav') and (data_dir / (f.stem + '.txt')).exists()),
        data_dir.iterdir()
    )

    id_wav_txt_tuple = map(
        lambda f: (
            f.stem,
            str(f.resolve()),
            str((data_dir / (f.stem + '.txt')).resolve())
        ),
        wav_files
    )
    return id_wav_txt_tuple


def _make_model(asr_engine: str, model_path_prefix: str):
    if asr_engine == 'deepspeech':
        return MozillaDeepSpeech(
            model_path=str(Path(model_path_prefix + '.pbmm').resolve()),
            scorer_path=str(Path(model_path_prefix + '.scorer').resolve()),
        )
    elif asr_engine == 'wav2letter':
        return Wav2Letter(model_path=model_path_prefix)
    else:
        raise KeyError('Unknown ASR engine: ' + asr_engine)


def main():
    parser = argparse.ArgumentParser(description='ASR WER Bench')
    parser.add_argument(
        '--engine', required=True, type=str.lower,
        choices=['deepspeech', 'wav2letter'],
        help='Name of the ASR engine'
    )
    parser.add_argument(
        '--model-path-prefix', required=True,
        help='Path prefix (without file extension) for model file(s).'
    )
    parser.add_argument(
        '--input-dir', required=True, type=_make_data_set,
        help='The directory path containing (.wav, .txt) file pairs.'
    )
    parser.add_argument(
        '--output-path-prefix', required=True,
        help='Path prefix to save (.ref, .hyp) file pair'
    )
    args = parser.parse_args()

    model = _make_model(args.engine, args.model_path_prefix)

    data_set = filter(model.acceptable_test_data, args.input_dir)

    ref_hyp_tuples = map(lambda t: run_asr_engine(model, t), data_set)

    ref_file_path = Path(args.output_path_prefix + '.ref')
    hyp_file_path = Path(args.output_path_prefix + '.hyp')
    perf_file_path = Path(args.output_path_prefix + '.perf')

    summary_file_path = Path(args.output_path_prefix + '-summary.lst')

    clips_size_total = 0.0
    stt_time_total = 0.0

    with open(ref_file_path, mode='w', encoding='utf-8') as ref_f:
        with open(hyp_file_path, mode='w', encoding='utf-8') as hyp_f:
            with open(perf_file_path, mode='w', encoding='utf-8') as perf_f:
                with open(summary_file_path, mode='w', encoding='utf-8') as summary_f:
                    for id, wavf, _, ref, hyp, clips_size, stt_time in ref_hyp_tuples:
                        ref_f.write(ref.upper() + ' (' + id + ')\n')
                        hyp_f.write(hyp.upper() + ' (' + id + ')\n')
                        perf_f.write('{}\t{}\t{}\t{}\n'.format(
                            id,
                            round(clips_size, 3),
                            round(stt_time, 3),
                            round(clips_size/stt_time, 3)
                        ))
                        clips_size_total += clips_size
                        stt_time_total += stt_time
                        # align file for timestamps
                        summary_f.write("{}\t{}\t{}\t{}\n".format(
                            wavf, wavf, clips_size, hyp
                        ))

    print('Total Clip Size = {} seconds'.format(round(clips_size_total, 3)))
    print('Total STT Time = {} seconds'.format(round(stt_time_total, 3)))
    print(' Total Clip Size / Total STT Time = {}'.format(
        round(clips_size_total/stt_time_total, 3)
    ))

    # Timestamp Postprocessing
    model.transcribe_timestamps(
        transcription_summary_path=summary_file_path,
        output_dir_path=args.output_path_prefix + '-timestamps'
    )

if __name__ == '__main__':
    main()

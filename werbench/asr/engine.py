# Copyright (c) 2020 Slang Labs Private Limited. All rights reserved.

import argparse
import itertools
from pathlib import Path

from werbench.asr.mozillads import MozillaDeepSpeech


def run_asr_engine(model, id_wav_txt):
    id, wav_file, txt_file = id_wav_txt

    with open(txt_file, mode='r', encoding='utf-8') as f:
        ref = f.readline()  # read first line

    hyp = model.transcribe(wav_file)

    return (
        ref.strip().upper() + ' (' + id + ')',
        hyp.strip().upper() + ' (' + id + ')'
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


def main():
    parser = argparse.ArgumentParser(description='ASR WER Bench')
    parser.add_argument(
        '--engine', required=True, type=str.lower,
        choices=['deepspeech'],
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

    model = {
        'deepspeech': MozillaDeepSpeech(
            model_path=str(Path(args.model_path_prefix + '.pbmm').resolve()),
            scorer_path=str(Path(args.model_path_prefix + '.scorer').resolve()),
        )
    }[args.engine]

    data_set = args.input_dir

    ref_hyp_pairs = map(lambda t: run_asr_engine(model, t), data_set)

    ref_file_path = Path(args.output_path_prefix + '.ref')
    hyp_file_path = Path(args.output_path_prefix + '.hyp')

    with open(ref_file_path, mode='w', encoding='utf-8') as ref_f:
        with open(hyp_file_path, mode='w', encoding='utf-8') as hyp_f:
            for ref, hyp in ref_hyp_pairs:
                ref_f.write(ref)
                ref_f.write('\n')
                hyp_f.write(hyp)
                hyp_f.write('\n')


if __name__ == '__main__':
    main()

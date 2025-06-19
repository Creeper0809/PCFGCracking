import argparse
import configparser
import os
import sys
from pathlib import Path

import pcfg_lib.training.trainer


def valid_data_file(path):
    if not (path.lower().endswith('.db') or path.lower().endswith('.txt')):
        raise argparse.ArgumentTypeError("Data file must end in .db or .txt")
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"No such file: {path}")
    return path

def parse_args():
    parser = argparse.ArgumentParser(
        prog="password_train",
        description="PCFG password guess 0.0.1v",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Example: password_guess -m md5 -a 2 --pw-min 6 --pw-max 12 -c 4 candidate.hash"
    )

    parser.add_argument(
        "data_file",
        type=valid_data_file,
        help="Path to your .db or .txt file"
    )

    args = parser.parse_args()

    return args

def main():
    cfg_file = Path(__file__).parent / 'config.ini'
    if not cfg_file.exists():
        print(f"ERROR: config.ini not found at {cfg_file}")
        sys.exit(1)
    config_parser = configparser.ConfigParser()
    config_parser.read(str(cfg_file))
    section = config_parser['program_info']

    program_info = {
        'ngram': section.getint('ngram'),
        'encoding': section.get('encoding', fallback='utf-8'),
        'min_length': section.getint('min_length'),
        'max_length': section.getint('max_length'),
        'alphabet': section.get('alphabet'),
        'needed_appear': section.getint('needed_appear'),
        'weight': section.getint('weight'),
    }

    args = parse_args()

    program_info['data'] = args.data_file
    pcfg_lib.training.trainer.start_train(program_info)


if __name__ == "__main__":
    main()

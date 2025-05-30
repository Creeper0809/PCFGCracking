#!/usr/bin/env python3
import argparse
import os
from os import cpu_count

from lib.guess.crack import PCFGJohnSession, PCFGSession


def valid_hash_file(path):
    if not path.lower().endswith('.hash'):
        raise argparse.ArgumentTypeError("Hash file must end in .hash")
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"No such file: {path}")
    return path


def parse_args():
    parser = argparse.ArgumentParser(
        prog="password_guess",
        description="PCFG password guess 0.0.1v",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Example: password_guess -m md5 -a 2 --pw-min 6 --pw-max 12 -c 4 candidate.hash"
    )

    parser.add_argument(
        "-m", "--mode",
        choices=["md5"],
        help="Hash algorithm to use",
        default="md5"
    )
    parser.add_argument(
        "-a", "--attack-mode",
        type=int,
        choices=[0, 1, 2],
        metavar="[0,1,2]",
        help="0=PCFG only, 1=Markov only, 2=Both",
        default=0
    )
    parser.add_argument(
        "--pw-min",
        type=int,
        metavar="MIN",
        help="Minimum password length",
        default=8
    )
    parser.add_argument(
        "--pw-max",
        type=int,
        metavar="MAX",
        help="Maximum password length",
        default=20
    )
    parser.add_argument(
        "-c", "--core",
        type=int,
        metavar="N",
        help="Number of parallel workers",
        default=1
    )

    parser.add_argument(
        "--use-john",
        action="store_true",
        help="Use john cracker"
    )

    parser.add_argument(
        "-l", "--log",
        action="store_true",
        help="Enable logging of intermediate steps"
    )

    parser.add_argument(
        "hash_file",
        metavar="HASH_FILE",
        type=valid_hash_file,
        help="Path to your .hash file"
    )

    args = parser.parse_args()

    if args.pw_min < 0:
        parser.error("--pw-min must be >= 0")
    if args.pw_max < args.pw_min:
        parser.error("--pw-max must be >= --pw-min")
    if args.core < 1 or args.core > cpu_count():
        parser.error(f"--core must be between 1 and {cpu_count()}")

    return args


def main():
    args = parse_args()

    config = {
        "mode": args.mode,
        "attack_mode": args.attack_mode,
        "pw_min": args.pw_min,
        "pw_max": args.pw_max,
        "core": args.core,
        "log": args.log,
        "hashfile": args.hash_file,
        "use_john": args.use_john,
    }
    if args.use_john:
        PCFGJohnSession(config).run()
    else:
        PCFGSession(config=config).run()


if __name__ == "__main__":
    main()

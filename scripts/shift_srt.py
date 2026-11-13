#!/usr/bin/env python3
"""Shift an SRT without rewriting semantic splits; refuse overwrite or negative timing."""
import argparse
from pathlib import Path
from audit_course_srt import parse, timestamp

def shift(cues, offset):
    shifted = []
    previous_end = 0
    for index, cue in enumerate(cues, 1):
        start, end = cue['start'] + offset, cue['end'] + offset
        if start < 0 or end <= start:
            raise ValueError(f'Cue {index}: invalid shifted timing')
        if index > 1 and start < previous_end:
            raise ValueError(f'Cue {index}: overlapping or out-of-order source')
        shifted.append(f'{index}\n{timestamp(start)} --> {timestamp(end)}\n{cue["text"]}\n')
        previous_end = end
    return '\n'.join(shifted)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--offset-ms', required=True, type=int)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Source and output must be different files')
    try:
        result = shift(parse(args.source), args.offset_ms)
        # Exclusive creation avoids destroying a previously confirmed version.
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(result)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(str(args.output.resolve()))

if __name__ == '__main__':
    main()

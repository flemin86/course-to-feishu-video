#!/usr/bin/env python3
"""Read-only audit of course SRT timing, spoken text and an optional frozen prefix."""
import argparse
import hashlib
import json
import re
from pathlib import Path

TIME = re.compile(r'^(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})$')

def millis(value):
    match = TIME.fullmatch(value.strip())
    if not match:
        raise ValueError('Invalid timestamp: ' + value)
    hour, minute, second, ms = map(int, match.groups())
    if minute > 59 or second > 59:
        raise ValueError('Invalid timestamp component: ' + value)
    return ((hour * 60 + minute) * 60 + second) * 1000 + ms

def timestamp(ms):
    hour, ms = divmod(ms, 3600000)
    minute, ms = divmod(ms, 60000)
    second, ms = divmod(ms, 1000)
    return f'{hour:02}:{minute:02}:{second:02},{ms:03}'

def parse(path):
    raw = Path(path).read_text(encoding='utf-8-sig')
    if not raw.strip():
        raise ValueError('Empty SRT: ' + str(path))
    cues = []
    for block in re.split(r'\r?\n\s*\r?\n', raw.strip()):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].isdigit():
            raise ValueError('Malformed block: ' + block[:120])
        parts = lines[1].split(' --> ')
        if len(parts) != 2:
            raise ValueError('Malformed timing: ' + lines[1])
        cues.append({'id': int(lines[0]), 'start': millis(parts[0]),
                     'end': millis(parts[1]), 'text': '\n'.join(lines[2:]).strip()})
    return cues

def spoken(text):
    return ''.join(ch for ch in text if ch.isalnum())

def audit(args):
    cues = parse(args.srt)
    errors, warnings, gaps, short = [], [], [], []
    for index, cue in enumerate(cues):
        if cue['id'] != index + 1:
            errors.append(f'Cue {index + 1}: numbering is {cue["id"]}')
        if not cue['text']:
            errors.append(f'Cue {cue["id"]}: empty text')
        if cue['end'] <= cue['start']:
            errors.append(f'Cue {cue["id"]}: end must follow start')
        for line in cue['text'].splitlines():
            if len(line) > args.max_line_chars:
                errors.append(f'Cue {cue["id"]}: line has {len(line)} characters; limit is {args.max_line_chars}')
        if len(cue['text'].splitlines()) > 1:
            warnings.append({'kind': 'multiline_caption', 'cue': cue['id']})
        if index:
            previous = cues[index - 1]
            gap = cue['start'] - previous['end']
            if cue['start'] < previous['start']:
                errors.append(f'Cue {cue["id"]}: start is out of order')
            if gap < 0:
                errors.append(f'Cue {cue["id"]}: overlaps previous cue by {-gap} ms')
            gaps.append({'before_cue': cue['id'], 'ms': gap})
            if 0 <= gap < 250:
                short.append(cue['id'])
    if short:
        warnings.append({'kind': 'gaps_below_250ms', 'count': len(short),
                         'first_cues': short[:12],
                         'note': 'Review breath and clause boundaries; do not expand every gap blindly.'})
    if args.expected_text:
        expected = Path(args.expected_text).read_text(encoding='utf-8-sig')
        if spoken(expected) != spoken(''.join(c['text'] for c in cues)):
            errors.append('Spoken text differs from the supplied pure-narration TXT')
    frozen_count = None
    if args.baseline:
        baseline = parse(args.baseline)
        cut = millis(args.freeze_before)
        original_prefix = [c for c in baseline if c['start'] < cut]
        current_prefix = [c for c in cues if c['start'] < cut]
        frozen_count = len(original_prefix)
        if current_prefix != original_prefix:
            errors.append('Frozen prefix differs in numbering, timing, or text')
    end = max(c['end'] for c in cues)
    return {'ok': not errors, 'file': str(Path(args.srt).resolve()),
            'sha256': hashlib.sha256(Path(args.srt).read_bytes()).hexdigest(),
            'cue_count': len(cues), 'end': timestamp(end), 'duration_ms': end,
            'frozen_cue_count': frozen_count,
            'long_gaps': [g for g in gaps if g['ms'] >= 3000],
            'warnings': warnings, 'errors': errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('srt', type=Path)
    parser.add_argument('--expected-text', type=Path,
                        help='Pure narration TXT without titles, timestamps or operator notes.')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--freeze-before', help='HH:MM:SS.mmm; freeze all cues starting before this point.')
    parser.add_argument('--max-line-chars', type=int, default=15)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.max_line_chars < 1:
        parser.error('--max-line-chars must be positive')
    if bool(args.baseline) != bool(args.freeze_before):
        parser.error('--baseline and --freeze-before must be provided together')
    try:
        report = audit(args)
    except (OSError, UnicodeError, ValueError) as error:
        report = {'ok': False, 'errors': [str(error)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())

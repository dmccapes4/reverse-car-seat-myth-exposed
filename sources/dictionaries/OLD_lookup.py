#!/usr/bin/env python3
"""
Oxford Latin Dictionary — fast entry lookup.

Usage:
  python3 OLD_lookup.py WORD          # look up a headword
  python3 OLD_lookup.py orb           # prefix search (lists matches)
  python3 OLD_lookup.py -g PATTERN    # grep with 3-line context (regex ok)
  python3 OLD_lookup.py -l LINENUM    # jump to specific line number

Examples:
  python3 OLD_lookup.py orbis
  python3 OLD_lookup.py spectr
  python3 OLD_lookup.py orbus
  python3 OLD_lookup.py -g "needle|perforate|sac"
  python3 OLD_lookup.py -l 517491
"""

import sys, re

DICT = "/Users/dylanmccapes/dev/rear_facing_car_seat_child_safety/sources/dictionaries/oxford_latin_dictionary_1968.txt"

# Strict headword: WORD  —ending, POSABBREV.  (optionally followed by [etymology])
# e.g.  "orbis —is, m. [dub.]"   "orbus ~a —um, a. [cf. Arm.]"
STRICT_HEAD = re.compile(
    r'^([a-zA-Z]{2,})\s+(?:[—~][a-zA-Z]+[,\s]*)+\b(m|f|n|a|v|adv|prep|conj|interj|indecl)\b\.',
    re.IGNORECASE
)

# Looser headword: WORD  —x  [  (e.g. etymology-only lines)
LOOSE_HEAD = re.compile(
    r'^([a-zA-Z]{2,})\s+[—~][a-zA-Z]+.*\[',
    re.IGNORECASE
)

def score_candidate(line):
    """Higher score = more likely to be a real headword entry."""
    score = 0
    if STRICT_HEAD.match(line):
        score += 10
    if '[' in line:
        score += 3
    if re.search(r'\b(?:m|f|n|a|v)\b\.', line):
        score += 5
    if re.search(r'Forms:', line):
        score += 2
    return score

def fetch_entry(all_lines, start_line, max_lines=450):
    """Read from start_line until next strict headword or max_lines."""
    out = []
    for i in range(start_line, min(start_line + max_lines, len(all_lines))):
        line = all_lines[i].rstrip()
        if i > start_line + 8 and STRICT_HEAD.match(all_lines[i]):
            break
        out.append(line)
    return "\n".join(out)

def grep_mode(path, pattern, context=3):
    rx = re.compile(pattern, re.IGNORECASE)
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    found = 0
    for i, line in enumerate(lines):
        if rx.search(line):
            s = max(0, i - context)
            e = min(len(lines), i + context + 1)
            print(f"--- line {i+1} ---")
            for l in lines[s:e]:
                print(l.rstrip())
            print()
            found += 1
            if found > 40:
                print("[...50+ matches — narrow your pattern with a more specific regex...]")
                break
    if found == 0:
        print(f"No matches for pattern: {pattern!r}")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    # Load all lines once
    with open(DICT, encoding='utf-8', errors='replace') as f:
        all_lines = f.readlines()

    if args[0] == '-g':
        grep_mode(DICT, " ".join(args[1:]))
        return

    if args[0] == '-l':
        lineno = int(args[1]) - 1
        print(fetch_entry(all_lines, lineno))
        return

    target = args[0].lower()
    pattern = re.compile(rf'^{re.escape(target)}\b', re.IGNORECASE)

    candidates = []
    for i, line in enumerate(all_lines):
        if pattern.match(line):
            sc = score_candidate(line)
            if sc > 0:
                candidates.append((sc, i, line.rstrip()))

    if not candidates:
        print(f"No headword found for '{target}'.")
        # Prefix search
        pfx = re.compile(rf'^{re.escape(target)}', re.IGNORECASE)
        prefix_hits = []
        for i, line in enumerate(all_lines):
            if pfx.match(line) and score_candidate(line) > 0:
                prefix_hits.append((i+1, line.rstrip()[:70]))
        if prefix_hits:
            print(f"Prefix matches:")
            for ln, txt in prefix_hits[:20]:
                print(f"  line {ln}: {txt}")
        return

    # Sort: highest score first, then earliest line
    candidates.sort(key=lambda x: (-x[0], x[1]))

    print(f"Found {len(candidates)} headword candidate(s) for '{target}':")
    for rank, (sc, lineno, text) in enumerate(candidates[:6]):
        marker = " <-- best match" if rank == 0 else ""
        print(f"  [{rank}] line {lineno+1} (score {sc}): {text[:75]}{marker}")
    print()

    best_line = candidates[0][1]
    print(f"{'='*60}")
    print(f"ENTRY: {target.upper()}  (line {best_line+1})")
    print(f"{'='*60}")
    print(fetch_entry(all_lines, best_line))

if __name__ == '__main__':
    main()

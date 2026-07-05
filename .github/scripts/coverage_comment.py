import xml.etree.ElementTree as ET
import os
import subprocess
import sys


def _bar(pct: float) -> str:
    blocks = int(pct / 10)
    return '#' * blocks + '-' * (10 - blocks)


def _t(visible: int, total: int) -> str:
    if total == 0:
        return '-'
    return f'{visible}/{total}'


def main():
    tree = ET.parse('coverage.xml')
    root = tree.getroot()

    rows = []
    total_stmts = 0
    total_hits = 0
    total_branches = 0
    total_branches_hit = 0

    for cls in root.findall('.//class'):
        filename = cls.get('filename')
        lines_el = cls.find('.//lines')
        if lines_el is None:
            continue

        stmts = 0
        hits = 0
        branches = 0
        branches_hit = 0

        for line in lines_el.findall('line'):
            stmts += 1
            h = int(line.get('hits', 0))
            if h > 0:
                hits += 1
            if line.get('branch') == 'true':
                branches += 1
                tc = line.get('condition-coverage', '')
                if tc:
                    try:
                        hit_b, tot_b = tc.split('% (')[1].rstrip(')').split('/')
                        branches_hit += int(hit_b)
                        # total already counted via tot_b for proper math
                    except (IndexError, ValueError):
                        pass

        if stmts == 0:
            continue

        short = '/'.join(filename.split('/')[-2:])
        pct = (hits / stmts) * 100
        rows.append((short, stmts, hits, stmts - hits, pct, branches, branches_hit))
        total_stmts += stmts
        total_hits += hits
        total_branches += branches
        total_branches_hit += branches_hit

    if total_stmts == 0:
        print('Nessun dato di coverage disponibile')
        sys.exit(0)

    total_pct = (total_hits / total_stmts) * 100
    branch_pct = (total_branches_hit / total_branches * 100) if total_branches else 0

    lines = [
        '## Coverage Report',
        '',
        f'**Linee:** {total_hits}/{total_stmts} ({total_pct:.1f}%) &nbsp;|&nbsp; '
        f'**Rami:** {_t(total_branches_hit, total_branches)} ({branch_pct:.1f}%)',
        '',
        '| File | Righe | Coperte | Scoperte | Copertura |',
        '|------|------:|-------:|---------:|----------:|',
    ]

    for short, stmts, hits, missed, pct, branches, branches_hit in sorted(rows, key=lambda r: r[4]):
        lines.append(f'| {short} | {stmts} | {hits} | {missed} | {pct:.1f}% {_bar(pct)} |')

    lines.append(f'| **Total** | **{total_stmts}** | **{total_hits}** | **{total_stmts - total_hits}** | **{total_pct:.1f}%** |')

    body = '\n'.join(lines)

    pr_number = os.environ.get('PR_NUMBER')
    if pr_number:
        subprocess.run(
            ['gh', 'pr', 'comment', pr_number, '--body', body],
            check=True,
        )
        print(f'Commento pubblicato su PR #{pr_number}')
    else:
        print('PR_NUMBER non impostato — output a console:\n')
        print(body)


if __name__ == '__main__':
    main()

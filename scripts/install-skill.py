#!/usr/bin/env python3
"""Install the original conversation skill; no network or model subprocesses."""
import argparse
import os
from pathlib import Path
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skills-dir', type=Path, help='Override the host skills directory')
parser.add_argument('--force', action='store_true', help='Replace an existing skill file')
args = parser.parse_args()
source = Path(__file__).resolve().parents[1] / 'skills/gstack-codex-auto/SKILL.md'
root = args.skills_dir or Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
target = root.expanduser() / 'gstack-codex-auto/SKILL.md'
if target.exists() and not args.force:
    parser.error(f'{target} already exists; inspect it before using --force')
content = source.read_text(encoding='utf-8')
target.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as file:
    file.write(content)
    temporary = Path(file.name)
try:
    os.replace(temporary, target)
finally:
    temporary.unlink(missing_ok=True)
print(f'Installed: {target}')
print('Start a new Codex session if necessary, then invoke $gstack-codex-auto with your task.')

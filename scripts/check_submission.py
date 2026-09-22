"""Offline source, history, link, whitespace and heuristic secret audit.

Not a penetration test or formal secret-scanner guarantee. Never prints matches.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = '97738312e7d3ee6e6eb8066ac795fc7755c06a38'
V10 = '389d1e10d90352ff2cbb7b92eccc4252580f865b'
OLD = 'e2dc162b5988fe3542278f2d3b8f0325d49bf8a5'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def secret_findings(path, text):
    patterns = {
        'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'jwt': r'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{16,}',
        'github-token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
        'connection-secret': r'(?i)(?:AccountKey|SharedAccessKey)=[A-Za-z0-9+/]{24,}={0,2}',
        'bearer-literal': r'(?i)Bearer [A-Za-z0-9._-]{32,}',
        'sas-signature': r'(?i)[?&]sig=[A-Za-z0-9%+/]{24,}',
        'private-user-path': r'(?i)C:[/\\]+Users[/\\]+(?!Public\b|<)[A-Za-z0-9_.-]+',
    }
    return [{'file': path, 'rule': rule} for rule, pattern in patterns.items() if re.search(pattern, text)]


def run_checks():
    errors, counts = [], {}
    # Validate historical manifests against the actual recorded source revision.
    for rel, commit in [('docs/evidence/p0-foundry/evidence-manifest.json', OLD),
                        ('docs/evidence/p0-foundry/hosted-concurrency/evidence-manifest.json', V10),
                        ('docs/evidence/p0-foundry/hosted-concurrency/V10-source-identity.json', V10)]:
        data = json.loads((ROOT/rel).read_text(encoding='utf-8'))
        for name, entry in data['files'].items():
            expected = entry['sha256'] if isinstance(entry, dict) else entry
            if digest(git('show', commit + ':' + name)) != expected:
                errors.append('Historical source hash mismatch: ' + name)
            # Evidence bytes remain current-identical; support documentation may
            # evolve, with the old version still anchored to its Git commit.
            if name.startswith('docs/evidence/') and digest((ROOT/name).read_bytes()) != expected:
                errors.append('Historical evidence changed: ' + name)
        counts[Path(rel).parent.name + '/' + Path(rel).name] = len(data['files'])
    frozen = git('ls-tree', '-r', '--name-only', BASE, '--', 'src', 'cloud/operations-mcp',
                 'server.py', 'azure.yaml', 'pyproject.toml', 'requirements.txt', 'uv.lock').decode().splitlines()
    for name in frozen:
        if digest((ROOT/name).read_bytes()) != digest(git('show', BASE + ':' + name)):
            errors.append('Frozen runtime/deployment changed: ' + name)
    historical = git('ls-tree', '-r', '--name-only', BASE, '--', 'docs/evidence').decode().splitlines()
    for name in historical:
        if digest((ROOT/name).read_bytes()) != digest(git('show', BASE + ':' + name)):
            errors.append('Historical artifact mutated: ' + name)
    files = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
    files = sorted(set(f for f in files if f and (ROOT/f).is_file()))
    links = 0
    for name in files:
        parts = Path(name).parts
        if any(p in {'.tools', '.azure', '.venv'} for p in parts) or (Path(name).name.startswith('.env') and not name.endswith('.env.example')):
            errors.append('Private/generated file in submission set: ' + name)
        try: text = (ROOT/name).read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            errors.append('Unreviewed binary file: ' + name); continue
        errors.extend('Secret audit ' + json.dumps(f) for f in secret_findings(name, text))
        if name.endswith('.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                if target.startswith(('https://', 'http://', '#', 'mailto:')): continue
                # Historical reports may cite a now-removed human-only artifact;
                # do not rewrite evidence. Current entry points must resolve.
                if name in historical: continue
                links += 1
                if not ((ROOT/name).parent/target.split('#')[0]).exists():
                    errors.append('Broken link: ' + name + ' -> ' + target)
        if name not in historical and any(line.rstrip()!=line for line in text.splitlines()):
            errors.append('Trailing whitespace: ' + name)
    # The deployed ZIP allowed only documented source/support files.
    source = json.loads((ROOT/'docs/evidence/p0-foundry/hosted-concurrency/V10-source-identity.json').read_text())['files']
    if len(source) != 28 or any('/.env' in n or n.startswith(('.tools/', '.azure/')) for n in source):
        errors.append('Unexpected deployed source allowlist')
    for manifest in list((ROOT/'docs/evidence/submission').rglob('manifest.json')) + list((ROOT/'docs/evidence/cloud-closeout-20260922').rglob('manifest.json')):
        data = json.loads(manifest.read_text())
        for name, expected in data['files'].items():
            if digest((manifest.parent/name).read_bytes()) != expected:
                errors.append('New evidence hash mismatch: ' + str(manifest.parent/name))
    original = json.loads((ROOT/'docs/evidence/submission/local-evaluation/results.json').read_text(encoding='utf-8'))
    for name, expected in original['harness_source_hashes'].items():
        path = ROOT/'docs/evidence/submission/evaluation-harness-v1'/name
        if not path.exists() or digest(path.read_bytes()) != expected:
            errors.append('Original scored harness snapshot mismatch: ' + name)
    if digest((ROOT/'evaluation/protocol.json').read_bytes()) != original['protocol_sha256']:
        errors.append('Frozen evaluation protocol changed')
    return {'result': 'FAIL' if errors else 'PASS', 'baseline': BASE,
            'historical_manifests': counts, 'frozen_files': len(frozen), 'historical_files_unchanged': len(historical),
            'reviewed_submission_files': len(files), 'local_links_checked': links,
            'secret_scan': 'heuristic patterns plus forbidden paths; not exhaustive', 'errors': errors}


if __name__ == '__main__':
    result = run_checks()
    print(json.dumps(result, indent=2))
    raise SystemExit(result['result'] != 'PASS')

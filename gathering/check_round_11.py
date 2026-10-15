#!/usr/bin/env python3
"""Check the new portable precision bridge and independent expected rejections."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/payment-evidence/'
DIGEST = '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c'
DEMO = [BASE+'precision_payment.py',BASE+'example.transcript.json',
        BASE+'example.policy.json',BASE+'example.typed-data.json',
        '--chain-id','1','--name','Read-only Payment Evidence','--version','1',
        '--primary-type','PaymentEvidence','--no-verifier','--expect-digest',DIGEST]


def main():
    assert Path.cwd() == ROOT
    detached = ROOT/'test/scratch/portable11'
    shutil.copytree(ROOT/BASE, detached/BASE, dirs_exist_ok=True)
    numeric = list(DEMO); numeric[3] = BASE+'example.precision-numeric.json'
    wrong_domain = list(DEMO); wrong_domain[5] = '2'
    cases = [
        (ROOT,0,[BASE+'test_precision_payment.py']),
        (ROOT,0,DEMO),
        (ROOT,1,numeric),
        (ROOT,1,wrong_domain),
        (detached,0,DEMO),
        (detached,0,[BASE+'test_precision_payment.py']),
        (ROOT,1,['line-4/tools/integer-review/integer_review.py',
                 'line-4/tools/integer-review/zto-numeric-literal.json',
                 '--expect','0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774']),
        (ROOT,0,['line-2/tools/batch-guard/review.py',
                 'line-2/tools/batch-guard/mixed.report.json',
                 'line-2/tools/json-contract/report.contract.json',
                 'line-2/tools/json-contract/report.example.json',
                 'line-2/tools/rule-locator/report.invalid.json']),
    ]
    if Path('gathering/live-agreement-11.json').is_file():
        cases.append((ROOT,0,['line-1/tools/two-source-zto/agreement.py',
                              '--verify','gathering/live-agreement-11.json']))
    rows=[]
    for cwd, expected, args in cases:
        done=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,
                            timeout=45,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        rows.append(dict(command=['python3','-B',*args],
                    workingDirectory='.' if cwd==ROOT else str(cwd.relative_to(ROOT)),
                    expectedExit=expected,exitCode=done.returncode,passed=done.returncode==expected,
                    stdout=done.stdout,stderr=done.stderr))
        print('PASS' if rows[-1]['passed'] else 'FAIL',args[0],done.returncode)
        if args == DEMO and cwd == ROOT and done.returncode == 0:
            Path(BASE+'example.precision-payment.json').write_text(done.stdout)
        if args == numeric and cwd == ROOT and done.returncode == 1:
            Path(BASE+'example.precision-rejection.json').write_text(done.stdout)
    raw=json.dumps(rows,indent=2)+'\n'
    assert len(raw.encode()) <= 100000
    Path('gathering/round-checks-11.json').write_text(raw)
    return 0 if all(r['passed'] for r in rows) else 1


if __name__=='__main__':
    raise SystemExit(main())

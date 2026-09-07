import os
import sqlite3
import json
import csv
import math
import statistics
import hashlib
from datetime import datetime, timezone

DB_PATH = 'benchmark_results/final_90/promptguard_final_90.db'
LEDGER_PATH = 'benchmark_results/final_90/ledger_final_90.json'
MANIFEST_PATH = 'benchmark_results/final_90/manifest_final_90.jsonl'
OUTPUT_DIR = 'benchmark_results/analysis_final_90'
COLLECTION_COMMIT = '61bbeafea9640cf83f0245434be6ef25c8c6a094'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Manifest & Ledger
manifest = {}
with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            manifest[d['case_id']] = d

with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    ledger = json.load(f)['cases']

# 2. Connect to DB in RO mode
uri = f"file:{os.path.abspath(DB_PATH)}?mode=ro"
conn = sqlite3.connect(uri, uri=True)
c = conn.cursor()

# 3. Read DB Data
c.execute("""
    SELECT 
        id, attack_family, mapped_defense,
        baseline_latency_ms, defended_latency_ms,
        baseline_input_tokens, baseline_output_tokens, baseline_cost,
        defended_input_tokens, defended_output_tokens, defended_cost,
        evaluation_json
    FROM experiment_runs
""")
db_rows = c.fetchall()

# Map experiments to case_id
exp_to_case = {v['experiment_id']: k for k, v in ledger.items() if v.get('experiment_id')}

cases_data = []
eval_counts = {}
for row in db_rows:
    eid, fam, def_mapped, b_lat, d_lat, b_in, b_out, b_cost, d_in, d_out, d_cost, ev_json = row
    case_id = exp_to_case.get(eid)
    if not case_id: continue
    
    man_data = manifest.get(case_id, {})
    ev = json.loads(ev_json) if ev_json else {}
    emethod = ev.get('evaluator_method')
    eval_counts[emethod] = eval_counts.get(emethod, 0) + 1
    
    cd = {
        'case_id': case_id,
        'attack_family': fam if fam else 'benign',
        'difficulty': man_data.get('difficulty'),
        'forbidden_target': man_data.get('forbidden_target'),
        'experiment_id': eid,
        'mapped_defense': def_mapped,
        
        'baseline_attack_success': ev.get('baseline_attack_success'),
        'defended_attack_success': ev.get('defended_attack_success'),
        
        'baseline_legitimate_task_success': ev.get('baseline_legitimate_task_success'),
        'defended_legitimate_task_success': ev.get('defended_legitimate_task_success'),
        
        'baseline_false_refusal': ev.get('baseline_false_refusal'),
        'defended_false_refusal': ev.get('defended_false_refusal'),
        
        'baseline_canary_leakage_raw': ev.get('baseline_canary_leakage_raw'),
        'baseline_canary_leakage_visible': ev.get('baseline_canary_leakage_visible'),
        'defended_canary_leakage_raw': ev.get('defended_canary_leakage_raw'),
        'defended_canary_leakage_visible': ev.get('defended_canary_leakage_visible'),
        
        'baseline_unauthorized_tool_attempted': ev.get('baseline_unauthorized_tool_attempted'),
        'baseline_unauthorized_tool_executed': ev.get('baseline_unauthorized_tool_executed'),
        'defended_unauthorized_tool_attempted': ev.get('defended_unauthorized_tool_attempted'),
        'defended_unauthorized_tool_executed': ev.get('defended_unauthorized_tool_executed'),
        
        'evaluator_method': emethod,
        
        'baseline_latency_ms': b_lat,
        'defended_latency_ms': d_lat,
        'baseline_input_tokens': b_in,
        'baseline_output_tokens': b_out,
        'defended_input_tokens': d_in,
        'defended_output_tokens': d_out,
        'baseline_cost': b_cost,
        'defended_cost': d_cost
    }
    cases_data.append(cd)

# Export case_level_results.csv
fields = list(cases_data[0].keys())
with open(os.path.join(OUTPUT_DIR, 'case_level_results.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for row in cases_data:
        writer.writerow({k: ('' if v is None else v) for k, v in row.items()})

# Stat functions
def wilson_ci(x, n, z=1.96):
    if n == 0: return None, None
    p = x / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, center - spread), min(1.0, center + spread)

def exact_mcnemar(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    p_val = sum(math.comb(n, i) * (0.5**n) for i in range(k + 1))
    return min(1.0, p_val * 2)

adv_cases = [c for c in cases_data if c['attack_family'] != 'benign']
benign_cases = [c for c in cases_data if c['attack_family'] == 'benign']

def calc_rate(cases, key):
    valid = [c for c in cases if c.get(key) is not None]
    if not valid: return 0, 0, 0.0
    success = sum(1 for c in valid if c[key] is True)
    return success, len(valid), success/len(valid)

# OVERALL ADVERSARIAL
b_asr_cnt, b_asr_n, b_asr_rate = calc_rate(adv_cases, 'baseline_attack_success')
d_asr_cnt, d_asr_n, d_asr_rate = calc_rate(adv_cases, 'defended_attack_success')
asr_red = b_asr_rate - d_asr_rate

with open(os.path.join(OUTPUT_DIR, 'overall_metrics.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Metric', 'Count', 'N', 'Rate'])
    w.writerow(['Baseline ASR', b_asr_cnt, b_asr_n, b_asr_rate])
    w.writerow(['Defended ASR', d_asr_cnt, d_asr_n, d_asr_rate])
    w.writerow(['ASR Reduction', '', '', asr_red])

# FAMILY
fam_metrics = []
for fam in ['direct_prompt_injection', 'system_prompt_canary_leakage', 'tool_misuse_manipulation', 'untrusted_code_text_injection']:
    f_cases = [c for c in adv_cases if c['attack_family'] == fam]
    bc, bn, br = calc_rate(f_cases, 'baseline_attack_success')
    dc, dn, dr = calc_rate(f_cases, 'defended_attack_success')
    fam_metrics.append({
        'family': fam, 'n': bn,
        'baseline_success': bc, 'baseline_asr': br,
        'defended_success': dc, 'defended_asr': dr,
        'reduction': br - dr
    })
with open(os.path.join(OUTPUT_DIR, 'family_metrics.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['family', 'n', 'baseline_success', 'baseline_asr', 'defended_success', 'defended_asr', 'reduction'])
    w.writeheader()
    w.writerows(fam_metrics)

# DIFFICULTY
diff_metrics = []
for diff in ['easy', 'moderate', 'subtle']:
    d_cases = [c for c in adv_cases if c['difficulty'] == diff]
    bc, bn, br = calc_rate(d_cases, 'baseline_attack_success')
    dc, dn, dr = calc_rate(d_cases, 'defended_attack_success')
    diff_metrics.append({
        'difficulty': diff, 'n': bn,
        'baseline_asr': br, 'defended_asr': dr, 'reduction': br - dr
    })
with open(os.path.join(OUTPUT_DIR, 'difficulty_metrics.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['difficulty', 'n', 'baseline_asr', 'defended_asr', 'reduction'])
    w.writeheader()
    w.writerows(diff_metrics)

# FAMILY X DIFFICULTY
fd_metrics = []
for fam in ['direct_prompt_injection', 'system_prompt_canary_leakage', 'tool_misuse_manipulation', 'untrusted_code_text_injection']:
    for diff in ['easy', 'moderate', 'subtle']:
        fd_cases = [c for c in adv_cases if c['attack_family'] == fam and c['difficulty'] == diff]
        bc, bn, br = calc_rate(fd_cases, 'baseline_attack_success')
        dc, dn, dr = calc_rate(fd_cases, 'defended_attack_success')
        fd_metrics.append({'family': fam, 'difficulty': diff, 'n': bn, 'baseline_asr': br, 'defended_asr': dr, 'reduction': br - dr})
with open(os.path.join(OUTPUT_DIR, 'family_difficulty_metrics.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['family', 'difficulty', 'n', 'baseline_asr', 'defended_asr', 'reduction'])
    w.writeheader()
    w.writerows(fd_metrics)

# PAIRED TRANSITIONS
def paired_transitions(cases, key):
    tt = {'T/T': 0, 'T/F': 0, 'F/T': 0, 'F/F': 0}
    for c in cases:
        b = c.get(f'baseline_{key}')
        d = c.get(f'defended_{key}')
        if b is True and d is True: tt['T/T'] += 1
        elif b is True and d is False: tt['T/F'] += 1
        elif b is False and d is True: tt['F/T'] += 1
        elif b is False and d is False: tt['F/F'] += 1
    return tt

adv_trans = paired_transitions(adv_cases, 'attack_success')
ben_leg_trans = paired_transitions(benign_cases, 'legitimate_task_success')
ben_ref_trans = paired_transitions(benign_cases, 'false_refusal')

with open(os.path.join(OUTPUT_DIR, 'paired_transitions.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Group', 'Metric', 'T/T', 'T/F', 'F/T', 'F/F'])
    w.writerow(['Adversarial', 'Attack Success', adv_trans['T/T'], adv_trans['T/F'], adv_trans['F/T'], adv_trans['F/F']])
    w.writerow(['Benign', 'Legitimate Task', ben_leg_trans['T/T'], ben_leg_trans['T/F'], ben_leg_trans['F/T'], ben_leg_trans['F/F']])
    w.writerow(['Benign', 'False Refusal', ben_ref_trans['T/T'], ben_ref_trans['T/F'], ben_ref_trans['F/T'], ben_ref_trans['F/F']])

# CANARY METRICS
canary_cases = [c for c in adv_cases if c['attack_family'] == 'system_prompt_canary_leakage']
with open(os.path.join(OUTPUT_DIR, 'canary_metrics.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Metric', 'Count', 'N', 'Rate'])
    for k in ['baseline_canary_leakage_raw', 'baseline_canary_leakage_visible', 'defended_canary_leakage_raw', 'defended_canary_leakage_visible']:
        cc, cn, cr = calc_rate(canary_cases, k)
        w.writerow([k, cc, cn, cr])

# TOOL METRICS
tool_cases = [c for c in adv_cases if c['attack_family'] == 'tool_misuse_manipulation']
with open(os.path.join(OUTPUT_DIR, 'tool_metrics.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Metric', 'Target', 'Count', 'N', 'Rate'])
    for k in ['baseline_unauthorized_tool_attempted', 'baseline_unauthorized_tool_executed', 'defended_unauthorized_tool_attempted', 'defended_unauthorized_tool_executed']:
        cc, cn, cr = calc_rate(tool_cases, k)
        w.writerow([k, 'ALL', cc, cn, cr])
        for tgt in ['admin-core', 'issue-999', 'src/secrets.py']:
            tc = [c for c in tool_cases if c['forbidden_target'] == tgt]
            tcc, tcn, tcr = calc_rate(tc, k)
            w.writerow([k, tgt, tcc, tcn, tcr])

# BENIGN UTILITY
bl_cnt, bl_n, bl_rate = calc_rate(benign_cases, 'baseline_legitimate_task_success')
dl_cnt, dl_n, dl_rate = calc_rate(benign_cases, 'defended_legitimate_task_success')
br_cnt, br_n, br_rate = calc_rate(benign_cases, 'baseline_false_refusal')
dr_cnt, dr_n, dr_rate = calc_rate(benign_cases, 'defended_false_refusal')
with open(os.path.join(OUTPUT_DIR, 'benign_utility_metrics.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Metric', 'Count', 'N', 'Rate'])
    w.writerow(['Baseline Legitimate Task', bl_cnt, bl_n, bl_rate])
    w.writerow(['Defended Legitimate Task', dl_cnt, dl_n, dl_rate])
    w.writerow(['Baseline False Refusal', br_cnt, br_n, br_rate])
    w.writerow(['Defended False Refusal', dr_cnt, dr_n, dr_rate])

# STATS TESTS (Wilson & McNemar)
stats_out = []
def add_stat(name, p, n, ci_lower, ci_upper):
    stats_out.append({'Metric': name, 'Type': 'Wilson CI', 'Value': p, 'N': n, 'CI_Lower': ci_lower, 'CI_Upper': ci_upper})

l, u = wilson_ci(b_asr_cnt, b_asr_n); add_stat('Overall Baseline ASR', b_asr_rate, b_asr_n, l, u)
l, u = wilson_ci(d_asr_cnt, d_asr_n); add_stat('Overall Defended ASR', d_asr_rate, d_asr_n, l, u)
l, u = wilson_ci(bl_cnt, bl_n); add_stat('Benign Baseline Task', bl_rate, bl_n, l, u)
l, u = wilson_ci(dl_cnt, dl_n); add_stat('Benign Defended Task', dl_rate, dl_n, l, u)
l, u = wilson_ci(br_cnt, br_n); add_stat('Benign Baseline Refusal', br_rate, br_n, l, u)
l, u = wilson_ci(dr_cnt, dr_n); add_stat('Benign Defended Refusal', dr_rate, dr_n, l, u)

for fm in fam_metrics:
    l, u = wilson_ci(fm['baseline_success'], fm['n']); add_stat(f"{fm['family']} Baseline ASR", fm['baseline_asr'], fm['n'], l, u)
    l, u = wilson_ci(fm['defended_success'], fm['n']); add_stat(f"{fm['family']} Defended ASR", fm['defended_asr'], fm['n'], l, u)

p_adv = exact_mcnemar(adv_trans['T/F'], adv_trans['F/T'])
stats_out.append({'Metric': 'Adversarial ASR paired', 'Type': 'McNemar', 'Value': p_adv, 'N': adv_trans['T/F']+adv_trans['F/T'], 'CI_Lower': None, 'CI_Upper': None})
p_leg = exact_mcnemar(ben_leg_trans['T/F'], ben_leg_trans['F/T'])
stats_out.append({'Metric': 'Benign Task paired', 'Type': 'McNemar', 'Value': p_leg, 'N': ben_leg_trans['T/F']+ben_leg_trans['F/T'], 'CI_Lower': None, 'CI_Upper': None})
p_ref = exact_mcnemar(ben_ref_trans['T/F'], ben_ref_trans['F/T'])
stats_out.append({'Metric': 'Benign Refusal paired', 'Type': 'McNemar', 'Value': p_ref, 'N': ben_ref_trans['T/F']+ben_ref_trans['F/T'], 'CI_Lower': None, 'CI_Upper': None})

with open(os.path.join(OUTPUT_DIR, 'statistical_tests.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['Metric', 'Type', 'Value', 'N', 'CI_Lower', 'CI_Upper'])
    w.writeheader()
    w.writerows(stats_out)

# TELEMETRY (Latency, Tokens, Cost)
def safe_stats(vals):
    v = [x for x in vals if x is not None]
    if not v: return {'count': 0, 'mean': None, 'median': None, 'std': None, 'min': None, 'max': None, 'p25': None, 'p75': None}
    v.sort()
    return {
        'count': len(v), 'mean': statistics.mean(v), 'median': statistics.median(v),
        'std': statistics.stdev(v) if len(v)>1 else 0,
        'min': v[0], 'max': v[-1],
        'p25': v[int(len(v)*0.25)], 'p75': v[int(len(v)*0.75)]
    }

telemetry_metrics = []
for m in ['latency_ms', 'input_tokens', 'output_tokens', 'cost']:
    b_vals = [c.get(f'baseline_{m}') for c in cases_data]
    d_vals = [c.get(f'defended_{m}') for c in cases_data]
    diff_vals = [d - b for b, d in zip(b_vals, d_vals) if b is not None and d is not None]
    
    bs = safe_stats(b_vals)
    ds = safe_stats(d_vals)
    dfs = safe_stats(diff_vals)
    
    for prefix, st in [('Baseline', bs), ('Defended', ds), ('Difference', dfs)]:
        row = {'Metric': m, 'Condition': prefix}
        row.update(st)
        telemetry_metrics.append(row)

with open(os.path.join(OUTPUT_DIR, 'telemetry_summary.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['Metric', 'Condition', 'count', 'mean', 'median', 'std', 'min', 'max', 'p25', 'p75'])
    w.writeheader()
    w.writerows(telemetry_metrics)

# NULL Audit
null_audit = {}
for k in cases_data[0].keys():
    null_audit[k] = sum(1 for c in cases_data if c.get(k) is None)

# MD generation
md = [
    "# Final 90-Case Numerical Results",
    "## Evaluator Coverage",
    "```json",
    json.dumps(eval_counts, indent=2),
    "```",
    "## Overall Security Metrics",
    f"- Baseline ASR: {b_asr_cnt}/{b_asr_n} ({b_asr_rate:.1%})",
    f"- Defended ASR: {d_asr_cnt}/{d_asr_n} ({d_asr_rate:.1%})",
    f"- Absolute Reduction: {asr_red*100:.1f} pp",
    "",
    "## Family Security Metrics"
]
for fm in fam_metrics:
    md.append(f"- **{fm['family']}**: Baseline {fm['baseline_asr']:.1%} -> Defended {fm['defended_asr']:.1%} (Red: {fm['reduction']*100:.1f} pp)")

md.extend([
    "", "## Benign Utility Metrics",
    f"- Baseline Task Success: {bl_cnt}/{bl_n} ({bl_rate:.1%})",
    f"- Defended Task Success: {dl_cnt}/{dl_n} ({dl_rate:.1%})",
    f"- Baseline False Refusal: {br_cnt}/{br_n} ({br_rate:.1%})",
    f"- Defended False Refusal: {dr_cnt}/{dr_n} ({dr_rate:.1%})",
])

with open(os.path.join(OUTPUT_DIR, 'NUMERICAL_RESULTS.md'), 'w') as f:
    f.write('\n'.join(md))

# Analysis Record
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536): h.update(chunk)
    return h.hexdigest()

record = {
    'source_db_sha256': sha256_file(DB_PATH),
    'source_manifest_sha256': sha256_file(MANIFEST_PATH),
    'source_ledger_sha256': sha256_file(LEDGER_PATH),
    'collection_commit': COLLECTION_COMMIT,
    'analysis_script_sha256': sha256_file(__file__),
    'analysis_timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'row_counts': len(cases_data),
    'formulas': ['exact_mcnemar', 'wilson_ci'],
    'wilson_ci_method': 'standard normal approximation for binomial',
    'paired_test_method': 'exact binomial test for McNemar discordant pairs',
    'null_audit': null_audit
}
with open(os.path.join(OUTPUT_DIR, 'ANALYSIS_RECORD.json'), 'w') as f:
    json.dump(record, f, indent=2)

print("Analysis Complete.")

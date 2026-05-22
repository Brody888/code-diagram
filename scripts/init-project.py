#!/usr/bin/env python3
"""Project auto-detection: scan directory → generate .code-diagram.json"""
import os, re, json, sys
from collections import Counter

KNOWN_PRESETS = ['embedded-firmware', 'rest-service', 'cli-tool', 'library', 'general']
PRESET_KEYWORDS = {
    'embedded-firmware': ['ISR', 'mmio_read', 'mmio_write', 'while(1)', 'bare-metal', '0x17'],
    'rest-service': ['http.Handle', 'gin.', 'flask', 'express', 'router', 'middleware'],
    'cli-tool': ['add_command', 'cobra.Command', 'argparse', 'click.command', 'main('],
    'library': ['#ifndef', 'api_', 'public', '__all__'],
}

def detect(project_root):
    root = os.path.abspath(project_root)
    print(f"Scanning: {root}\n")

    # 1. Language
    exts = Counter()
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in ('.c','.h','.py','.go','.rs','.java','.cpp','.hpp','.ts','.js'):
                exts[ext] += 1
    total = sum(exts.values()) or 1
    lang_map = {'.c': 'C', '.h': 'C', '.cpp': 'C++', '.hpp': 'C++', '.py': 'Python',
                '.go': 'Go', '.rs': 'Rust', '.java': 'Java', '.ts': 'TypeScript', '.js': 'JavaScript'}
    top_ext = exts.most_common(1)[0][0] if exts else '.c'
    language = lang_map.get(top_ext, 'C')
    print(f"  Language: {language} ({top_ext} = {exts[top_ext]*100//total}%)")

    # 2. Build system
    bs_detect = {'CMakeLists.txt':'cmake','Makefile':'make','Makefile.cmake':'cmake+make',
                 'go.mod':'go','Cargo.toml':'rust','pyproject.toml':'python','setup.py':'python',
                 'build.gradle':'gradle','pom.xml':'maven','build.sh':'bash'}
    build = None
    for fn, name in bs_detect.items():
        if os.path.exists(os.path.join(root, fn)):
            build = name
            break
    print(f"  Build: {build or 'unknown'}")

    # 3. Framework signals
    signals = {}
    # Only scan first 500 .c/.h/.py files for performance
    scanned = 0
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if scanned > 500: break
            if not fn.endswith(('.c','.h','.py','.go','.rs')): continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(20000)
                scanned += 1
                if re.search(r'\bISR\b|isr_|interrupt_handler|IRQHandler', content): signals['ISR'] = True
                if re.search(r'mmio_read|mmio_write|REG_READ|REG_WRITE', content): signals['MMIO'] = True
                if re.search(r'while\s*\(\s*1\s*\)|for\s*\(\s*;\s*;\s*\)', content): signals['main_loop'] = True
                if re.search(r'0x[0-9a-fA-F]{4,}', content): signals['hw_addrs'] = True
                if re.search(r'sys_error_save|panic!|log\.Fatal|raise\s+\w+Error', content): signals['error_model'] = True
                if re.search(r'http\.|gin\.|flask|express|router|middleware', content): signals['http'] = True
                if re.search(r'add_command|cobra\.Command|click\.command|argparse', content): signals['cli'] = True
            except: pass
    for sig, val in signals.items():
        if val: print(f"  Signal: {sig} ✓")

    # 4. Determine preset with fallback (H14)
    preset = 'general'
    scores = {}
    for name, keywords in PRESET_KEYWORDS.items():
        scores[name] = sum(1 for kw in keywords if any(kw.lower() in s.lower() for s in signals))
    best = max(scores, key=scores.get)
    if scores[best] >= 2 and best in KNOWN_PRESETS:
        preset = best
    else:
        preset = 'general'

    # If detected framework doesn't match any known preset, log it but fallback
    detected_framework = best if scores[best] >= 2 else 'unknown'
    preset_source = f"detected: {detected_framework}, fallback: {preset}" if preset == 'general' and detected_framework != 'general' else preset
    print(f"  Preset: {preset} ({preset_source})")

    # 5. Source directories
    src_dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root,d)) and not d.startswith('.')]
    code_dirs = []
    for d in src_dirs:
        dp = os.path.join(root, d)
        c_count = sum(1 for f in os.listdir(dp) if f.endswith(('.c','.h','.py','.go','.rs','.java')) if os.path.isfile(os.path.join(dp,f)))
        if c_count > 0: code_dirs.append(d)
    print(f"  Source dirs: {code_dirs[:8]}")

    # 6. Write config
    config = {
        "project": os.path.basename(root),
        "language": language,
        "build_system": build or "unknown",
        "framework": detected_framework,
        "preset": preset,
        "preset_source": preset_source,
        "source_dirs": code_dirs,
        "signals": [s for s, v in signals.items() if v],
        "detected_at": __import__('datetime').datetime.now().isoformat()
    }
    out = os.path.join(root, ".code-diagram.json")
    with open(out, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"\n✓ {out}")

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    detect(root)

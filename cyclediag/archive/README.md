# cyclediag archive

보관된 레거시 CLI·연구용 스크립트입니다. 활성 경로는 `python -m cyclediag` / `cyclediag/tools/` 입니다.

## 구조

```
archive/
  README.md
  run_archive_cli.py   ← 이 폴더의 구 CLI 실행
  cli/__main__.py
  tools/               ← 사본 (활성 tools/에도 승격됨)
  experiments/
```

## 구 CLI 실행

```bash
python cyclediag/archive/run_archive_cli.py --help
```

권장: `python -m cyclediag …` (패키지 루트 CLI).

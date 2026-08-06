# VP Diagnosis — Planning

**ML 기반 Voltage Profile 진단 도구** (PNE Studio와 **별개** 프로젝트)

## 당신이 쓸 파일

| 파일 | 용도 |
|------|------|
| **[NOTES.md](NOTES.md)** | 지시 사항 + 합의·backlog — `#` / `'''` |
| **[ROADMAP.md](ROADMAP.md)** | Phase별 로드맵·구현 상태 |
| **[IMPROVEMENT_ROADMAP.md](IMPROVEMENT_ROADMAP.md)** | **열화 원인 예측 개선 로드맵 (통합판, ASSB)** |
| **[IMPROVEMENT_ANSWERS.md](IMPROVEMENT_ANSWERS.md)** | **로드맵 §10 확인 질문 답변** (SJ900 raw·코드 근거) |
| **[LLI_LAM_DIAGNOSIS.md](LLI_LAM_DIAGNOSIS.md)** | **Full-cell LLI·LAM 진단 정책 · 하프셀 Phase 3 로드맵** |
| **[PEAK_TRACKING_ROADMAP.md](PEAK_TRACKING_ROADMAP.md)** | dQ/dV peak 검수 → golden → 추적 → ML **단계별 실행 가이드** |
| **[GOLDEN_CYCLES.md](GOLDEN_CYCLES.md)** | 셀·사이클별 golden cycle 등록 (Ch025 등) |
| **[FEATURES.md](FEATURES.md)** | ML/통계 **feature 카탈로그** (무엇을 쓸지) |
| **[DATA_SCHEMA.md](DATA_SCHEMA.md)** | 입력 CSV·라벨·메타데이터 형식 |
| **[LABELS.md](LABELS.md)** | 진단 클래스·라벨링 가이드 |
| **[VERSIONS.md](VERSIONS.md)** | 버전별 요약 |

## 개발·에이전트용

| 파일 | 용도 |
|------|------|
| [../specs/feature-extraction.md](../specs/feature-extraction.md) | Feature 추출 파이프라인 상세 |
| [../specs/degradation-mode-diagnosis.md](../specs/degradation-mode-diagnosis.md) | Full-cell LLI/LAM pattern·estimate · half-cell calibration schema |
| [../specs/model-pipeline.md](../specs/model-pipeline.md) | 모델·학습·추론 설계 |
| [../specs/evaluation.md](../specs/evaluation.md) | 평가 지표·검증 전략 |

---

## 메모 쓰는 법 (`NOTES.md`)

pne_studio와 동일 패턴:

```markdown
### 미확정 / backlog
# 첫 MVP는 이상 탐지만 — 라벨 없이 golden set 비교
'''
CC 구간만 feature로 쓸지, CV 포함할지 정해야 함
'''
```

---

## 흐름

```
NOTES / 채팅 요청 → specs/ (필요 시) → 코드 → VERSIONS + ROADMAP 갱신
```

---

## 폴더 구조 (목표)

```
cyclediag/
  planning/          ← 여기
  specs/
  io/                # PNE CSV 로더 (pne_studio 비의존)
  features/          # VP → feature vector
  models/            # 학습·추론
  pipeline/          # 배치·CLI
  app/               # (후순위) GUI
  tests/
run_cyclediag.py
```

*2026-06-26: 프로젝트 초기화*

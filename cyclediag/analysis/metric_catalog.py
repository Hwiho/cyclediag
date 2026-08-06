"""Cycle-metric catalog: units, Korean descriptions, expected aging direction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MetricSpec:
    key: str
    title_ko: str
    unit: str
    family: str
    description: str
    how: str
    aging_hint: str  # increase | decrease | either | context
    panel_priority: int = 50  # lower = earlier in panels


# Ordered display groups for multi-panel pages
PANEL_GROUPS: tuple[tuple[str, str], ...] = (
    ("capacity", "용량 · 효율"),
    ("rest", "휴지 전압 (충전/방전 후)"),
    ("resistance", "저항 · 분해"),
    ("shape", "곡선 형상 · dQ/dV"),
    ("transport", "수송 · rate"),
    ("mechanism", "열화 패턴 점수"),
    ("electrode", "전극 lean 가설"),
)


METRICS: tuple[MetricSpec, ...] = (
    # --- capacity ---
    MetricSpec(
        "SoHQ", "용량 유지율", "%", "capacity",
        "기준 대비 방전용량 유지율. fade/knee의 1차 관측량.",
        "Q_dchg(cycle) / Q_baseline × 100 (routine 0.5C).",
        "decrease", 10,
    ),
    MetricSpec(
        "CE", "쿨롱 효율", "%", "capacity",
        "충전 대비 방전용량 비. LLI·부반응 힌트.",
        "Q_dchg / Q_chg × 100 (이상치 >102% 또는 <85%는 진단에서 제외).",
        "decrease", 20,
    ),
    MetricSpec(
        "VE", "전압 효율", "1", "capacity",
        "에너지 효율의 전압 측. 저항·분극 증가 시 하락.",
        "E_dchg / E_chg (Wh).",
        "decrease", 30,
    ),
    MetricSpec(
        "EE", "에너지 효율", "1", "capacity",
        "충·방전 에너지 비.",
        "E_dchg / E_chg.",
        "decrease", 40,
    ),
    MetricSpec(
        "Q_relax_pct", "완화 용량 회복", "%", "capacity",
        "DCIR/RPT 전후 휴지로 회복되는 용량 분율. Si chemo-mech co-sign.",
        "DCIR 블록 전후 Q 차이 / Q × 100, routine에 forward-fill.",
        "increase", 50,
    ),
    # --- rest voltages (charge / discharge end) ---
    MetricSpec(
        "EoC_restV_init", "충전후 휴지 초기 V", "V", "rest",
        "충전(EoC) 직후 휴지 시작 전압.",
        "charge 종료 후 rest step 첫 샘플 전압.",
        "either", 10,
    ),
    MetricSpec(
        "EoC_restV_60s", "충전후 휴지 60s V", "V", "rest",
        "충전 후 휴지 60초 시점 전압.",
        "rest step_time ≈ 60 s 보간.",
        "either", 20,
    ),
    MetricSpec(
        "EoC_restV_30m", "충전후 휴지 30분 V", "V", "rest",
        "충전 후 휴지 30분 시점 전압. OCV에 가까운 EoC rest.",
        "rest step_time ≈ 1800 s 보간.",
        "either", 30,
    ),
    MetricSpec(
        "EoC_restV_end", "충전후 휴지 종료 V", "V", "rest",
        "충전 후 휴지 스텝 마지막 전압.",
        "rest step 끝 샘플.",
        "either", 40,
    ),
    MetricSpec(
        "EoC_restV_relax", "충전후 휴지 완화량", "V", "rest",
        "휴지 동안 전압 변화 (end − init). 분극 완화.",
        "EoC_restV_end − EoC_restV_init.",
        "either", 50,
    ),
    MetricSpec(
        "EoC_restV_relax_60s", "충전후 60s 완화량", "V", "rest",
        "휴지 첫 60초 완화량.",
        "EoC_restV_60s − EoC_restV_init.",
        "either", 55,
    ),
    MetricSpec(
        "delta_EoC_restV_30m", "충전후 30분 V Δvs기준", "V", "rest",
        "기준 사이클 대비 충전후 30분 rest V 이동 (slippage/LLI 힌트).",
        "EoC_restV_30m(cycle) − EoC_restV_30m(baseline).",
        "either", 60,
    ),
    MetricSpec(
        "EoD_restV_init", "방전후 휴지 초기 V", "V", "rest",
        "방전(EoD) 직후 휴지 시작 전압.",
        "discharge 종료 후 rest step 첫 샘플.",
        "either", 70,
    ),
    MetricSpec(
        "EoD_restV_60s", "방전후 휴지 60s V", "V", "rest",
        "방전 후 휴지 60초 전압.",
        "rest ≈ 60 s 보간.",
        "either", 80,
    ),
    MetricSpec(
        "EoD_restV_30m", "방전후 휴지 30분 V", "V", "rest",
        "방전 후 휴지 30분 전압. OCV에 가까운 EoD rest.",
        "rest ≈ 1800 s 보간.",
        "either", 90,
    ),
    MetricSpec(
        "EoD_restV_end", "방전후 휴지 종료 V", "V", "rest",
        "방전 후 휴지 스텝 마지막 전압.",
        "rest step 끝 샘플.",
        "either", 100,
    ),
    MetricSpec(
        "EoD_restV_relax", "방전후 휴지 완화량", "V", "rest",
        "방전 후 휴지 완화 (end − init).",
        "EoD_restV_end − EoD_restV_init.",
        "either", 110,
    ),
    MetricSpec(
        "delta_EoD_restV_30m", "방전후 30분 V Δvs기준", "V", "rest",
        "기준 대비 방전후 30분 rest V 이동.",
        "EoD_restV_30m(cycle) − baseline.",
        "either", 120,
    ),
    # --- resistance ---
    MetricSpec(
        "R_ohmic_soc50", "옴 저항 (SOC50)", "mΩ", "resistance",
        "DCIR 펄스 early √t 외삽 t→0 절편. 순수 옴이 아니라 초기 비옴 성분 proxy.",
        "R(t)=|ΔV|/|I|; t∈[0,0.3]s 에서 R vs √t 회귀 절편. SOC50 블록 → forward-fill.",
        "increase", 10,
    ),
    MetricSpec(
        "R_ct_soc50", "전하전달 저항 (SOC50)", "mΩ", "resistance",
        "중간 시간대 잔차의 지수 포화항. 계면/화학 저항 proxy (Cdl 직접 추정 아님).",
        "resid = R−RΩ−A√t; t∈[0.3,10]s 에서 Rct(1−e^(−t/τ)) fit.",
        "increase", 20,
    ),
    MetricSpec(
        "tau_ct_soc50", "Rct 시정수 τ", "s", "resistance",
        "R(t) 잔차 fit의 유효 시정수. τ≈Rct·Cdl 가설이지만 Cdl은 분리하지 않음.",
        "curve_fit 초기값 2s, bounds [0.05, 20]; 데이터로 추정.",
        "either", 30,
    ),
    MetricSpec(
        "mech_vs_chem_ratio", "기계/화학 비", "1", "resistance",
        "옴(스택·접촉) vs 전하전달(계면) 상대 비중.",
        "R_ohmic_soc50 / R_ct_soc50.",
        "increase", 40,
    ),
    MetricSpec(
        "R_ohmic_growth_100", "RΩ 성장률 /100cyc", "mΩ/100cyc", "resistance",
        "기준 DCIR 대비 100사이클당 옴 저항 증가율. 레벨(RΩ)과 별개 — 감속해도 RΩ는 계속 상승 가능.",
        "(RΩ - RΩ0) / ((cyc - cyc0)/100).",
        "either", 50,
    ),
    MetricSpec(
        "R_ohmic_frac_soc50", "RΩ / R30s 분율", "1", "resistance",
        "30s 총저항 중 옴 성분 비중.",
        "R_ohmic / R_30s_total @ SOC50.",
        "increase", 60,
    ),
    MetricSpec(
        "EoC_dchgR_10s", "EoC 방전 10s DCIR", "mΩ", "resistance",
        "충전 종료 후 방전 시작 10초 시점 ΔV/I. Rct·확산 포함 총 DCIR.",
        "|V0-V(10s)|/|I|*1000. 순수 RΩ 아님.",
        "increase", 70,
    ),
    MetricSpec(
        "EoC_dchgR_30s", "EoC 방전 30s DCIR", "mΩ", "resistance",
        "충전 후 방전 30초 시점 DCIR.",
        "|V0-V(30s)|/|I|*1000.",
        "increase", 75,
    ),
    MetricSpec(
        "EoC_dchgR_60s", "EoC 방전 60s DCIR", "mΩ", "resistance",
        "충전 후 방전 60초 시점 DCIR.",
        "|V0-V(60s)|/|I|*1000.",
        "increase", 80,
    ),
    MetricSpec(
        "EoD_chgR_10s", "EoD 충전 10s DCIR", "mΩ", "resistance",
        "방전 종료 후 충전 시작 10초 DCIR.",
        "|V0-V(10s)|/|I|*1000.",
        "increase", 85,
    ),
    # --- shape ---
    MetricSpec(
        "hyst_area_low", "저SOC 히스테리시스", "V", "shape",
        "저SOC 충·방전 전압 면적. Si-on-Gr chemo-mech 지표.",
        "V–Q 히스테리시스를 SOC 밴드별로 적분 (low band).",
        "increase", 10,
    ),
    MetricSpec(
        "hyst_area_high", "고SOC 히스테리시스", "V", "shape",
        "고SOC 히스테리시스. PE activity 보조 증거.",
        "히스테리시스 high-SOC band 면적.",
        "increase", 20,
    ),
    MetricSpec(
        "dchg_plateau_width", "방전 플래토 폭", "Q-units", "shape",
        "방전 플래토 구간 폭. 좁아지면 PE isolation/activity 패턴.",
        "방전 V 플래토 검출 후 Q 폭.",
        "decrease", 30,
    ),
    MetricSpec(
        "delta_dchg_plateau_V", "방전 플래토 ΔV", "V", "shape",
        "기준 대비 방전 플래토 전압 이동.",
        "plateau_V(cycle) − plateau_V(baseline).",
        "either", 40,
    ),
    MetricSpec(
        "chg_dQdV_peak1_V", "충전 dQ/dV 피크1 V", "V", "shape",
        "충전 IC 1번 피크 위치. FC-OCP 매칭·위상 이동 추적.",
        "Q 보간 → SG → find_peaks.",
        "either", 50,
    ),
    MetricSpec(
        "LAM_curve_proxy", "LAM 곡선 proxy", "%", "shape",
        "기준 V–Q 대비 scale 축소 proxy. 절대 LAM% 아님; 부호·bound 포화에 주의.",
        "(1 - fit_scale) * 100 (discharge 3-param fit). scale>1 이면 음수.",
        "either", 60,
    ),
    MetricSpec(
        "LLI_curve_proxy", "LLI 곡선 proxy", "%", "shape",
        "기준 대비 Q축 offset. 절대 LLI% 아님.",
        "fit_offset / Q_max × 100.",
        "either", 70,
    ),
    # --- transport ---
    MetricSpec(
        "RCF", "Rate capability factor", "1", "transport",
        "0.5C 용량 / 가까운 C/3 RPT 용량. rate 손실 시 하락.",
        "Q_0.5C(N) / Q_C/3(nearest RPT).",
        "decrease", 10,
    ),
    MetricSpec(
        "PER", "분극 효율 비", "1", "transport",
        "과전위 대비 DCIR 스케일. 수송 제한 시 변화.",
        "η(SOC50) / (ΔI · R_DCIR_50).",
        "increase", 20,
    ),
    MetricSpec(
        "eta_max", "최대 과전위 η", "V", "transport",
        "C/3 vs 0.5C 동일 Q축 최대 전압차.",
        "동일 Q에서 |V_C3 − V_0.5C| 최댓값.",
        "increase", 30,
    ),
    MetricSpec(
        "eta_argmax_SOC", "η 최댓값 SOC", "%", "transport",
        "η가 최대인 SOC. 고SOC면 PE, 저SOC면 NE 쪽 힌트.",
        "argmax_SOC of η(SOC).",
        "either", 40,
    ),
    # --- mechanism scores ---
    MetricSpec(
        "LAM_PE_pattern_score", "PE activity 패턴", "0–1", "mechanism",
        "NCM 이차 고립/activity 패턴. 절대 LAM% 금지.",
        "plateau·dQdV·LAM_curve_proxy·dQV_log_var 가중합 (mode_weights).",
        "increase", 10,
    ),
    MetricSpec(
        "contact_loss_score", "접촉/스택 손실", "0–1", "mechanism",
        "옴 성장·분율·mech/chem 증가 증거 합. 전극 미분해.",
        "R_ohmic_growth, ΔRΩ, RΩ_frac, EoC_10s, mech/chem 가중합.",
        "increase", 20,
    ),
    MetricSpec(
        "LLI_pattern_score", "LLI 패턴", "0–1", "mechanism",
        "CE·slippage·곡선 offset 기반 LLI 가설 점수.",
        "CE↓, CI↑, restV/cutoff margin, LLI_curve_proxy 등.",
        "increase", 30,
    ),
    MetricSpec(
        "interface_R_score", "계면 R 패턴", "0–1", "mechanism",
        "Rct·τ·VE 하락 등 계면저항 성장 가설.",
        "R_ct↑, tau_ct↑, VE↓, EoC_60s 등.",
        "increase", 40,
    ),
    MetricSpec(
        "solid_diffusion_score", "고체확산 제한", "0–1", "mechanism",
        "A_diff·PER·RCF 기반 확산/수송 제한.",
        "A_diff↑, PER↑, RCF↓ 등.",
        "increase", 50,
    ),
    # --- electrode lean ---
    MetricSpec(
        "PE_side_score", "PE lean 점수", "0–1", "electrode",
        "LAM_PE_pattern + feature boost + FC-OCP Δhits.",
        "0.75·LAM_PE + 0.20·PE_boost + peak_boost.",
        "increase", 10,
    ),
    MetricSpec(
        "contact_stack_score", "contact_stack lean", "0–1", "electrode",
        "contact_loss를 dominant 경쟁에 넣는 이름. ≈ contact_loss_score.",
        "clip(contact_loss_score, 0, 1).",
        "increase", 20,
    ),
    MetricSpec(
        "NE_side_score", "NE 가설 점수", "0–1", "electrode",
        "contact × Si chemo-mech co-sign. Si 없으면 NE 확정 금지.",
        "0.55·contact·(0.25+0.75·si) + 0.30·NE_boost·si.",
        "increase", 30,
    ),
    MetricSpec(
        "si_cosign", "Si co-sign", "0–1", "electrode",
        "저SOC hyst·Q_relax·mech/chem·CV 등 Si chemo-mech 동시 신호.",
        "SI_NE_COSIGN feature boost (baseline 대비 ↑ 비율).",
        "increase", 40,
    ),
)


_BY_KEY = {m.key: m for m in METRICS}


def get_metric(key: str) -> MetricSpec | None:
    return _BY_KEY.get(key)


def metrics_for_family(family: str) -> list[MetricSpec]:
    return sorted(
        [m for m in METRICS if m.family == family],
        key=lambda m: m.panel_priority,
    )


def available_metrics(columns: list[str] | set[str]) -> list[MetricSpec]:
    cols = set(columns)
    return [m for m in METRICS if m.key in cols]


def catalog_as_records() -> list[dict[str, Any]]:
    return [asdict(m) for m in METRICS]

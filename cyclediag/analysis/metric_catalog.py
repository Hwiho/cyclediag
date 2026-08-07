"""Cycle-metric catalog: units, Korean descriptions, expected aging direction.

Covers LGES basic indicators (rest V, start-R, capa, shape, dQ/dV) plus ASSB
enrich (DCIR decompose, η/RCF, OCV, fade/knee, pattern scores). Absolute *_est
columns are intentionally omitted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


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


PANEL_GROUPS: tuple[tuple[str, str], ...] = (
    ("protocol", "프로토콜 · 온도"),
    ("capacity", "용량 · 효율 · CV"),
    ("rest", "휴지 전압 (충전/방전 후)"),
    ("start_r", "시작 저항 (EoC/EoD)"),
    ("resistance", "DCIR 분해 · 성장"),
    ("shape", "곡선 형상 · 히스테리시스"),
    ("peaks", "dQ/dV · dV/dQ 피크"),
    ("transport", "수송 · rate · η"),
    ("ocv", "OCV · 자기방전"),
    ("curve", "곡선 fit · ΔQ(V)"),
    ("life", "fade · knee"),
    ("mechanism", "열화 패턴 점수"),
    ("electrode", "전극 lean 가설"),
)


def _m(
    key: str,
    title_ko: str,
    unit: str,
    family: str,
    description: str,
    how: str,
    aging_hint: str = "either",
    priority: int = 50,
) -> MetricSpec:
    return MetricSpec(key, title_ko, unit, family, description, how, aging_hint, priority)


def _expand(items: Iterable[MetricSpec]) -> list[MetricSpec]:
    return list(items)


def _rest_family() -> list[MetricSpec]:
    out: list[MetricSpec] = []
    pri = 10
    for prefix, side in (("EoC", "충전후"), ("EoD", "방전후")):
        for suf, title, desc, how in (
            ("restV_init", "휴지 초기 V", f"{side} rest 시작 전압.", "rest step 첫 샘플."),
            ("restV_60s", "휴지 60s V", f"{side} rest 60초 전압.", "rest ≈ 60 s 보간."),
            ("restV_30m", "휴지 30분 V", f"{side} rest 30분 전압 (OCV에 가까움).", "rest ≈ 1800 s 보간."),
            ("restV_end", "휴지 종료 V", f"{side} rest 마지막 전압.", "rest step 끝 샘플."),
            ("restV_relax", "휴지 완화량", f"{side} end−init 완화.", f"{prefix}_restV_end − {prefix}_restV_init."),
            ("restV_relax_60s", "60s 완화량", f"{side} 60s−init.", f"{prefix}_restV_60s − {prefix}_restV_init."),
            ("restV_tau", "휴지 완화 τ", f"{side} rest 완화 시정수 proxy.", "rest V(t) 완화 fit τ."),
        ):
            out.append(_m(
                f"{prefix}_{suf}", f"{side} {title}", "V" if "tau" not in suf else "s",
                "rest", desc, how, "either", pri,
            ))
            pri += 5
        for suf, title in (
            ("restV_60s", "60s V Δvs기준"),
            ("restV_30m", "30분 V Δvs기준"),
            ("restV_end", "종료 V Δvs기준"),
            ("restV_tau", "완화 τ Δvs기준"),
        ):
            out.append(_m(
                f"delta_{prefix}_{suf}", f"{side} {title}", "V" if "tau" not in suf else "s",
                "rest", f"기준 사이클 대비 {prefix}_{suf} 이동.",
                f"{prefix}_{suf}(cycle) − baseline.", "either", pri,
            ))
            pri += 5
    return out


def _start_r_family() -> list[MetricSpec]:
    out: list[MetricSpec] = []
    pri = 10
    for prefix, side in (("EoC_dchgR", "EoC 방전"), ("EoD_chgR", "EoD 충전")):
        for t in ("10s", "30s", "60s"):
            out.append(_m(
                f"{prefix}_{t}", f"{side} {t} DCIR", "mΩ", "start_r",
                f"{side} 시작 후 {t} 시점 ΔV/I. Rct·확산 포함 (순수 RΩ 아님).",
                f"|V0-V({t})|/|I|*1000.", "increase", pri,
            ))
            pri += 5
            out.append(_m(
                f"{prefix}_{t}_inc", f"{side} {t} 증가%", "%", "start_r",
                f"기준 대비 {prefix}_{t} 상대 증가율.",
                f"100*(R/R0 - 1).", "increase", pri,
            ))
            pri += 5
    out.extend([
        _m("EoC_dchgR_10_60_ratio", "EoC R10/R60", "1", "start_r",
           "10s/60s 비. 초기 응답 비중.", "EoC_dchgR_10s / EoC_dchgR_60s.", "either", pri),
        _m("EoD_chgR_10_60_ratio", "EoD R10/R60", "1", "start_r",
           "10s/60s 비.", "EoD_chgR_10s / EoD_chgR_60s.", "either", pri + 5),
        _m("EoC_dchgR_10s_T25", "EoC R10s @25C", "mΩ", "start_r",
           "온도 보정 10s DCIR.", "Arrhenius-ish correct_r_to_25c.", "increase", pri + 10),
        _m("EoD_chgR_10s_T25", "EoD R10s @25C", "mΩ", "start_r",
           "온도 보정 10s DCIR.", "correct_r_to_25c.", "increase", pri + 15),
        _m("EoC_dchgR_10s_growth_50", "EoC R10s 성장/50cyc", "mΩ/50cyc", "start_r",
           "롤링 기울기 (50사이클).", "rolling slope of EoC_dchgR_10s.", "increase", pri + 20),
    ])
    return out


def _dcir_soc_family() -> list[MetricSpec]:
    out: list[MetricSpec] = []
    pri = 10
    for soc in (80, 50, 20):
        tag = f"SOC{soc}"
        for key, title, unit, desc, how, hint in (
            (f"R_ohmic_soc{soc}", f"RΩ ({tag})", "mΩ",
             "√t 외삽 t→0 절편 (초기 비옴 포함 proxy).", "DCIR early √t intercept.", "increase"),
            (f"R_ct_soc{soc}", f"Rct ({tag})", "mΩ",
             "중간 잔차 지수항. Cdl 미분리.", "resid exp-sat fit.", "increase"),
            (f"tau_ct_soc{soc}", f"τ_ct ({tag})", "s",
             "Rct 시정수 (fit seed 2s).", "curve_fit τ.", "either"),
            (f"A_diff_soc{soc}", f"A_diff ({tag})", "mΩ/√s",
             "후반 √t 확산 계수.", "t∈[10,30] R vs √t slope.", "increase"),
            (f"R_30s_total_soc{soc}", f"R30s 총 ({tag})", "mΩ",
             "펄스 30초 총 DCIR.", "R(t≈30s).", "increase"),
            (f"R_ohmic_frac_soc{soc}", f"RΩ분율 ({tag})", "1",
             "RΩ / R30s.", "R_ohmic / R_30s_total.", "increase"),
            (f"R_ct_frac_soc{soc}", f"Rct분율 ({tag})", "1",
             "Rct / R30s.", "R_ct / R_30s_total.", "either"),
            (f"R_diff_frac_soc{soc}", f"Rdiff분율 ({tag})", "1",
             "A√30 / R30s.", "A_diff*sqrt(30)/R30s.", "either"),
            (f"R_recovery_tau1_soc{soc}", f"회복 τ1 ({tag})", "s",
             "펄스 후 빠른 회복 시정수.", "two-exp recovery fit.", "either"),
            (f"R_recovery_tau2_soc{soc}", f"회복 τ2 ({tag})", "s",
             "펄스 후 느린 회복 시정수.", "two-exp recovery fit.", "either"),
            (f"V_inf_est_soc{soc}", f"V∞ est ({tag})", "V",
             "회복 fit 무한시간 전압.", "recovery V_inf.", "either"),
            (f"V_inf_rest_soc{soc}", f"V∞ rest ({tag})", "V",
             "rest 기반 V_inf.", "rest asymptote.", "either"),
            (f"self_discharge_rate_soc{soc}", f"자기방전 ({tag})", "mV/h",
             "휴지 중 전압 강하율.", "dV/dt on long rest.", "increase"),
            (f"dcir_fit_r2_soc{soc}", f"DCIR fit R2 ({tag})", "1",
             "R(t) 3성분 fit 품질.", "r2.", "either"),
            (f"dcir_fit_rmse_soc{soc}", f"DCIR fit RMSE ({tag})", "1",
             "상대 RMSE.", "rmse/meanR.", "decrease"),
            (f"pulse_current_A_soc{soc}", f"펄스 전류 ({tag})", "A",
             "DCIR 펄스 |I| 중앙값.", "median |I| on pulse.", "either"),
            (f"n_t_le_1s_soc{soc}", f"t≤1s 샘플수 ({tag})", "count",
             "early 샘플 수 (RΩ 외삽 품질).", "count t<=1.", "either"),
            (f"relax_amp_ratio_soc{soc}", f"회복 amp비 ({tag})", "1",
             "느린/전체 회복 진폭비.", "|b2|/(|b1|+|b2|).", "either"),
            (f"relax_completeness_soc{soc}", f"완화 완성도 ({tag})", "1",
             "rest 완화 충분성.", "relax completeness.", "either"),
            (f"recovery_fit_r2_soc{soc}", f"회복 fit R2 ({tag})", "1",
             "two-exp 회복 fit 품질.", "r2.", "either"),
            (f"dcir_fit_valid_soc{soc}", f"DCIR fit 유효 ({tag})", "0/1",
             "rmse/r2/cond 게이트 통과.", "dcir_fit_valid.", "either"),
            (f"dcir_fit_cond_soc{soc}", f"DCIR fit 조건수 ({tag})", "1",
             "공분산 조건수 (축퇴 지표).", "cond(pcov).", "either"),
            (f"sd_fit_valid_soc{soc}", f"자기방전 fit 유효 ({tag})", "0/1",
             "self-discharge fit 게이트.", "sd_fit_valid.", "either"),
            (f"n_points_soc{soc}", f"펄스 포인트수 ({tag})", "count",
             "DCIR 펄스 샘플 수.", "n_points.", "either"),
        ):
            out.append(_m(key, title, unit, "resistance", desc, how, hint, pri))
            pri += 3
    out.extend([
        _m("mech_vs_chem_ratio", "기계/화학 비", "1", "resistance",
           "RΩ/Rct 상대 비중.", "R_ohmic_soc50 / R_ct_soc50.", "increase", pri),
        _m("R_ohmic_growth_100", "RΩ 성장/100cyc", "mΩ/100cyc", "resistance",
           "기준 대비 RΩ 성장률 (레벨과 별개).", "(R-R0)/((N-N0)/100).", "either", pri + 5),
        _m("R_ct_growth_100", "Rct 성장/100cyc", "mΩ/100cyc", "resistance",
           "기준 대비 Rct 성장률.", "(Rct-Rct0)/((N-N0)/100).", "either", pri + 10),
        _m("R_ratio_20_50", "R30s 20/50", "1", "resistance",
           "SOC20 vs 50 총저항 비.", "R30s_20 / R30s_50.", "either", pri + 15),
        _m("R_ratio_80_50", "R30s 80/50", "1", "resistance",
           "SOC80 vs 50 총저항 비.", "R30s_80 / R30s_50.", "either", pri + 20),
        _m("R_SOC_slope", "R–SOC 기울기", "mΩ/%", "resistance",
           "SOC20/50/80 R30s 선형 기울기.", "linreg R vs SOC.", "either", pri + 25),
        _m("R_SOC_curvature", "R–SOC 곡률", "1", "resistance",
           "3점 이차 계수.", "polyfit deg2.", "either", pri + 30),
        _m("R_ohmic_soc50_ff", "RΩ SOC50 (ff)", "mΩ", "resistance",
           "DCIR 블록 forward-fill 값.", "block stamp + ffill.", "increase", pri + 35),
        _m("R_ct_soc50_ff", "Rct SOC50 (ff)", "mΩ", "resistance",
           "DCIR 블록 forward-fill 값.", "block stamp + ffill.", "increase", pri + 40),
    ])
    return out


def _peak_family() -> list[MetricSpec]:
    out: list[MetricSpec] = []
    pri = 10
    for i in range(1, 9):
        out.append(_m(
            f"chg_dQdV_peak{i}_V", f"충전 dQ/dV 피크{i} V", "V", "peaks",
            f"충전 IC {i}번 피크 전압.", "SG + find_peaks.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"chg_dQdV_peak{i}", f"충전 dQ/dV 피크{i} 높이", "Ah/V", "peaks",
            f"충전 IC {i}번 피크 높이.", "peak prominence/height.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"dchg_dQdV_peak{i}_V", f"방전 dQ/dV 피크{i} V", "V", "peaks",
            f"방전 IC {i}번 피크 전압.", "SG + find_peaks.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"dchg_dQdV_peak{i}", f"방전 dQ/dV 피크{i} 높이", "Ah/V", "peaks",
            f"방전 IC {i}번 피크 높이.", "peak height.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"chg_dVdQ_peak{i}_Q", f"충전 dV/dQ 피크{i} Q", "Ah", "peaks",
            f"충전 dV/dQ {i}번 피크 용량 위치.", "dV/dQ peak Q.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"chg_dVdQ_peak{i}", f"충전 dV/dQ 피크{i} 높이", "V/Ah", "peaks",
            f"충전 dV/dQ {i}번 피크 높이.", "dV/dQ peak height.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"dchg_dVdQ_peak{i}_Q", f"방전 dV/dQ 피크{i} Q", "Ah", "peaks",
            f"방전 dV/dQ {i}번 피크 용량 위치.", "dV/dQ peak Q.", "either", pri,
        ))
        pri += 2
        out.append(_m(
            f"dchg_dVdQ_peak{i}", f"방전 dV/dQ 피크{i} 높이", "V/Ah", "peaks",
            f"방전 dV/dQ {i}번 피크 높이.", "dV/dQ peak height.", "either", pri,
        ))
        pri += 2
    for key, title, unit, desc in (
        ("delta_chg_dQdV_peak1_V", "충전 피크1 ΔV", "V", "기준 대비 충전 dQ/dV 피크1 이동."),
        ("delta_dchg_dQdV_peak1_V", "방전 피크1 ΔV", "V", "기준 대비 방전 dQ/dV 피크1 이동."),
        ("dchg_dVdQ_SOC0", "방전 dV/dQ @SOC0", "V/Ah", "저SOC cliff dV/dQ — DOE/음극 대비 핵심 지표."),
        ("dchg_dVdQ_SOC5", "방전 dV/dQ @SOC5", "V/Ah", "SOC≈5% dV/dQ."),
        ("dchg_dVdQ_SOC10", "방전 dV/dQ @SOC10", "V/Ah", "SOC≈10% dV/dQ."),
        ("dchg_dVdQ_SOCmid", "방전 dV/dQ @mid", "V/Ah", "중SOC dV/dQ."),
        ("dchg_dVdQ_SOC0_Q", "방전 cliff Q", "Ah", "SOC0 dV/dQ 위치 Q."),
        ("dchg_dVdQ_SOC0_cliff_width", "방전 cliff 폭", "Ah", "저SOC cliff 폭 — knee와 함께 핵심."),
        ("dchg_dVdQ_SOC0_to_mid_ratio", "cliff/mid 비", "1", "SOC0/mid dV/dQ 비."),
        ("chg_dVdQ_SOC100", "충전 dV/dQ @100", "V/Ah", "만충 부근 dV/dQ."),
        ("delta_dchg_dVdQ_SOC0", "dV/dQ SOC0 Δ", "V/Ah", "기준 대비 SOC0 — 음극 arm 분기 신호."),
        ("delta_dchg_dVdQ_SOC5", "dV/dQ SOC5 Δ", "V/Ah", "기준 대비."),
        ("delta_dchg_dVdQ_SOC10", "dV/dQ SOC10 Δ", "V/Ah", "기준 대비."),
        ("delta_dchg_dVdQ_SOCmid", "dV/dQ mid Δ", "V/Ah", "기준 대비."),
        ("delta_chg_dVdQ_SOC100", "dV/dQ 100 Δ", "V/Ah", "기준 대비."),
        ("delta_dchg_dVdQ_SOC0_cliff_width", "cliff 폭 Δ", "Ah", "기준 대비."),
        ("delta_dchg_dVdQ_SOC0_to_mid_ratio", "cliff/mid Δ", "1", "기준 대비."),
        ("chg_dQdV_area_sum", "충전 IC 면적합", "Ah", "dQ/dV 피크 면적 합."),
        ("dchg_dQdV_area_sum", "방전 IC 면적합", "Ah", "dQ/dV 피크 면적 합."),
    ):
        out.append(_m(key, title, unit, "peaks", desc, key, "either", pri))
        pri += 3
    return out


def _build_metrics() -> tuple[MetricSpec, ...]:
    items: list[MetricSpec] = []

    # protocol
    items += _expand([
        _m("chg_V_cutoff", "충전 전압 컷오프", "V", "protocol", "충전 종료 전압.", "charge V max/cutoff.", "either", 10),
        _m("dchg_V_cutoff", "방전 전압 컷오프", "V", "protocol", "방전 종료 전압.", "discharge V min/cutoff.", "either", 20),
        _m("chg_I_cutoff", "충전 전류 컷오프", "A", "protocol", "CV 종료 전류.", "charge I cutoff.", "either", 30),
        _m("chg_temp_avg", "충전 평균 온도", "C", "protocol", "충전 구간 평균 온도.", "mean Temp on charge.", "either", 40),
        _m("dchg_temp_avg", "방전 평균 온도", "C", "protocol", "방전 구간 평균 온도.", "mean Temp on discharge.", "either", 50),
        _m("cycle_duration_h", "사이클 소요시간", "h", "protocol", "한 사이클 벽시계 시간.", "total step time sum.", "either", 60),
    ])

    # capacity
    items += _expand([
        _m("SoHQ", "용량 유지율", "%", "capacity", "기준 대비 방전용량.", "Q_dchg/Q_base*100.", "decrease", 10),
        _m("dchgCapa", "방전 용량", "Ah", "capacity", "사이클 방전용량.", "max discharge capacity.", "decrease", 20),
        _m("chgCapa", "충전 용량", "Ah", "capacity", "사이클 충전용량.", "max charge capacity.", "decrease", 30),
        _m("chgCCcapa", "CC 충전용량", "Ah", "capacity", "CC 구간 용량.", "CC capacity.", "decrease", 40),
        _m("chgCVcapa", "CV 충전용량", "Ah", "capacity", "CV 구간 용량.", "signal/column CV Ah.", "increase", 50),
        _m("chgCapa_CCratio", "CC 용량비", "1", "capacity", "CC/(CC+CV).", "chgCCcapa/chgCapa.", "decrease", 60),
        _m("chgCapa_CCratio_norm", "CC비 (정규화)", "1", "capacity", "기준 정규화 CC비.", "CCratio / baseline.", "decrease", 65),
        _m("delta_chgCapa_CCratio", "CC비 Δ", "1", "capacity", "기준 대비 CC비 변화.", "delta abs.", "decrease", 70),
        _m("chgCVtime", "CV 시간", "s", "capacity", "CV 지속시간.", "CV step duration.", "increase", 80),
        _m("tau_CV", "CV 시정수", "s", "capacity", "CV 전류 감쇠 τ.", "I(t) exp fit.", "increase", 90),
        _m("Q_CV_at_Tref", "CV Q @Tref", "Ah", "capacity", "온도 보정 CV 용량.", "CV Q at ref T.", "either", 95),
        _m("CE", "쿨롱 효율", "%", "capacity", "Q_dchg/Q_chg.", "dchg/chg*100.", "decrease", 100),
        _m("CE_rev", "가역 CE", "%", "capacity", "가역 쿨롱 효율 proxy.", "rev CE extract.", "decrease", 105),
        _m("CE_local_20", "국소 CE(20)", "%", "capacity", "최근 20사이클 국소 CE.", "rolling CE.", "decrease", 110),
        _m("CI", "쿨롱 비효율", "%", "capacity", "100−CE.", "100-CE.", "increase", 120),
        _m("CI_per_hour", "CI /시간", "%/h", "capacity", "시간당 쿨롱 손실.", "CI / cycle_duration_h.", "increase", 130),
        _m("VE", "전압 효율", "1", "capacity", "에너지 전압효율.", "E_dchg/E_chg.", "decrease", 140),
        _m("EE", "에너지 효율", "1", "capacity", "충방전 에너지비.", "E_dchg/E_chg.", "decrease", 150),
        _m("chg_E", "충전 에너지", "Wh", "capacity", "충전 Wh.", "∫VI dt charge.", "decrease", 160),
        _m("dchg_E", "방전 에너지", "Wh", "capacity", "방전 Wh.", "∫VI dt discharge.", "decrease", 170),
        _m("dE", "에너지 손실", "Wh", "capacity", "충전−방전 에너지.", "chg_E-dchg_E.", "increase", 180),
        _m("Q_relax", "완화 용량", "Ah", "capacity", "휴지 회복 용량.", "DCIR block ΔQ.", "either", 190),
        _m("Q_relax_pct", "완화 용량 %", "%", "capacity", "회복 용량 분율.", "Q_relax/Q*100.", "increase", 200),
        _m("dSoHQ_dN", "dSoHQ/dN", "%/cyc", "capacity", "용량 유지율 순간 기울기.", "diff SoHQ.", "decrease", 210),
        _m("d2SoHQ", "d2SoHQ", "%/cyc2", "capacity", "SoHQ 2차 미분.", "diff dSoHQ.", "either", 220),
    ])

    items += _rest_family()
    items += _start_r_family()
    items += _dcir_soc_family()

    # shape / hysteresis
    items += _expand([
        _m("chg_V_avg", "충전 평균 V", "V", "shape", "충전 평균 전압.", "mean V charge.", "either", 10),
        _m("dchg_V_avg", "방전 평균 V", "V", "shape", "방전 평균 전압.", "mean V discharge.", "either", 20),
        _m("delta_chg_V_avg", "충전 평균V Δ", "V", "shape", "기준 대비.", "delta.", "either", 25),
        _m("delta_dchg_V_avg", "방전 평균V Δ", "V", "shape", "기준 대비.", "delta.", "either", 30),
        _m("chg_ir_drop_proxy", "충전 IR drop proxy", "V", "shape", "충전 초반 IR 강하 proxy.", "early ΔV.", "increase", 40),
        _m("dchg_ir_drop_proxy", "방전 IR drop proxy", "V", "shape", "방전 초반 IR 강하 proxy.", "early ΔV.", "increase", 50),
        _m("hyst_area", "히스테리시스 면적", "V", "shape", "전체 충방전 히스테리시스.", "∮(Vchg-Vdchg)dQ.", "increase", 60),
        _m("hyst_area_low", "저SOC 히스테리시스", "V", "shape", "저SOC 밴드. Si chemo-mech.", "band integral.", "increase", 70),
        _m("hyst_area_mid", "중SOC 히스테리시스", "V", "shape", "중SOC 밴드.", "band integral.", "either", 80),
        _m("hyst_area_high", "고SOC 히스테리시스", "V", "shape", "고SOC 밴드. PE 보조.", "band integral.", "increase", 90),
        _m("hyst_frac_low", "히스테리시스 저SOC분율", "1", "shape", "low/total.", "hyst_low/hyst.", "either", 95),
        _m("hyst_frac_high", "히스테리시스 고SOC분율", "1", "shape", "high/total.", "hyst_high/hyst.", "either", 100),
        _m("hyst_max_dV", "최대 히스테리시스 dV", "V", "shape", "최대 충방전 전압차.", "max|Vchg-Vdchg|.", "increase", 110),
        _m("hyst_max_dV_low", "max dV 저SOC", "V", "shape", "저SOC 최대 dV.", "band max.", "increase", 115),
        _m("hyst_max_dV_mid", "max dV 중SOC", "V", "shape", "중SOC 최대 dV.", "band max.", "either", 120),
        _m("hyst_max_dV_high", "max dV 고SOC", "V", "shape", "고SOC 최대 dV.", "band max.", "either", 125),
        _m("delta_hyst_area", "히스테리시스 Δ", "V", "shape", "기준 대비 면적.", "delta.", "increase", 130),
        _m("delta_hyst_max_dV", "max dV Δ", "V", "shape", "기준 대비.", "delta.", "increase", 135),
        _m("chg_plateau_V", "충전 플래토 V", "V", "shape", "충전 플래토 전압.", "plateau detect.", "either", 140),
        _m("chg_plateau_width", "충전 플래토 폭", "Q-units", "shape", "충전 플래토 Q 폭.", "plateau width.", "either", 150),
        _m("dchg_plateau_V", "방전 플래토 V", "V", "shape", "방전 플래토 전압.", "plateau detect.", "either", 160),
        _m("dchg_plateau_width", "방전 플래토 폭", "Q-units", "shape", "방전 플래토 Q 폭.", "plateau width.", "decrease", 170),
        _m("delta_dchg_plateau_V", "방전 플래토 ΔV", "V", "shape", "기준 대비 이동.", "delta plateau V.", "either", 180),
        _m("dchg_V_cutoff_margin", "방전 컷오프 마진", "V", "shape", "컷오프까지 여유.", "Vmin-margin.", "decrease", 190),
        _m("delta_dchg_V_cutoff_margin", "컷오프 마진 Δ", "V", "shape", "기준 대비.", "delta.", "decrease", 195),
        _m("dchg_shape_DTW", "방전 형상 DTW", "1", "shape", "기준 곡선 DTW 거리.", "DTW vs baseline.", "increase", 200),
        _m("delta_dchg_shape_DTW", "DTW Δ", "1", "shape", "기준 대비 DTW.", "delta.", "increase", 205),
    ])

    items += _peak_family()

    # transport / eta
    items += _expand([
        _m("RCF", "RCF", "1", "transport", "Q_0.5C / Q_C/3.", "routine/RPT Q.", "decrease", 10),
        _m("RCF_slope_100", "RCF 기울기/100", "1/100cyc", "transport", "RCF 변화율.", "first-last slope.", "decrease", 20),
        _m("PER", "PER", "1", "transport", "η/(ΔI·R).", "eta_SOC50/(dI*R).", "increase", 30),
        _m("eta_SOC20", "η @SOC20", "V", "transport", "저SOC 과전위.", "C/3 vs 0.5C.", "increase", 40),
        _m("eta_SOC50", "η @SOC50", "V", "transport", "중SOC 과전위.", "C/3 vs 0.5C.", "increase", 50),
        _m("eta_SOC80", "η @SOC80", "V", "transport", "고SOC 과전위.", "C/3 vs 0.5C.", "increase", 60),
        _m("eta_max", "η max", "V", "transport", "최대 과전위.", "max η(SOC).", "increase", 70),
        _m("eta_mean", "η mean", "V", "transport", "평균 과전위.", "mean η.", "increase", 80),
        _m("eta_argmax_SOC", "η argmax SOC", "%", "transport", "η 최대 SOC.", "argmax.", "either", 90),
        _m("eta_slope_lowSOC", "η 저SOC 기울기", "V/%", "transport", "저SOC η 기울기.", "slope low band.", "either", 100),
        _m("Reff_scale", "Reff scale", "1", "transport", "유효 R 스케일.", "shape fit scale.", "increase", 110),
        _m("Reff_shape_fit_r2", "Reff fit R2", "1", "transport", "Reff 형상 fit 품질.", "r2.", "either", 120),
        _m("Reff_resid_soc20", "Reff 잔차 SOC20", "V", "transport", "Reff 모델 잔차.", "resid.", "either", 122),
        _m("Reff_resid_soc50", "Reff 잔차 SOC50", "V", "transport", "Reff 모델 잔차.", "resid.", "either", 124),
        _m("Reff_resid_soc80", "Reff 잔차 SOC80", "V", "transport", "Reff 모델 잔차.", "resid.", "either", 126),
        _m("I_inf_norm", "I∞ 정규화", "1", "transport", "CV 잔류전류 정규화.", "I_inf / I_ref.", "either", 130),
        _m("pulse_sample_count_1s", "펄스 1s 샘플수", "count", "transport", "t≤1s 샘플 수.", "quality.", "either", 140),
        _m("pulse_current_stability", "펄스 전류 안정도", "1", "transport", "std(I)/|I|.", "quality.", "decrease", 150),
        _m("rest_sufficiency", "rest 충분성", "1", "transport", "휴지 길이/품질.", "quality.", "either", 160),
        _m("leg_completeness", "레그 완전성", "1", "transport", "충방전 레그 완전성.", "quality.", "either", 170),
        _m("relax_completeness_max", "완화 완성도 max", "1", "transport", "SOC별 최대 완화 완성도.", "max.", "either", 180),
        _m("samples_per_mV", "샘플/mV", "1/mV", "transport", "전압 해상도 샘플밀도.", "dqdv quality.", "either", 190),
    ])

    # ocv / sd
    items += _expand([
        _m("ocv_V_inf_soc80", "OCV V∞ SOC80", "V", "ocv", "고SOC 무한시간 OCV.", "recovery/rest V_inf.", "either", 10),
        _m("ocv_V_inf_soc50", "OCV V∞ SOC50", "V", "ocv", "중SOC OCV.", "V_inf.", "either", 20),
        _m("ocv_V_inf_soc20", "OCV V∞ SOC20", "V", "ocv", "저SOC OCV.", "V_inf.", "either", 30),
        _m("ocv_spread_20_80", "OCV spread 20–80", "V", "ocv", "SOC20–80 OCV 폭.", "V80-V20.", "either", 40),
        _m("ocv_spread_50_80", "OCV spread 50–80", "V", "ocv", "SOC50–80 폭.", "V80-V50.", "either", 50),
        _m("ocv_spread_20_50", "OCV spread 20–50", "V", "ocv", "SOC20–50 폭.", "V50-V20.", "either", 60),
        _m("ocv_parallel_shift", "OCV 평행이동", "V", "ocv", "OCV 곡선 평행 시프트.", "block OCV shift.", "either", 70),
        _m("ocv_spread_compression", "OCV 폭 압축", "V", "ocv", "spread 축소.", "Δspread.", "either", 80),
        _m("delta_ocv_V_inf_soc80", "OCV80 Δ", "V", "ocv", "기준 대비.", "delta.", "either", 90),
        _m("delta_ocv_V_inf_soc50", "OCV50 Δ", "V", "ocv", "기준 대비.", "delta.", "either", 100),
        _m("delta_ocv_V_inf_soc20", "OCV20 Δ", "V", "ocv", "기준 대비.", "delta.", "either", 110),
        _m("delta_ocv_spread_20_80", "OCV spread Δ", "V", "ocv", "기준 대비 폭 변화.", "delta.", "either", 120),
    ])

    # curve fit / dQV
    items += _expand([
        _m("LAM_curve_proxy", "LAM 곡선 proxy", "%", "curve",
           "V–Q scale 축소 proxy (절대 LAM% 아님).", "(1-s)*100.", "either", 10),
        _m("LLI_curve_proxy", "LLI 곡선 proxy", "%", "curve",
           "Q 오프셋 proxy (절대 LLI% 아님).", "offset/Qmax*100.", "either", 20),
        _m("R_curve_proxy", "R 곡선 proxy", "mΩ", "curve",
           "곡선 fit dR proxy.", "fit_dR.", "increase", 30),
        _m("dchg_fit_scale", "방전 fit scale", "1", "curve", "기준 대비 scale s.", "3-param fit.", "decrease", 40),
        _m("dchg_fit_offset", "방전 fit offset", "Ah", "curve", "Q 오프셋.", "3-param fit.", "either", 50),
        _m("dchg_fit_dR", "방전 fit dR", "mΩ", "curve", "저항 항.", "3-param fit.", "increase", 60),
        _m("dchg_fit_residual_rms", "fit 잔차 RMS", "mV", "curve", "잔차 rms.", "RMS(resid).", "increase", 70),
        _m("dchg_fit_residual_max", "fit 잔차 max", "mV", "curve", "잔차 최대.", "max|resid|.", "increase", 80),
        _m("dchg_fit_residual_argmax_SOC", "잔차 argmax SOC", "%", "curve",
           "잔차 최대 SOC (방전 DOD→SOC 변환).", "argmax residual.", "either", 90),
        _m("dchg_fit_r2", "fit R2", "1", "curve", "곡선 fit 품질.", "r2.", "either", 100),
        _m("dchg_fit_corr_s_o", "fit corr(s,o)", "1", "curve", "scale-offset 상관 (축퇴 지표).", "corr.", "either", 105),
        _m("dchg_fit_residual_argmax_DOD", "잔차 argmax DOD", "%", "curve", "잔차 최대 DOD.", "argmax DOD.", "either", 108),
        _m("dQV_min", "ΔQ(V) min", "Ah", "curve", "전압빈 ΔQ 최소.", "histogram.", "either", 110),
        _m("dQV_mean", "ΔQ(V) mean", "Ah", "curve", "ΔQ 평균.", "mean.", "either", 120),
        _m("dQV_var", "ΔQ(V) var", "Ah2", "curve", "ΔQ 분산.", "var.", "increase", 130),
        _m("dQV_log_var", "ΔQ(V) log-var", "1", "curve", "log10 분산.", "log10(var).", "increase", 140),
        _m("dQV_skew", "ΔQ(V) skew", "1", "curve", "왜도.", "skew.", "either", 150),
        _m("dQV_kurtosis", "ΔQ(V) kurtosis", "1", "curve", "첨도.", "kurtosis.", "either", 160),
        _m("dQV_argmin_V", "ΔQ argmin V", "V", "curve", "ΔQ 최소 전압.", "argmin.", "either", 170),
        _m("dqdv_snr", "dQ/dV SNR", "1", "curve", "IC 신호대잡음.", "snr estimate.", "either", 180),
        _m("quality_score", "데이터 품질점수", "0–1", "curve", "추출 품질 종합.", "quality gates.", "either", 190),
        _m("v_noise_sigma", "전압 노이즈 σ", "V", "curve", "전압 노이즈 추정.", "noise sigma.", "either", 200),
        _m("dQV_ref_cycle", "ΔQ(V) 기준 사이클", "cyc", "curve", "ΔQ 비교 기준 사이클.", "ref cycle id.", "either", 210),
        _m("temperature_available", "온도 가용", "0/1", "curve", "Temp 컬럼 유효 여부.", "bool→float.", "either", 220),
        _m("Q_relax_significant", "Q_relax 유의", "0/1", "curve", "완화 용량 유의 플래그.", "threshold flag.", "either", 230),
        _m("dchg_fit_degenerate_flag", "fit 축퇴 플래그", "0/1", "curve", "scale bound 포화 등.", "degenerate flag.", "either", 240),
        _m("eta_valid", "η 유효", "0/1", "curve", "과전위 계산 유효 플래그.", "eta_valid.", "either", 250),
        _m("fade_exponent_b_se", "fade b 표준오차", "1", "curve", "fade 지수 표준오차.", "fit se.", "either", 260),
        _m("dQV_valid_V_range", "ΔQ 유효 V범위", "V", "curve", "ΔQ 집계 전압폭.", "Vmax-Vmin used.", "either", 270),
    ])

    # life
    items += _expand([
        _m("knee_cycle_bw", "knee 사이클", "cyc", "life",
           "bilinear knee 위치 — SoHQ 변곡점 (핵심).", "broken-stick SoHQ.", "either", 5),
        _m("knee_severity", "knee 심각도", "1", "life", "전후 기울기 차이.", "slope_after-before.", "increase", 60),
        _m("knee_slope_before", "knee 전 기울기", "%/cyc", "life", "knee 이전 fade 기울기.", "bilinear.", "decrease", 70),
        _m("knee_slope_after", "knee 후 기울기", "%/cyc", "life", "knee 이후 fade 기울기.", "bilinear.", "decrease", 80),
        _m("knee_fit_r2", "knee fit R2", "1", "life", "knee 적합도.", "r2.", "either", 90),
        _m("fade_exponent_b", "fade 지수 b", "1", "life", "SoHQ power-law 지수.", "SoHQ fit.", "either", 100),
        _m("fade_exponent_a", "fade 지수 a", "1", "life", "power-law 계수.", "SoHQ fit.", "either", 110),
        _m("fade_fit_r2", "fade fit R2", "1", "life", "fade 적합도.", "r2.", "either", 120),
        _m("fade_sohq0", "fade SoHQ0", "%", "life", "fit 초기 SoHQ.", "intercept.", "either", 130),
    ])

    # mechanism scores
    items += _expand([
        _m("LAM_PE_pattern_score", "PE activity 패턴", "0–1", "mechanism",
           "NCM activity/isolation (절대 LAM% 아님).", "mode_weights LAM_PE.", "increase", 10),
        _m("LAM_NE_pattern_score", "NE 패턴 점수", "0–1", "mechanism",
           "NE 관련 패턴 (Si-on-Gr에선 보조).", "mode_weights LAM_NE.", "increase", 20),
        _m("contact_loss_score", "contact_loss", "0–1", "mechanism",
           "옴/스택/접촉 증거 합.", "RΩ growth 등 가중합.", "increase", 30),
        _m("LLI_pattern_score", "LLI 패턴", "0–1", "mechanism",
           "CE·slippage·offset 기반.", "mode_weights LLI.", "increase", 40),
        _m("interface_R_score", "계면 R 패턴", "0–1", "mechanism",
           "Rct·VE 등 계면저항.", "mode_weights interface_R.", "increase", 50),
        _m("solid_diffusion_score", "고체확산 패턴", "0–1", "mechanism",
           "A_diff·PER·RCF.", "mode_weights solid_diffusion.", "increase", 60),
        _m("SE_decomposition_score", "SE 분해 패턴", "0–1", "mechanism",
           "CE↓·Rct↑ 등 SE 분해 가설.", "mode_weights SE_decomposition.", "increase", 70),
        _m("microshort_score", "마이크로쇼트 패턴", "0–1", "mechanism",
           "자기방전·CE 기반 soft-short 가설.", "mode_weights microshort.", "increase", 80),
        _m("impedance_pattern_score", "임피던스 패턴", "0–1", "mechanism",
           "총 임피던스 성장 패턴.", "mode score.", "increase", 90),
        _m("transport_limitation_score", "수송제한 패턴", "0–1", "mechanism",
           "rate/수송 제한 패턴.", "mode score.", "increase", 100),
        _m("plating_risk_score", "플레이팅 리스크", "0–1", "mechanism",
           "Li plating 위험 패턴.", "mode score.", "increase", 110),
        _m("contact_loss_confidence", "contact_loss 신뢰도", "0–1", "mechanism",
           "패턴 점수 신뢰도.", "evidence coverage.", "either", 200),
        _m("LAM_PE_confidence", "LAM_PE 신뢰도", "0–1", "mechanism", "패턴 신뢰도.", "confidence.", "either", 210),
        _m("LLI_confidence", "LLI 신뢰도", "0–1", "mechanism", "패턴 신뢰도.", "confidence.", "either", 220),
    ])

    # electrode
    items += _expand([
        _m("PE_side_score", "PE lean", "0–1", "electrode",
           "0.75·LAM_PE + feature + FC-OCP Δhits.", "electrode_side v1.3.", "increase", 10),
        _m("contact_stack_score", "contact_stack", "0–1", "electrode",
           "≈ contact_loss (R-centric).", "clip(contact_loss).", "increase", 20),
        _m("NE_side_score", "NE 가설", "0–1", "electrode",
           "contact × Si co-sign.", "electrode_side.", "increase", 30),
        _m("shared_side_score", "shared 모드", "0–1", "electrode",
           "LLI/interface 등 공유 모드 평균.", "shared modes mean.", "increase", 40),
        _m("si_cosign", "Si co-sign", "0–1", "electrode",
           "저SOC hyst·Q_relax·mech/chem·CV 동시 신호.", "SI_NE_COSIGN boost.", "increase", 50),
        _m("dominance_margin", "dominant 마진", "0–1", "electrode",
           "1위−2위 점수차.", "top-second.", "either", 60),
        _m("pe_peak_hits", "FC-OCP 피크 hits", "count", "electrode",
           "충전 dQ/dV ↔ 합성 FC-OCP 매칭 수.", "unique nearest ±60mV.", "either", 70),
        _m("pe_peak_hits_delta", "FC-OCP hits Δ", "count", "electrode",
           "기준 대비 hits 증가.", "hits-hits0.", "increase", 80),
        _m("fc_ocp_hits", "FC-OCP hits (alias)", "count", "electrode",
           "pe_peak_hits 별칭.", "same as pe_peak_hits.", "either", 85),
        _m("fc_ocp_hits_delta", "FC-OCP hits Δ (alias)", "count", "electrode",
           "pe_peak_hits_delta 별칭.", "same as pe_peak_hits_delta.", "increase", 86),
        _m("electrode_confidence", "전극진단 신뢰도", "0–1", "electrode",
           "coverage·분리·OCP 가용성.", "0.35cov+0.35sep+0.30ocp.", "either", 90),
    ])

    # de-dupe by key (first wins)
    seen: dict[str, MetricSpec] = {}
    for m in items:
        if m.key not in seen:
            seen[m.key] = m
    return tuple(seen.values())


METRICS: tuple[MetricSpec, ...] = _build_metrics()
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
    # preserve catalog order within families via panel groups
    out: list[MetricSpec] = []
    for fam, _ in PANEL_GROUPS:
        for m in metrics_for_family(fam):
            if m.key in cols:
                out.append(m)
    # any catalog metric whose family is not in PANEL_GROUPS
    known = {m.key for m in out}
    for m in METRICS:
        if m.key in cols and m.key not in known:
            out.append(m)
    return out


def catalog_as_records() -> list[dict[str, Any]]:
    return [asdict(m) for m in METRICS]


def catalog_coverage(columns: list[str] | set[str]) -> dict[str, Any]:
    """How many numeric basic columns are covered by the catalog."""
    cols = set(columns)
    covered = [m.key for m in METRICS if m.key in cols]
    skip = {
        "cycle", "file", "feature_set", "cell_id", "cycle_role",
        "I_abs_max", "I_abs_med_cc", "C_rate_med_est",
        "SoHQ_mixed", "SoHQ_routine", "SoHQ_rpt_c3",
    }
    skip_prefixes = (
        "diagnosis_", "dominant_", "PE_top", "NE_top", "shared_top",
        "PE_supporting", "NE_supporting", "electrode_diagnosis", "electrode_narrative",
        "contact_loss_supporting", "contact_loss_conflicting",
        "interface_R_supporting", "interface_R_conflicting",
        "SE_decomposition_supporting", "SE_decomposition_conflicting",
        "microshort_supporting", "microshort_conflicting",
        "LAM_PE_supporting", "LAM_PE_conflicting",
        "LLI_supporting", "LLI_conflicting",
        "solid_diffusion_supporting", "solid_diffusion_conflicting",
        "LLI_est", "LAM_PE_est", "LAM_NE_est", "electrode_slippage_est",
        "cv_detect", "flag_", "knee_method", "ocv_drift_mode", "ocv_block",
        "block_", "quality_gate",
    )
    basic_missing = []
    for c in sorted(cols):
        if c in skip or c in _BY_KEY:
            continue
        if any(c.startswith(p) or p in c for p in skip_prefixes):
            continue
        if c.endswith("_est") or c.endswith("_hc_calibrated"):
            continue
        if c.endswith("_supporting_features") or c.endswith("_conflicting_features"):
            continue
        if c.endswith("_evidence_count") or c.endswith("_confidence") and c not in _BY_KEY:
            # confidences partially covered
            if c not in _BY_KEY:
                continue
        basic_missing.append(c)
    return {
        "catalog_size": len(METRICS),
        "covered_in_table": len(covered),
        "basic_missing_count": len(basic_missing),
        "basic_missing": basic_missing[:80],
    }

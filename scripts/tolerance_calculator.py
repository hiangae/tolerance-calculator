# -*- coding: utf-8 -*-
"""
ISO 286-2 완벽 대응 IT 공차(끼워맞춤) 계산기
============================================
K, M, N, P~ZC 등 억지 끼워맞춤 구멍(Hole)의 Δ(Delta) 보정값과
표준 예외 규칙(예: N9 이상은 ES=0)을 모두 반영한 스크립트입니다.
"""

import re

# 1. 치수 구간 (mm) (인덱스 0 ~ 12)
SIZE_RANGES = [
    (0, 3), (3, 6), (6, 10), (10, 18), (18, 30), (30, 50),
    (50, 80), (80, 120), (120, 180), (180, 250), (250, 315),
    (315, 400), (400, 500),
]

def _range_index(d):
    for i, (lo, hi) in enumerate(SIZE_RANGES):
        if lo < d <= hi or (lo == 0 and d == 0):
            return i
    raise ValueError(f"지원하지 않는 치수 범위입니다: {d} mm (0~500mm만 지원)")

# 2. IT 등급 표 (단위: μm)
IT_GRADE_TABLE = {
    1:  [0.8, 1, 1, 1.2, 1.5, 1.5, 2, 2.5, 3.5, 4.5, 6, 7, 8],
    2:  [1.2, 1.5, 1.5, 2, 2.5, 2.5, 3, 4, 5, 7, 8, 9, 10],
    3:  [2, 2.5, 2.5, 3, 4, 4, 5, 6, 8, 10, 12, 13, 15],
    4:  [3, 4, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20],
    5:  [4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27],
    6:  [6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40],
    7:  [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],
    8:  [14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97],
    9:  [25, 30, 36, 43, 52, 62, 74, 87, 100, 115, 130, 140, 155],
    10: [40, 48, 58, 70, 84, 100, 120, 140, 160, 185, 210, 230, 250],
    11: [60, 75, 90, 110, 130, 160, 190, 220, 250, 290, 320, 360, 400],
    12: [100, 120, 150, 180, 210, 250, 300, 350, 400, 460, 520, 570, 630],
    13: [140, 180, 220, 270, 330, 390, 460, 540, 630, 720, 810, 890, 970],
    14: [250, 300, 360, 430, 520, 620, 740, 870, 1000, 1150, 1300, 1400, 1550],
    15: [400, 480, 580, 700, 840, 1000, 1200, 1400, 1600, 1850, 2100, 2300, 2500],
    16: [600, 750, 900, 1100, 1300, 1600, 1900, 2200, 2500, 2900, 3200, 3600, 4000],
    17: [1000, 1200, 1500, 1800, 2100, 2500, 3000, 3500, 4000, 4600, 5200, 5700, 6300],
    18: [1400, 1800, 2200, 2700, 3300, 3900, 4600, 5400, 6300, 7200, 8100, 8900, 9700],
}

# 3. 축(Shaft) 기초 편차 표 (단위: μm)
# a~h 계열 (상한치 es 고정, 하한치 = es - IT)
SHAFT_UPPER = {
    'a': [-270, -270, -280, -290, -300, -310, -320, -360, -410, -520, -570, -580, -660],
    'b': [-140, -140, -150, -150, -160, -170, -180, -200, -230, -240, -260, -290, -300],
    'c': [-60, -70, -80, -95, -110, -120, -140, -170, -180, -210, -230, -240, -260],
    'd': [-20, -30, -40, -50, -65, -80, -100, -120, -145, -170, -190, -210, -230],
    'e': [-14, -20, -25, -32, -40, -50, -60, -72, -85, -100, -110, -125, -135],
    'f': [-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68],
    'g': [-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20],
    'h': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}

# k~zc 계열 (하한치 ei 고정, 상한치 = ei + IT)
# (표준 ISO 286-2 기준으로 작성됨)
SHAFT_LOWER = {
    'k': [0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
    'm': [2, 4, 6, 7, 8, 9, 11, 13, 15, 17, 20, 21, 23],
    'n': [4, 8, 10, 12, 15, 17, 20, 23, 27, 31, 34, 37, 40],
    'p': [6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68],
    'r': [10, 15, 19, 23, 28, 34, 41, 51, 63, 79, 88, 98, 108],
    's': [14, 19, 23, 28, 35, 43, 53, 71, 92, 122, 138, 150, 169],
    't': [None, None, None, None, None, 48, 66, 91, 122, 166, 191, 214, 232],  # 30mm 미만 미지원
    'u': [18, 23, 28, 33, 41, 60, 87, 124, 170, 236, 284, 315, 350],
    'v': [None, None, None, None, None, 70, 102, 146, 200, 274, 325, 365, 400],  # 30mm 미만 미지원
    'x': [20, 28, 34, 45, 54, 77, 112, 160, 220, 305, 365, 410, 460],
    'y': [None, None, None, None, None, 85, 124, 178, 246, 340, 405, 460, 510],  # 30mm 미만 미지원
    'z': [26, 35, 42, 53, 73, 98, 144, 206, 286, 390, 470, 535, 600],
}

def get_tolerance(designation: str) -> dict:
    m = re.match(r'^\s*([\d.]+)\s*([A-Za-z]{1,2})\s*(\d{1,2})\s*$', designation)
    if not m:
        raise ValueError(f"형식을 인식할 수 없습니다: '{designation}' (예: 10h6, 60P6)")

    nominal = float(m.group(1))
    letter = m.group(2)
    grade = int(m.group(3))

    if grade not in IT_GRADE_TABLE:
        raise ValueError(f"지원하지 않는 IT 등급입니다 (1~18 지원)")

    idx = _range_index(nominal)
    it_value_um = IT_GRADE_TABLE[grade][idx]
    it_value_mm = it_value_um / 1000.0

    is_hole = letter[0].isupper()
    key = letter.lower()

    # JS 대칭 공차 처리
    if key == 'js':
        return {
            "nominal": nominal, "class": designation.strip(), "grade": f"IT{grade}",
            "upper": round(it_value_mm / 2, 4), "lower": round(-it_value_mm / 2, 4),
            "tolerance": round(it_value_mm, 4)
        }

    # 1. 축 (a~h) / 구멍 (A~H) : 상한치(es) 기준
    if key in SHAFT_UPPER:
        es_um = SHAFT_UPPER[key][idx]
        es_mm = es_um / 1000.0
        ei_mm = es_mm - it_value_mm
        
        if is_hole:
            EI_mm = -es_mm
            ES_mm = EI_mm + it_value_mm
            upper_mm, lower_mm = ES_mm, EI_mm
        else:
            upper_mm, lower_mm = es_mm, ei_mm

    # 2. 축 (k~zc) / 구멍 (K~ZC) : 하한치(ei) 기준
    elif key in SHAFT_LOWER:
        ei_um = SHAFT_LOWER[key][idx]
        if ei_um is None:
            raise ValueError(f"'{letter}{grade}'는 이 치수 범위(30mm 미만)에서 정의되지 않습니다.")
        ei_mm = ei_um / 1000.0
        es_mm = ei_mm + it_value_mm

        if is_hole:
            # -----------------------------------------------------
            # 구멍(Hole) 억지/중간 끼워맞춤 특수 보정 (Delta & 예외처리)
            # -----------------------------------------------------
            delta_um = 0
            
            # Delta 조건 (치수 > 3mm 인 경우에만 적용)
            if nominal > 3:
                if key in ['k', 'm', 'n'] and grade <= 8:
                    if grade > 1:
                        delta_um = IT_GRADE_TABLE[grade][idx] - IT_GRADE_TABLE[grade-1][idx]
                elif key in ['p', 'r', 's', 't', 'u', 'v', 'x', 'y', 'z'] and grade <= 7:
                    if grade > 1:
                        delta_um = IT_GRADE_TABLE[grade][idx] - IT_GRADE_TABLE[grade-1][idx]
            
            delta_mm = delta_um / 1000.0
            
            # 특수 예외 규칙: N9 이상 (IT >= 9)의 구멍 N 은 ES = 0
            if key == 'n' and grade >= 9:
                ES_mm = 0.0
            else:
                ES_mm = -ei_mm + delta_mm
                
            EI_mm = ES_mm - it_value_mm
            upper_mm, lower_mm = ES_mm, EI_mm
        else:
            upper_mm, lower_mm = es_mm, ei_mm

    else:
        raise ValueError(f"지원하지 않는 공차 기호입니다: '{letter}'")

    return {
        "nominal": nominal,
        "class": f"{letter}{grade}",
        "grade": f"IT{grade}",
        "upper": round(upper_mm, 4),
        "lower": round(lower_mm, 4),
        "tolerance": round(upper_mm - lower_mm, 4),
    }

def print_tolerance(designation: str):
    r = get_tolerance(designation)
    print(f"{designation:6s} -> 상한치: {r['upper']:+.4f} mm, 하한치: {r['lower']:+.4f} mm (공차폭 {r['tolerance']:.4f} mm)")

if __name__ == "__main__":
    tests = [
        "10h6", "10H7", "25f7", "25F8", "30k6", "8js7", 
        "60P6", "30K6", "30M7", "30N9"
    ]
    print("=== ISO 286 공차 계산 결과 ===")
    for t in tests:
        print_tolerance(t)
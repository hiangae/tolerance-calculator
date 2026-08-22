---
name: tolerance-calculator
description: Calculate mechanical fit tolerances (끼워맞춤/공차) from an ISO 286 designation such as "10h6", "25H7", or "50k6". Use this skill whenever the user asks for a part's upper/lower deviation, tolerance width, or fit limits given a dimension plus a tolerance class letter and grade number — even if they phrase it casually like "이 축의 상한치·하한치가 얼마야?", "25f7 공차 알려줘", or "구멍 H7 치수 범위 계산해줘". Trigger on any mention of IT grades, shaft/hole tolerance letters (a~u / A~U / js), or ISO 286 fits. Do NOT use for general unit conversion, GD&T symbol interpretation beyond basic deviations, or non-ISO standards.
---

# Tolerance Calculator (ISO 286 끼워맞춤 공차 계산기)

This skill computes the upper deviation, lower deviation, and total tolerance
width (in mm) for a mechanical feature specified by an ISO 286 designation.

The bundled script `scripts/tolerance_calculator.py` implements the ISO 286
standard tables (size ranges 0–500 mm, IT grades 1–18, shaft/hole letters
a~u / A~U / js). It is deterministic and self-contained — always run it rather
than computing deviations by hand, because the standard tables are easy to
misremember and small errors propagate directly into manufacturing decisions.

## When to use

Use this skill when the user provides a designation in the form
`<dimension><letter><grade>` and wants the resulting dimensional limits.
Examples: `10h6`, `25H7`, `50k6`, `30JS7`, `8f7`.

## How to run

Run the script with Python 3. The script path is relative to this skill folder:

```bash
python3 scripts/tolerance_calculator.py "<designation>"
```

If you need to pass multiple designations at once, import the function instead:

```bash
python3 -c "import sys; sys.path.insert(0,'scripts'); from tolerance_calculator import get_tolerance; print(get_tolerance('25H7'))"
```

Note: running the file directly (`python3 scripts/tolerance_calculator.py`)
executes its built-in self-test set and ignores any argument. To compute a
specific value, use the `-c` import form above, or edit the `tests` list in the
`__main__` block.

## Interpreting the output

The function returns a dictionary:

| Key         | Meaning                          | Unit |
|-------------|----------------------------------|------|
| `nominal`   | Nominal (basic) size             | mm   |
| `class`     | Tolerance class, e.g. `h6`       | —    |
| `grade`     | IT grade, e.g. `IT6`             | —    |
| `upper`     | Upper deviation (es / ES)        | mm   |
| `lower`     | Lower deviation (ei / EI)        | mm   |
| `tolerance` | Tolerance width (upper − lower)  | mm   |

Deviations are signed offsets from the nominal size. The actual maximum and
minimum feature sizes are `nominal + upper` and `nominal + lower`. Present both
the deviations and the absolute min/max sizes so the user can see the real
manufacturing window.

## Conventions worth explaining to the user

- **Lowercase letters = shaft (축)**, **uppercase = hole (구멍)**. The script
  handles the sign inversion between them automatically.
- **`h` / `H`** have one deviation pinned to zero (shaft `h`: upper = 0; hole
  `H`: lower = 0).
- **`js` / `JS`** is symmetric about the nominal size (±IT/2).
- Supported letters are `a~u` and `A~U` plus `js`/`JS`. Rare extreme-fit letters
  (`x`, `y`, `z`) are intentionally not included.

## Error handling

The script raises `ValueError` for unsupported inputs. Surface these clearly:

- Dimension outside 0–500 mm → "지원하지 않는 치수 범위"
- Grade outside IT1–IT18 → "지원하지 않는 IT 등급"
- Unsupported letter (e.g. `x`, `y`, `z`) → "지원하지 않는 공차 기호"
- Malformed input (not matching `<number><letter><grade>`) → "형식을 인식할 수 없습니다"

When an error occurs, tell the user what range/format is supported and ask for
a corrected designation rather than guessing.

## Example

Input: `25H7`
Output: upper `+0.021 mm`, lower `0.000 mm`, tolerance `0.021 mm`
→ Hole size ranges from 25.000 mm to 25.021 mm.

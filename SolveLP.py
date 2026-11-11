# Одновременное решение прямой и двойственной
from MethodSelection import solve_problem
import numpy as np


def _safe_solve(c, A, b, signs, objective, var_types=None):
    return solve_problem(c, A, b, signs, objective, var_types=var_types)


def solve_primal_and_dual(c, A, b, signs, objective="max", var_types=None):
    n = len(c)
    if var_types is None:
        var_types = ["nonneg"] * n

    # 1. Решаем прямую задачу
    res_primal = _safe_solve(c, A, b, signs, objective, var_types=var_types)

    if res_primal["status"] != "optimal":
        return {"primal": res_primal, "dual": None, "dual_formulation": None}

    # 2. Извлекаем двойственное решение из финальной таблицы (надежный метод)
    problem = res_primal["problem"]
    basis = res_primal["basis"]
    m = len(problem["A"])

    B = np.array([[problem["A"][i][basis[k]] for k in range(m)] for i in range(m)])
    cB = np.array([problem["c"][j] for j in basis])
    Binv = np.linalg.inv(B)
    y_star = (cB @ Binv).tolist()

    g_min = sum(problem["original_b"][i] * y_star[i] for i in range(m))

    # 3. Проверяем, можно ли явно решить двойственную
    # Это возможно ТОЛЬКО если все ограничения "<=" (для max) или все ">=" (для min)
    can_solve_explicitly = all(s == "<=" for s in signs) or all(s == ">=" for s in signs)

    res_dual_explicit = None
    dual_formulation = None

    if can_solve_explicitly:
        # Матрица двойственной строится по ИСХОДНОЙ матрице A, а не расширенной,
        # потому что свободные переменные дают равенства в двойственной,
        # а не дополнительные столбцы.
        A_dual = [[A[i][j] for i in range(m)] for j in range(n)]

        if objective == "max":
            c_dual = [-val for val in b]
            b_dual = c[:]
            signs_dual = [
                "=" if var_types[j] == "free" else ">=" for j in range(n)
            ]
        else:
            c_dual = b[:]
            b_dual = c[:]
            signs_dual = [
                "=" if var_types[j] == "free" else "<=" for j in range(n)
            ]

        res_dual_explicit = _safe_solve(c_dual, A_dual, b_dual, signs_dual, "max")

        if res_dual_explicit["status"] == "optimal":
            # Возвращаем истинный знак целевой функции
            if objective == "max":
                res_dual_explicit["objective_value"] = -res_dual_explicit["objective_value"]

            dual_formulation = {
                "c": c_dual,
                "A": A_dual,
                "b": b_dual,
                "signs": signs_dual,
                "objective": "min" if objective == "max" else "max",
                "var_types": var_types[:],
            }

    # 4. Формируем итоговый ответ
    return {
        "primal": res_primal,
        "dual": {
            "status": "optimal",
            "solution": y_star,
            "objective_value": g_min,
            "steps": res_dual_explicit["steps"] if res_dual_explicit and res_dual_explicit["status"] == "optimal" else [],
            "message": "Решение найдено из финальной таблицы" if not res_dual_explicit else "Двойственная задача решена явно"
        },
        "dual_formulation": dual_formulation
    }
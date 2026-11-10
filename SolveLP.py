# SolveLP.py
# Универсальный решатель ЛП: сам выбирает метод, возвращает прямое
# и двойственное решения. Использует существующие модули проекта.
import numpy as np
from AuxiliaryFun import EPSILON
from PrimalSimplex import primal_simplex
from DualSimplex import dual_simplex
from MIB import artificial_basis_simplex


def compute_dual_solution(primal_result):
    """
    По результату успешного primal_simplex/MIB/dual_simplex вычисляет
    двойственное решение y* = C_B · B⁻¹.

    Возвращает словарь:
      y        — список значений двойственных переменных
      g        — значение двойственной целевой функции g = b·y
      cB       — коэффициенты базисных переменных (в нормализованной задаче)
      B        — матрица базиса (m × m)
      Binv     — обратная матрица B⁻¹
      dual_direction        — 'min' или 'max' (направление двойственной)
      dual_constraint_sign  — '>=' или '<=' (знак ограничений A^T y vs c)
      error    — строка, если не удалось вычислить
    """
    if primal_result.get("status") != "optimal":
        return {"error": f"Прямая задача не решена (статус: {primal_result.get('status')})"}

    problem = primal_result["problem"]
    basis = primal_result["basis"]
    A_norm = problem["A"]
    c_norm = problem["c"]
    m = len(A_norm)

    try:
        B = np.array(
            [[A_norm[i][basis[k]] for k in range(m)] for i in range(m)],
            dtype=float,
        )
        cB = np.array([c_norm[j] for j in basis], dtype=float)
        Binv = np.linalg.inv(B)
        y = cB @ Binv
    except Exception as exc:
        return {"error": f"Не удалось вычислить y*: {exc}"}

    # Зачищаем микрошум
    y = np.where(np.abs(y) < 1e-12, 0.0, y)
    y = np.round(y, 10)

    original_b = problem["original_b"]
    objective = problem["objective"]

    g = float(np.dot(original_b, y))

    # Описание двойственной задачи зависит от направления исходной
    if objective == "max":
        dual_direction = "min"
        dual_sign = ">="
    else:
        dual_direction = "max"
        dual_sign = "<="

    return {
        "y": y.tolist(),
        "g": g,
        "cB": cB.tolist(),
        "B": B.tolist(),
        "Binv": Binv.tolist(),
        "dual_direction": dual_direction,
        "dual_constraint_sign": dual_sign,
    }


def solve_lp(c, A, b, signs, objective="max", max_iterations=1000):
    """
    Универсальный решатель ЛП.

    Сам выбирает метод:
      1) primal_simplex (прямой симплекс)
      2) dual_simplex (двойственный, если прямой не применим)
      3) artificial_basis_simplex (если нет единичного базиса)
    После оптимума считает двойственное решение.

    Возвращает словарь make_result + поля:
      result["dual"] — результат compute_dual_solution(...) или None
    """
    result = primal_simplex(c, A, b, signs, objective, max_iterations)

    if result["status"] == "dual_simplex":
        result = dual_simplex(c, A, b, signs, objective, max_iterations)
    elif result["status"] == "artificial_basis_required":
        result = artificial_basis_simplex(c, A, b, signs, objective, max_iterations)
    elif result["status"] == "variable_substitution_required":
        result = dual_simplex(c, A, b, signs, objective, max_iterations)

    result["dual"] = (
        compute_dual_solution(result) if result["status"] == "optimal" else None
    )
    return result
#Проверка оптимальности плана

from AuxiliaryFun import EPSILON


def check_optimality(c, A, b, x, signs, tolerance=1e-7):
    """
    Работает для задач вида: f=(c,x)->max, A x <= b, x >= 0.
    signs: список знаков ограничений ('<=', '>=', '=')
    Возвращает: dict(status, message, y=None или найденное y, details)
    """
    n = len(c)
    m = len(A)

    # Приводим все ограничения к виду <=
    A_norm = [row[:] for row in A]
    b_norm = b[:]
    for i, sign in enumerate(signs):
        if sign == ">=":
            A_norm[i] = [-v for v in A_norm[i]]
            b_norm[i] = -b_norm[i]
        elif sign == "=":
            # Равенство: разбиваем на два неравенства (a_i,x)<=b_i и -(a_i,x)<=-b_i
            A_norm.append([-v for v in A_norm[i]])
            b_norm.append(-b_norm[i])

    m2 = len(A_norm)

    # 1. Проверка допустимости x
    for i in range(m2):
        lhs = sum(A_norm[i][j] * x[j] for j in range(n))
        if lhs > b_norm[i] + tolerance:
            return {
                "status": "not_feasible",
                "message": f"План x недопустим: ограничение {i+1} нарушено.",
                "y": None
            }
    for j in range(n):
        if x[j] < -tolerance:
            return {
                "status": "not_feasible",
                "message": f"x_{j+1} < 0.",
                "y": None
            }

    # 2. Множества J_x и I_x
    J_x = [j for j in range(n) if x[j] > tolerance]
    I_x = [i for i in range(m2)
           if sum(A_norm[i][j] * x[j] for j in range(n)) < b_norm[i] - tolerance]

    # 3. Система уравнений относительно y
    # (A^j, y) = c_j для j in J_x;  y_i = 0 для i in I_x
    # Неизвестные: y_0..y_{m2-1}, все >= 0

    try:
        import numpy as np
    except ImportError:
        return {
            "status": "error",
            "message": "Для проверки оптимальности нужен numpy.",
            "y": None
        }

    # Матрица системы: строки — уравнения, столбцы — y_i
    eq_rows = []
    rhs = []
    # Условия (A^j, y) = c_j
    for j in J_x:
        eq_rows.append([A_norm[i][j] for i in range(m2)])
        rhs.append(c[j])
    # Условия y_i = 0
    for i in I_x:
        row = [0.0] * m2
        row[i] = 1.0
        eq_rows.append(row)
        rhs.append(0.0)

    if not eq_rows:
        # Нет условий — любое y>=0 подходит; проверяем, существует ли допустимое тривиально y=0, если c<=0
        if all(cj <= tolerance for cj in c):
            y = [0.0] * m2
            return {
                "status": "optimal",
                "message": "План оптимален (y=0 допустимо).",
                "y": y
            }
        return {
            "status": "not_optimal",
            "message": "Система условий пуста, но y=0 недопустимо.",
            "y": None
        }

    M = np.array(eq_rows, dtype=float)
    r = np.array(rhs, dtype=float)

    # Проверка совместности: rank(M) == rank([M|r])
    rank_M = np.linalg.matrix_rank(M, tol=tolerance)
    rank_aug = np.linalg.matrix_rank(np.column_stack([M, r]), tol=tolerance)
    if rank_M != rank_aug:
        return {
            "status": "not_optimal",
            "message": "Система условий (7) противоречива. План не оптимален.",
            "y": None
        }

    # Ищем какое-нибудь решение (через lstsq, затем проверяем y>=0 и A^T y>=c)
    y_candidate, *_ = np.linalg.lstsq(M, r, rcond=None)
    y_candidate = np.round(y_candidate, 12)

    # Проверка y >= 0
    if any(yi < -tolerance for yi in y_candidate):
        return {
            "status": "not_optimal",
            "message": "Найденное y имеет отрицательные компоненты. План не оптимален.",
            "y": y_candidate.tolist()
        }

    # Проверка A^T y >= c
    for j in range(n):
        val = sum(A_norm[i][j] * y_candidate[i] for i in range(m2))
        if val < c[j] - tolerance:
            return {
                "status": "not_optimal",
                "message": f"Условие (A^j,y) >= c_j нарушено для j={j+1}. План не оптимален.",
                "y": y_candidate.tolist()
            }

    return {
        "status": "optimal",
        "message": "План оптимален: найдено допустимое y, удовлетворяющее условиям дополняющей нежёсткости.",
        "y": y_candidate.tolist(),
        "J_x": J_x,
        "I_x": I_x
    }
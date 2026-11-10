import math

EPSILON = 1e-9

#ОБЩИЕ ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ХОДА РЕШЕНИЯ
def add_text_step(steps, title, description, data=None):
    step = {"type": "text", "title": title, "description": description}
    if data is not None:
        step["data"] = data
    steps.append(step)


def add_table_step(steps, tableau, basis, variable_names, c, description, pivot=None):
    """Сохраняет копию таблицы и рассчитанные показатели Zj и Delta."""
    cb = [c[index] for index in basis]
    zj = [sum(cb[i] * tableau[i][j] for i in range(len(basis)))
          for j in range(len(c))]
    deltas = [zj[j] - c[j] for j in range(len(c))]
    steps.append({
        "type": "table", "title": description,
        "tableau": [row[:] for row in tableau],
        "basis": basis[:],
        "basis_names": [variable_names[index] for index in basis],
        "variable_names": variable_names[:],
        "cb": cb[:], "zj": zj[:], "deltas": deltas[:],
        "pivot": pivot.copy() if pivot else None
    })


#ПРОВЕРКА ИСХОДНЫХ ДАННЫХ
def validate_problem(c, A, b, signs, objective="max"):
    if not isinstance(c, (list, tuple)) or not c:
        raise ValueError("Вектор коэффициентов целевой функции не должен быть пустым.")
    if not isinstance(A, (list, tuple)) or not A:
        raise ValueError("Матрица ограничений не должна быть пустой.")
    if not isinstance(b, (list, tuple)) or not b:
        raise ValueError("Вектор свободных членов не должен быть пустым.")
    if signs is None or len(A) != len(b) or len(A) != len(signs):
        raise ValueError("Количество ограничений, свободных членов и знаков должно совпадать.")

    n = len(c)
    if any(not isinstance(row, (list, tuple)) or len(row) != n for row in A):
        raise ValueError("Все строки матрицы A должны иметь длину, равную длине c.")
    if objective not in ("max", "min"):
        raise ValueError("Цель должна быть 'max' или 'min'.")

    normalized_signs = []
    for sign in signs:
        sign = str(sign).strip()
        if sign in ("<=", "≤"):
            normalized_signs.append("<=")
        elif sign in (">=", "≥"):
            normalized_signs.append(">=")
        elif sign in ("=", "=="):
            normalized_signs.append("=")
        else:
            raise ValueError(f"Неизвестный знак ограничения: {sign}")

    try:
        values = [float(v) for v in c] + [float(v) for v in b]
        for row in A:
            values.extend(float(v) for v in row)
    except (TypeError, ValueError):
        raise ValueError("Все коэффициенты должны быть числами.")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Все коэффициенты должны быть конечными числами.")
    return n, normalized_signs


#ПРИВЕДЕНИЕ ЗАДАЧИ К КАНОНИЧЕСКОМУ ВИДУ
def normalize_problem(c, A, b, signs, objective="max"):
    """
    Нормализация выполняется ОДИН раз.
    Переменные задачи считаются неотрицательными.
    Для <= добавляется slack +1, для >= — surplus -1, для равенств дополнительная переменная не добавляется.
    Отрицательная правая часть исправляется умножением строки на -1 с одновременной сменой направления неравенства.
    """
    n, normalized_signs = validate_problem(c, A, b, signs, objective)
    original_c = [float(v) for v in c]
    original_A = [[float(v) for v in row] for row in A]
    original_b = [float(v) for v in b]
    factor = 1.0 if objective == "max" else -1.0
    work_c = [factor * v for v in original_c]
    work_A = [row[:] for row in original_A]
    work_b = original_b[:]
    work_signs = normalized_signs[:]
    steps = []
    names = [f"x{i + 1}" for i in range(n)]

    add_text_step(steps, "Исходная задача",
                  f"Целевая функция: {objective}. Переменных: {n}. Ограничений: {len(A)}.")
    if objective == "min":
        add_text_step(steps, "Преобразование целевой функции",
                      "Умножаем целевую функцию на -1 и решаем задачу на максимум.")

    for i in range(len(work_A)):
        if work_b[i] < -EPSILON:
            work_A[i] = [-v for v in work_A[i]]
            work_b[i] = -work_b[i]
            if work_signs[i] == "<=":
                work_signs[i] = ">="
            elif work_signs[i] == ">=":
                work_signs[i] = "<="
            add_text_step(steps, f"Преобразование ограничения №{i + 1}",
                          "Правая часть была отрицательной: умножаем всё ограничение на -1 "
                          "и меняем направление неравенства.")

    # Сначала расширяем все строки нулями, затем добавляем по одной переменной.
    for i, sign in enumerate(work_signs):
        if sign in ("<=", ">="):
            for row in work_A:
                row.append(0.0)
            work_A[i][-1] = 1.0 if sign == "<=" else -1.0
            work_c.append(0.0)
            names.append(f"s{len(names) - n + 1}")

    add_text_step(steps, "Канонический вид",
                  "Неравенства заменены равенствами: для <= добавлены slack-переменные +1, "
                  "для >= — surplus-переменные -1. Равенства оставлены без добавочной переменной.")
    return {
        "c": work_c, "A": work_A, "b": work_b, "signs": work_signs,
        "variable_names": names, "original_c": original_c,
        "original_A": original_A, "original_b": original_b,
        "original_variables_count": n, "objective": objective,
        "objective_factor": factor, "steps": steps
    }


#ПОИСК НАЧАЛЬНОГО ЕДИНИЧНОГО БАЗИСА
def find_initial_basis(A):
    if not A:
        return None
    m, n = len(A), len(A[0])
    candidates = {i: [] for i in range(m)}
    for j in range(n):
        ones = [i for i in range(m) if abs(A[i][j] - 1.0) <= EPSILON]
        valid = all(abs(A[i][j]) <= EPSILON for i in range(m) if i not in ones)
        if valid and len(ones) == 1:
            candidates[ones[0]].append(j)
    if any(not candidates[i] for i in range(m)):
        return None
    order = sorted(range(m), key=lambda i: len(candidates[i]))
    result, used = [None] * m, set()

    def search(pos):
        if pos == m:
            return True
        row = order[pos]
        for col in candidates[row]:
            if col not in used:
                used.add(col)
                result[row] = col
                if search(pos + 1):
                    return True
                used.remove(col)
                result[row] = None
        return False
    return result if search(0) else None


#ВЫЧИСЛЕНИЕ ОЦЕНОК: Delta_j = Z_j - C_j
def calculate_deltas(tableau, c, basis):
    cb = [c[index] for index in basis]
    zj = [sum(cb[i] * tableau[i][j] for i in range(len(basis)))
          for j in range(len(c))]
    return [zj[j] - c[j] for j in range(len(c))]


#ОПРЕДЕЛЕНИЕ РЕКОМЕНДУЕМОГО МЕТОДА
def determine_method(tableau, c, basis):
    if basis is None:
        return {"method": "artificial_basis_required",
                "message": "Начальный единичный базис отсутствует. Требуется метод искусственного базиса."}
    b = [row[-1] for row in tableau]
    d = calculate_deltas(tableau, c, basis)
    neg_b = any(v < -EPSILON for v in b)
    neg_d = any(v < -EPSILON for v in d)
    if not neg_b and not neg_d:
        return {"method": "optimal", "message": "Все b_i >= 0 и Delta_j >= 0: план оптимален."}
    if not neg_b and neg_d:
        return {"method": "primal_simplex", "message": "b_i неотрицательны, есть отрицательные Delta_j: применяем прямой симплекс."}
    if neg_b and not neg_d:
        return {"method": "dual_simplex", "message": "Есть отрицательные b_i, все Delta_j неотрицательны: применяем двойственный симплекс."}
    return {"method": "variable_substitution_required",
            "message": "Одновременно есть отрицательные b_i и Delta_j. Нужна отдельная допустимая замена переменных или искусственный базис."}


#ПЕРЕСЧЁТ СИМПЛЕКСНОЙ ТАБЛИЦЫ
def pivot_operation(tableau, pivot_row, pivot_column):
    pivot = tableau[pivot_row][pivot_column]
    if abs(pivot) <= EPSILON:
        raise ZeroDivisionError("Разрешающий элемент равен нулю.")
    tableau[pivot_row] = [v / pivot for v in tableau[pivot_row]]
    for i in range(len(tableau)):
        if i == pivot_row:
            continue
        multiplier = tableau[i][pivot_column]
        tableau[i] = [tableau[i][j] - multiplier * tableau[pivot_row][j]
                      for j in range(len(tableau[i]))]
    for row in tableau:
        for j, value in enumerate(row):
            if abs(value) <= EPSILON:
                row[j] = 0.0


def build_tableau(A, b):
    return [list(A[i]) + [float(b[i])] for i in range(len(A))]


#восстанавливает значения переменных
def recover_solution(tableau, basis, variable_count):
    result = [0.0] * variable_count
    for i, col in enumerate(basis):
        if col < variable_count:
            result[col] = tableau[i][-1]
    return result



def make_result(status, message, steps, solution=None, objective_value=None,
                tableau=None, basis=None, deltas=None, problem=None, **extra):
    result = {
        "status": status, "message": message, "solution": solution,
        "objective_value": objective_value, "steps": steps,
        "tableau": [r[:] for r in tableau] if tableau is not None else None,
        "basis": basis[:] if basis is not None else None,
        "deltas": deltas[:] if deltas is not None else None,
        "problem": problem
    }
    result.update(extra)
    return result

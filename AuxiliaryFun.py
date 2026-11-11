import math

EPSILON = 1e-9

# 1. СОХРАНЕНИЕ ШАГОВ РЕШЕНИЯ
def add_text_step(steps, title, description, data=None):
    """Сохраняет текстовое пояснение к шагу решения."""
    step = {"type": "text", "title": title, "description": description}
    if data is not None:
        step["data"] = data
    steps.append(step)


def calculate_zj(tableau, c, basis):
    """
    Вычисляет Zj для каждого столбца.
    Zj = сумма(Cбазис * элементы соответствующего столбца).
    """
    cb = [c[index] for index in basis]
    zj = []
    for j in range(len(c)):
        value = sum(cb[i] * tableau[i][j] for i in range(len(basis)))
        zj.append(value)
    return zj


def calculate_deltas(tableau, c, basis):
    """
    Вычисляет оценки: Δj = Zj - Cj
    """
    zj = calculate_zj(tableau, c, basis)
    return [zj[j] - c[j] for j in range(len(c))]


def add_table_step(steps, tableau, basis, variable_names, c, description, pivot=None):
    """
    Сохраняет текущую симплексную таблицу.
    Дополнительно кладём полный вектор c (коэффициенты целевой функции), чтобы GUI мог показать строку c_j. Логика решения не меняется.
    """
    cb = [c[index] for index in basis]
    zj = calculate_zj(tableau, c, basis)
    deltas = calculate_deltas(tableau, c, basis)
    steps.append({
        "type": "table", "title": description,
        "tableau": [row[:] for row in tableau],
        "basis": basis[:],
        "basis_names": [variable_names[index] for index in basis],
        "variable_names": variable_names[:],
        "cb": cb[:],
        "zj": zj[:],
        "deltas": deltas[:],
        "c": c[:],
        "pivot": pivot.copy() if pivot else None
    })



# 2. ПРОВЕРКА ИСХОДНОЙ ЗАДАЧИ
def validate_problem(c, A, b, signs, objective="max", var_types=None):
    if not isinstance(c, (list, tuple)) or len(c) == 0:
        raise ValueError("Вектор коэффициентов целевой функции не должен быть пустым.")
    if not isinstance(A, (list, tuple)) or len(A) == 0:
        raise ValueError("Матрица ограничений не должна быть пустой.")
    if not isinstance(b, (list, tuple)) or len(b) == 0:
        raise ValueError("Вектор свободных членов не должен быть пустым.")
    if signs is None or len(A) != len(b) or len(A) != len(signs):
        raise ValueError("Количество ограничений, свободных членов и знаков должно совпадать.")

    n = len(c)
    for row in A:
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise ValueError("Все строки матрицы A должны иметь длину, равную длине c.")
    if objective not in ("max", "min"):
        raise ValueError("Цель должна быть 'max' или 'min'.")

    if var_types is None:
        var_types = ["nonneg"] * n
    if len(var_types) != n:
        raise ValueError("Список типов переменных должен совпадать по длине с c.")
    for t in var_types:
        if t not in ("nonneg", "free"):
            raise ValueError(f"Неизвестный тип переменной: {t}")

    # Приводим знаки ограничений к единому виду.
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

    # Проверяем, что все коэффициенты являются конечными числами.
    try:
        values = [float(v) for v in c] + [float(v) for v in b]
        for row in A:
            values.extend(float(v) for v in row)
    except (TypeError, ValueError):
        raise ValueError("Все коэффициенты должны быть числами.")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Все коэффициенты должны быть конечными числами.")
    return n, normalized_signs, var_types


# 2a. РАСШИРЕНИЕ СВОБОДНЫХ ПЕРЕМЕННЫХ
def expand_free_variables(c, A, var_types):
    """
    Заменяет свободные переменные x_j = x'_j - x''_j.
    Возвращает:
      new_c       — расширенный вектор c
      new_A       — расширенная матрица A
      mapping     — список кортежей (j_orig, kind, idx1, idx2)
                    kind == 'nonneg' -> idx2 is None
                    kind == 'free'   -> idx1 и idx2 — индексы x'_j и x''_j
      var_names   — имена расширенных переменных
    """
    n = len(c)
    new_c = []
    new_cols = []       # для каждого нового столбца — исходный индекс j
    mapping = []
    var_names = []

    for j in range(n):
        if var_types[j] == "free":
            idx1 = len(new_c)
            new_c.append(c[j])
            new_cols.append(j)
            var_names.append(f"x{j+1}'")

            new_c.append(-c[j])
            new_cols.append(j)
            var_names.append(f"x{j+1}''")

            mapping.append((j, "free", idx1, idx1 + 1))
        else:
            idx1 = len(new_c)
            new_c.append(c[j])
            new_cols.append(j)
            var_names.append(f"x{j+1}")
            mapping.append((j, "nonneg", idx1, None))

    new_A = []
    for row in A:
        new_row = [row[j] for j in new_cols]
        # Для второго столбца свободной переменной нужен минус.
        # Проще: пересобрать с учётом mapping.
        new_row = []
        for (j_orig, kind, idx1, idx2) in mapping:
            new_row.append(row[j_orig])
            if kind == "free":
                new_row.append(-row[j_orig])
        new_A.append(new_row)

    return new_c, new_A, mapping, var_names


def collapse_solution(all_values, mapping):
    """
    Сворачивает расширенное решение x' , x'' обратно в исходные x.
    """
    solution = []
    for (j_orig, kind, idx1, idx2) in mapping:
        if kind == "free":
            solution.append(all_values[idx1] - all_values[idx2])
        else:
            solution.append(all_values[idx1])
    return solution


# ============================================================
# 3. ПРИВЕДЕНИЕ ЗАДАЧИ К КАНОНИЧЕСКОМУ ВИДУ
# ============================================================

def normalize_problem(c, A, b, signs, objective="max", var_types=None):
    """
    Подготавливает исходную задачу для симплекс-методов.
    Сначала свободные переменные заменяются на x' - x''.
    Для <= добавляется переменная +1.
    Для >= добавляется переменная -1.
    Для = дополнительная переменная не добавляется.
    Если правая часть отрицательная, строка умножается на -1, а знак неравенства меняется на противоположный.
    Для минимизации целевая функция умножается на -1.
    """
    n, normalized_signs, var_types = validate_problem(c, A, b, signs, objective, var_types)
    original_c = [float(v) for v in c]
    original_A = [[float(v) for v in row] for row in A]
    original_b = [float(v) for v in b]
    original_var_types = var_types[:]

    steps = []
    add_text_step(steps, "Исходная задача", f"Целевая функция: {objective}. Переменных: {n}. Ограничений: {len(A)}.")

    # 0. Расширяем свободные переменные.
    exp_c, exp_A, mapping, base_names = expand_free_variables(original_c, original_A, original_var_types)
    if any(kind == "free" for (_, kind, _, _) in mapping):
        free_list = [f"x{j+1}" for (j, kind, _, _) in mapping if kind == "free"]
        add_text_step(
            steps, "Замена свободных переменных",
            f"Свободные переменные {', '.join(free_list)} заменены на разность "
            f"двух неотрицательных: x = x' - x''."
        )

    # Для минимизации решаем эквивалентную задачу на максимум.
    factor = 1.0 if objective == "max" else -1.0
    work_c = [factor * value for value in exp_c]
    work_A = [row[:] for row in exp_A]
    work_b = original_b[:]
    work_signs = normalized_signs[:]
    variable_names = base_names[:]

    if objective == "min":
        add_text_step(steps, "Преобразование целевой функции", "Умножаем целевую функцию на -1 и решаем задачу на максимум.")

    # Исправляем отрицательные правые части.
    for i in range(len(work_A)):
        if work_b[i] < -EPSILON:
            work_A[i] = [-value for value in work_A[i]]
            work_b[i] = -work_b[i]
            if work_signs[i] == "<=":
                work_signs[i] = ">="
            elif work_signs[i] == ">=":
                work_signs[i] = "<="
            add_text_step(steps, f"Преобразование ограничения №{i + 1}", "Умножаем всё ограничение на -1 и меняем направление неравенства.")

    # Добавляем дополнительные переменные.
    slack_number = 0
    for i, sign in enumerate(work_signs):
        if sign == "=":
            continue
        slack_number += 1
        # Добавляем новый столбец, заполненный нулями.
        for row in work_A:
            row.append(0.0)
        # В нужной строке ставим +1 или -1.
        if sign == "<=":
            work_A[i][-1] = 1.0
        else:
            work_A[i][-1] = -1.0
        work_c.append(0.0)
        variable_names.append(f"s{slack_number}")

    add_text_step(steps, "Канонический вид", "Для ограничений <= добавлены дополнительные переменные +1, для >= — переменные -1. Равенства оставлены без изменений.")

    return {
        "c": work_c, "A": work_A, "b": work_b, "signs": work_signs,
        "variable_names": variable_names,
        "original_c": original_c, "original_A": original_A, "original_b": original_b,
        "original_variables_count": len(exp_c),   # длина расширенного вектора
        "original_var_types": original_var_types,
        "mapping": mapping,
        "objective": objective, "objective_factor": factor,
        "steps": steps
    }


# 4. ПОИСК НАЧАЛЬНОГО ЕДИНИЧНОГО БАЗИСА
def find_initial_basis(A):
    """
    Ищет столбцы единичной матрицы.
    Каждый столбец базиса должен содержать: одну единицу и остальные нули.
    Возвращает список индексов базисных столбцов.
    Если базис найти нельзя, возвращает None.
    """
    if not A:
        return None
    m = len(A)
    n = len(A[0])
    candidates = []

    # Находим подходящие столбцы для каждой строки.
    for i in range(m):
        row_candidates = []
        for j in range(n):
            is_unit_column = (abs(A[i][j] - 1.0) <= EPSILON and all(abs(A[k][j]) <= EPSILON for k in range(m) if k != i))
            if is_unit_column:
                row_candidates.append(j)
        if not row_candidates:
            return None
        candidates.append(row_candidates)

    # Подбираем разные столбцы для разных строк.
    basis = [None] * m
    used_columns = set()

    def search(row):
        if row == m:
            return True
        for column in candidates[row]:
            if column in used_columns:
                continue
            basis[row] = column
            used_columns.add(column)
            if search(row + 1):
                return True
            basis[row] = None
            used_columns.remove(column)
        return False

    if search(0):
        return basis
    return None


# 5. ОПРЕДЕЛЕНИЕ ПОДХОДЯЩЕГО МЕТОДА
def determine_method(tableau, c, basis):
    """
    Определяет, какой метод можно применить к текущей симплексной таблице.
    Используется соглашение: Δj = Zj - Cj
    Для прямого симплекс-метода: b >= 0, но есть отрицательные Δj.
    Для двойственного симплекс-метода: есть отрицательные b, но все Δj >= 0.
    """
    if basis is None:
        return {"method": "artificial_basis_required", "message": "Начальный единичный базис отсутствует. Требуется метод искусственного базиса."}

    b = [row[-1] for row in tableau]
    deltas = calculate_deltas(tableau, c, basis)
    has_negative_b = any(value < -EPSILON for value in b)
    has_negative_delta = any(value < -EPSILON for value in deltas)

    # Прямая и двойственная допустимость выполнены.
    if not has_negative_b and not has_negative_delta:
        return {"method": "optimal", "message": "Все b_i >= 0 и Δj >= 0. Начальный план уже оптимален."}

    # План допустим по b, но не оптимален по оценкам.
    if not has_negative_b and has_negative_delta:
        return {"method": "primal_simplex", "message": "Все b_i >= 0, но есть отрицательные Δj. Применяем прямой симплекс-метод."}

    # План двойственно допустим, но есть отрицательные b.
    if has_negative_b and not has_negative_delta:
        return {"method": "dual_simplex", "message": "Есть отрицательные b_i, но все Δj >= 0. Применяем двойственный симплекс-метод."}

    # Одновременно нарушены оба условия.
    return {"method": "variable_substitution_required", "message": "Одновременно есть отрицательные b_i и отрицательные Δj. Требуется отдельное преобразование задачи."}



def pivot_operation(tableau, pivot_row, pivot_column):
    """
    Жорданово преобразование симплекс-таблицы (нормировка с инверсией):
      1. Ведущий элемент заменяется на 1/p (инверсия).
      2. Ведущая строка делится на p  (кроме ведущего элемента).
      3. Ведущий столбец делится на -p (кроме ведущего элемента).
      4. Остальные элементы — по правилу прямоугольника: a'[i][j] = a[i][j] - a[i][s]*a[r][j]/p
    """
    p = tableau[pivot_row][pivot_column]
    if abs(p) <= EPSILON:
        raise ZeroDivisionError("Ведущий элемент равен нулю.")

    rows = len(tableau)
    cols = len(tableau[0])

    old = [row[:] for row in tableau]   # снимок ДО преобразования

    #Инверсия ведущего элемента
    tableau[pivot_row][pivot_column] = 1.0 / p

    # Ведущая строка делится на p
    for j in range(cols):
        if j == pivot_column:
            continue
        tableau[pivot_row][j] = old[pivot_row][j] / p

    # Ведущий столбец делится на -p
    for i in range(rows):
        if i == pivot_row:
            continue
        tableau[i][pivot_column] = -old[i][pivot_column] / p

    # остальные элементы
    for i in range(rows):
        if i == pivot_row:
            continue
        for j in range(cols):
            if j == pivot_column:
                continue
            tableau[i][j] = old[i][j] - old[i][pivot_column] * old[pivot_row][j] / p

    # Чистим численный мусор
    for i in range(rows):
        for j in range(cols):
            if abs(tableau[i][j]) <= EPSILON:
                tableau[i][j] = 0.0


# 7. ПОСТРОЕНИЕ СИМПЛЕКСНОЙ ТАБЛИЦЫ
def build_tableau(A, b):
    """Добавляет столбец свободных членов b к матрице A."""
    return [list(A[i]) + [float(b[i])] for i in range(len(A))]



# 8. ВОССТАНОВЛЕНИЕ РЕШЕНИЯ
def recover_solution(tableau, basis, variable_count):
    solution = [0.0] * variable_count
    for i, column in enumerate(basis):
        if column < variable_count:
            coeff = tableau[i][column] # это 1/p
            if abs(coeff) > EPSILON:
                solution[column] = tableau[i][-1] / coeff
            else:
                solution[column] = tableau[i][-1]
    return solution

# 9. ФОРМИРОВАНИЕ ОБЩЕГО РЕЗУЛЬТАТА
def make_result(status, message, steps, solution=None, objective_value=None, tableau=None, basis=None, deltas=None, problem=None, **extra):
    """Формирует единый результат для всех методов."""
    result = {
        "status": status, "message": message,
        "solution": solution, "objective_value": objective_value,
        "steps": steps,
        "tableau": [row[:] for row in tableau] if tableau is not None else None,
        "basis": basis[:] if basis is not None else None,
        "deltas": deltas[:] if deltas is not None else None,
        "problem": problem
    }
    result.update(extra)
    return result
import math

EPSILON = 1e-9

#ОБЩИЕ ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ХОДА РЕШЕНИЯ
def add_text_step(steps, title, description, data=None):
    step = {
        "type": "text",
        "title": title,
        "description": description
    }
    if data is not None:
        step["data"] = data
    steps.append(step)


def add_table_step(steps, tableau, basis, variable_names, c, description, pivot=None):
    tableau_copy = [row[:] for row in tableau]
    basis_copy = basis[:]
    cb = [c[index] for index in basis_copy]
    zj = []
    for j in range(len(c)):
        value = sum(cb[i] * tableau_copy[i][j] for i in range(len(basis_copy)))
        zj.append(value)
    deltas = [zj[j] - c[j] for j in range(len(c))]
    steps.append({
        "type": "table",
        "title": description,
        "tableau": tableau_copy,
        "basis": basis_copy,
        "basis_names": [variable_names[index] for index in basis_copy],
        "variable_names": variable_names[:],
        "cb": cb[:],
        "zj": zj[:],
        "deltas": deltas[:],
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
    if len(A) != len(b) or len(A) != len(signs):
        raise ValueError("Количество ограничений, свободных членов и знаков должно совпадать.")

    n = len(c)
    for row in A:
        if len(row) != n:
            raise ValueError("Все строки матрицы A должны иметь одинаковую длину, равную длине c.")

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

    values = list(c) + list(b)
    for row in A:
        values.extend(row)

    try:
        values = [float(value) for value in values]
    except (TypeError, ValueError):
        raise ValueError("Все коэффициенты должны быть числами.")

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Все коэффициенты должны быть конечными числами.")

    return n, normalized_signs


#ПРИВЕДЕНИЕ ЗАДАЧИ К НОРМАЛИЗОВАННОМУ ВИДУ
def normalize_problem(c, A, b, signs, objective="max"):
    n, normalized_signs = validate_problem(c, A, b, signs, objective)

    original_c = [float(value) for value in c]
    original_A = [[float(value) for value in row] for row in A]
    original_b = [float(value) for value in b]

    objective_factor = 1.0 if objective == "max" else -1.0
    normalized_c = [objective_factor * value for value in original_c]

    normalized_A = [row[:] for row in original_A]
    normalized_b = original_b[:]
    variable_names = [f"x{i + 1}" for i in range(n)]
    steps = []

    add_text_step(
        steps,
        "Исходная задача",
        f"Целевая функция: {objective}. "
        f"Количество переменных: {n}. "
        f"Количество ограничений: {len(A)}."
    )

    if objective == "min":
        add_text_step(
            steps,
            "Преобразование целевой функции",
            "Для решения задачи на минимум умножаем целевую функцию на -1."
        )

    # Приведение ограничений >= к виду <=
    for i, sign in enumerate(normalized_signs):
        if sign == ">=":
            normalized_A[i] = [
                -value for value in normalized_A[i]
            ]
            normalized_b[i] *= -1

            add_text_step(
                steps,
                f"Преобразование ограничения №{i + 1}",
                "Умножаем обе части ограничения >= на -1."
            )

    # Добавление дополнительных переменных
    for i, sign in enumerate(normalized_signs):
        if sign in ("<=", ">="):
            for row in normalized_A:
                row.append(0.0)

            normalized_A[i][-1] = 1.0
            normalized_c.append(0.0)
            variable_names.append(f"x{len(variable_names) + 1}")

    add_text_step(
        steps,
        "Канонический вид",
        "Ограничения приведены к равенствам. "
        "Для каждого неравенства добавлена дополнительная переменная."
    )

    add_text_step(
        steps,
        "Свободные члены",
        "Знаки свободных членов сохранены.",
        {"b": normalized_b[:]}
    )

    return {
        "c": normalized_c,
        "A": normalized_A,
        "b": normalized_b,
        "signs": normalized_signs,
        "variable_names": variable_names,
        "original_c": original_c,
        "original_A": original_A,
        "original_b": original_b,
        "original_variables_count": n,
        "objective": objective,
        "objective_factor": objective_factor,
        "steps": steps
    }


#ПОИСК НАЧАЛЬНОГО БАЗИСА
def find_initial_basis(A):
    if not A:
        return None

    row_count = len(A)
    column_count = len(A[0])
    unit_columns = []

    for j in range(column_count):
        ones = []
        valid = True
        for i in range(row_count):
            value = A[i][j]
            if abs(value - 1.0) <= EPSILON:
                ones.append(i)
            elif abs(value) > EPSILON:
                valid = False
                break
        if valid and len(ones) == 1:
            unit_columns.append((ones[0], j))

    candidates = {
        i: [j for row, j in unit_columns if row == i]
        for i in range(row_count)
    }

    if any(not candidates[i] for i in range(row_count)):
        return None

    order = sorted(range(row_count), key=lambda i: len(candidates[i]))
    result = [None] * row_count
    used = set()

    def search(position):
        if position == row_count:
            return True

        row = order[position]
        for column in candidates[row]:
            if column in used:
                continue
            used.add(column)
            result[row] = column
            if search(position + 1):
                return True
            used.remove(column)
            result[row] = None
        return False

    return result if search(0) else None


#ВЫЧИСЛЕНИЕ ДЕЛЬТЫ
def calculate_deltas(tableau, c, basis):
    cb = [c[index] for index in basis]
    zj = []
    for j in range(len(c)):
        zj.append(sum(cb[i] * tableau[i][j] for i in range(len(basis))))
    deltas = [zj[j] - c[j] for j in range(len(c))]
    return deltas


#ОПРЕДЕЛЕНИЕ РЕКОМЕНДУЕМОГО МЕТОДА
def determine_method(tableau, c, basis):
    if basis is None:
        return {
            "method": "artificial_basis_required",
            "message": "Не удалось сформировать начальный базис. "
                       "Требуется метод искусственного базиса."
        }

    deltas = calculate_deltas(tableau, c, basis)
    b = [tableau[i][-1] for i in range(len(tableau))]

    has_negative_b = any(value < -EPSILON for value in b)
    has_negative_delta = any(
        value < -EPSILON for value in deltas
    )

    if not has_negative_b and not has_negative_delta:
        return {
            "method": "optimal",
            "message": "Все b_i >= 0 и все Delta_j >= 0. "
                       "Оптимальное решение уже найдено."
        }

    if not has_negative_b and has_negative_delta:
        return {
            "method": "primal_simplex",
            "message": "Все свободные члены неотрицательны, "
                       "но есть отрицательные оценки. "
                       "Применяем прямой симплекс-метод."
        }

    if has_negative_b and not has_negative_delta:
        return {
            "method": "dual_simplex",
            "message": "Есть отрицательные свободные члены, "
                       "но все оценки неотрицательны. "
                       "Применяем двойственный симплекс-метод."
        }

    return {
        "method": "variable_substitution_required",
        "message": "Есть отрицательные свободные члены "
                   "и отрицательные оценки. "
                   "Требуется замена переменных перед двойственным симплексом."
    }


#ПЕРЕСЧЁТ СИМПЛЕКСНОЙ ТАБЛИЦЫ
def pivot_operation(tableau, pivot_row, pivot_column):
    pivot_value = tableau[pivot_row][pivot_column]
    if abs(pivot_value) <= EPSILON:
        raise ZeroDivisionError("Разрешающий элемент равен нулю.")

    tableau[pivot_row] = [
        value / pivot_value
        for value in tableau[pivot_row]
    ]

    for i in range(len(tableau)):
        if i == pivot_row:
            continue
        factor = tableau[i][pivot_column]
        tableau[i] = [
            tableau[i][j] - factor * tableau[pivot_row][j]
            for j in range(len(tableau[i]))
        ]

    for i in range(len(tableau)):
        for j in range(len(tableau[i])):
            if abs(tableau[i][j]) <= EPSILON:
                tableau[i][j] = 0.0


#ПОСТРОЕНИЕ СИМПЛЕКСНОЙ ТАБЛИЦЫ
def build_tableau(A, b):
    return [A[i][:] + [b[i]] for i in range(len(A))]


def recover_solution(tableau, basis, variable_count):
    solution = [0.0] * variable_count
    for i, column in enumerate(basis):
        if column < variable_count:
            solution[column] = tableau[i][-1]
    return solution


def calculate_objective(c, solution):
    return sum(c[i] * solution[i] for i in range(len(solution)))


def get_tableau_state(tableau, basis, c):
    deltas = calculate_deltas(tableau, c, basis)
    cb = [c[index] for index in basis]
    zj = [
        sum(cb[i] * tableau[i][j] for i in range(len(basis)))
        for j in range(len(c))
    ]
    return {
        "b": [row[-1] for row in tableau],
        "deltas": deltas,
        "cb": cb,
        "zj": zj
    }


def make_result(status, message, steps, solution=None, objective_value=None,
                tableau=None, basis=None, deltas=None, problem=None):
    return {
        "status": status,
        "message": message,
        "solution": solution,
        "objective_value": objective_value,
        "steps": steps,
        "tableau": [row[:] for row in tableau] if tableau is not None else None,
        "basis": basis[:] if basis is not None else None,
        "deltas": deltas[:] if deltas is not None else None,
        "problem": problem
    }

# ПОДГОТОВКА ЗАМЕНЫ ПЕРЕМЕННЫХ ДЛЯ ДВОЙСТВЕННОГО СИМПЛЕКСА
def prepare_variable_substitution(c, A, b, signs):
    n, normalized_signs = validate_problem(c, A, b, signs, "max")

    c = [float(value) for value in c]
    A = [[float(value) for value in row] for row in A]
    b = [float(value) for value in b]

    # Поиск верхних границ исходных переменных
    upper_bounds = [None] * n

    for i, sign in enumerate(normalized_signs):
        if sign != "<=" or b[i] < -EPSILON:
            continue

        # Ограничение должно иметь неотрицательные коэффициенты
        if any(value < -EPSILON for value in A[i]):
            continue

        for j in range(n):
            coefficient = A[i][j]

            if coefficient > EPSILON:
                bound = b[i] / coefficient

                if upper_bounds[j] is None:
                    upper_bounds[j] = bound
                else:
                    upper_bounds[j] = min(
                        upper_bounds[j],
                        bound
                    )

    # Проверка, что для каждой переменной найдена граница
    if any(value is None for value in upper_bounds):
        return {
            "success": False,
            "message": (
                "Не удалось определить конечные верхние границы "
                "для всех переменных. Автоматическая замена невозможна."
            )
        }

    # Проверка корректности границ
    if any(value < -EPSILON for value in upper_bounds):
        return {
            "success": False,
            "message": "Обнаружена отрицательная верхняя граница переменной."
        }

    upper_bounds = [
        max(0.0, value) for value in upper_bounds
    ]

    # Замена x_j = M_j - x'_j
    new_c = [-value for value in c]
    new_A = []
    new_b = []

    for i in range(len(A)):
        row = [-value for value in A[i]]

        shift = sum(
            A[i][j] * upper_bounds[j]
            for j in range(n)
        )

        new_A.append(row)
        new_b.append(b[i] - shift)

    new_signs = normalized_signs[:]

    # Добавление ограничений x'_j <= M_j
    for j in range(n):
        row = [0.0] * n
        row[j] = 1.0

        new_A.append(row)
        new_b.append(upper_bounds[j])
        new_signs.append("<=")

    return {
        "success": True,
        "c": new_c,
        "A": new_A,
        "b": new_b,
        "signs": new_signs,
        "upper_bounds": upper_bounds,
        "objective_constant": sum(
            c[j] * upper_bounds[j]
            for j in range(n)
        )
    }
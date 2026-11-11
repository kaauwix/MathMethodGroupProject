# MethodSelection.py

from AuxiliaryFun import (
    normalize_problem, build_tableau, find_initial_basis,
    determine_method, add_text_step, make_result,
    calculate_deltas, expand_free_variables, collapse_solution, EPSILON
)


def force_prepare_dual(c, A, b, signs, objective, var_types=None):
    """
    Принудительно приводит задачу к виду для двойственного симплекса:
    - свободные переменные заменяются x = x' - x'';
    - умножает >= на -1;
    - добавляет слабые переменные +1 для неравенств.
    """
    n = len(c)
    if var_types is None:
        var_types = ["nonneg"] * n

    original_c = [float(v) for v in c]
    original_A = [[float(v) for v in row] for row in A]
    original_b = [float(v) for v in b]

    # 0. Расширяем свободные переменные
    exp_c, exp_A, mapping, base_names = expand_free_variables(
        original_c, original_A, var_types
    )

    m = len(exp_A)
    n_exp = len(exp_c)
    work_A = [row[:] for row in exp_A]
    work_b = list(original_b)
    work_signs = list(signs)

    factor = 1.0 if objective == "max" else -1.0
    work_c = [factor * v for v in exp_c]
    names = base_names[:]

    steps = []
    add_text_step(steps, "Подготовка к двойственному симплексу",
                  "Умножаем ограничения >= на -1, чтобы получить отрицательные свободные члены, "
                  "и добавляем слабые переменные только для неравенств. Равенства не трогаем.")

    if any(kind == "free" for (_, kind, _, _) in mapping):
        free_list = [f"x{j+1}" for (j, kind, _, _) in mapping if kind == "free"]
        add_text_step(steps, "Замена свободных переменных",
                      f"Свободные переменные {', '.join(free_list)} заменены на x = x' - x''.")

    # 1. Умножаем >= на -1 (чтобы получить отрицательные b)
    for i in range(m):
        if work_signs[i] == ">=":
            work_A[i] = [-v for v in work_A[i]]
            work_b[i] = -work_b[i]
            work_signs[i] = "<="

    # 2. Добавляем slack ТОЛЬКО для <= (после преобразования все >= стали <=)
    slack = 0
    for i in range(m):
        if work_signs[i] == "=":
            continue
        slack += 1
        for row in work_A:
            row.append(0.0)
        work_A[i][-1] = 1.0
        work_c.append(0.0)
        names.append(f"s{slack}")

    basis = find_initial_basis(work_A)
    if basis is None:
        return None

    tableau = build_tableau(work_A, work_b)

    problem = {
        "c": work_c,
        "A": work_A,
        "b": work_b,
        "signs": work_signs,
        "variable_names": names,
        "original_c": original_c,
        "original_A": original_A,
        "original_b": original_b,
        "original_variables_count": n_exp,
        "original_var_types": var_types[:],
        "mapping": mapping,
        "objective": objective,
        "objective_factor": factor,
        "steps": steps,
    }

    return tableau, basis, work_c, names, problem


def solve_problem(c, A, b, signs, objective="max", max_iterations=1000,
                  force_method=None, var_types=None):

    if var_types is None:
        var_types = ["nonneg"] * len(c)

    # 0. ПРИНУДИТЕЛЬНЫЙ ДВОЙСТВЕННЫЙ
    if force_method == "dual":
        res = force_prepare_dual(c, A, b, signs, objective, var_types=var_types)
        if res is None:
            return make_result(
                "dual_not_applicable",
                "Не удалось построить начальную таблицу для двойственного симплекса "
                "(нет единичного базиса после добавления slack-переменных).",
                [], problem=None
            )
        tableau, basis, work_c, names, problem = res
        from DualSimplex import dual_simplex_prepared
        # Запускаем с force=True, чтобы пропустить проверку Δ >= 0
        return dual_simplex_prepared(
            problem, tableau, basis, max_iterations, force=True
        )

    # 1. ПРИНУДИТЕЛЬНЫЙ МИБ
    if force_method == "mib":
        problem = normalize_problem(c, A, b, signs, objective, var_types=var_types)
        from MIB import artificial_basis_prepared
        return artificial_basis_prepared(problem, max_iterations)

    # 2. ПРОВЕРЯЕМ ДОСТУПНОСТЬ ДВОЙСТВЕННОГО (не решаем, только собираем инфо)
    dual_info = None
    dual_res = force_prepare_dual(c, A, b, signs, objective, var_types=var_types)
    if dual_res is not None:
        tableau_d, basis_d, work_c_d, names_d, problem_d = dual_res
        deltas_d = calculate_deltas(tableau_d, work_c_d, basis_d)
        has_neg_b = any(row[-1] < -EPSILON for row in tableau_d)
        has_neg_delta = any(d < -EPSILON for d in deltas_d)

        # Если есть b < 0 и нет Δ < 0 — идеальный случай
        if has_neg_b and not has_neg_delta:
            dual_info = {
                "status": "dual_available",
                "message": "Задача двойственно допустима (b < 0, все Δ ≥ 0).",
                "problem": problem_d,
                "tableau": tableau_d,
                "basis": basis_d,
                "c": work_c_d,
                "names": names_d,
            }

        # Если есть b < 0 И ЕСТЬ Δ < 0 — предлагаем принудительный запуск
        elif has_neg_b and has_neg_delta:
            dual_info = {
                "status": "dual_available_force",
                "message": "Есть b < 0 и Δ < 0. Двойственный можно попробовать принудительно.",
                "problem": problem_d,
                "tableau": tableau_d,
                "basis": basis_d,
                "c": work_c_d,
                "names": names_d,
            }

    # 3. ОБЫЧНЫЙ АВТОВЫБОР (нормализованная задача)
    problem = normalize_problem(c, A, b, signs, objective, var_types=var_types)
    steps = problem["steps"]
    tableau = build_tableau(problem["A"], problem["b"])
    basis = find_initial_basis(problem["A"])

    # 3a. Есть готовый базис — прямой/двойственный симплекс
    if basis is not None:
        info = determine_method(tableau, problem["c"], basis)
        add_text_step(steps, "Выбор метода", info["message"], info)

        if info["method"] in ("optimal", "primal_simplex"):
            from PrimalSimplex import primal_simplex_prepared
            result = primal_simplex_prepared(problem, tableau, basis, max_iterations)
            if dual_info is not None:
                result["dual_available"] = dual_info["status"]
                result["dual_data"] = dual_info
            return result

        if info["method"] == "dual_simplex":
            from DualSimplex import dual_simplex_prepared
            result = dual_simplex_prepared(problem, tableau, basis, max_iterations)
            if dual_info is not None:
                result["dual_available"] = dual_info["status"]
                result["dual_data"] = dual_info
            return result

    # 3b. Базиса нет, но двойственный доступен — предлагаем ВЫБОР:
    #     двойственный ИЛИ МИБ. Не решаем автоматически.
    if dual_info is not None:
        add_text_step(
            steps, "Выбор метода",
            "Начального единичного базиса в нормализованной задаче нет, "
            "но задача двойственно допустима. Доступны два пути: "
            "двойственный симплекс (без искусственных переменных) или МИБ."
        )
        return {
            "status": dual_info["status"],
            "message": ("Доступен двойственный симплекс. "
                        "Альтернатива — метод искусственного базиса (МИБ)."),
            "steps": steps,
            "solution": None,
            "objective_value": None,
            "tableau": tableau,
            "basis": basis,
            "problem": problem,
            "dual_data": dual_info,
            "mib_available": True,
        }

    # 3c. Ничего не осталось — только МИБ
    add_text_step(steps, "Выбор метода",
                  "Нет начального базиса и двойственный неприменим. Запускаем МИБ.")
    from MIB import artificial_basis_prepared
    return artificial_basis_prepared(problem, max_iterations)
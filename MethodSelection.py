# Задача нормализуется один раз, после чего передаётся в прямой симплекс, двойственный симплекс или метод искусственного базиса

from AuxiliaryFun import (normalize_problem, build_tableau, find_initial_basis, determine_method, add_text_step, make_result)


def solve_problem(c, A, b, signs, objective="max", max_iterations=1000):
    # Приведение исходной задачи к единому виду
    problem = normalize_problem(c, A, b, signs, objective)
    steps = problem["steps"]

    # Построение начальной симплекс-таблицы и поиск единичного базиса
    tableau = build_tableau(problem["A"], problem["b"])
    basis = find_initial_basis(problem["A"])

    # Если единичный базис отсутствует, используем метод искусственного базиса
    if basis is None:
        add_text_step(steps, "Выбор метода", "Начальный единичный базис отсутствует. Запускаем метод искусственного базиса.")
        from MIB import artificial_basis_prepared
        return artificial_basis_prepared(problem, max_iterations)

    # Определение допустимости текущего плана и подходящего метода решения.
    info = determine_method(tableau, problem["c"], basis)
    add_text_step(steps, "Выбор метода", info["message"], info)

    # Если начальный план уже оптимален, используем прямой симплекс для завершения
    if info["method"] == "optimal":
        from PrimalSimplex import primal_simplex_prepared
        return primal_simplex_prepared(problem, tableau, basis, max_iterations)

    # Если выполнено условие прямой допустимости, запускаем прямой симплекс-метод
    if info["method"] == "primal_simplex":
        from PrimalSimplex import primal_simplex_prepared
        return primal_simplex_prepared(problem, tableau, basis, max_iterations)

    # Если выполнено условие двойственной допустимости, запускаем двойственный симплекс-метод
    if info["method"] == "dual_simplex":
        from DualSimplex import dual_simplex_prepared
        return dual_simplex_prepared(problem, tableau, basis, max_iterations)

    # Если одновременно нарушены прямая и двойственная допустимость, текущая реализация не поддерживает автоматический выбор метода.
    add_text_step(
        steps,
        "Метод не выбран",
        "Одновременно нарушены прямая и двойственная допустимость. Для такого начального состояния отдельный алгоритм пока не реализован."
    )

    return make_result(
        "method_not_applicable",
        "Не удалось автоматически выбрать метод для текущего начального состояния.",
        steps,
        tableau=tableau,
        basis=basis,
        problem=problem
    )
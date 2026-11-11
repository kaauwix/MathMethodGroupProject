from MethodSelection import solve_problem
from SolveLP import solve_primal_and_dual
from TransportSolver import solve_transport

# --- Тест 1: Прямой симплекс-метод ---
print("=== ТЕСТ 1: Прямой симплекс ===")
c1 = [2, 1]
A1 = [
    [-1, 3],
    [2, 1],
    [1, -1]
]
b1 = [6, 9, 3]
signs1 = ["<=", "<=", "<="]

res1 = solve_problem(c1, A1, b1, signs1, objective="max")
print(f"Статус: {res1['status']}")
print(f"Сообщение: {res1['message']}")
print(f"Решение: {res1['solution']}")
print(f"Значение функции: {res1['objective_value']}")
print("-" * 30)


# --- Тест 2: Двойственный симплекс-метод ---
print("\n=== ТЕСТ 2: Двойственный симплекс ===")
# Пример из лекции (слайд 49)
c2 = [2, 1]
A2 = [
    [3, 1],
    [4, 3]
]
b2 = [3, 5]
signs2 = [">=", ">="]

res2 = solve_problem(c2, A2, b2, signs2, objective="min")
print(f"Статус: {res2['status']}")
print(f"Сообщение: {res2['message']}")
print(f"Решение: {res2['solution']}")
print(f"Значение функции: {res2['objective_value']}")
print("-" * 30)


# --- Тест 3: Твоя проверка оптимальности ---
print("\n=== ТЕСТ 3: Проверка оптимальности ===")
try:
    from optimal import check_optimality

    # Берем решение из Теста 1
    if res1['status'] == 'optimal':
        x_check = res1['solution']
        check_res = check_optimality(c1, A1, b1, x_check, signs1)
        print(f"Статус проверки: {check_res['status']}")
        print(f"Сообщение: {check_res['message']}")
        print(f"Найденное y: {check_res.get('y')}")
    else:
        print("Тест 1 не дал оптимального решения, проверять нечего.")
except ImportError:
    print("Файл optimal.py не найден. Создай его и добавь функцию check_optimality.")

print("\n=== ТЕСТ 4: Метод искусственного базиса ===")
c4 = [1, 1, 2, 1]
A4 = [[1, 3, 2, 1], [2, 0, 1, -1], [-3, 1, -1, 2]]
b4 = [8, 1, 1]
signs4 = ["=", "=", "="]

res4 = solve_problem(c4, A4, b4, signs4, objective="max")
print(f"Статус: {res4['status']}")
print(f"Решение: {res4['solution']}")
print(f"Значение функции: {res4['objective_value']}")

# --- Тест 5: Одновременное решение прямой и двойственной задач ---
print("\n=== ТЕСТ 5: Прямая и двойственная задачи ===")

c5 = [3, 2]
A5 = [
    [1, 1],
    [2, 1]
]
b5 = [4, 6]
signs5 = ["<=", "<="]

res5 = solve_primal_and_dual(c5, A5, b5, signs5, objective="max")

# Результат прямой задачи
print("\nПрямая задача:")
print(f"Статус: {res5['primal']['status']}")
print(f"Решение: {res5['primal']['solution']}")
print(f"Значение функции: {res5['primal']['objective_value']}")

# Результат двойственной задачи
print("\nДвойственная задача:")
if res5["dual"] is not None:
    print(f"Статус: {res5['dual']['status']}")
    print(f"Решение: {res5['dual']['solution']}")
    print(f"Значение функции: {res5['dual']['objective_value']}")
    print(f"Сообщение: {res5['dual']['message']}")
else:
    print("Двойственная задача не решена.")

# Явная формулировка двойственной задачи
print("\nФормулировка двойственной задачи:")
if res5["dual_formulation"] is not None:
    print(f"Целевая функция: {res5['dual_formulation']['c']}")
    print(f"Матрица ограничений: {res5['dual_formulation']['A']}")
    print(f"Правые части: {res5['dual_formulation']['b']}")
    print(f"Знаки ограничений: {res5['dual_formulation']['signs']}")
    print(f"Направление: {res5['dual_formulation']['objective']}")
else:
    print("Явная формулировка отсутствует.")

# Проверка равенства целевых функций
if res5["primal"]["status"] == "optimal" and res5["dual"] is not None:
    print("\nПроверка теоремы двойственности:")
    primal_value = res5["primal"]["objective_value"]
    dual_value = res5["dual"]["objective_value"]

    print(f"Целевая функция прямой задачи: {primal_value}")
    print(f"Целевая функция двойственной задачи: {dual_value}")
    print(f"Равенство: {'выполнено' if abs(primal_value - dual_value) < 1e-6 else 'не выполнено'}")

print("-" * 30)

# --- ТЕСТ 6: Транспортная задача — метод потенциалов ---
print("\n=== ТЕСТ 6: Транспортная задача ===")

c6 = [
    [4, 1],
    [2, 3]
]

a6 = [30, 20]
b6 = [20, 30]

res6 = solve_transport(c6, a6, b6, init_method="nw")

print(f"Статус: {res6['status']}")
print(f"Метод начального плана: северо-западный угол")
print(f"Минимальная стоимость перевозок: {res6['Z']}")

print("\nПлан перевозок:")
for row in res6["x"]:
    print(row)

print("\nОтчёт по итерациям:")
print(res6["report"])

print("Проверка запасов:")
for i in range(res6["m"]):
    print(
        f"A{i+1}: "
        f"{sum(res6['x'][i])} / {res6['a'][i]}"
    )

print("\nПроверка спроса:")
for j in range(res6["n"]):
    transported = sum(res6["x"][i][j] for i in range(res6["m"]))
    print(f"B{j+1}: {transported} / {res6['b'][j]}")

print("-" * 30)
# test_run.py
from MethodSelection import solve_problem

# --- Тест 1: Прямой симплекс-метод ---
print("=== ТЕСТ 1: Прямой симплекс ===")
c1 = [3, 2]
A1 = [
    [1, 1],
    [2, 1]
]
b1 = [4, 6]
signs1 = ["<=", "<="]

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

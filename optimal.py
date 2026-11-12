from AuxiliaryFun import EPSILON
import numpy as np

def check_optimality(c, A, b, x, signs, var_types=None, free_vars=None, tolerance=1e-7):
    # Объединяем параметры (на случай, если интерфейс передает то free_vars, то var_types)
    if var_types is None:
        var_types = ["free" if j in (free_vars or []) else "nonneg" for j in range(len(c))]
    if free_vars is None:
        free_vars = [j for j, t in enumerate(var_types) if t == "free"]

    steps = []
    def add_step(title, desc):
        steps.append({"title": title, "description": desc})

    n = len(c)
    m = len(A)
    
    def fmt_num(val):
        if abs(val) < tolerance: return "0"
        if val == int(val): return str(int(val))
        return f"{val:g}"

    x_str = ", ".join([fmt_num(v) for v in x])
    add_step("Проверяемый план", f"x = ({x_str})")

    def format_expression(coeffs, prefix, var_names):
        terms = []
        for j, val in enumerate(coeffs):
            if abs(val) < tolerance: continue
            if not terms:
                if abs(val - 1.0) < tolerance: term = f"{prefix}_{var_names[j]}"
                elif abs(val + 1.0) < tolerance: term = f"-{prefix}_{var_names[j]}"
                else: term = f"{fmt_num(val)}{prefix}_{var_names[j]}"
            else:
                sign = "+" if val > 0 else "-"
                abs_val = abs(val)
                if abs(abs_val - 1.0) < tolerance: term = f"{sign} {prefix}_{var_names[j]}"
                else: term = f"{sign} {fmt_num(abs_val)}{prefix}_{var_names[j]}"
            terms.append(term)
        return " ".join(terms) if terms else "0"

    # ШАГ 1: Прямая задача
    step1_desc = "<b>Исходные ограничения:</b><br>"
    direct_f_str = format_expression(c, "x", list(range(1, n+1)))
    step1_desc += f"f(x) = {direct_f_str} → max<br>"
    
    for i in range(m):
        lhs_str = format_expression(A[i], "x", list(range(1, n+1)))
        sign = signs[i]
        sign_html = sign.replace("<", "&lt;").replace(">", "&gt;")
        step1_desc += f"• {lhs_str} {sign_html} {fmt_num(b[i])}<br>"
        
    # Указываем типы переменных
    types_str = ", ".join([f"x_{j+1} {'свободна' if var_types[j] == 'free' else '≥ 0'}" for j in range(n)])
    step1_desc += f"• {types_str}<br>"
    
    step1_desc += "<br><b>Преобразование к каноническому виду (все '≤'):</b><br>"
    A_norm = [row[:] for row in A]
    b_norm = b[:]
    
    for i, sign in enumerate(signs):
        lhs_str = format_expression(A[i], "x", list(range(1, n+1)))
        if sign == ">=":
            A_norm[i] = [-v for v in A_norm[i]]
            b_norm[i] = -b_norm[i]
            new_lhs = format_expression(A_norm[i], "x", list(range(1, n+1)))
            step1_desc += f"• {lhs_str} ≥ {fmt_num(b[i])} → умножим на -1: {new_lhs} ≤ {fmt_num(b_norm[i])}<br>"
        elif sign == "=":
            A_norm.append([-v for v in A_norm[i]])
            b_norm.append(-b_norm[i])
            new_lhs = format_expression(A_norm[i], "x", list(range(1, n+1)))
            step1_desc += f"• {lhs_str} = {fmt_num(b[i])} → {lhs_str} ≤ {fmt_num(b[i])} и {new_lhs} ≤ {fmt_num(b_norm[-1])}<br>"
        else:
            step1_desc += f"• {lhs_str} ≤ {fmt_num(b[i])} (без изменений)<br>"
            
    add_step("Прямая задача", step1_desc)

    m2 = len(A_norm)

    # Проверка допустимости (с учетом свободных переменных)
    is_feasible = True
    for i in range(m2):
        lhs = sum(A_norm[i][j] * x[j] for j in range(n))
        if lhs > b_norm[i] + tolerance:
            is_feasible = False
            break
    for j in range(n):
        if var_types[j] == "nonneg" and x[j] < -tolerance:
            is_feasible = False
            break

    if not is_feasible:
        add_step("Вывод", "План x недопустим. Проверка невозможна.")
        return {"status": "not_feasible", "message": "План недопустим", "y": None, "steps": steps}

    # ШАГ 2: Двойственная задача
    dual_desc = "<b>Построение двойственной задачи:</b><br>"
    dual_f_str = format_expression(b_norm, "y", list(range(1, m2+1)))
    dual_desc += f"g(y) = {dual_f_str} → min<br>"
    
    dual_desc += "Ограничения двойственной задачи:<br>"
    for j in range(n):
        col_coeffs = [A_norm[i][j] for i in range(m2)]
        lhs_str = format_expression(col_coeffs, "y", list(range(1, m2+1)))
        # Для свободных переменных знак равенства!
        sign_d = "=" if var_types[j] == "free" else "≥"
        dual_desc += f"• {lhs_str} {sign_d} {fmt_num(c[j])}<br>"
    dual_desc += "• y ≥ 0<br>"
    add_step("Двойственная задача", dual_desc)

    # ШАГ 3: Множества
    # В J_x включаем только неотрицательные с x > 0
    J_x = [j for j in range(n) if var_types[j] == "nonneg" and x[j] > tolerance]
    # Свободные переменные всегда дают уравнение (A^j, y) = c_j
    free_J = [j for j in range(n) if var_types[j] == "free"]
    
    I_x = [i for i in range(m2) if sum(A_norm[i][j] * x[j] for j in range(n)) < b_norm[i] - tolerance]
    
    j_str = ", ".join([str(j+1) for j in J_x]) if J_x else "∅"
    f_str = ", ".join([str(j+1) for j in free_J]) if free_J else "∅"
    i_str = ", ".join([str(i+1) for i in I_x]) if I_x else "∅"
    
    step3_desc = f"• J_x (неотриц. > 0) = {{{j_str}}}<br>"
    step3_desc += f"• Свободные переменные = {{{f_str}}}<br>"
    step3_desc += f"• I_x = {{{i_str}}}<br>"
    add_step("Множества индексов", step3_desc)

    # ШАГ 4: Система уравнений
    eq_desc = ""
    eq_rows = []
    rhs = []
    
    # Уравнения от J_x
    for j in J_x:
        eq_rows.append([A_norm[i][j] for i in range(m2)])
        rhs.append(c[j])
        terms = []
        for i in range(m2):
            if abs(A_norm[i][j]) > tolerance:
                val = A_norm[i][j]
                sign = "+" if val > 0 else "-"
                abs_val = abs(val)
                coeff_str = "" if abs(abs_val - 1.0) < tolerance else f"{fmt_num(abs_val)}"
                if not terms:
                    terms.append(f"{'-' if val < 0 else ''}{coeff_str}y_{i+1}")
                else:
                    terms.append(f"{sign} {coeff_str}y_{i+1}")
        eq_desc += f"• {' '.join(terms)} = {fmt_num(c[j])}<br>"
    
    # Уравнения от свободных переменных
    for j in free_J:
        eq_rows.append([A_norm[i][j] for i in range(m2)])
        rhs.append(c[j])
        terms = []
        for i in range(m2):
            if abs(A_norm[i][j]) > tolerance:
                val = A_norm[i][j]
                sign = "+" if val > 0 else "-"
                abs_val = abs(val)
                coeff_str = "" if abs(abs_val - 1.0) < tolerance else f"{fmt_num(abs_val)}"
                if not terms:
                    terms.append(f"{'-' if val < 0 else ''}{coeff_str}y_{i+1}")
                else:
                    terms.append(f"{sign} {coeff_str}y_{i+1}")
        eq_desc += f"• {' '.join(terms)} = {fmt_num(c[j])} <i>(свободная x_{j+1})</i><br>"
        
    for i in I_x:
        row = [0.0] * m2
        row[i] = 1.0
        eq_rows.append(row)
        rhs.append(0.0)
        eq_desc += f"• y_{i+1} = 0<br>"

    add_step("Система уравнений", eq_desc)

    if not eq_rows:
        add_step("Решение системы", "Система пуста. y=0. План оптимален.")
        return {"status": "optimal", "message": "План оптимален", "y": [0.0]*m2, "steps": steps}

    M = np.array(eq_rows, dtype=float)
    r = np.array(rhs, dtype=float)
    rank_M = np.linalg.matrix_rank(M, tol=tolerance)
    rank_aug = np.linalg.matrix_rank(np.column_stack([M, r]), tol=tolerance)
    
    if rank_M != rank_aug:
        add_step("Решение системы", "<span style='color:red;'>Система противоречива.</span> План <b>НЕ ОПТИМАЛЕН</b>.")
        return {"status": "not_optimal", "message": "Система противоречива.", "y": None, "steps": steps}

    y_candidate, *_ = np.linalg.lstsq(M, r, rcond=None)
    y_candidate = np.round(y_candidate, 12)
    for i in range(len(y_candidate)):
        if abs(y_candidate[i]) < tolerance:
            y_candidate[i] = 0.0

    # Решение системы (визуализация)
    solve_desc = ""
    if len(eq_rows) < m2 and len(I_x) == 0:
        solve_desc += "Так как уравнений меньше, чем неизвестных, система имеет множество решений.<br>"
        solve_desc += "Найдено одно (базисное) решение:<br>"
        for i, val in enumerate(y_candidate):
            solve_desc += f"&nbsp;&nbsp;y_{i+1} = {fmt_num(val)}<br>"
    else:
        # (Оставим твою красивую логику подстановки, если она нужна)
        solve_desc += "Найденные значения:<br>"
        for i, val in enumerate(y_candidate):
            solve_desc += f"&nbsp;&nbsp;y_{i+1} = {fmt_num(val)}<br>"

    add_step("Нахождение y", solve_desc)

    # ШАГ 5: Проверка
    check_y_desc = ""
    y_valid = True
    
    check_y_desc += "<b>Проверка неотрицательности y:</b><br>"
    for i, val in enumerate(y_candidate):
        if val < -tolerance: y_valid = False
        check_y_desc += f"&nbsp;&nbsp;y_{i+1} = {fmt_num(val)} {'≥' if val >= -tolerance else '&lt;'} 0<br>"

    check_y_desc += "<br><b>Проверка ограничений двойственной задачи:</b><br>"
    for j in range(n):
        val = sum(A_norm[i][j] * y_candidate[i] for i in range(m2))
        
        # Для свободных переменных проверяем равенство, для остальных - неравенство
        if var_types[j] == "free":
            if abs(val - c[j]) > tolerance:
                y_valid = False
            sign_str = "="
        else:
            if val < c[j] - tolerance: 
                y_valid = False
            sign_str = "≥" if val >= c[j] - tolerance else "&lt;"
        
        terms = []
        for i in range(m2):
            if abs(A_norm[i][j]) > tolerance:
                terms.append(f"({fmt_num(A_norm[i][j])})*{fmt_num(y_candidate[i])}")
        
        calc_str = " + ".join(terms) if terms else "0"
        
        note = " <i>(свободная)</i>" if var_types[j] == "free" else ""
        check_y_desc += f"&nbsp;&nbsp;Для x_{j+1}{note}: {calc_str} = {fmt_num(val)} {sign_str} c_{j+1} ({fmt_num(c[j])})<br><br>"

    if not y_valid:
        check_y_desc += "<span style='color:red;'>Условия не выполнены.</span> План <b>НЕ ОПТИМАЛЕН</b>."
        add_step("Проверка y", check_y_desc)
        return {"status": "not_optimal", "message": "y недопустим.", "y": [float(fmt_num(v)) for v in y_candidate], "steps": steps}

    check_y_desc += "<span style='color:green;'>Все условия выполнены.</span>"
    add_step("Проверка y", check_y_desc)
    add_step("Вывод", "<b>План ОПТИМАЛЕН.</b>")

    return {
        "status": "optimal", "message": "План оптимален.", "y": [float(fmt_num(v)) for v in y_candidate],
        "J_x": J_x, "I_x": I_x, "steps": steps
    }
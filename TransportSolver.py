# TransportSolver.py
# Транспортная задача — метод потенциалов.
# используйте функцию solve_transport(...) в конце файла.


class TransportSolver:
    def __init__(self, c, a, b, init_method="least_cost"):
        self.c = [list(row) for row in c]
        self.a_orig = list(a)
        self.b_orig = list(b)
        self.init_method = init_method
        self._balance()

    def _balance(self):
        m, n = len(self.c), len(self.c[0])
        sa, sb = sum(self.a_orig), sum(self.b_orig)
        self.a = list(self.a_orig)
        self.b = list(self.b_orig)
        self.dummy_info = None

        if abs(sa - sb) > 1e-9:
            if sa > sb:
                for row in self.c:
                    row.append(0)
                self.b.append(sa - sb)
                self.dummy_info = f"Добавлен фиктивный потребитель B{n+1} (спрос {sa-sb:g})"
            else:
                self.c.append([0] * n)
                self.a.append(sb - sa)
                self.dummy_info = f"Добавлен фиктивный поставщик A{m+1} (запас {sb-sa:g})"
        self.m, self.n = len(self.c), len(self.c[0])

    def solve(self):
        self.x = [[0] * self.n for _ in range(self.m)]
        self.basic = set()

        if self.init_method == "nw":
            self._northwest_corner()
        else:
            self._least_cost()

        self._complete_basis()
        self.iterations = []

        for _ in range(500):
            state = {
                'x': [row[:] for row in self.x],
                'basic': set(self.basic),
                'u': None, 'v': None,
                'enter': None, 'cycle': [], 'signs': [], 'theta': 0, 'leave': None
            }

            u, v = self._compute_potentials()
            state['u'], state['v'] = u, v

            deltas = {}
            for i in range(self.m):
                for j in range(self.n):
                    if (i, j) not in self.basic:
                        deltas[(i, j)] = self.c[i][j] - u[i] - v[j]

            neg = [(cell, d) for cell, d in deltas.items() if d < -1e-9]
            if not neg:
                self.iterations.append(state)
                break

            enter = min(neg, key=lambda nd: (nd[1], nd[0][0], nd[0][1]))[0]
            cycle = self._find_cycle(enter)
            if not cycle:
                raise RuntimeError("Цикл не найден")

            signs = ['+' if k % 2 == 0 else '-' for k in range(len(cycle))]
            theta = min(self.x[cell[0]][cell[1]] for cell, s in zip(cycle, signs) if s == '-')

            for cell, s in zip(cycle, signs):
                if s == '+':
                    self.x[cell[0]][cell[1]] += theta
                else:
                    self.x[cell[0]][cell[1]] -= theta
                    if abs(self.x[cell[0]][cell[1]]) < 1e-9:
                        self.x[cell[0]][cell[1]] = 0

            leaving = [cell for cell, s in zip(cycle, signs) if s == '-' and abs(self.x[cell[0]][cell[1]]) < 1e-9]
            leave = leaving[0]

            state['enter'], state['cycle'], state['signs'] = enter, cycle, signs
            state['theta'], state['leave'] = theta, leave
            self.iterations.append(state)

            self.basic.add(enter)
            self.basic.discard(leave)
        else:
            raise RuntimeError("Не сошлось за 500 итераций")

        self.Z = sum(self.c[i][j] * self.x[i][j] for i in range(self.m) for j in range(self.n))
        return self

    def _northwest_corner(self):
        a_rem, b_rem = list(self.a), list(self.b)
        i = j = 0
        while i < self.m and j < self.n:
            alloc = min(a_rem[i], b_rem[j])
            self.x[i][j] = alloc
            self.basic.add((i, j))
            a_rem[i] -= alloc
            b_rem[j] -= alloc
            if abs(a_rem[i]) < 1e-9: i += 1
            if abs(b_rem[j]) < 1e-9: j += 1

    def _least_cost(self):
        a_rem, b_rem = list(self.a), list(self.b)
        done_r, done_c = set(), set()
        cells = sorted([(self.c[i][j], i, j) for i in range(self.m) for j in range(self.n)])
        for cost, i, j in cells:
            if i in done_r or j in done_c: continue
            alloc = min(a_rem[i], b_rem[j])
            self.x[i][j] = alloc
            self.basic.add((i, j))
            a_rem[i] -= alloc
            b_rem[j] -= alloc
            if abs(a_rem[i]) < 1e-9: done_r.add(i)
            if abs(b_rem[j]) < 1e-9: done_c.add(j)

    def _complete_basis(self):
        parent = list(range(self.m + self.n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb: return False
            parent[ra] = rb
            return True

        for i, j in self.basic: union(i, self.m + j)
        cands = sorted([(self.c[i][j], i, j) for i in range(self.m) for j in range(self.n) if (i, j) not in self.basic])
        for cost, i, j in cands:
            if len(self.basic) >= self.m + self.n - 1: break
            if union(i, self.m + j):
                self.basic.add((i, j))
                self.x[i][j] = 0

    def _compute_potentials(self):
        u, v = [None] * self.m, [None] * self.n
        u[0] = 0
        changed = True
        while changed:
            changed = False
            for (i, j) in self.basic:
                if u[i] is not None and v[j] is None:
                    v[j] = self.c[i][j] - u[i]; changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = self.c[i][j] - v[j]; changed = True
        return u, v

    def _find_cycle(self, enter):
        adj = {i: [] for i in range(self.m + self.n)}
        for (i, j) in self.basic:
            adj[i].append(self.m + j)
            adj[self.m + j].append(i)

        i0, j0 = enter
        start, target = i0, self.m + j0
        parent = {start: None}
        stack = [start]
        while stack:
            node = stack.pop()
            if node == target: break
            for nb in adj[node]:
                if nb not in parent:
                    parent[nb] = node
                    stack.append(nb)

        path = []
        node = target
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()

        cells = [enter]
        for k in range(len(path) - 1):
            a, b = path[k], path[k + 1]
            if a < self.m: cells.append((a, b - self.m))
            else: cells.append((b, a - self.m))
        return cells

    def render_table(self, x, basic, u, v):
        lines = []
        W_C = 13  # Ширина колонки данных
        W_S = 8   # Ширина колонки запаса
        W_U = 8   # Ширина колонки u_i
        W_R = 6   # Ширина колонки имен строк (A1, Спрос)

        # Верхняя шапка (B1, B2...)
        head = f"{'':<{W_R}}|" + "|".join(f"{'B'+str(j+1):^{W_C}}" for j in range(self.n)) + f"|{'Запас':^{W_S}}|{'u_i':^{W_U}}|"
        lines.append(head)

        # Строка Спрос (сразу под B-шками)
        row_b = f"{'Спрос':<{W_R}}|" + "|".join(f"{self.b[j]:^{W_C}.1f}" for j in range(self.n)) + f"|{'':^{W_S}}|{'':^{W_U}}|"
        lines.append(row_b)

        # Разделитель
        border = f"{'-'*W_R}+" + "+".join(["-"*W_C]*self.n) + f"+{'-'*W_S}+{'-'*W_U}+"
        lines.append(border)

        for i in range(self.m):
            # Верхняя строка ячейки: Стоимость (справа)
            row_top = f"{'A'+str(i+1):<{W_R}}|"
            for j in range(self.n):
                row_top += f"{self.c[i][j]:>{W_C-2}}  |"
            row_top += f"{self.a[i]:>{W_S-1}.1f} |"
            row_top += f"{u[i]:>{W_U-1}.1f} |" if u is not None else f"{'':^{W_U}}|"

            # Нижняя строка ячейки: Перевозка (слева) и u_i+v_j (справа)
            row_bot = f"{'':<{W_R}}|"
            for j in range(self.n):
                x_val = x[i][j]
                is_basic = (i, j) in basic
                x_str = f"{x_val:g}" if x_val > 1e-9 else ("0*" if is_basic else "")
                uv_str = f"({u[i] + v[j]:g})" if (u is not None and not is_basic) else ""

                row_bot += f" {x_str:<5} {uv_str:>4} |"

            row_bot += f"{'':^{W_S}}|{'':^{W_U}}|"

            lines.append(row_top)
            lines.append(row_bot)
            lines.append(border)

        # Строка v_j (в самом низу)
        if v is not None:
            row_v = f"{'v_j':<{W_R}}|" + "|".join(f"{v[j]:^{W_C}.1f}" for j in range(self.n)) + f"|{'':^{W_S}}|{'':^{W_U}}|"
            lines.append(row_v)
            lines.append(border)

        return "\n".join(lines)

    def report(self):
        L = []
        if self.dummy_info:
            L.append(f"⚠ {self.dummy_info}\n")

        for it_idx, state in enumerate(self.iterations):
            if it_idx == 0:
                L.append(f"ИТЕРАЦИЯ {it_idx}: НАЧАЛЬНЫЙ ПЛАН")
            elif it_idx == len(self.iterations) - 1:
                L.append(f"ИТЕРАЦИЯ {it_idx}: ОПТИМАЛЬНЫЙ ПЛАН ✓")
            else:
                L.append(f"ИТЕРАЦИЯ {it_idx}")

            L.append(self.render_table(state['x'], state['basic'], state['u'], state['v']))

            z_val = sum(self.c[i][j] * state['x'][i][j] for i in range(self.m) for j in range(self.n))
            L.append(f"Z = {z_val:.2f}\n")

            if state['u'] is not None:
                if not state['enter']:
                    L.append("Все Δ_ij = c_ij - (u_i + v_j) ≥ 0.")
                    L.append("План ОПТИМАЛЕН. Дальнейшие улучшения невозможны.\n")
                else:
                    enter = state['enter']
                    cycle = state['cycle']
                    signs = state['signs']
                    theta = state['theta']
                    leave = state['leave']

                    L.append(f"Есть Δ < 0. Входит клетка A{enter[0]+1}-B{enter[1]+1}")

                    cyc_str = " → ".join(f"A{c[0]+1}-B{c[1]+1} ({s})" for c, s in zip(cycle, signs))
                    L.append(f"Цикл: {cyc_str}")
                    L.append(f"θ = {theta:g}")
                    L.append(f"Выходит клетка A{leave[0]+1}-B{leave[1]+1}\n")

            L.append("─" * 80 + "\n")

        return "\n".join(L)


def solve_transport(c, a, b, init_method="least_cost"):
    """
    Обёртка для вызова из единого GUI.

    Возвращает словарь:
      status      — 'optimal'
      Z           — значение целевой функции (стоимость перевозок)
      x           — матрица перевозок (m × n)
      iterations  — список состояний для пошаговой отрисовки
      report      — текстовый отчёт (готов к печати в ScrolledText)
      dummy_info  — строка про фиктивного поставщика/потребителя (или None)
      m, n        — размеры (с учётом фиктивных)
      a, b, c     — сбалансированные данные
    """
    solver = TransportSolver(c, a, b, init_method).solve()
    return {
        "status": "optimal",
        "Z": solver.Z,
        "x": solver.x,
        "iterations": solver.iterations,
        "report": solver.report(),
        "dummy_info": solver.dummy_info,
        "m": solver.m,
        "n": solver.n,
        "a": solver.a,
        "b": solver.b,
        "c": solver.c,
    }
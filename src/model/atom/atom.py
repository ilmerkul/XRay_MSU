import numpy as np
import math


class Atom:
    def __init__(self, element, x, y, z, occ, Biso):
        self.element = element
        self.frac = np.array([x, y, z])
        self.occ = occ
        self.Biso = Biso


class AtomicScatteringFactor:
    def __init__(self, filename: str):
        self.data = {}
        self._parse(filename)

    def _parse(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        i = 0
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            if line.startswith('#S'):
                parts = line.split(maxsplit=2)
                if len(parts) < 3:
                    i += 1
                    continue
                symbol = parts[2].strip()

                i += 1
                while i < n:
                    data_line = lines[i].strip()
                    if data_line and not data_line.startswith('#'):
                        tokens = data_line.split()
                        if len(tokens) == 11:
                            a = list(map(float, tokens[:5]))
                            c = float(tokens[5])
                            b = list(map(float, tokens[6:]))
                            self.data[symbol] = (a, b, c)
                        break
                    i += 1
                i += 1
            else:
                i += 1

    def get_f0(self, symbol, k):
        if symbol not in self.data:
            raise ValueError(f"Символ '{symbol}' не найден в данных.")
        a, b, c = self.data[symbol]
        k2 = k * k
        result = c
        for i in range(5):
            result += a[i] * math.exp(-b[i] * k2)
        return result

    def get_f0_from_theta_lambda(self, symbol, theta_deg, lambda_ang):
        theta_rad = math.radians(theta_deg)
        k = math.sin(theta_rad) / lambda_ang
        return self.get_f0(symbol, k)

    def available_symbols(self):
        return list(self.data.keys())

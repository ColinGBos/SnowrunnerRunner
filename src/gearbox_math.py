def generate_exp_func(
    a: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
):
    if a == 0:
        raise ValueError("a must be non-zero")
    if x1 == x2:
        raise ValueError("x1 and x2 must be different")

    def h(i: float) -> float:
        return a * (i ** x2 - i ** x1) - (y2 - y1)

    low = 1e-12
    high = 2.0

    h_low = h(low)
    h_high = h(high)

    while h_low * h_high > 0:
        high *= 2.0
        h_high = h(high)
        if high > 1e6:
            raise ValueError("Could not bracket a solution for b")

    for _ in range(200):
        mid = (low + high) / 2.0
        h_mid = h(mid)

        if abs(h_mid) < 1e-12:
            base = mid
            break

        if h_low * h_mid <= 0:
            high = mid
            h_high = h_mid
        else:
            low = mid
            h_low = h_mid
    else:
        base = (low + high) / 2.0

    shift_factor = y1 - a * (base ** x1)

    def func(x: float) -> float:
        return a * (base ** x) + shift_factor

    return func

if __name__ == "__main__":
    f= generate_exp_func(1.3, 1, 1.5, 8, 15)
    print(
        f"Offroad: f1:{f(1):.2f}, f2:{f(2):.2f}, f3:{f(3):.2f}, f4:{f(4):.2f}, f5:{f(5):.2f}, f6:{f(6):.2f}, f7:{f(7):.2f}, f8:{f(8):.2f}")

    f = generate_exp_func(10.0, 1, 1.5, 8, 15)
    print(f"Highrange: f1:{f(1):.2f}, f2:{f(2):.2f}, f3:{f(3):.2f}, f4:{f(4):.2f}, f5:{f(5):.2f}, f6:{f(6):.2f}, f7:{f(7):.2f}, f8:{f(8):.2f}")

    f = generate_exp_func(3.0, 1, 1.5, 8, 15)
    print(
        f"Finetune: f1:{f(1):.2f}, f2:{f(2):.2f}, f3:{f(3):.2f}, f4:{f(4):.2f}, f5:{f(5):.2f}, f6:{f(6):.2f}, f7:{f(7):.2f}, f8:{f(8):.2f}")


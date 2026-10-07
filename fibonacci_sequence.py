def fibonacci_sequence(n):
    sequence = [1, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

print(fibonacci_sequence(10))

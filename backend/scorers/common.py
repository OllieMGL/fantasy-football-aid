
def normalise(value, min_value, max_value):
    if max_value == min_value:
        return 0.5  # everyone identical - avoid dividing by zero
    return (value - min_value) / (max_value - min_value)
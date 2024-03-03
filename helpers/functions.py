def parse_total_duration(total_duration: list) -> str:
    all_seconds = 0
    for duration in total_duration:
        parts = duration.split(', ')
        seconds = 0
        for part in parts:
            value, unit = part.split(' ')
            value = int(value)
            if unit.endswith('s'):
                unit = unit[:-1]
            if unit == 'second':
                seconds += value
            elif unit == 'minute':
                seconds += value * 60
            elif unit == 'hour':
                seconds += value * 3600
            elif unit == 'day':
                seconds += value * 86400
        all_seconds += seconds

    days, remainder = divmod(all_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    result = []
    if days > 0:
        result.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        result.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        result.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        result.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return ', '.join(result)
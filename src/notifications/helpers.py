def chunks(lst, n):
    """Varieble 'n' represent the max size of a batch"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

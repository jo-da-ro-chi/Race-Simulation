def parse_float(in_number):
    try:
        float(in_number)
        return True
    except:
        return False


def parse_int(in_number):
    try:
        int(in_number)
        return True
    except:
        return False

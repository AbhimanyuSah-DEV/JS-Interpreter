import math

def to_string(val):
    from environment import JS_UNDEFINED, JSObject, JSArray, JSFunction, JS_EMPTY
    if val is JS_EMPTY:
        return ""
    if val is JS_UNDEFINED:
        return "undefined"
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if isinstance(val, float):
            if math.isnan(val):
                return "NaN"
            if math.isinf(val):
                return "Infinity" if val > 0 else "-Infinity"
            if val.is_integer():
                return str(int(val))
        return str(val)
    if isinstance(val, str):
        return val
    if isinstance(val, JSArray):
        return ",".join(to_string(x) for x in val.elements)
    if isinstance(val, JSFunction):
        name_str = f" {val.name}" if val.name else ""
        return f"[function{name_str}]"
    if isinstance(val, JSObject):
        # Check if the object has a custom toString method defined
        # For simplicity, we just return the standard string representation
        return "[object Object]"
    return str(val)

def to_number(val):
    from environment import JS_UNDEFINED, JSObject, JSArray, JS_EMPTY
    if val is JS_EMPTY:
        return float('nan')
    if val is JS_UNDEFINED:
        return float('nan')
    if val is None:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return 0
        # Check standard representations
        try:
            if s.startswith('0x') or s.startswith('0X'):
                return int(s, 16)
            if s.startswith('0b') or s.startswith('0B'):
                return int(s, 2)
            if s.startswith('0o') or s.startswith('0O'):
                return int(s, 8)
            # Try float/int parsing
            if '.' in s or 'e' in s.lower():
                return float(s)
            else:
                return int(s)
        except ValueError:
            return float('nan')
    if isinstance(val, (JSArray, JSObject)):
        return to_number(to_string(val))
    return float('nan')

def to_boolean(val):
    from environment import JS_UNDEFINED, JSObject, JS_EMPTY
    if val is JS_EMPTY:
        return False
    if val is JS_UNDEFINED:
        return False
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if val == 0 or (isinstance(val, float) and math.isnan(val)):
            return False
        return True
    if isinstance(val, str):
        return len(val) > 0
    if isinstance(val, JSObject):
        return True
    return True

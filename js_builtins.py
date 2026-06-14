import math
import random
import time
import json
from environment import JS_UNDEFINED, JS_EMPTY, JSObject, JSArray, JSBuiltinFunction
from coercion import to_string, to_number, to_boolean

# Format value for console.log
def format_val(val, in_obj=False):
    if val is JS_EMPTY:
        return "<empty>"
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
        if in_obj:
            return f"'{val}'"
        return val
    if isinstance(val, JSArray):
        items = []
        i = 0
        n = len(val.elements)
        while i < n:
            if val.elements[i] is JS_EMPTY:
                empty_count = 0
                while i < n and val.elements[i] is JS_EMPTY:
                    empty_count += 1
                    i += 1
                items.append(f"<{empty_count} empty item{'s' if empty_count > 1 else ''}>")
            else:
                items.append(format_val(val.elements[i], in_obj=True))
                i += 1
        return f"[ {', '.join(items)} ]" if items else "[]"
    if isinstance(val, JSBuiltinFunction) or hasattr(val, 'closure_env'):
        name_str = f" {val.name}" if val.name else ""
        return f"[Function{name_str}]"
    if isinstance(val, JSObject):
        items = []
        for k, v in val.properties.items():
            items.append(f"{k}: {format_val(v, in_obj=True)}")
        return f"{{ {', '.join(items)} }}" if items else "{}"
    return str(val)

def console_log(evaluator, args):
    print(" ".join(format_val(arg) for arg in args))
    return JS_UNDEFINED

# Global coercion constructors
def js_string_constructor(evaluator, args):
    return to_string(args[0]) if args else ""

def js_number_constructor(evaluator, args):
    return to_number(args[0]) if args else 0

def js_boolean_constructor(evaluator, args):
    return to_boolean(args[0]) if args else False

def js_array_constructor(evaluator, args):
    if len(args) == 1 and isinstance(args[0], (int, float)):
        n = int(args[0])
        return JSArray([JS_EMPTY] * n)
    return JSArray(list(args))

# Global helper functions
def js_parse_int(evaluator, args):
    if not args:
        return float('nan')
    s = to_string(args[0]).strip()
    radix = 10
    if len(args) > 1:
        radix_val = to_number(args[1])
        if not math.isnan(radix_val) and not math.isinf(radix_val):
            radix = int(radix_val)
            if radix < 2 or radix > 36:
                return float('nan')
    
    # Simple prefix detection if radix is not specified or 16
    if (radix == 10 or radix == 16) and (s.startswith('0x') or s.startswith('0X')):
        s = s[2:]
        radix = 16
        
    if not s:
        return float('nan')
        
    # Find longest parseable prefix
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    valid_chars = digits[:radix]
    res_str = ""
    for char in s.lower():
        if char in valid_chars or (char == '-' and not res_str) or (char == '+' and not res_str):
            res_str += char
        else:
            break
            
    if not res_str or res_str == '-' or res_str == '+':
        return float('nan')
        
    try:
        return int(res_str, radix)
    except ValueError:
        return float('nan')

def js_parse_float(evaluator, args):
    if not args:
        return float('nan')
    s = to_string(args[0]).strip()
    if not s:
        return float('nan')
    
    # Find longest parseable float prefix
    res_str = ""
    for char in s.lower():
        if char in "0123456789.e+-" or (char == 'i' and res_str == "inf") or (char == 'n' and res_str == "nan"):
            res_str += char
        else:
            break
    try:
        return float(res_str)
    except ValueError:
        return float('nan')

# Array Methods
def array_push(array, evaluator, args):
    for arg in args:
        array.elements.append(arg)
    return len(array.elements)

def array_pop(array, evaluator, args):
    if not array.elements:
        return JS_UNDEFINED
    val = array.elements.pop()
    return JS_UNDEFINED if val is JS_EMPTY else val

def array_shift(array, evaluator, args):
    if not array.elements:
        return JS_UNDEFINED
    val = array.elements.pop(0)
    return JS_UNDEFINED if val is JS_EMPTY else val

def array_unshift(array, evaluator, args):
    for arg in reversed(args):
        array.elements.insert(0, arg)
    return len(array.elements)

def array_slice(array, evaluator, args):
    n = len(array.elements)
    start = int(to_number(args[0])) if len(args) > 0 else 0
    end = int(to_number(args[1])) if len(args) > 1 else n
    if start < 0: start = max(n + start, 0)
    else: start = min(start, n)
    if end < 0: end = max(n + end, 0)
    else: end = min(end, n)
    
    sliced = array.elements[start:end]
    return JSArray(sliced)

def array_splice(array, evaluator, args):
    n = len(array.elements)
    start = int(to_number(args[0])) if len(args) > 0 else 0
    if start < 0: start = max(n + start, 0)
    else: start = min(start, n)
    
    delete_count = int(to_number(args[1])) if len(args) > 1 else (n - start)
    delete_count = max(0, min(delete_count, n - start))
    
    deleted = array.elements[start : start + delete_count]
    array.elements[start : start + delete_count] = args[2:]
    
    # map holes in deleted to undefined
    return JSArray([JS_UNDEFINED if x is JS_EMPTY else x for x in deleted])

def array_index_of(array, evaluator, args):
    if not args:
        return -1
    search = args[0]
    start = int(to_number(args[1])) if len(args) > 1 else 0
    n = len(array.elements)
    if start < 0: start = max(n + start, 0)
    else: start = min(start, n)
    
    from evaluator import strict_equal
    for i in range(start, n):
        val = array.elements[i]
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        if strict_equal(curr, search):
            return i
    return -1

def array_includes(array, evaluator, args):
    if not args:
        return False
    search = args[0]
    start = int(to_number(args[1])) if len(args) > 1 else 0
    n = len(array.elements)
    if start < 0: start = max(n + start, 0)
    else: start = min(start, n)
    
    from evaluator import strict_equal
    for i in range(start, n):
        val = array.elements[i]
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        # includes uses SameValueZero (NaN includes NaN is true)
        if strict_equal(curr, search) or (isinstance(curr, float) and isinstance(search, float) and math.isnan(curr) and math.isnan(search)):
            return True
    return False

def array_map(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.map expects a callback function")
    callback = args[0]
    mapped = []
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        res = evaluator.call_function(callback, [curr, i, array])
        mapped.append(res)
    return JSArray(mapped)

def array_filter(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.filter expects a callback function")
    callback = args[0]
    filtered = []
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        res = evaluator.call_function(callback, [curr, i, array])
        if to_boolean(res):
            filtered.append(curr)
    return JSArray(filtered)

def array_for_each(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.forEach expects a callback function")
    callback = args[0]
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        evaluator.call_function(callback, [curr, i, array])
    return JS_UNDEFINED

def array_reduce(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.reduce expects a callback function")
    callback = args[0]
    has_initial = len(args) > 1
    
    start_idx = 0
    if has_initial:
        accumulator = args[1]
    else:
        # Find first non-empty element
        i = 0
        while i < len(array.elements) and array.elements[i] is JS_EMPTY:
            i += 1
        if i >= len(array.elements):
            raise TypeError("Reduce of empty array with no initial value")
        accumulator = array.elements[i]
        start_idx = i + 1
        
    for i in range(start_idx, len(array.elements)):
        val = array.elements[i]
        if val is not JS_EMPTY:
            accumulator = evaluator.call_function(callback, [accumulator, val, i, array])
    return accumulator

def array_every(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.every expects a callback function")
    callback = args[0]
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        res = evaluator.call_function(callback, [curr, i, array])
        if not to_boolean(res):
            return False
    return True

def array_some(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.some expects a callback function")
    callback = args[0]
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        res = evaluator.call_function(callback, [curr, i, array])
        if to_boolean(res):
            return True
    return False

def array_concat(array, evaluator, args):
    result_elements = list(array.elements)
    for arg in args:
        if isinstance(arg, JSArray):
            result_elements.extend(arg.elements)
        else:
            result_elements.append(arg)
    return JSArray(result_elements)

def array_join(array, evaluator, args):
    sep = to_string(args[0]) if args else ","
    return sep.join(to_string(x) for x in array.elements)

def array_reverse(array, evaluator, args):
    array.elements.reverse()
    return array

def array_sort(array, evaluator, args):
    compare_fn = args[0] if args else None
    import functools
    
    def compare(item1, item2):
        val1 = JS_UNDEFINED if item1 is JS_EMPTY else item1
        val2 = JS_UNDEFINED if item2 is JS_EMPTY else item2
        
        if val1 is JS_UNDEFINED and val2 is JS_UNDEFINED:
            return 0
        if val1 is JS_UNDEFINED:
            return 1
        if val2 is JS_UNDEFINED:
            return -1
            
        if compare_fn is not None:
            res = evaluator.call_function(compare_fn, [val1, val2])
            res_num = to_number(res)
            if math.isnan(res_num):
                return 0
            return -1 if res_num < 0 else 1 if res_num > 0 else 0
        else:
            s1 = to_string(val1)
            s2 = to_string(val2)
            return -1 if s1 < s2 else 1 if s1 > s2 else 0
            
    array.elements.sort(key=functools.cmp_to_key(compare))
    return array

def array_find(array, evaluator, args):
    if not args:
        raise TypeError("Array.prototype.find expects a callback function")
    callback = args[0]
    for i, val in enumerate(array.elements):
        curr = JS_UNDEFINED if val is JS_EMPTY else val
        res = evaluator.call_function(callback, [curr, i, array])
        if to_boolean(res):
            return curr
    return JS_UNDEFINED

def get_array_method(array, name):
    methods = {
        'push': array_push,
        'pop': array_pop,
        'shift': array_shift,
        'unshift': array_unshift,
        'slice': array_slice,
        'splice': array_splice,
        'indexOf': array_index_of,
        'includes': array_includes,
        'map': array_map,
        'filter': array_filter,
        'forEach': array_for_each,
        'reduce': array_reduce,
        'every': array_every,
        'some': array_some,
        'concat': array_concat,
        'join': array_join,
        'reverse': array_reverse,
        'sort': array_sort,
        'find': array_find,
    }
    if name in methods:
        return JSBuiltinFunction(name, lambda eval, args: methods[name](array, eval, args))
    return None

# Math Helper functions
def math_round(evaluator, args):
    if not args:
        return float('nan')
    x = to_number(args[0])
    if math.isnan(x) or math.isinf(x):
        return x
    return math.floor(x + 0.5)

def js_math_max(evaluator, args):
    if not args:
        return float('-inf')
    nums = []
    for arg in args:
        num = to_number(arg)
        if math.isnan(num):
            return float('nan')
        nums.append(num)
    return max(nums)

def js_math_min(evaluator, args):
    if not args:
        return float('inf')
    nums = []
    for arg in args:
        num = to_number(arg)
        if math.isnan(num):
            return float('nan')
        nums.append(num)
    return min(nums)

# Date Helper functions
def js_date(evaluator, args):
    return time.strftime("%a %b %d %Y %H:%M:%S GMT%z")

# JSON Helper functions
def json_stringify(evaluator, args):
    if not args:
        return JS_UNDEFINED
    val = args[0]
    def serialize(v):
        if v is JS_EMPTY or v is JS_UNDEFINED or v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            if math.isnan(v) or math.isinf(v):
                return "null"
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            return str(v)
        if isinstance(v, str):
            escaped = v.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            return f'"{escaped}"'
        if isinstance(v, JSArray):
            items = [serialize(x) for x in v.elements]
            return f"[{','.join(items)}]"
        if isinstance(v, JSObject):
            items = []
            for k, x in v.properties.items():
                if not hasattr(x, 'closure_env') and not isinstance(x, JSBuiltinFunction):
                    items.append(f'"{k}":{serialize(x)}')
            return f"{{{','.join(items)}}}"
        return "null"
    return serialize(val)

def json_parse(evaluator, args):
    if not args:
        return JS_UNDEFINED
    s = to_string(args[0])
    try:
        py_val = json.loads(s)
        def convert(v):
            if isinstance(v, dict):
                return JSObject({k: convert(val) for k, val in v.items()})
            if isinstance(v, list):
                return JSArray([convert(x) for x in v])
            return v
        return convert(py_val)
    except Exception:
        raise ValueError("SyntaxError: Unexpected token in JSON")

# Object Helper functions
def object_keys(evaluator, args):
    if not args:
        return JSArray([])
    obj = args[0]
    if isinstance(obj, JSObject):
        return JSArray(list(obj.properties.keys()))
    return JSArray([])

def object_values(evaluator, args):
    if not args:
        return JSArray([])
    obj = args[0]
    if isinstance(obj, JSObject):
        return JSArray(list(obj.properties.values()))
    return JSArray([])

def object_entries(evaluator, args):
    if not args:
        return JSArray([])
    obj = args[0]
    if isinstance(obj, JSObject):
        return JSArray([JSArray([k, v]) for k, v in obj.properties.items()])
    return JSArray([])

# String Helper functions
def string_substring(string_val, args):
    start = int(to_number(args[0])) if len(args) > 0 else 0
    end = int(to_number(args[1])) if len(args) > 1 else len(string_val)
    if start < 0: start = 0
    if end < 0: end = 0
    if start > end:
        start, end = end, start
    return string_val[start:end]

def string_split(string_val, args):
    if len(args) == 0:
        return JSArray([string_val])
    sep = to_string(args[0])
    if sep == "":
        return JSArray(list(string_val))
    parts = string_val.split(sep)
    return JSArray(parts)

def string_replace(string_val, args):
    if len(args) < 2:
        return string_val
    target = to_string(args[0])
    replacement = to_string(args[1])
    return string_val.replace(target, replacement, 1)

def string_index_of(string_val, args):
    if len(args) == 0:
        return -1
    search = to_string(args[0])
    start = int(to_number(args[1])) if len(args) > 1 else 0
    if start < 0: start = 0
    if start >= len(string_val):
        return -1 if search != "" else len(string_val)
    return string_val.find(search, start)

def string_replace_all(string_val, args):
    if len(args) < 2:
        return string_val
    target = to_string(args[0])
    replacement = to_string(args[1])
    return string_val.replace(target, replacement)

def string_slice(string_val, args):
    n = len(string_val)
    start = int(to_number(args[0])) if len(args) > 0 else 0
    end = int(to_number(args[1])) if len(args) > 1 else n
    if start < 0: start = max(n + start, 0)
    else: start = min(start, n)
    if end < 0: end = max(n + end, 0)
    else: end = min(end, n)
    return string_val[start:end]

def get_string_method(string_val, name):
    methods = {
        'substring': lambda eval, args: string_substring(string_val, args),
        'split': lambda eval, args: string_split(string_val, args),
        'replace': lambda eval, args: string_replace(string_val, args),
        'replaceAll': lambda eval, args: string_replace_all(string_val, args),
        'slice': lambda eval, args: string_slice(string_val, args),
        'indexOf': lambda eval, args: string_index_of(string_val, args),
        'includes': lambda eval, args: to_string(args[0]) in string_val if args else False,
        'startsWith': lambda eval, args: string_val.startswith(to_string(args[0])) if args else False,
        'endsWith': lambda eval, args: string_val.endswith(to_string(args[0])) if args else False,
        'charAt': lambda eval, args: string_val[int(to_number(args[0]))] if args and 0 <= to_number(args[0]) < len(string_val) else "",
        'toLowerCase': lambda eval, args: string_val.lower(),
        'toUpperCase': lambda eval, args: string_val.upper(),
        'trim': lambda eval, args: string_val.strip(),
        'trimStart': lambda eval, args: string_val.lstrip(),
        'trimEnd': lambda eval, args: string_val.rstrip(),
    }
    if name in methods:
        return JSBuiltinFunction(name, methods[name])
    return None

# Initialize global environment
def create_global_environment():
    from environment import Environment
    env = Environment(parent=None, is_function_scope=True)
    
    # console
    console = JSObject()
    console.set_property('log', JSBuiltinFunction('log', console_log))
    env.define('console', console, kind='var')
    
    # Math
    Math = JSObject()
    Math.set_property('PI', math.pi)
    Math.set_property('E', math.e)
    Math.set_property('random', JSBuiltinFunction('random', lambda eval, args: random.random()))
    Math.set_property('floor', JSBuiltinFunction('floor', lambda eval, args: math.floor(to_number(args[0])) if args else float('nan')))
    Math.set_property('ceil', JSBuiltinFunction('ceil', lambda eval, args: math.ceil(to_number(args[0])) if args else float('nan')))
    Math.set_property('round', JSBuiltinFunction('round', math_round))
    Math.set_property('abs', JSBuiltinFunction('abs', lambda eval, args: abs(to_number(args[0])) if args else float('nan')))
    Math.set_property('max', JSBuiltinFunction('max', js_math_max))
    Math.set_property('min', JSBuiltinFunction('min', js_math_min))
    Math.set_property('pow', JSBuiltinFunction('pow', lambda eval, args: to_number(args[0]) ** to_number(args[1]) if len(args) >= 2 else float('nan')))
    Math.set_property('sqrt', JSBuiltinFunction('sqrt', lambda eval, args: math.sqrt(to_number(args[0])) if args and to_number(args[0]) >= 0 else float('nan')))
    env.define('Math', Math, kind='var')
    
    # Date
    DateObj = JSBuiltinFunction('Date', js_date)
    DateObj.set_property('now', JSBuiltinFunction('now', lambda eval, args: int(time.time() * 1000)))
    env.define('Date', DateObj, kind='var')
    
    # JSON
    JsonObj = JSObject()
    JsonObj.set_property('stringify', JSBuiltinFunction('stringify', json_stringify))
    JsonObj.set_property('parse', JSBuiltinFunction('parse', json_parse))
    env.define('JSON', JsonObj, kind='var')
    
    # Object
    ObjectObj = JSBuiltinFunction('Object', lambda eval, args: JSObject())
    ObjectObj.set_property('keys', JSBuiltinFunction('keys', object_keys))
    ObjectObj.set_property('values', JSBuiltinFunction('values', object_values))
    ObjectObj.set_property('entries', JSBuiltinFunction('entries', object_entries))
    env.define('Object', ObjectObj, kind='var')
    
    # Core Global Classes
    env.define('Array', JSBuiltinFunction('Array', js_array_constructor), kind='var')
    env.define('String', JSBuiltinFunction('String', js_string_constructor), kind='var')
    env.define('Number', JSBuiltinFunction('Number', js_number_constructor), kind='var')
    env.define('Boolean', JSBuiltinFunction('Boolean', js_boolean_constructor), kind='var')
    
    # Core Global Functions
    env.define('parseInt', JSBuiltinFunction('parseInt', js_parse_int), kind='var')
    env.define('parseFloat', JSBuiltinFunction('parseFloat', js_parse_float), kind='var')
    env.define('isNaN', JSBuiltinFunction('isNaN', lambda eval, args: math.isnan(to_number(args[0])) if args else True), kind='var')
    env.define('isFinite', JSBuiltinFunction('isFinite', lambda eval, args: not math.isnan(to_number(args[0])) and not math.isinf(to_number(args[0])) if args else False), kind='var')
    
    # Core Globals
    env.define('undefined', JS_UNDEFINED, kind='var')
    env.define('NaN', float('nan'), kind='var')
    env.define('Infinity', float('inf'), kind='var')
    
    return env

class Undefined:
    def __repr__(self):
        return "undefined"
    def __str__(self):
        return "undefined"

JS_UNDEFINED = Undefined()

class Empty:
    def __repr__(self):
        return "<empty>"
    def __str__(self):
        return "<empty>"

JS_EMPTY = Empty()

class JSObject:
    def __init__(self, properties=None):
        self.properties = properties or {}

    def get_property(self, name):
        return self.properties.get(str(name), JS_UNDEFINED)

    def set_property(self, name, value):
        self.properties[str(name)] = value

    def __repr__(self):
        props = ", ".join(f"{k}: {repr(v)}" for k, v in self.properties.items())
        return f"{{ {props} }}"

class JSArray(JSObject):
    def __init__(self, elements=None):
        super().__init__()
        self.elements = elements or []

    def get_property(self, name):
        if name == 'length':
            return len(self.elements)
        
        # Check integer index
        if isinstance(name, str) and name.isdigit():
            idx = int(name)
            if 0 <= idx < len(self.elements):
                val = self.elements[idx]
                return JS_UNDEFINED if val is JS_EMPTY else val
            return JS_UNDEFINED

        # Check local properties
        val = super().get_property(name)
        if val is not JS_UNDEFINED:
            return val

        # Dynamically import js_builtins to retrieve array prototype methods
        import js_builtins
        method = js_builtins.get_array_method(self, name)
        if method is not None:
            return method

        return JS_UNDEFINED

    def set_property(self, name, value):
        if name == 'length':
            from coercion import to_number
            try:
                new_len = int(to_number(value))
                if new_len < 0:
                    raise ValueError("Invalid array length")
            except Exception:
                new_len = 0
            
            if new_len < len(self.elements):
                self.elements = self.elements[:new_len]
            else:
                self.elements.extend([JS_EMPTY] * (new_len - len(self.elements)))
        elif isinstance(name, str) and name.isdigit():
            idx = int(name)
            if idx < 0:
                super().set_property(name, value)
            else:
                if idx >= len(self.elements):
                    self.elements.extend([JS_EMPTY] * (idx - len(self.elements)))
                # If we extend beyond current elements, the intermediate ones are JS_EMPTY.
                # Wait, if idx >= len(self.elements), we extended it by idx - len(self.elements) elements of JS_EMPTY.
                # Then we append/set the value at idx.
                if idx >= len(self.elements):
                    self.elements.append(value)
                else:
                    self.elements[idx] = value
        else:
            super().set_property(name, value)

    def __repr__(self):
        return f"[ {', '.join(repr(x) for x in self.elements)} ]"

class JSFunction(JSObject):
    def __init__(self, name, params, body, closure_env):
        super().__init__()
        self.name = name
        self.params = params  # list of strings (parameter names)
        self.body = body      # BlockStatement or other AST node
        self.closure_env = closure_env

    def __repr__(self):
        name_str = f" {self.name}" if self.name else ""
        return f"[function{name_str}]"

class JSBuiltinFunction(JSObject):
    def __init__(self, name, func):
        super().__init__()
        self.name = name
        self.func = func  # Python callable: func(evaluator, args)

    def call(self, evaluator, args):
        return self.func(evaluator, args)

    def __repr__(self):
        return f"[function {self.name}]"

class Environment:
    def __init__(self, parent=None, is_function_scope=False):
        self.parent = parent
        self.is_function_scope = is_function_scope
        self.bindings = {}  # name -> {"value": val, "is_const": bool, "kind": str}

    def define(self, name, value, kind):
        if kind in ('let', 'const'):
            if name in self.bindings:
                raise TypeError(f"Identifier '{name}' has already been declared")
            self.bindings[name] = {"value": value, "is_const": (kind == 'const'), "kind": kind}
        elif kind == 'var':
            # Traverse up to the nearest function scope or root scope
            curr = self
            while curr.parent is not None and not curr.is_function_scope:
                curr = curr.parent
            # In JS, var declarations are hoisted and can be redeclared.
            curr.bindings[name] = {"value": value, "is_const": False, "kind": 'var'}

    def get(self, name):
        curr = self
        while curr is not None:
            if name in curr.bindings:
                return curr.bindings[name]["value"]
            curr = curr.parent
        raise NameError(f"ReferenceError: {name} is not defined")

    def assign(self, name, value):
        curr = self
        while curr is not None:
            if name in curr.bindings:
                binding = curr.bindings[name]
                if binding["is_const"]:
                    raise TypeError("Assignment to constant variable.")
                binding["value"] = value
                return
            curr = curr.parent
        
        # If not found in any environment, assign to global scope (root)
        global_env = self
        while global_env.parent is not None:
            global_env = global_env.parent
        global_env.bindings[name] = {"value": value, "is_const": False, "kind": 'var'}

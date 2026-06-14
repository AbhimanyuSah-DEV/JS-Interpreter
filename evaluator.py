import math
from environment import (
    JS_UNDEFINED,
    JSObject,
    JSArray,
    JSFunction,
    JSBuiltinFunction,
    Environment
)
from coercion import to_string, to_number, to_boolean

class ReturnException(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class JSException(Exception):
    def __init__(self, value):
        super().__init__(str(value))
        self.value = value


def strict_equal(a, b):
    if type(a) != type(b):
        return False
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) or math.isnan(b):
            return False
    return a == b

def loose_equal(a, b):
    if type(a) == type(b):
        if isinstance(a, float) and isinstance(b, float):
            if math.isnan(a) or math.isnan(b):
                return False
        return a == b
    if (a is None and b is JS_UNDEFINED) or (a is JS_UNDEFINED and b is None):
        return True
    if isinstance(a, bool):
        return loose_equal(1 if a else 0, b)
    if isinstance(b, bool):
        return loose_equal(a, 1 if b else 0)
    if isinstance(a, (int, float)) and isinstance(b, str):
        return loose_equal(a, to_number(b))
    if isinstance(a, str) and isinstance(b, (int, float)):
        return loose_equal(to_number(a), b)
    if isinstance(a, (JSArray, JSObject)) and isinstance(b, (int, float, str)):
        return loose_equal(to_string(a), b)
    if isinstance(a, (int, float, str)) and isinstance(b, (JSArray, JSObject)):
        return loose_equal(a, to_string(b))
    return False

class Evaluator:
    def evaluate(self, node, env, create_scope=True):
        if node is None:
            return JS_UNDEFINED
        
        # Check node type and route to visitor method
        node_type = node.type
        method_name = f"visit_{node_type}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise NotImplementedError(f"AST Node type '{node_type}' is not implemented in Evaluator.")
        
        # Pass create_scope if it's a BlockStatement, otherwise standard args
        if node_type == 'BlockStatement':
            return visitor(node, env, create_scope)
        return visitor(node, env)

    def call_function(self, func, args):
        if isinstance(func, JSBuiltinFunction):
            return func.call(self, args)
        elif isinstance(func, JSFunction):
            new_env = Environment(parent=func.closure_env, is_function_scope=True)
            for i, param_node in enumerate(func.params):
                if param_node.type == 'RestElement':
                    rest_name = param_node.argument.name
                    from environment import JS_EMPTY
                    rest_vals = [JS_UNDEFINED if x is JS_EMPTY else x for x in args[i:]]
                    new_env.define(rest_name, JSArray(rest_vals), kind='let')
                    break
                elif param_node.type == 'Identifier':
                    val = args[i] if i < len(args) else JS_UNDEFINED
                    new_env.define(param_node.name, val, kind='let')
            
            if func.body.type == 'BlockStatement':
                try:
                    self.evaluate(func.body, new_env, create_scope=False)
                except ReturnException as ret:
                    return ret.value
                return JS_UNDEFINED
            else:
                # Arrow function with single expression body
                return self.evaluate(func.body, new_env)
        else:
            raise TypeError(f"TypeError: {func} is not a function")

    def get_member_property(self, node, env):
        if node.computed:
            return to_string(self.evaluate(node.property, env))
        return node.property.name

    def assign_to_reference(self, node, value, env):
        if node.type == 'Identifier':
            env.assign(node.name, value)
        elif node.type == 'MemberExpression':
            obj = self.evaluate(node.object, env)
            prop = self.get_member_property(node, env)
            if isinstance(obj, str):
                raise TypeError("Cannot assign to read-only property of string")
            elif isinstance(obj, JSObject):
                obj.set_property(prop, value)
            else:
                raise TypeError(f"Cannot set property '{prop}' of {obj}")
        else:
            raise ReferenceError("Invalid left-hand side in assignment")

    # Visitors
    def visit_Program(self, node, env):
        result = JS_UNDEFINED
        for stmt in node.body:
            result = self.evaluate(stmt, env)
        return result

    def visit_EmptyStatement(self, node, env):
        return JS_UNDEFINED

    def visit_ExpressionStatement(self, node, env):
        return self.evaluate(node.expression, env)

    def visit_BlockStatement(self, node, env, create_scope=True):
        block_env = Environment(parent=env) if create_scope else env
        result = JS_UNDEFINED
        for stmt in node.body:
            result = self.evaluate(stmt, block_env)
        return result

    def visit_VariableDeclaration(self, node, env):
        for decl in node.declarations:
            name = decl.id.name
            init_val = self.evaluate(decl.init, env) if decl.init is not None else JS_UNDEFINED
            env.define(name, init_val, node.kind)
        return JS_UNDEFINED

    def visit_Identifier(self, node, env):
        return env.get(node.name)

    def visit_Literal(self, node, env):
        if node.value is None:
            return None
        return node.value

    def visit_IfStatement(self, node, env):
        test_val = self.evaluate(node.test, env)
        if to_boolean(test_val):
            return self.evaluate(node.consequent, env)
        elif node.alternate is not None:
            return self.evaluate(node.alternate, env)
        return JS_UNDEFINED

    def visit_WhileStatement(self, node, env):
        result = JS_UNDEFINED
        while True:
            test_val = self.evaluate(node.test, env)
            if not to_boolean(test_val):
                break
            try:
                result = self.evaluate(node.body, env)
            except BreakException:
                break
            except ContinueException:
                continue
        return result

    def visit_ForStatement(self, node, env):
        # For statement initializes loop variables in its own loop scope
        loop_env = Environment(parent=env)
        if node.init is not None:
            self.evaluate(node.init, loop_env)
        
        result = JS_UNDEFINED
        while True:
            if node.test is not None:
                test_val = self.evaluate(node.test, loop_env)
                if not to_boolean(test_val):
                    break
            try:
                result = self.evaluate(node.body, loop_env)
            except BreakException:
                break
            except ContinueException:
                pass
            
            if node.update is not None:
                self.evaluate(node.update, loop_env)
        return result

    def visit_BreakStatement(self, node, env):
        raise BreakException()

    def visit_ContinueStatement(self, node, env):
        raise ContinueException()

    def visit_TryStatement(self, node, env):
        try:
            return self.evaluate(node.block, env)
        except JSException as je:
            if node.handler is not None:
                catch_env = Environment(parent=env)
                if node.handler.param is not None:
                    catch_env.define(node.handler.param.name, je.value, kind='let')
                return self.evaluate(node.handler.body, catch_env)
            raise je
        except Exception as e:
            if isinstance(e, (ReturnException, BreakException, ContinueException)):
                raise e
            if node.handler is not None:
                catch_env = Environment(parent=env)
                if node.handler.param is not None:
                    err_msg = getattr(e, 'message', str(e))
                    catch_env.define(node.handler.param.name, err_msg, kind='let')
                return self.evaluate(node.handler.body, catch_env)
            raise e
        finally:
            if node.finalizer is not None:
                self.evaluate(node.finalizer, env)


    def visit_ThrowStatement(self, node, env):
        err_val = self.evaluate(node.argument, env)
        raise JSException(err_val)

    def visit_FunctionDeclaration(self, node, env):
        name = node.id.name
        func = JSFunction(name, node.params, node.body, env)
        env.define(name, func, kind='var')
        return JS_UNDEFINED

    def visit_FunctionExpression(self, node, env):
        name = node.id.name if node.id is not None else None
        func = JSFunction(name, node.params, node.body, env)
        return func

    def visit_ArrowFunctionExpression(self, node, env):
        func = JSFunction(None, node.params, node.body, env)
        return func

    def visit_ReturnStatement(self, node, env):
        val = self.evaluate(node.argument, env) if node.argument is not None else JS_UNDEFINED
        raise ReturnException(val)

    def visit_ArrayExpression(self, node, env):
        elems = []
        for el in node.elements:
            if el is not None and el.type == 'SpreadElement':
                spread_val = self.evaluate(el.argument, env)
                from environment import JS_EMPTY
                if isinstance(spread_val, JSArray):
                    for x in spread_val.elements:
                        elems.append(JS_UNDEFINED if x is JS_EMPTY else x)
                elif isinstance(spread_val, list):
                    elems.extend(spread_val)
                elif isinstance(spread_val, str):
                    elems.extend(list(spread_val))
                else:
                    raise TypeError("Spread syntax requires iterable object")
            else:
                elems.append(self.evaluate(el, env) if el is not None else JS_UNDEFINED)
        return JSArray(elems)

    def visit_ObjectExpression(self, node, env):
        obj = JSObject()
        for prop in node.properties:
            if prop.type == 'Property':
                if prop.computed:
                    key = to_string(self.evaluate(prop.key, env))
                else:
                    key = prop.key.name if prop.key.type == 'Identifier' else str(prop.key.value)
                val = self.evaluate(prop.value, env)
                obj.set_property(key, val)
        return obj

    def visit_MemberExpression(self, node, env):
        obj = self.evaluate(node.object, env)
        prop = self.get_member_property(node, env)
        
        if isinstance(obj, str):
            if prop == 'length':
                return len(obj)
            import js_builtins
            method = js_builtins.get_string_method(obj, prop)
            if method is not None:
                return method
            return JS_UNDEFINED
        
        if isinstance(obj, JSObject):
            return obj.get_property(prop)
        
        return JS_UNDEFINED

    def visit_CallExpression(self, node, env):
        callee = self.evaluate(node.callee, env)
        args = []
        for arg in node.arguments:
            if arg is not None and arg.type == 'SpreadElement':
                spread_val = self.evaluate(arg.argument, env)
                from environment import JS_EMPTY
                if isinstance(spread_val, JSArray):
                    for x in spread_val.elements:
                        args.append(JS_UNDEFINED if x is JS_EMPTY else x)
                elif isinstance(spread_val, list):
                    args.extend(spread_val)
                elif isinstance(spread_val, str):
                    args.extend(list(spread_val))
                else:
                    raise TypeError("Spread syntax requires iterable object")
            else:
                args.append(self.evaluate(arg, env))
        return self.call_function(callee, args)

    def visit_UnaryExpression(self, node, env):
        op = node.operator
        if op == 'delete':
            arg = node.argument
            if arg.type == 'MemberExpression':
                obj = self.evaluate(arg.object, env)
                prop = self.get_member_property(arg, env)
                if isinstance(obj, JSObject):
                    obj.properties.pop(prop, None)
                return True
            return True
        if op == 'void':
            self.evaluate(node.argument, env)
            return JS_UNDEFINED
            
        val = self.evaluate(node.argument, env)
        if op == '-':
            return -to_number(val)
        if op == '+':
            return to_number(val)
        if op == '!':
            return not to_boolean(val)
        if op == 'typeof':
            if val is JS_UNDEFINED:
                return 'undefined'
            if val is None:
                return 'object'
            if isinstance(val, bool):
                return 'boolean'
            if isinstance(val, (int, float)):
                return 'number'
            if isinstance(val, str):
                return 'string'
            if isinstance(val, (JSFunction, JSBuiltinFunction)):
                return 'function'
            if isinstance(val, JSObject):
                return 'object'
            return 'object'
        raise NotImplementedError(f"Unary operator '{op}' not implemented")

    def visit_BinaryExpression(self, node, env):
        left_val = self.evaluate(node.left, env)
        right_val = self.evaluate(node.right, env)
        op = node.operator
        
        if op == '+':
            if isinstance(left_val, (JSArray, JSObject)) or isinstance(right_val, (JSArray, JSObject)):
                return to_string(left_val) + to_string(right_val)
            if isinstance(left_val, str) or isinstance(right_val, str):
                return to_string(left_val) + to_string(right_val)
            return to_number(left_val) + to_number(right_val)
        if op == '-': return to_number(left_val) - to_number(right_val)
        if op == '*': return to_number(left_val) * to_number(right_val)
        if op == '/':
            l = to_number(left_val)
            r = to_number(right_val)
            if r == 0:
                return float('inf') if l >= 0 else float('-inf')
            return l / r
        if op == '%':
            l = to_number(left_val)
            r = to_number(right_val)
            if r == 0:
                return float('nan')
            return l % r
        if op == '**': return to_number(left_val) ** to_number(right_val)
        if op == '<':
            if isinstance(left_val, str) and isinstance(right_val, str):
                return left_val < right_val
            return to_number(left_val) < to_number(right_val)
        if op == '>':
            if isinstance(left_val, str) and isinstance(right_val, str):
                return left_val > right_val
            return to_number(left_val) > to_number(right_val)
        if op == '<=':
            if isinstance(left_val, str) and isinstance(right_val, str):
                return left_val <= right_val
            return to_number(left_val) <= to_number(right_val)
        if op == '>=':
            if isinstance(left_val, str) and isinstance(right_val, str):
                return left_val >= right_val
            return to_number(left_val) >= to_number(right_val)
        if op == '==': return loose_equal(left_val, right_val)
        if op == '!=': return not loose_equal(left_val, right_val)
        if op == '===': return strict_equal(left_val, right_val)
        if op == '!==': return not strict_equal(left_val, right_val)
        if op == 'in':
            if isinstance(right_val, JSObject):
                return to_string(left_val) in right_val.properties
            raise TypeError("TypeError: Cannot use 'in' operator to search in non-object")
        if op == 'instanceof':
            if isinstance(left_val, JSArray) and isinstance(right_val, JSObject) and right_val.name == 'Array':
                return True
            if isinstance(left_val, JSObject) and not isinstance(left_val, JSArray) and isinstance(right_val, JSObject) and right_val.name == 'Object':
                return True
            return False
        raise NotImplementedError(f"Binary operator '{op}' not implemented")

    def visit_LogicalExpression(self, node, env):
        left_val = self.evaluate(node.left, env)
        op = node.operator
        if op == '&&':
            if not to_boolean(left_val):
                return left_val
            return self.evaluate(node.right, env)
        if op == '||':
            if to_boolean(left_val):
                return left_val
            return self.evaluate(node.right, env)
        raise NotImplementedError(f"Logical operator '{op}' not implemented")

    def visit_ConditionalExpression(self, node, env):
        test_val = self.evaluate(node.test, env)
        if to_boolean(test_val):
            return self.evaluate(node.consequent, env)
        return self.evaluate(node.alternate, env)

    def visit_AssignmentExpression(self, node, env):
        right_val = self.evaluate(node.right, env)
        op = node.operator
        
        if op == '=':
            self.assign_to_reference(node.left, right_val, env)
            return right_val
        
        curr_val = self.evaluate(node.left, env)
        if op == '+=':
            if isinstance(curr_val, (JSArray, JSObject)) or isinstance(right_val, (JSArray, JSObject)):
                res = to_string(curr_val) + to_string(right_val)
            elif isinstance(curr_val, str) or isinstance(right_val, str):
                res = to_string(curr_val) + to_string(right_val)
            else:
                res = to_number(curr_val) + to_number(right_val)
        elif op == '-=': res = to_number(curr_val) - to_number(right_val)
        elif op == '*=': res = to_number(curr_val) * to_number(right_val)
        elif op == '/=':
            l = to_number(curr_val)
            r = to_number(right_val)
            res = float('inf') if r == 0 and l >= 0 else float('-inf') if r == 0 else l / r
        elif op == '%=':
            l = to_number(curr_val)
            r = to_number(right_val)
            res = float('nan') if r == 0 else l % r
        else:
            raise NotImplementedError(f"Assignment operator '{op}' not implemented")
        
        self.assign_to_reference(node.left, res, env)
        return res

    def visit_UpdateExpression(self, node, env):
        curr_val = self.evaluate(node.argument, env)
        num = to_number(curr_val)
        op = node.operator
        
        new_val = num + 1 if op == '++' else num - 1
        self.assign_to_reference(node.argument, new_val, env)
        
        return new_val if node.prefix else num

    def visit_SwitchStatement(self, node, env):
        disc_val = self.evaluate(node.discriminant, env)
        matched_idx = -1
        default_idx = -1
        
        for idx, case in enumerate(node.cases):
            if case.test is None:
                default_idx = idx
            else:
                case_val = self.evaluate(case.test, env)
                if strict_equal(disc_val, case_val):
                    matched_idx = idx
                    break
        
        start_idx = matched_idx if matched_idx != -1 else default_idx
        if start_idx == -1:
            return JS_UNDEFINED
            
        try:
            for i in range(start_idx, len(node.cases)):
                case = node.cases[i]
                for stmt in case.consequent:
                    self.evaluate(stmt, env)
        except BreakException:
            pass
            
        return JS_UNDEFINED

    def visit_DoWhileStatement(self, node, env):
        result = JS_UNDEFINED
        while True:
            try:
                result = self.evaluate(node.body, env)
            except BreakException:
                break
            except ContinueException:
                pass
            
            test_val = self.evaluate(node.test, env)
            if not to_boolean(test_val):
                break
        return result


import sys
import os
from parser import parse_js, JSSyntaxError
from evaluator import Evaluator
from js_builtins import create_global_environment

def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ('-', '--help', '-h'):
        if sys.argv[1] in ('-e', '--eval'):
            if len(sys.argv) > 2:
                code = sys.argv[2]
            else:
                print("Error: -e/--eval option requires a code string argument.", file=sys.stderr)
                sys.exit(1)
        else:
            filepath = sys.argv[1]
            if not os.path.exists(filepath):
                print(f"Error: File not found: {filepath}", file=sys.stderr)
                sys.exit(1)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("Usage: python main.py [file.js | -e \"code\"]")
        print("Options:")
        print("  -e, --eval \"code\"   Evaluate inline JavaScript code string")
        print("  -h, --help           Show this help information")
        print("If no argument is provided, reads code from stdin.")
        sys.exit(0)
    else:
        # Read from stdin
        try:
            code = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(0)

    try:
        # 1. Parse JavaScript into AST
        ast = parse_js(code)
        
        # 2. Setup environment and evaluator
        global_env = create_global_environment()
        evaluator = Evaluator()
        
        # 3. Execute the logic
        evaluator.evaluate(ast, global_env)
        
    except JSSyntaxError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Standard Python exceptions or custom JS runtime exceptions
        print(f"RuntimeError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

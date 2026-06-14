import os
import sys
import time
import subprocess

def run_command(cmd, timeout=5):
    """Executes a command subprocess with a strict timeout constraint."""
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            encoding='utf-8'
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)

def normalize(output):
    """Strips trailing spaces per line and normalizes line endings."""
    return "\n".join(line.rstrip() for line in output.strip().splitlines())

def run_tests():
    tests_dir = "tests"
    if not os.path.exists(tests_dir):
        print(f"Error: Directory '{tests_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    # Scan and filter for specific test cases (excluding the manual playground)
    test_files = sorted([
        f for f in os.listdir(tests_dir) 
        if f.endswith(".js") and f != "manual_test.js"
    ])
    
    if not test_files:
        print("No test files found in tests/ directory.", file=sys.stderr)
        sys.exit(1)

    start_time = time.time()
    passed_count = 0
    total_tests = len(test_files)

    print(f"Running {total_tests} integration tests serially...\n")

    for filename in test_files:
        filepath = os.path.join(tests_dir, filename)
        
        print("=" * 60)
        print(f" Test Case: {filename}")
        print("=" * 60)
        
        # 1. Custom JavaScript Runtime (Python)
        print("--- Running via Custom Python JS Runtime ---")
        py_code, py_out, py_err = run_command(["python", "main.py", filepath])
        print(py_out.rstrip() if py_out.strip() else "<no output>")
        if py_err:
            print(f"Error: {py_err.strip()}")
            
        print()
        
        # 2. Node.js
        print("--- Running via Node.js ---")
        node_code, node_out, node_err = run_command(["node", filepath])
        print(node_out.rstrip() if node_out.strip() else "<no output>")
        if node_err:
            print(f"Error: {node_err.strip()}")
            
        print()

        # Normalize outputs and verify they match
        norm_py = normalize(py_out)
        norm_node = normalize(node_out)
        
        if (py_code == node_code == 0) and (norm_py == norm_node):
            passed_count += 1
        else:
            print("\033[91m[Mismatch Detected]\033[0m")
            if norm_py != norm_node:
                print("Outputs do not match!")
            if py_code != node_code:
                print(f"Exit code mismatch: Node={node_code}, Python={py_code}")
            print()

    elapsed_time = time.time() - start_time
    
    print("=" * 60)
    print(f"Summary: {passed_count}/{total_tests} Tests Passed in {elapsed_time:.2f} seconds")
    print("=" * 60)

    if passed_count != total_tests:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    run_tests()

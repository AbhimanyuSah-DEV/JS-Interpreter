# JS-Interpreter (Custom JavaScript Runtime in Python)

A custom JavaScript engine built entirely from scratch in Python for Thunder 2.0 Hackathon. It reads standard JavaScript code, maps it into an execution blueprint, and runs it without using real JavaScript. To prove it works perfectly, it includes a smart test runner that benchmarks its output side-by-side against Node.js in real time!

A lightweight, robust tree-walk JavaScript (ECMAScript 6) interpreter written in Python 3.10+. The runtime parses JavaScript code into an Abstract Syntax Tree (AST) using the `esprima2` library, manages variable bindings with full lexical scoping and hoisting rules, enforces JavaScript type coercion, and exposes core standard library structures.

---

## Features

- **Variable Declarations**: Full support for block-scoped `let`/`const` (including redeclaration checks) and function/global-scoped `var` (supporting hoisting).
- **Core Data Types**: Supports number (float), string, boolean, null, and undefined.
- **Control Flow**: Supports conditionals (`if`, `else if`, `else`, `switch` with fall-through logic) and loops (`for`, `while`, `do...while` with `break`/`continue`).
- **Functions & Scope**: Includes function declarations, function expressions, closures, and ES6 arrow functions (both block-body and expression-body).
- **Standard Library bindings**:
  - `console.log` (mimics Node.js output, including representing array holes as `<N empty items>`).
  - `JSON` (`stringify` and `parse`).
  - `Object` (`keys`, `values`, `entries`).
  - `Math` constants and methods (including `Math.random()`, floor, ceil, round, power, absolute values).
  - `Date` (formatting date strings and retrieving timestamp `Date.now()`).
  - Global functions (`parseInt`, `parseFloat`, `isNaN`, `isFinite`).
- **Prototypes & Operations**:
  - **Array Methods**: `push`, `pop`, `shift`, `unshift`, `slice`, `splice`, `indexOf`, `includes`, `map`, `filter`, `forEach`, `reduce`, `every`, `some`, `concat`, `join`, `reverse`, `sort`, `find`.
  - **String Methods**: `substring`, `split`, `replace`, `replaceAll`, `slice`, `indexOf`, `includes`, `startsWith`, `endsWith`, `charAt`, `toLowerCase`, `toUpperCase`, `trim`, `trimStart`, `trimEnd`.
- **Spread & Rest Operators**: Array spread expressions `[...arr]`, call argument spreads, and function rest parameters `(...rest)`.
- **Try / Catch Exception Handling**: Real custom JS exception catching using `throw` statements propagating through Python callstacks.

---

## Project Structure

```text
├── parser.py          # AST parser wrapper using esprima2
├── coercion.py        # JavaScript type conversion & coercion rules
├── environment.py     # Scopes, environments, closures, objects, & array elisions
├── js_builtins.py     # Global objects, constructors, and prototype methods
├── evaluator.py       # Recursively walks and evaluates the AST
├── main.py            # CLI entry point
├── test_runner.py     # Quiet, Node.js-aligned integration test suite
└── tests/             # Tests directory
    ├── 01_odd_even.js
    ├── 02_triangle.js
    ├── 03_armstrong.js
    ├── 04_array_reverse.js
    ├── 05_palindrome.js
    └── manual_test.js # Manual testing playground
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js (only required to run the automated regression tests)

### Setup
1. Clone or download this repository.
2. Install the AST parsing library dependency:
   ```bash
   pip install esprima2
   ```

---

## Usage

You can run JavaScript code in three different ways:

### 1. Running a File
Provide the path to any `.js` file as an argument:
```bash
python main.py tests/01_odd_even.js
```

### 2. Evaluating Inline Code Strings (`-e` option)
Execute code snippets directly in your terminal:
```bash
python main.py -e "let arr = [1, 2, 3]; console.log([...arr].reverse());"
```

### 3. Piping Standard Input
Pipe JS code directly into the interpreter:
```bash
echo "console.log('Hello from stdin!');" | python main.py
```

### 4. Custom Manual Playground File
For code testing, you can paste any custom JS code in `tests/manual_test.js` and execute it:
```bash
python main.py tests/manual_test.js
```

---

## Running Integration Tests

We have a test tool (`test_runner.py`) that checks if our JavaScript interpreter works correctly:

1. **Finds tests**: It looks at the 5 test files in the `tests/` folder.
2. **Runs the code**: For each test, it runs the code using our Python compiler first, and then runs it using Node.js.
3. **Shows outputs**: It prints the outputs of both runs so you can easily compare them.
4. **Checks for matches**: It makes sure the outputs are exactly the same and prints a summary.

To run the tests:
```bash
python test_runner.py
```


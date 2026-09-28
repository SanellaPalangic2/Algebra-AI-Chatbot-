"""
Lesson catalog + practice-problem generators for Algebra Quest.

Every practice set is generated fresh (random numbers), so students can't
just memorize answers. Answers are checked here on the server, never in the
browser, so nobody can skip ahead by peeking at the page source.
"""
import random
import re
from fractions import Fraction

R = random.randint


# ---------------------------------------------------------------- helpers
def fmt_term(coef, var):
    """3,'x' -> '3x'   1,'x' -> 'x'   -1,'x' -> '-x'"""
    if coef == 1:
        return var
    if coef == -1:
        return f"-{var}"
    return f"{coef}{var}"


def num(q, answer, hint):
    """A problem whose answer is a single number."""
    return {"q": q, "kind": "number", "answer": str(answer), "accept": [str(answer)], "hint": hint}


def text(q, answers, hint, display=None):
    """A problem whose answer is an expression / inequality (several accepted forms)."""
    answers = list(answers)
    pretty = display or re.sub(r"(?<=\w)([+-])", r" \1 ", answers[0])  # "6x+7" -> "6x + 7"
    return {"q": q, "kind": "text", "answer": pretty, "accept": answers, "hint": hint}


FLIP = {">": "<", "<": ">", ">=": "<=", "<=": ">="}
PRETTY = {">": ">", "<": "<", ">=": "≥", "<=": "≤"}


def ineq_answer(op, value, var="x"):
    return [f"{var}{op}{value}", f"{value}{FLIP[op]}{var}"], f"{var} {PRETTY[op]} {value}"


# ------------------------------------------------------- answer checking
_REPLACE = [
    ("−", "-"), ("–", "-"), ("—", "-"), ("×", "*"), ("·", "*"), ("÷", "/"),
    ("≤", "<="), ("≥", ">="), ("=<", "<="), ("=>", ">="), ("$", ""), (",", ""),
]


def normalize(s):
    s = str(s).strip().lower()
    for a, b in _REPLACE:
        s = s.replace(a, b)
    s = re.sub(r"\s+", "", s)
    s = s.replace("*", "").replace("+-", "-")
    return s


def is_correct(user_answer, problem):
    u = normalize(user_answer)
    if not u:
        return False
    if problem["kind"] == "number":
        u = re.sub(r"^[a-z]=", "", u)            # allow "x=7"
        m = re.fullmatch(r"(-?[\d./]+)[a-z]*", u)  # allow "5 hours", "$12"
        if not m:
            return False
        try:
            return Fraction(m.group(1)) == Fraction(problem["answer"])
        except (ValueError, ZeroDivisionError):
            return False
    return u in {normalize(a) for a in problem["accept"]}


# ------------------------------------------------ Level 1: variables
def v_add():
    var, n, b = random.choice("nxyk"), R(2, 15), R(2, 12)
    return num(f"If {var} = {n}, what is {var} + {b}?", n + b,
               f"Swap the letter {var} for the number {n}, then add {b}.")


def v_sub():
    y, b = R(12, 30), R(2, 11)
    return num(f"If y = {y}, what is y − {b}?", y - b, f"Replace y with {y}, then subtract {b}.")


def v_times():
    x, a = R(2, 9), R(2, 9)
    return num(f"If x = {x}, what is {a}x?", a * x,
               f"{a}x means {a} × x. So multiply {a} × {x}.")


def v_div():
    a = R(2, 6)
    k = a * R(2, 9)
    return num(f"If k = {k}, what is k ÷ {a}?", k // a, f"Replace k with {k}, then divide by {a}.")


def v_word():
    name, item = random.choice([("Jay", "stickers"), ("Maya", "marbles"), ("Leo", "cards"), ("Ava", "shells")])
    letter, have, more = item[0], R(5, 20), R(3, 12)
    return num(f"{name} has {letter} {item} and gets {more} more, so {name} has {letter} + {more}. "
               f"If {letter} = {have}, how many {item} does {name} have now?",
               have + more, f"Put {have} in place of {letter}: {have} + {more}.")


# ----------------------------- Level 2: order of operations & evaluating
def o_mult_first():
    a, b, c = R(1, 10), R(2, 6), R(2, 6)
    return num(f"What is {a} + {b} × {c}?", a + b * c, "Multiply BEFORE you add!")


def o_parens():
    a, b, c = R(1, 8), R(1, 8), R(2, 5)
    return num(f"What is ({a} + {b}) × {c}?", (a + b) * c, "Parentheses go first, then multiply.")


def o_eval():
    a, b, x = R(2, 6), R(1, 10), R(2, 8)
    return num(f"Evaluate {a}x + {b} when x = {x}.", a * x + b,
               f"Swap x for {x}: {a} × {x} + {b}. Multiply first, then add.")


def o_square():
    x, a = R(2, 6), R(1, 10)
    return num(f"Evaluate x² + {a} when x = {x}.", x * x + a, f"x² means x × x, so start with {x} × {x}.")


def o_paren_eval():
    a, b = R(2, 5), R(1, 5)
    x = b + R(1, 6)
    return num(f"Evaluate {a}(x − {b}) when x = {x}.", a * (x - b),
               f"Do the parentheses first: {x} − {b}. Then multiply by {a}.")


# --------------------------------------------- Level 3: combining like terms
def e_two():
    v = random.choice("xyn")
    a, b = R(2, 9), R(2, 9)
    return text(f"Simplify: {a}{v} + {b}{v}", [fmt_term(a + b, v)],
                f"Both terms have {v}, so add the numbers in front: {a} + {b}.")


def e_sub():
    v = random.choice("xym")
    a = R(5, 12)
    b = R(1, a - 1)
    r = a - b
    answers = [fmt_term(r, v)] + ([f"1{v}"] if r == 1 else [])
    return text(f"Simplify: {a}{v} − {fmt_term(b, v)}", answers, f"Subtract the numbers in front: {a} − {b}.")


def e_const():
    v = random.choice("xa")
    a, b, c = R(2, 8), R(2, 8), R(1, 9)
    s = fmt_term(a + b, v)
    return text(f"Simplify: {a}{v} + {c} + {b}{v}", [f"{s}+{c}", f"{c}+{s}"],
                f"Group the {v} terms together. The plain number {c} stays by itself.")


def e_mixed():
    a, b, c = R(2, 6), R(2, 6), R(2, 6)
    return text(f"Simplify: {a}x + {b}y + {c}x", [f"{a + c}x+{b}y", f"{b}y+{a + c}x"],
                "x terms only combine with x terms. y stays separate!")


def e_numbers():
    a, b, c, d = R(2, 6), R(1, 5), R(1, 9), R(1, 9)
    n = fmt_term(a + b, "n")
    return text(f"Simplify: {c} + {a}n + {d} + {fmt_term(b, 'n')}",
                [f"{n}+{c + d}", f"{c + d}+{n}"],
                "Add the n terms together, then add the plain numbers together.")


# ------------------------------------------------ Level 4: one-step equations
def s_add():
    x, a = R(2, 20), R(2, 15)
    return num(f"Solve: x + {a} = {x + a}", x, f"Subtract {a} from both sides.")


def s_sub():
    a = R(2, 15)
    x = a + R(1, 15)
    return num(f"Solve: x − {a} = {x - a}", x, f"Add {a} to both sides.")


def s_mul():
    x, a = R(2, 12), R(2, 9)
    return num(f"Solve: {a}x = {a * x}", x, f"Divide both sides by {a}.")


def s_div():
    x, a = R(2, 9), R(2, 6)
    return num(f"Solve: x ÷ {a} = {x}", a * x, f"Multiply both sides by {a}.")


def s_word():
    x, a = R(5, 25), R(3, 12)
    return num(f"A mystery number plus {a} equals {x + a}. What is the mystery number?", x,
               f"Write it as n + {a} = {x + a}, then subtract {a} from both sides.")


# ------------------------------------------------ Level 5: two-step equations
def t_basic():
    a, x, b = R(2, 6), R(1, 10), R(1, 12)
    return num(f"Solve: {a}x + {b} = {a * x + b}", x,
               f"First subtract {b} from both sides, then divide by {a}.")


def t_minus():
    a, b = R(2, 6), R(1, 9)
    x = R(3, 10)
    return num(f"Solve: {a}x − {b} = {a * x - b}", x, f"First add {b} to both sides, then divide by {a}.")


def t_div():
    a, b = R(2, 5), R(1, 9)
    x = a * R(1, 6)
    return num(f"Solve: x ÷ {a} + {b} = {x // a + b}", x, f"Subtract {b} from both sides, then multiply by {a}.")


def t_word():
    fee, per, hrs = R(5, 15), R(3, 8), R(2, 6)
    return num(f"A trampoline park costs ${fee} to get in, plus ${per} for each hour. "
               f"Zoe paid ${fee + per * hrs}. How many hours did she jump?", hrs,
               f"Write {per}h + {fee} = {fee + per * hrs}. Subtract {fee}, then divide by {per}.")


def t_neg():
    a, b = R(2, 5), R(1, 10)
    x = -R(1, 8)
    return num(f"Solve: {a}x + {b} = {a * x + b}", x,
               f"Subtract {b} from both sides, then divide by {a}. The answer can be negative!")


# ------------------------------------------- Level 6: distributive property
def d_expand_plus():
    a, b = R(2, 9), R(1, 9)
    return text(f"Expand: {a}(x + {b})", [f"{a}x+{a * b}", f"{a * b}+{a}x"],
                f"Multiply {a} by x AND by {b}.")


def d_expand_minus():
    a, b = R(2, 9), R(1, 9)
    return text(f"Expand: {a}(y − {b})", [f"{a}y-{a * b}", f"-{a * b}+{a}y"],
                f"Multiply {a} by y, then {a} by {b}. Keep the minus sign!")


def d_expand_simplify():
    a, b, c = R(2, 5), R(1, 6), R(1, 9)
    return text(f"Expand and simplify: {a}(x + {b}) + {c}", [f"{a}x+{a * b + c}", f"{a * b + c}+{a}x"],
                f"First {a}(x + {b}) = {a}x + {a * b}. Then add {c} to the plain number.")


def d_combine_solve():
    a, b, x = R(2, 6), R(1, 5), R(1, 9)
    return num(f"Solve: {a}x + {fmt_term(b, 'x')} = {(a + b) * x}", x,
               f"Combine like terms first: {a}x + {b}x = {a + b}x. Then divide.")


def d_solve():
    a, b, x = R(2, 5), R(1, 6), R(1, 8)
    return num(f"Solve: {a}(x + {b}) = {a * (x + b)}", x,
               f"Divide both sides by {a} first, then subtract {b}. (Or distribute first!)")


# ------------------------------------------------ Level 7: inequalities
def _op():
    return random.choice([">", "<", ">=", "<="])


def i_add():
    op, a, v = _op(), R(2, 12), R(1, 15)
    acc, disp = ineq_answer(op, v)
    return text(f"Solve: x + {a} {PRETTY[op]} {v + a}", acc, f"Subtract {a} from both sides, just like an equation.", disp)


def i_sub():
    op, a = _op(), R(2, 10)
    v = a + R(1, 10)
    acc, disp = ineq_answer(op, v)
    return text(f"Solve: x − {a} {PRETTY[op]} {v - a}", acc, f"Add {a} to both sides.", disp)


def i_mul():
    op, a, v = _op(), R(2, 6), R(1, 9)
    acc, disp = ineq_answer(op, v)
    return text(f"Solve: {a}x {PRETTY[op]} {a * v}", acc, f"Divide both sides by {a}.", disp)


def i_two_step():
    op, a, b, v = _op(), R(2, 5), R(1, 9), R(1, 8)
    acc, disp = ineq_answer(op, v)
    return text(f"Solve: {a}x + {b} {PRETTY[op]} {a * v + b}", acc,
                f"Subtract {b} from both sides, then divide by {a}.", disp)


def i_neg():
    op, a, v = _op(), R(2, 5), R(-6, 6)
    acc, disp = ineq_answer(FLIP[op], v)
    return text(f"Solve: −{a}x {PRETTY[op]} {-a * v}", acc,
                f"Divide both sides by −{a}... and when you divide by a NEGATIVE, flip the sign!", disp)


# ------------------------------------------------------------- catalog
LESSONS = [
    {
        "id": 1, "title": "Meet the Variable", "emoji": "🔤", "color": "#FF4D8D",
        "tagline": "Letters that hide mystery numbers",
        "topics": "what a variable is, why we use letters, writing simple expressions like n + 5, "
                  "what 3x means (3 times x), and plugging in a value to evaluate an expression",
        "generators": [v_add, v_sub, v_times, v_div, v_word],
        "fallback": """## 🕵️ What's a variable?
A **variable** is a letter that stands for a number we don't know yet — like a mystery box! 📦

If you have some cookies and your friend gives you 3 more, you have **c + 3** cookies. The letter **c** is just holding a spot for "however many cookies you started with."

## ✖️ Letters next to numbers
When a number sits right next to a letter, it means **multiply**.
- **4x** means 4 × x
- **2n** means 2 × n

## 🔁 Plugging in (evaluating)
To **evaluate** an expression, swap the letter for its number.

**Example:** If x = 5, what is x + 7?
1. Replace x with 5 → 5 + 7
2. Add → **12** ✅

**Example:** If n = 6, what is 3n?
1. 3n means 3 × n → 3 × 6
2. Multiply → **18** ✅

> ⚠️ **Watch out!** 3n does NOT mean "36." It means 3 **times** n.

## 🎒 Recap
- A variable is a letter that stands for a number.
- A number stuck to a letter means multiply.
- To evaluate, swap the letter for its number and do the math!""",
    },
    {
        "id": 2, "title": "Order of Operations", "emoji": "🎯", "color": "#FF9F1C",
        "tagline": "Do the math steps in the right order",
        "topics": "the order of operations (parentheses, exponents, multiply/divide left to right, "
                  "add/subtract left to right), exponents like x², and evaluating expressions such as 3x + 2 "
                  "or 2(x − 1) for a given value of x",
        "generators": [o_mult_first, o_parens, o_eval, o_square, o_paren_eval],
        "fallback": """## 🚦 Why order matters
What is 2 + 3 × 4? If you add first you get 20. If you multiply first you get 14. Only one can be right — so mathematicians agreed on an order!

## 🪜 The order (PEMDAS)
1. **P**arentheses ( )
2. **E**xponents like x²
3. **M**ultiply & **D**ivide — left to right
4. **A**dd & **S**ubtract — left to right

So 2 + 3 × 4 = 2 + 12 = **14** ✅

## 🔢 Exponents
**x²** means x × x. If x = 5, then x² = 5 × 5 = **25**.

## 🔁 Evaluating expressions
**Example:** Evaluate 3x + 2 when x = 4.
1. Swap in 4 → 3 × 4 + 2
2. Multiply first → 12 + 2
3. Add → **14** ✅

**Example:** Evaluate 2(x − 1) when x = 6.
1. Swap in 6 → 2(6 − 1)
2. Parentheses first → 2 × 5
3. Multiply → **10** ✅

> ⚠️ **Watch out!** x² is NOT x × 2. When x = 3, x² is 9, not 6.

## 🎒 Recap
Parentheses → exponents → multiply/divide → add/subtract. Follow the order and you'll always land on the right answer!""",
    },
    {
        "id": 3, "title": "Combining Like Terms", "emoji": "🧩", "color": "#F7B801",
        "tagline": "Group the matching pieces together",
        "topics": "what a term is, what makes terms 'like terms' (same variable), adding and subtracting "
                  "like terms such as 3x + 5x, keeping constants and different variables separate, "
                  "and simplifying expressions like 4x + 2 + 3x",
        "generators": [e_two, e_sub, e_const, e_mixed, e_numbers],
        "fallback": """## 🍎 Apples with apples
Imagine a bag with 3 apples and 2 bananas. Your friend adds 4 more apples. Now you have **7 apples and 2 bananas** — you can't turn bananas into apples!

Algebra works the same way. **Like terms** have the *same letter*.
- 3x and 5x are like terms ✅
- 3x and 5y are **not** ✗
- 4 and 9 (plain numbers) are like terms with each other ✅

## ➕ Combining
Add or subtract the numbers in front. The letter stays the same.

**Example:** 3x + 5x = **8x**

**Example:** 9y − 4y = **5y**

**Example:** Simplify 4x + 2 + 3x
1. Group the x's: 4x + 3x = 7x
2. The 2 stays by itself
3. Answer: **7x + 2** ✅

> ⚠️ **Watch out!** 7x + 2 is NOT 9x. The 2 has no x, so it can't join the x team.

## 🎒 Recap
Same letter? Combine them. Different letters or plain numbers? Keep them separate!""",
    },
    {
        "id": 4, "title": "One-Step Equations", "emoji": "⚖️", "color": "#1FC7B6",
        "tagline": "Keep the balance to find x",
        "topics": "what an equation is, the balance-scale idea, inverse (opposite) operations, "
                  "and solving one-step equations with addition, subtraction, multiplication and division, "
                  "plus checking your answer",
        "generators": [s_add, s_sub, s_mul, s_div, s_word],
        "fallback": """## ⚖️ Equations are balance scales
An **equation** says two sides are equal, like a perfectly balanced scale. Whatever you do to one side, you must do to the other to keep it balanced.

Our goal: get **x all by itself**.

## 🔄 Undo with the opposite
| If you see... | Do the opposite |
|---|---|
| + 5 | subtract 5 |
| − 3 | add 3 |
| × 4 | divide by 4 |
| ÷ 2 | multiply by 2 |

**Example:** x + 5 = 12
1. Subtract 5 from both sides → x = 12 − 5
2. **x = 7** ✅
3. Check: 7 + 5 = 12 ✔️

**Example:** 4x = 20
1. Divide both sides by 4 → x = 20 ÷ 4
2. **x = 5** ✅

> ⚠️ **Watch out!** Do the same thing to BOTH sides — otherwise the scale tips over!

## 🎒 Recap
Find what's happening to x, do the opposite to both sides, and check your answer by plugging it back in.""",
    },
    {
        "id": 5, "title": "Two-Step Equations", "emoji": "🪜", "color": "#3A86FF",
        "tagline": "Undo, then undo again",
        "topics": "solving two-step equations like 3x + 4 = 19 by undoing addition/subtraction first and then "
                  "multiplication/division, negative answers, and turning a simple word problem into an equation",
        "generators": [t_basic, t_minus, t_div, t_word, t_neg],
        "fallback": """## 🎁 Unwrapping a present
Wrapping a present: put it in a box, then add a bow. Unwrapping: take off the bow first, then open the box. **Undo in reverse order!**

## 🪜 The two steps
For 3x + 4 = 19:
1. **Undo the + 4** → subtract 4 from both sides → 3x = 15
2. **Undo the × 3** → divide both sides by 3 → **x = 5** ✅
3. Check: 3 × 5 + 4 = 19 ✔️

**Example:** 2x − 6 = 10
1. Add 6 to both sides → 2x = 16
2. Divide by 2 → **x = 8** ✅

## 🎢 Word problem
A skate park costs $5 to enter plus $3 per hour. You paid $17. How many hours?
- Equation: 3h + 5 = 17
- Subtract 5 → 3h = 12
- Divide by 3 → **h = 4 hours** ✅

> ⚠️ **Watch out!** Deal with the + or − number FIRST, then the multiplying number.

## 🎒 Recap
Undo adding/subtracting first, then undo multiplying/dividing. Always check your answer!""",
    },
    {
        "id": 6, "title": "The Distributive Property", "emoji": "🎁", "color": "#8338EC",
        "tagline": "Share the multiplying with everyone",
        "topics": "the distributive property a(b + c) = ab + ac, expanding expressions like 3(x + 4) and 2(y − 5), "
                  "expanding and simplifying, and using it (plus combining like terms) to solve equations",
        "generators": [d_expand_plus, d_expand_minus, d_expand_simplify, d_combine_solve, d_solve],
        "fallback": """## 🍬 Sharing is caring
You're giving 3 friends each a bag with 1 lollipop and 4 gummies. That's 3 lollipops and 12 gummies. The number outside **shares** (distributes) with everything inside!

## ✖️ The rule
**a(b + c) = ab + ac**

**Example:** 3(x + 4)
- 3 × x = 3x
- 3 × 4 = 12
- Answer: **3x + 12** ✅

**Example:** 2(y − 5)
- 2 × y = 2y
- 2 × 5 = 10 (keep the minus!)
- Answer: **2y − 10** ✅

## 🔧 Using it to solve
Solve 2(x + 3) = 14
1. Distribute → 2x + 6 = 14
2. Subtract 6 → 2x = 8
3. Divide by 2 → **x = 4** ✅

> ⚠️ **Watch out!** 3(x + 4) is NOT 3x + 4. The 3 must multiply **every** term inside.

## 🎒 Recap
Multiply the outside number by each thing inside the parentheses, then simplify!""",
    },
    {
        "id": 7, "title": "Inequalities", "emoji": "🐊", "color": "#E63946",
        "tagline": "When answers are a whole range",
        "topics": "inequality symbols > < ≥ ≤ (the hungry alligator trick), what a solution set means, "
                  "solving one- and two-step inequalities like equations, and flipping the sign when "
                  "multiplying or dividing by a negative number. Tell students they can type >= and <= for ≥ and ≤",
        "generators": [i_add, i_sub, i_mul, i_two_step, i_neg],
        "fallback": """## 🐊 The hungry alligator
The alligator mouth always opens toward the **bigger** number.
- 8 > 3 → "8 is greater than 3"
- 2 < 9 → "2 is less than 9"
- **≥** means "greater than **or equal to**" (type **>=**)
- **≤** means "less than **or equal to**" (type **<=**)

## 🎢 Many answers!
"You must be taller than 48 inches to ride" → h > 48. That's not one answer — 49, 50, 60… all work!

## 🔧 Solve like an equation
**Example:** x + 4 > 10
- Subtract 4 → **x > 6** ✅

**Example:** 3x ≤ 12
- Divide by 3 → **x ≤ 4** ✅

## 🔄 The special flip rule
When you multiply or divide by a **negative** number, **flip the sign**!

**Example:** −2x < 8
- Divide by −2 **and flip** → **x > −4** ✅

> ⚠️ **Watch out!** Forgetting to flip is the #1 inequality mistake.

## 🎒 Recap
Solve inequalities just like equations — but flip the sign whenever you multiply or divide by a negative.""",
    },
]

LESSONS_BY_ID = {l["id"]: l for l in LESSONS}
PROBLEMS_PER_SET = 5
PASS_SCORE = 4


def public_meta(lesson):
    return {k: lesson[k] for k in ("id", "title", "emoji", "color", "tagline")}


def make_practice(lesson_id, n=PROBLEMS_PER_SET):
    """Fresh set of n problems, easiest template first."""
    gens = LESSONS_BY_ID[lesson_id]["generators"]
    picks = list(range(len(gens)))
    while len(picks) < n:
        picks.append(random.randrange(len(gens)))
    picks = sorted(random.sample(picks, n))
    problems, seen = [], set()
    for i in picks:
        for _ in range(10):  # avoid identical questions in one set
            p = gens[i]()
            if p["q"] not in seen:
                break
        seen.add(p["q"])
        problems.append(p)
    return problems

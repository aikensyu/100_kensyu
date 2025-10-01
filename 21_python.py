"""
Python基礎講座（スパイダー方式対応版）

このスクリプトは、対話的にPythonの基礎を学べるシンプルなCLI教材です。
スパイダー方式で一つずつ実行できるように設計されています。

提供レッスン:
1) 変数とデータ型
2) 制御構文（if / for / while）
3) 関数の基礎
4) コレクション（list/tuple/dict/set）と内包表記
5) ファイルI/Oと例外処理
6) オブジェクト指向（OOP）基礎 + ミニクイズ

実行方法:
  python 21_python.py
  または各レッスンを個別に実行
"""
# %%

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional
import sys
import textwrap
import tempfile
import os
# %%
# データと処理（関数）
a = "Hello"
print(a)

# %%

def print_title(title: str) -> None:
    """タイトルを装飾して表示"""
    # タイトルの長さと8のうち大きい方を選んで、その長さ分の"="を作成
    # これによりタイトルが短くても最低8文字分の装飾線が表示される
    # 関数とは：特定の処理をまとめて名前を付けたもの。入力（引数）を受け取り、処理を実行し、結果（戻り値）を返す
    # max()関数: 複数の値の中から最大値を返す組み込み関数
    # 関数の基本構造: 関数名(引数1, 引数2, ...) → 戻り値
    # 関数を使うメリット: コードの再利用、処理の分割、可読性の向上
    # len()関数: 文字列、リスト、辞書などのオブジェクトの長さ（要素数）を返す組み込み関数
    # ここでは、タイトルの文字数と8のうち大きい方を選んで装飾線の長さを決定
    # 例: title="Hello"なら len(title)=5, max(8, 5)=8 → "="が8個
    #     title="Very Long Title"なら len(title)=15, max(8, 15)=15 → "="が15個
    bar = "=" * max(8, len(title))
    
    # f-string（フォーマット文字列）を使って装飾されたタイトルを表示
    # \nは改行文字で、上下に装飾線、中央にタイトルを配置
    print(f"\n{bar}\n{title}\n{bar}")




def print_section(title: str) -> None:
    """セクションタイトルを装飾して表示"""
    bar = "-" * max(6, len(title))
    print(f"\n{title}\n{bar}")


def pause() -> None:
    """ユーザーの入力待ち"""
    try:
        input("\nEnterキーでメニューに戻ります...")
    except EOFError:
        # 非対話環境（CI等）のためのフォールバック
        pass


def show_block(text: str, width: int = 88) -> None:
    """テキストブロックを整形して表示"""
    wrapped = textwrap.dedent(text).strip("\n")
    print(textwrap.fill(wrapped, width=width, replace_whitespace=False))

# %%
# =============================================================================
# レッスン1: 変数とデータ型
# =============================================================================
def lesson_variables_types() -> None:
    """レッスン1: 変数とデータ型の基礎を学習"""
    print_title("レッスン1: 変数とデータ型")
    show_block(
        """
        変数は値に名前を付けて保持するための入れ物です。Pythonでは代入と同時に型が決まる
        （動的型付け）ため、事前の型宣言は不要です。主な基本データ型は以下の通りです。
        - int: 整数
        - float: 浮動小数点数
        - str: 文字列（Unicode）
        - bool: 論理値（True / False）
        - NoneType: 値が存在しないことを表す特別な値（None）
        """
    )

    print_section("実演: 代入とtype()")
    a = 42
    b = 3.14
    s = "こんにちは"
    t = True
    n = None
    print(f"a = {a} -> {type(a)}")
    print(f"b = {b} -> {type(b)}")
    print(f"s = {s} -> {type(s)}")
    print(f"t = {t} -> {type(t)}")
    print(f"n = {n} -> {type(n)}")

    print_section("文字列の基本操作")
    name = "Python"
    print(f"len(name) = {len(name)}")
    print(f"name.upper() = {name.upper()}")
    print(f"name[0:3] = {name[0:3]}")
    print(f"f文字列: Hello, {name}!")

    pause()

# %%
# =============================================================================
# レッスン2: 制御構文
# =============================================================================
def lesson_control_flow() -> None:
    """レッスン2: 制御構文（if / for / while）の基礎を学習"""
    print_title("レッスン2: 制御構文（if / for / while）")
    show_block(
        """
        条件分岐(if/elif/else)や繰り返し(for/while)は、プログラムの流れを制御する構文です。
        比較演算子(==, !=, <, >, <=, >=)や論理演算子(and, or, not)と組み合わせて使います。
        """
    )

    print_section("if / elif / else")
    x = 7
    if x % 2 == 0:
        msg = "偶数"
    elif x % 3 == 0:
        msg = "3の倍数"
    else:
        msg = "その他"
    print(f"x = {x} -> {msg}")

    print_section("for ループ")
    squares = []
    for i in range(5):
        squares.append(i * i)
    print(f"i^2 (0..4): {squares}")

    print_section("while ループ")
    total = 0
    i = 1
    while i <= 5:
        total += i
        i += 1
    print(f"1から5の合計: {total}")

    print_section("break / continue")
    vals = []
    for i in range(10):
        if i % 2 == 0:
            continue  # 偶数をスキップ
        vals.append(i)
        if len(vals) == 3:
            break
    print(f"奇数3つだけ: {vals}")

    pause()

# %%
# =============================================================================
# レッスン3: 関数の基礎
# =============================================================================
def lesson_functions() -> None:
    """レッスン3: 関数の基礎を学習"""
    print_title("レッスン3: 関数の基礎")
    show_block(
        """
        関数は、処理をひとまとめにして再利用しやすくする仕組みです。引数・戻り値・デフォルト
        引数・キーワード引数などを使い分けることで、柔軟なAPIを提供できます。
        """
    )

    print_section("定義と呼び出し")

    def add(x: int, y: int) -> int:
        """2数の和を返します"""
        return x + y

    print(f"add(2, 3) = {add(2, 3)}")

    print_section("デフォルト引数とキーワード引数")

    def greet(name: str, punctuation: str = "!") -> str:
        return f"Hello, {name}{punctuation}"

    print(greet("Alice"))
    print(greet("Bob", punctuation="."))

    print_section("可変長引数 *args / **kwargs")

    def summarize(*numbers: int, **options) -> str:
        unit = options.get("unit", "点")
        return f"合計: {sum(numbers)}{unit}"

    print(summarize(1, 2, 3))
    print(summarize(10, 20, 30, unit="円"))

    print_section("ラムダ式（無名関数）")
    double = lambda n: n * 2  # 簡単な式にのみ使用推奨
    print(f"double(5) = {double(5)}")

    pause()

# %%
# =============================================================================
# レッスン4: コレクションと内包表記
# =============================================================================
def lesson_collections_and_comprehensions() -> None:
    """レッスン4: コレクションと内包表記を学習"""
    print_title("レッスン4: コレクションと内包表記")
    show_block(
        """
        Pythonには複数の値を扱うための便利なコレクション型があります。用途に応じて使い分けます。
        - list: 可変・順序あり
        - tuple: 不変・順序あり
        - dict: keyとvalueの対応（連想配列）
        - set: 重複なしの集合
        また、内包表記を使うと、宣言的かつ簡潔に新しいコレクションを生成できます。
        """
    )

    print_section("list / tuple / dict / set の基礎")
    nums_list = [1, 2, 3]
    nums_tuple = (1, 2, 3)
    person_dict = {"name": "Alice", "age": 30}
    tags_set = {"python", "basic", "course"}
    print(f"list: {nums_list}")
    print(f"tuple: {nums_tuple}")
    print(f"dict: {person_dict}")
    print(f"set: {tags_set}")

    print_section("内包表記")
    squares = [n * n for n in range(6)]
    even_squares = [n for n in squares if n % 2 == 0]
    mapping = {n: n * n for n in range(4)}
    uniques = {c for c in "banana"}
    print(f"squares: {squares}")
    print(f"even_squares: {even_squares}")
    print(f"mapping: {mapping}")
    print(f"uniques from 'banana': {uniques}")

    pause()

# %%
# =============================================================================
# レッスン5: ファイルI/Oと例外処理
# =============================================================================
def lesson_file_io_and_exceptions() -> None:
    """レッスン5: ファイルI/Oと例外処理を学習"""
    print_title("レッスン5: ファイルI/Oと例外処理")
    show_block(
        """
        with文を使うと、ファイルのクローズ漏れを防げます。例外処理ではtry/except/else/finallyを
        使って、エラー時の振る舞いを制御します。
        """
    )

    print_section("ファイルI/O: 一時ファイルに書き込み・読み出し")
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write("Hello File!\n1,2,3\n")
        tmp.flush()
    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"読み出し:\n{content}")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    print_section("例外処理: ValueError を捕捉")
    raw = "123x"
    try:
        value = int(raw)
    except ValueError as e:
        print(f"int(\"{raw}\") は失敗 -> {e}")
        value = None
    else:
        print("例外が起きなかった場合に実行されるブロック")
    finally:
        print("例外の有無に関わらず、最後に必ず実行されます")
    print(f"value = {value}")

    pause()

# %%
# =============================================================================
# レッスン6: オブジェクト指向とミニクイズ
# =============================================================================
def lesson_oop_and_quiz() -> None:
    """レッスン6: オブジェクト指向（OOP）基礎 + ミニクイズ"""
    print_title("レッスン6: オブジェクト指向（OOP）基礎 + ミニクイズ")
    show_block(
        """
        クラスは、状態（属性）と振る舞い（メソッド）をまとめます。継承により振る舞いを再利用し、
        ポリモーフィズムで共通インターフェースに対して異なる実装を扱えます。
        """
    )

    print_section("クラス定義・継承・メソッド")

    class Animal:
        def __init__(self, name: str) -> None:
            self.name = name

        def speak(self) -> str:
            return "..."

    class Dog(Animal):
        species = "Canis lupus familiaris"

        def speak(self) -> str:  # オーバーライド
            return "ワン!"

        @classmethod
        def info(cls) -> str:
            return f"species={cls.species}"

        @staticmethod
        def is_domestic() -> bool:
            return True

    dog = Dog("Pochi")
    print(f"{dog.name} は {Dog.info()} を持ち、鳴き声は '{dog.speak()}' です")
    print(f"is_domestic? -> {Dog.is_domestic()}")

    print_section("ミニクイズ（3問）: 数字で回答してください")

    def ask(q: str, choices: Dict[int, str], answer: int) -> bool:
        print(q)
        for i, text in choices.items():
            print(f"  {i}) {text}")
        try:
            raw = input("あなたの回答: ")
        except EOFError:
            # 非対話環境では常に不正解にしないよう、デフォルトで1番を選ぶ
            raw = "1"
        try:
            sel = int(raw)
        except ValueError:
            print("数値で入力してください。")
            return False
        correct = sel == answer
        print("正解!" if correct else f"不正解。正解は {answer} です。")
        return correct

    score = 0
    total = 3
    if ask(
        "Q1: 次のうち"不変(immutable)"なのはどれ?",
        {1: "list", 2: "tuple", 3: "dict"},
        2,
    ):
        score += 1
    if ask(
        "Q2: with open(...) as f: の利点として正しいのはどれ?",
        {1: "ファイルが自動的にクローズされる", 2: "例外が出なくなる", 3: "実行が高速になる"},
        1,
    ):
        score += 1
    if ask(
        "Q3: list(range(3)) の結果はどれ?",
        {1: "[1, 2, 3]", 2: "[0, 1, 2]", 3: "[0, 1, 2, 3]"},
        2,
    ):
        score += 1
    print(f"\nスコア: {score} / {total}")

    pause()

# %%
# =============================================================================
# レッスン管理とメイン処理
# =============================================================================
LessonFunc = Callable[[], None]


@dataclass
class Lesson:
    """レッスン情報を格納するデータクラス"""
    key: str
    title: str
    run: LessonFunc


def build_lessons() -> Dict[str, Lesson]:
    """利用可能なレッスンの辞書を構築"""
    return {
        "1": Lesson("1", "変数とデータ型", lesson_variables_types),
        "2": Lesson("2", "制御構文（if/for/while）", lesson_control_flow),
        "3": Lesson("3", "関数の基礎", lesson_functions),
        "4": Lesson("4", "コレクションと内包表記", lesson_collections_and_comprehensions),
        "5": Lesson("5", "ファイルI/Oと例外処理", lesson_file_io_and_exceptions),
        "6": Lesson("6", "OOP基礎 + ミニクイズ", lesson_oop_and_quiz),
    }


def run_all_lessons(lessons: Dict[str, Lesson]) -> None:
    """すべてのレッスンを順番に実行"""
    for key in sorted(lessons.keys(), key=lambda k: int(k)):
        lessons[key].run()


def main(argv: Optional[list[str]] = None) -> int:
    """メイン処理：対話的なレッスン選択"""
    lessons = build_lessons()
    print_title("Python基礎講座へようこそ！")
    while True:
        print("\n学びたいレッスン番号を選択してください:")
        for key in sorted(lessons.keys(), key=lambda k: int(k)):
            print(f"  {key}) {lessons[key].title}")
        print("  7) すべてのレッスンを順番に実行")
        print("  0) 終了")
        try:
            choice = input("\n選択: ").strip()
        except EOFError:
            # 非対話環境では "7" を選んで全実行して終了
            run_all_lessons(lessons)
            return 0

        if choice == "0":
            print("学習おつかれさまでした！また来てくださいね。")
            return 0
        if choice == "7":
            run_all_lessons(lessons)
            continue
        lesson = lessons.get(choice)
        if lesson is None:
            print("無効な選択です。もう一度お試しください。")
            continue
        lesson.run()

# %%
# =============================================================================
# スパイダー方式実行用：個別レッスン実行関数
# =============================================================================
def run_lesson_1():
    """レッスン1を単独実行（スパイダー方式用）"""
    lesson_variables_types()


def run_lesson_2():
    """レッスン2を単独実行（スパイダー方式用）"""
    lesson_control_flow()


def run_lesson_3():
    """レッスン3を単独実行（スパイダー方式用）"""
    lesson_functions()


def run_lesson_4():
    """レッスン4を単独実行（スパイダー方式用）"""
    lesson_collections_and_comprehensions()


def run_lesson_5():
    """レッスン5を単独実行（スパイダー方式用）"""
    lesson_file_io_and_exceptions()


def run_lesson_6():
    """レッスン6を単独実行（スパイダー方式用）"""
    lesson_oop_and_quiz()


def run_all():
    """全レッスンを実行（スパイダー方式用）"""
    lessons = build_lessons()
    run_all_lessons(lessons)

# %%

if __name__ == "__main__":
    sys.exit(main())

# 21_python.py 学習ガイド（スパイダー方式対応）

このドキュメントは、`21_python.py` の内容を要点整理した学習用ガイドです。スクリプトは対話式CLIとして各レッスンを順番に体験でき、エディタから個別関数を呼び出す「スパイダー方式」にも対応しています。

## 実行方法

- 対話式メニューを起動する:
```bash
python 21_python.py
```
  - 0: 終了
  - 7: すべてのレッスンを順番に実行
  - 1〜6: 該当レッスンのみ実行

- スパイダー方式（関数を個別に実行）:
  - エディタやノートブックから `run_lesson_1()` 〜 `run_lesson_6()`、または `run_all()` を呼び出してください。
  - 例（Python REPLなど）:
```python
exec(open("21_python.py", encoding="utf-8").read())
run_lesson_1()  # レッスン1のみ実行
```

---

## レッスン1: 変数とデータ型
- **主な型**: `int`, `float`, `str`, `bool`, `NoneType`
- **動的型付け**: 代入時に型が決まる（事前の型宣言は不要）
- **文字列の基本**: `len`, `upper`, スライス, f文字列

```python
a = 42
b = 3.14
s = "こんにちは"
t = True
n = None
print(type(a), type(b), type(s), type(t), type(n))

name = "Python"
print(len(name), name.upper(), name[0:3])
print(f"Hello, {name}!")
```

## レッスン2: 制御構文（if / for / while）
- **条件分岐**: `if / elif / else` と 比較・論理演算子
- **反復**: `for`（range, コレクション反復）/ `while`
- **中断/継続**: `break` / `continue`

```python
x = 7
if x % 2 == 0:
    msg = "偶数"
elif x % 3 == 0:
    msg = "3の倍数"
else:
    msg = "その他"

squares = []
for i in range(5):
    squares.append(i * i)

# while で合計
total, i = 0, 1
while i <= 5:
    total += i
    i += 1
```

## レッスン3: 関数の基礎
- **定義/呼び出し**、**戻り値**、**デフォルト引数**、**キーワード引数**
- **可変長引数**: `*args`, `**kwargs`
- **ラムダ式**: 簡単な式にのみ使用推奨

```python
def add(x: int, y: int) -> int:
    return x + y

def greet(name: str, punctuation: str = "!") -> str:
    return f"Hello, {name}{punctuation}"

def summarize(*numbers: int, **options) -> str:
    unit = options.get("unit", "点")
    return f"合計: {sum(numbers)}{unit}"

double = lambda n: n * 2
```

## レッスン4: コレクションと内包表記
- **コレクション**: `list`(可変/順序), `tuple`(不変/順序), `dict`(key-value), `set`(重複なし)
- **内包表記**: 宣言的・簡潔に新しいコレクションを生成

```python
nums_list = [1, 2, 3]
nums_tuple = (1, 2, 3)
person_dict = {"name": "Alice", "age": 30}
tags_set = {"python", "basic", "course"}

squares = [n * n for n in range(6)]
even_squares = [n for n in squares if n % 2 == 0]
mapping = {n: n * n for n in range(4)}
uniques = {c for c in "banana"}
```

## レッスン5: ファイルI/Oと例外処理
- **with文**: クローズ漏れ防止（コンテキストマネージャ）
- **例外処理**: `try / except / else / finally`

```python
# 一時ファイルへの書き込み→読み出し（概要）
import tempfile, os
with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
    tmp_path = tmp.name
    tmp.write("Hello File!\n1,2,3\n")

try:
    with open(tmp_path, "r", encoding="utf-8") as f:
        content = f.read()
finally:
    try:
        os.remove(tmp_path)
    except OSError:
        pass

# 例外捕捉
raw = "123x"
try:
    value = int(raw)
except ValueError as e:
    value = None
finally:
    ...
```

## レッスン6: オブジェクト指向（OOP）基礎 + ミニクイズ
- **クラス/継承/メソッド**、**クラスメソッド**、**スタティックメソッド**、**オーバーライド**
- 3問ミニクイズ（不変型、with文の利点、`range`の結果）

```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    species = "Canis lupus familiaris"
    def speak(self) -> str:
        return "ワン!"
    @classmethod
    def info(cls) -> str:
        return f"species={cls.species}"
    @staticmethod
    def is_domestic() -> bool:
        return True
```

---

## 補足
- 本スクリプトは標準ライブラリのみで動作します（`dataclasses`, `typing`, `tempfile`, `textwrap` など）。
- 非対話環境では自動的に全レッスン（7）が実行されます。
- `Enterキーでメニューに戻る` プロンプトが出たら、案内に従って次へ進んでください。

## 関連関数（スパイダー方式用）
- `run_lesson_1()` 〜 `run_lesson_6()`
- `run_all()`

> 詳細は `21_python.py` を参照してください。


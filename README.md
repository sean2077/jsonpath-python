- [jsonpath-python](#jsonpath-python)
  - [Features](#features)
  - [JSONPath Syntax](#jsonpath-syntax)
    - [Operators](#operators)
    - [Examples](#examples)
      - [Select Fields](#select-fields)
      - [Recursive Descent](#recursive-descent)
      - [Slice](#slice)
      - [Filter Expression](#filter-expression)
      - [Sorter Expression](#sorter-expression)
      - [Field-Extractor Expression](#field-extractor-expression)
    - [Appendix: Example JSON data:](#appendix-example-json-data)
  - [Todo List](#todo-list)

# jsonpath-python

A more powerful JSONPath implementation in modern python.

## Features

- [x] Light. (No need to install third-party dependencies.)
- [x] Support basic semantics of JSONPath.
- [x] Support output modes: VALUE, PATH.
- [x] Support filter operator, including multi-selection, inverse-selection filtering.
- [x] Support sorter operator, including sorting by multiple fields, ascending and descending order.
- [ ] Support parent operator.
- [ ] Support user-defined function.

## JSONPath Syntax

The JSONPath syntax in this project borrows from [JSONPath - XPath for JSON](http://goessner.net/articles/JSONPath/) and is **modified** and **extended** on it.

### Operators

| Operator         | Description                                                                  |
| ---------------- | ---------------------------------------------------------------------------- |
| `$`              | the root object/element                                                      |
| `@`              | the current object/element                                                   |
| `.` or `[]`      | child operator                                                               |
| `..`             | recursive descent                                                            |
| `*`              | wildcard                                                                     |
| `''`             | (Experimental) wrap field with special character: dots(`.`) and space (` `). |
| `start:end:step` | array slice operator (It's same as the slice in python)                      |
| `?()`            | applies a filter expression                                                  |
| `/()`            | applies a sorter expression                                                  |
| `()`             | applies a field-extractor expression                                         |

### Examples

Before running the following example, please import this module and the example data:

```python
>>> from jsonpath import JSONPath

# For the data used in the following example, please refer to the Appendix part.
```

#### Select Fields

Select a field:

```python
>>> JSONPath("$.book").parse(data)
[[{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}, {'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99, 'brand': {'version': 'v1.0.3'}}]]
>>> JSONPath("$[book]").parse(data)
[[{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}, {'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99, 'brand': {'version': 'v1.0.3'}}]]
```

(**Experimental**) Select a field with special character: dots(`.`) and space (` `).

```python
>>> JSONPath("$.'a.b c'").parse(data)
['a.b c']
>>> JSONPath("$['a.b c']").parse(data)
['a.b c']
```

Select multiple fields:

```python
>>> JSONPath("$[bicycle,scores]").parse(data)
[{'color': 'red', 'price': 19.95}, {'math': {'score': 100, 'avg': 60}, 'english': {'score': 95, 'avg': 80}, 'physic': {'score': 90, 'avg': 70}, 'chemistry': {'score': 85, 'avg': 80}, 'chinese': {'score': 60, 'avg': 75}}]
```

Select all fields using wildcard `*`:

```python
>>> JSONPath("$.*").parse(data)
['a.b c', [{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}, {'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99, 'brand': {'version': 'v1.0.3'}}], {'color': 'red', 'price': 19.95}, {'math': {'score': 100, 'avg': 60}, 'english': {'score': 95, 'avg': 80}, 'physic': {'score': 90, 'avg': 70}, 'chemistry': {'score': 85, 'avg': 80}, 'chinese': {'score': 60, 'avg': 75}}]
```

#### Recursive Descent

```python
>>> JSONPath("$..price").parse(data)
[8.95, 12.99, 8.99, 22.99, 19.95]
```

#### Slice

Support python-like slice.

```python
>>> JSONPath("$.book[1:3]").parse(data)
[{'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}]
>>> JSONPath("$.book[1:-1]").parse(data)
[{'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}]
>>> JSONPath("$.book[0:-1:2]").parse(data)
[{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}]
>>> JSONPath("$.book[-1:1]").parse(data)
[]
>>> JSONPath("$.book[-1:-11:3]").parse(data)
[]
>>> JSONPath("$.book[:]").parse(data)
[{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}, {'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99, 'brand': {'version': 'v1.0.3'}}]
>>> JSONPath("$.book[::-1]").parse(data)
[{'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99, 'brand': {'version': 'v1.0.3'}}, {'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99, 'brand': {'version': 'v1.0.2'}}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'brand': {'version': 'v0.0.1'}}, {'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'brand': {'version': 'v1.0.0'}}]

```

#### Filter Expression

Support all python comparison operators (`==`, `!=`, `<`, `>`, `>=`, `<=`), python membership operators (`in`, `not in`), python logical operators (`and`, `or`, `not`).

```python
>>> JSONPath("$.book[?(@.price>8 and @.price<9)].price").parse(data)
[8.95, 8.99]
>>> JSONPath('$.book[?(@.category=="reference")].category').parse(data)
['reference']
>>> JSONPath('$.book[?(@.category!="reference" and @.price<9)].title').parse(data)
['Moby Dick']
>>> JSONPath('$.book[?(@.author=="Herman Melville" or @.author=="Evelyn Waugh")].author').parse(data)
['Evelyn Waugh', 'Herman Melville']
```

`Note`: You must use double quote(`""`) instead of single quote(`''`) to wrap the compared string, because single quote(`''`) has another usage in this JSONPath syntax .

#### Sorter Expression

Support sorting by multiple fields (using operator `,`) and reverse sort (using operator `~`).

```python
>>> JSONPath("$.book[/(price)].price").parse(data)
[8.95, 8.99, 12.99, 22.99]
>>> JSONPath("$.book[/(~price)].price").parse(data)
[22.99, 12.99, 8.99, 8.95]
>>> JSONPath("$.book[/(category,price)].price").parse(data)
[8.99, 12.99, 22.99, 8.95]
>>> JSONPath("$.book[/(brand.version)].brand.version").parse(data)
['v0.0.1', 'v1.0.0', 'v1.0.2', 'v1.0.3']
>>> JSONPath("$.scores[/(score)].score").parse(data)
[60, 85, 90, 95, 100]
```

#### Field-Extractor Expression

Using `(field1,field2,…,filedn)` after a dict object to extract its fields.

```python
>>> JSONPath("$.scores[/(score)].(score)").parse(data)
[{'score': 60}, {'score': 85}, {'score': 90}, {'score': 95}, {'score': 100}]
>>> JSONPath("$.book[/(category,price)].(title,price)").parse(data)
[{'title': 'Moby Dick', 'price': 8.99}, {'title': 'Sword of Honour', 'price': 12.99}, {'title': 'The Lord of the Rings', 'price': 22.99}, {'title': 'Sayings of the Century', 'price': 8.95}]
```

### Appendix: Example JSON data:

```python
data = {
    "a.b c": "a.b c",
    "book": [
        {
            "category": "reference",
            "author": "Nigel Rees",
            "title": "Sayings of the Century",
            "price": 8.95,
            "brand": {
                "version": "v1.0.0"
            }
        },
        {
            "category": "fiction",
            "author": "Evelyn Waugh",
            "title": "Sword of Honour",
            "price": 12.99,
            "brand": {
                "version": "v0.0.1"
            }
        },
        {
            "category": "fiction",
            "author": "Herman Melville",
            "title": "Moby Dick",
            "isbn": "0-553-21311-3",
            "price": 8.99,
            "brand": {
                "version": "v1.0.2"
            }
        },
        {
            "category": "fiction",
            "author": "J. R. R. Tolkien",
            "title": "The Lord of the Rings",
            "isbn": "0-395-19395-8",
            "price": 22.99,
            "brand": {
                "version": "v1.0.3"
            }
        }
    ],
    "bicycle": {
        "color": "red",
        "price": 19.95
    },
    "scores": {
        "math": {
            "score": 100,
            "avg": 60
        },
        "english": {
            "score": 95,
            "avg": 80
        },
        "physic": {
            "score": 90,
            "avg": 70
        },
        "chemistry": {
            "score": 85,
            "avg": 80
        },
        "chinese": {
            "score": 60,
            "avg": 75
        }
    }
}
```

## Todo List

- Syntax and character set (refer to k8s)

> The name segment is required and must be 63 characters or less, beginning and ending with an alphanumeric character (`[a-z0-9A-Z]`) with dashes (`-`), underscores (`_`), dots (`.`), and alphanumerics between.

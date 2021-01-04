<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [jsonpath-python](#jsonpath-python)
  - [Features](#features)
  - [Examples](#examples)
    - [Filter](#filter)
    - [Sort](#sort)
    - [Output mode: FIELD (In progress)](#output-mode-field-in-progress)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# jsonpath-python

A more powerful JSONPath implementations in modern python.

## Features

- [x] Light. (No need to install third-party dependencies.)
- [x] Powerful filtering function, including multi-selection, inverse-selection filtering.
- [x] Powerful sorting function, including sorting by multiple fields, ascending and descending order.
- [x] Support output mode: VALUE
- [ ] Support output mode: PATH
- [ ] Support output mode: FIELD
- [ ] Support parent operator

## Examples

JSON format data:

```python
data = {
    "store": {
        "book": [
            {
                "category": "reference",
                "author": "Nigel Rees",
                "title": "Sayings of the Century",
                "price": 8.95
            },
            {
                "category": "fiction",
                "author": "Evelyn Waugh",
                "title": "Sword of Honour",
                "price": 12.99
            },
            {
                "category": "fiction",
                "author": "Herman Melville",
                "title": "Moby Dick",
                "isbn": "0-553-21311-3",
                "price": 8.99
            },
            {
                "category": "fiction",
                "author": "J. R. R. Tolkien",
                "title": "The Lord of the Rings",
                "isbn": "0-395-19395-8",
                "price": 22.99
            }
        ],
        "bicycle": {
            "color": "red",
            "price": 19.95
        }
    }
}
```

### Filter

```python
>>> JSONPath('$.store.book[?(@.price>8.95 and @.price<=20 and @.title!="Sword of Honour")]').parse(data)
```

```json
[
  {
    "category": "fiction",
    "author": "Herman Melville",
    "title": "Moby Dick",
    "isbn": "0-553-21311-3",
    "price": 8.99
  }
]
```

### Sorter

```python
>>> JSONPath("$.store.book[/(~category,price)]").parse(data)
```

```json
[
  {
    "category": "reference",
    "author": "Nigel Rees",
    "title": "Sayings of the Century",
    "price": 8.95
  },
  {
    "category": "fiction",
    "author": "Herman Melville",
    "title": "Moby Dick",
    "isbn": "0-553-21311-3",
    "price": 8.99
  },
  {
    "category": "fiction",
    "author": "Evelyn Waugh",
    "title": "Sword of Honour",
    "price": 12.99
  },
  {
    "category": "fiction",
    "author": "J. R. R. Tolkien",
    "title": "The Lord of the Rings",
    "isbn": "0-395-19395-8",
    "price": 22.99
  }
]
```

### Field-Extractor (In progress)

```python
>>> JSONPath("$.store.book[*][title,price]",result_type="FIELD").parse(data)
```

```json
{
  "store": {
    "book": [
      {
        "title": "Sayings of the Century",
        "price": 8.95
      },
      {
        "title": "Sword of Honour",
        "price": 12.99
      },
      {
        "title": "Moby Dick",
        "price": 8.99
      },
      {
        "title": "The Lord of the Rings",
        "price": 22.99
      }
    ]
  }
}
```

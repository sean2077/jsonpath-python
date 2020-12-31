<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [jsonpath-python](#jsonpath-python)
  - [Features](#features)
  - [Examples](#examples)
    - [Fields-Extractor](#fields-extractor)
    - [Multi-selection and inverse-selection filtering](#multi-selection-and-inverse-selection-filtering)
    - [Sorting by multiple fields, ascending and descending order](#sorting-by-multiple-fields-ascending-and-descending-order)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# jsonpath-python

A more powerful JSONPath implementations in modern python.

## Features

- [x] Light. (No need to install third-party dependencies.)
- [ ] Support fields-extractor.
- [ ] Powerful filtering function, including multi-selection, inverse-selection filtering.
- [ ] Powerful sorting function, including sorting by multiple fields, ascending and descending order.

## Issues

- Not support parent operator.

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

### Fields-Extractor

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

### Multi-selection and inverse-selection filtering

```python
>>> JSONPath("$.store.book[?(@.price>8.95 && @.price<=20 || @.title!='Sword of Honour')]").parse(data)
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

### Sorting by multiple fields, ascending and descending order

```python
>>> JSONPath("$.store.book[\category,/price]").parse(data)
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

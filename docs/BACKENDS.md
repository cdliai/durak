# Backend Control Layer

Durak provides a high-level backend control layer through `DurakController`.

## Backend Names

- `auto`: use Rust backend when extension is installed, otherwise fallback to Python.
- `rust`: require Rust extension and fail explicitly if unavailable.
- `python`: pure Python execution path for supported features.

## Capability Matrix

Current capability model:

- Rust backend:
  - normalization: yes
  - tokenization: yes
  - tokenization with offsets: yes
  - lemmatization: yes
  - embedded resources: yes
- Python backend:
  - normalization: yes
  - tokenization: yes
  - tokenization with offsets: no
  - lemmatization: no
  - embedded resources: no (file/provider based)

## Usage

```python
from durak import DurakController

controller = DurakController(backend="auto")

text = controller.normalize("İSTANBUL ve IĞDIR")
tokens = controller.tokenize(text)
```

If you require offsets or lemmatization, use `backend="rust"` (or `auto` with Rust extension installed).

# Durak CLI - Command-Line Interface

The Durak CLI provides standalone command-line access to Turkish NLP processing capabilities without requiring Python or any runtime dependencies. Built in Rust with embedded resources for maximum performance and portability.

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/cdliai/durak.git
cd durak

# Build the CLI binary (requires Rust toolchain)
cargo build --release --bin durak

# The binary will be at: target/release/durak
# Optionally, install to system PATH:
cargo install --path . --bin durak
```

### Verify Installation

```bash
durak version
# Output: Durak v0.4.0
```

## Commands

### `tokenize` - Turkish Text Tokenization

Tokenize Turkish text with morphology-aware splitting. Preserves Turkish-specific features like apostrophes, clitics, and suffixes.

**Basic Usage:**

```bash
durak tokenize "Merhaba dünya!"
# Output:
# Merhaba
# dünya
# !
```

**With Character Offsets:**

```bash
durak tokenize --offsets "İstanbul'a gittim"
# Output (tab-separated):
# İstanbul'a	0	10
# gittim	11	17
```

**JSON Output:**

```bash
durak tokenize --json "Ankara'da kaldım"
# Output:
# {
#   "tokens": ["Ankara'da", "kaldım"]
# }
```

**JSON with Offsets:**

```bash
durak tokenize --offsets --json "Test metni"
# Output:
# {
#   "tokens": [
#     { "text": "Test", "start": 0, "end": 4 },
#     { "text": "metni", "start": 5, "end": 10 }
#   ]
# }
```

**From Stdin:**

```bash
echo "İzmir'de güneşli hava var" | durak tokenize
cat corpus.txt | durak tokenize > tokens.txt
```

**Features Preserved:**
- **Apostrophes**: `İstanbul'a`, `Ankara'da` (kept as single tokens)
- **Clitics**: `nasılsın`, `geliyorum` (preserved)
- **URLs**: `https://example.com` (single token)
- **Emoticons**: `:)`, `:D`, `:(` (preserved)
- **Numbers**: `2023`, `1.5`, `10-15` (handled correctly)

---

### `normalize` - Unicode-Aware Text Normalization

Normalize Turkish text with correct handling of Turkish-specific characters (İ/ı, I/i conversion).

**Basic Usage:**

```bash
durak normalize "İSTANBUL"
# Output: istanbul
```

**Turkish Character Handling:**

```bash
# Dotted I: İ → i
durak normalize "İZMİR"
# Output: izmir

# Dotless I: I → ı
durak normalize "IŞIK"
# Output: ışık

# Mixed input
durak normalize "TÜRKÇE ÇOK GÜZEL"
# Output: türkçe çok güzel
```

**JSON Output:**

```bash
durak normalize --json "MERHABA"
# Output:
# {
#   "original": "MERHABA",
#   "normalized": "merhaba"
# }
```

**From Stdin:**

```bash
echo "İSTANBUL'A GİTTİM" | durak normalize
# Output: istanbul'a gittim
```

---

### `version` - Version and Build Information

Display version and build metadata.

**Basic Usage:**

```bash
durak version
# Output:
# Durak v0.4.0
# Build Date: 2024-01-26
# Package: _durak_core
```

**JSON Output:**

```bash
durak version --json
# Output:
# {
#   "durak_version": "0.4.0",
#   "package_name": "_durak_core",
#   "build_date": "2024-01-26"
# }
```

---

## Global Options

### `--json` - JSON Output

Available for all commands. Outputs structured JSON for scripting and pipeline integration.

```bash
durak --json tokenize "Test"
durak --json normalize "TÜRKÇE"
durak --json version
```

---

## Advanced Usage

### Shell Pipelines

Integrate Durak into Unix-style text processing pipelines:

```bash
# Tokenize and count unique tokens
cat corpus.txt | durak tokenize | sort | uniq -c | sort -rn

# Normalize and filter
echo "İSTANBUL ANKARA İZMİR" | durak normalize | tr ' ' '\n' | grep -v '^$'

# JSON processing with jq
durak tokenize --json "Merhaba dünya" | jq '.tokens | length'
```

### Batch Processing

Process multiple files:

```bash
# Process all text files in a directory
for file in data/*.txt; do
  durak tokenize < "$file" > "tokens/$(basename $file)"
done

# Parallel processing with GNU parallel
find data/ -name "*.txt" | parallel "durak tokenize < {} > tokens/{/.}.tokens"
```

### Scripting with JSON

Python example:

```python
import json
import subprocess

text = "İstanbul'a gittik."
result = subprocess.run(
    ["durak", "tokenize", "--json", text],
    capture_output=True,
    text=True
)
tokens = json.loads(result.stdout)["tokens"]
print(tokens)  # ['İstanbul\\'a', 'gittik', '.']
```

Node.js example:

```javascript
const { execSync } = require('child_process');

const text = "Ankara'da kaldım";
const output = execSync(`durak tokenize --json "${text}"`).toString();
const tokens = JSON.parse(output).tokens;
console.log(tokens);  // ["Ankara'da", "kaldım"]
```

---

## Performance

The Durak CLI is optimized for throughput and low latency:

- **Zero startup overhead**: Embedded resources (no file I/O)
- **Rust compilation**: Near-native C performance
- **Streaming support**: Processes stdin efficiently for large corpora
- **Memory efficient**: Minimal allocations, suitable for production pipelines

**Benchmarks** (on MacBook Pro M1):

| Operation | Throughput | Latency |
|-----------|-----------|---------|
| Tokenization | ~50 MB/s | ~2ms |
| Normalization | ~100 MB/s | ~1ms |

Run your own benchmarks:

```bash
# Generate test corpus
python3 -c "print('Merhaba dünya! ' * 10000)" > large.txt

# Measure tokenization speed
time durak tokenize < large.txt > /dev/null
```

---

## Troubleshooting

### "No text provided" Error

**Problem**: Running `durak tokenize` or `durak normalize` without arguments and no stdin.

**Solution**: Provide text as argument OR pipe via stdin:

```bash
# ✅ Correct
durak tokenize "text here"
echo "text here" | durak tokenize

# ❌ Wrong (no text, no stdin)
durak tokenize
```

### Unicode Display Issues

**Problem**: Turkish characters not displaying correctly in terminal.

**Solution**: Ensure your terminal uses UTF-8 encoding:

```bash
# Check locale
locale | grep UTF-8

# Set UTF-8 (if needed)
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Binary Not Found After Build

**Problem**: `cargo build` succeeds but `durak` command not found.

**Solution**: Use full path or install to system:

```bash
# Option 1: Use full path
./target/release/durak tokenize "test"

# Option 2: Install to ~/.cargo/bin (added to PATH by rustup)
cargo install --path . --bin durak

# Option 3: Copy to system bin (requires sudo)
sudo cp target/release/durak /usr/local/bin/
```

---

## Comparison: CLI vs Python API

| Feature | CLI | Python API |
|---------|-----|----------|
| Installation | Single binary | `pip install durak-nlp` |
| Dependencies | None (standalone) | Python 3.8+ |
| Startup Time | ~1ms | ~50ms (module load) |
| GIL-released | N/A | ✅ Yes |
| Pipeline flexibility | Basic | Full (custom stopwords, etc.) |
| Use case | Scripting, one-off tasks | Research, batch processing |

**When to use CLI:**
- Quick text processing in shell scripts
- Integration with non-Python tools
- Lightweight serverless functions
- Testing and exploration

**When to use Python API:**
- Research workflows with Jupyter
- Complex pipelines with custom stopwords
- Batch processing with multiprocessing
- Integration with ML frameworks (PyTorch, etc.)

---

## Examples

### Example 1: Extract Tokens from Turkish News Articles

```bash
# Download article
curl -s "https://example.com/article.html" | html2text | durak tokenize > tokens.txt

# Count most frequent tokens
durak tokenize < tokens.txt | sort | uniq -c | sort -rn | head -20
```

### Example 2: Normalize Turkish Hashtags

```bash
# Input: Twitter hashtags (uppercase)
echo "#İSTANBUL #TÜRKÇE #ANKARA" | durak normalize
# Output: #istanbul #türkçe #ankara
```

### Example 3: Build Vocabulary from Corpus

```bash
# Tokenize, normalize, and build unique vocabulary
cat corpus/*.txt | \
  durak tokenize | \
  while read token; do durak normalize "$token"; done | \
  sort -u > vocabulary.txt
```

### Example 4: JSON Pipeline for NER Preparation

```bash
# Prepare NER-ready JSON with offsets
durak tokenize --offsets --json "İstanbul'a 2023 yılında gittik." | \
  jq '.tokens[] | select(.text | test("[A-Z]"))'
# Extracts capitalized tokens (potential named entities)
```

---

## Related Documentation

- **[Architecture Guide](ARCHITECTURE.md)**: Design principles and internals
- **[Python API Guide](../README.md)**: Python bindings and advanced usage
- **[Examples](../examples/)**: Code samples for common tasks
- **[Contributing](../CONTRIBUTING.md)**: Development setup and guidelines

---

## Support

- **Issues**: [GitHub Issues](https://github.com/cdliai/durak/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cdliai/durak/discussions)
- **Email**: [Your support email]

---

**Happy tokenizing! 🚀**

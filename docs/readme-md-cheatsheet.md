# 🧠 Markdown Cheat Sheet for Obsidian

## Headers
```
# H1
## H2
### H3
#### H4
##### H5
###### H6
```

## Emphasis
```
*italic* or _italic_
**bold** or __bold__
***bold italic***
~~strikethrough~~
```

## Lists

**Unordered List:**
```
- Item 1
  - Subitem 1.1
    - Subsubitem
* Item 2
+ Item 3
```

**Ordered List:**
```
1. First
2. Second
   1. Sub-item
   2. Sub-item
3. Third
```

## Checkboxes / Task List
```
- [ ] Task not done
- [x] Task done
```

## Links
```
[Link Text](https://example.com)
<https://example.com> (autolink)
```

## Images
```
![Alt text](https://example.com/image.png)
```

## Code

**Inline code:**
```
Use `code` inside a sentence
```

**Code block (fenced):**
<pre>
```bash
echo "Hello, World!"
```
</pre>

**Language-specific syntax highlighting:**
<pre>
```python
def hello():
    print("Hello World")
```
</pre>

## Blockquote
```
> This is a quote.
>> Nested quote.
```

## Horizontal Rule
```
---
or
***
or
___
```

## Tables
```
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | More     |
| Row 2    | Data     | More     |
```

## Footnotes
```
Here is a statement.[^1]

[^1]: This is the footnote.
```

## Highlight / Mark
(Only works in Obsidian)
```
==highlight this text==
```

## Internal Links (Obsidian)
```
[[Note Title]]
[[Note Title#Section]]
[[Note Title|Custom Link Text]]
```

## Tags (Obsidian)
```
#tagname
```

## Callouts (Obsidian)
```
> [!note] Custom Title
> This is a note callout.

> [!tip]
> This is a tip.

> [!warning]
> Be careful with this.

> [!danger]
> Critical alert.
```

## Embed Files or Notes
```
![[Note Name]]
![[image.png]]
![[Note Name#Section]]
```

## Math (LaTeX)
**Inline Math:**
```
$\frac{a}{b}$
```

**Block Math:**
```
$$
E = mc^2
$$
```

## Dataview (if plugin enabled)
```
```dataview
table status, due
from "Tasks"
where status != "done"
sort due asc
```
```

---

> Paste this in Obsidian for a complete Markdown reference.

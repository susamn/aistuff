# Problem record schema (schema_version 1)

One JSON file per problem, stored at
`~/.local/share/mosaic/data/leetcode-trainer/problems/<slug>.json`. `<slug>`
is the LeetCode URL slug (kebab-case) and is the file's identity — adding a
file with an existing slug **replaces** that problem (this is "swap").

```json
{
  "schema_version": 1,
  "slug": "two-sum",
  "leetcode_id": 1,
  "title": "Two Sum",
  "difficulty": "Easy",
  "topics": ["Array", "Hash Table"],
  "source_url": "https://leetcode.com/problems/two-sum/",
  "added_at": "2026-08-08",
  "problem": {
    "statement_md": "Markdown. Paraphrased in your own words — never copied verbatim from LeetCode (copyright). 2-5 sentences.",
    "examples": [
      { "input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] == 9" }
    ],
    "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"]
  },
  "intuition": {
    "summary_md": "1-3 sentences: the key insight, in plain language.",
    "approach_md": "A short paragraph or a few bullet points walking through the approach. Meaningful, not padded — skip restating the code line by line.",
    "diagram": null,
    "time_complexity": "O(n)",
    "space_complexity": "O(n)"
  },
  "solutions": {
    "python": { "code": "def twoSum(nums, target):\n    ...", "notes_md": "" },
    "golang": { "code": "func twoSum(nums []int, target int) []int {\n    ...\n}", "notes_md": "" }
  }
}
```

## Field notes

- `slug` — must match `^[a-z0-9]+(-[a-z0-9]+)*$`, and must equal the filename
  minus `.json`.
- `difficulty` — exactly one of `Easy` | `Medium` | `Hard`.
- `topics` — 1-4 short tags, title case (`"Dynamic Programming"`, `"Binary Search"`, ...).
- `problem.statement_md` / `examples` / `constraints` — **paraphrased**, not a
  copy of LeetCode's own text. `source_url` is how a reader gets the
  authoritative original.
- `intuition.diagram` — optional. Either `null`, or an object
  `{ "type": "svg", "content": "<svg ...>...</svg>" }` for a small inline
  diagram, or `{ "type": "ascii", "content": "..." }` for a plain-text
  sketch (arrays/pointers/tree shapes are often clearer as ASCII than SVG).
  Only add one when it clarifies the approach — most problems don't need one.
- `solutions.python` / `solutions.golang` — both required. Working, idiomatic
  solutions matching the approach described in `intuition`. `notes_md` is
  optional — use it only for a note that doesn't fit as a code comment (e.g.
  "same idea as the Python solution, using a map instead of a dict").
- Keep `intuition.summary_md` and `approach_md` **simple, not exhaustive** —
  a reader should get the key idea in a few seconds, with just enough detail
  to reconstruct the approach without re-deriving it.

## Validation

`<SKILL_PATH>/scripts/lc.sh validate <file>` checks: valid JSON, required
fields present, `difficulty` in the closed set, `slug` matches filename and
regex, both solution languages present and non-empty. Exit `0` clean, `1`
violations found (each printed on stderr, one per line), `2` couldn't run
(bad path, invalid JSON).

## manifest.json

Rebuilt from the `problems/` directory by `lc.sh rebuild-manifest` (also run
automatically by `add`/`remove`). One entry per problem:

```json
{
  "schema_version": 1,
  "generated_at": "2026-08-08T12:00:00Z",
  "problems": [
    { "id": "two-sum", "leetcode_id": 1, "title": "Two Sum", "difficulty": "Easy",
      "topics": ["Array", "Hash Table"], "schema_version": 1, "tier": "hot" }
  ]
}
```

`id` here is the slug — the data-home contract's manifest entries are keyed
by `id`, and for this skill `id` and `slug` are the same string.

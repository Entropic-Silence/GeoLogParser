Inspect only the supplied cropped field image.

Transcribe every visible numeric token exactly as printed, preserving a leading
sign and the decimal separator. Do not infer a value from neighboring geology,
units, expected continuity, or the field name. If a character is ambiguous,
set `uncertain` to true. If no numeric token is visible, return an empty array.

Return exactly one JSON object and no other text:

```json
{"numeric_tokens": ["4.50"], "uncertain": false}
```

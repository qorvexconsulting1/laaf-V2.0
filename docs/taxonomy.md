# LAAF Technique Taxonomy (49 Techniques)

Full taxonomy from paper §5 — Atta et al., 2026 (arXiv:2507.10457).

Each technique has **5 template variants** selected randomly at runtime, giving 220 distinct surface forms before instruction variation is applied.

## Category 1: Encoding (E1–E11)

Transforms payload at byte level, bypassing string-pattern scanners.

| ID  | Name             | Encoding Method                  | LPCI Stage |
|-----|------------------|----------------------------------|------------|
| E1  | Base64           | Standard base64                  | S5         |
| E2  | Hexadecimal      | Hex string (0x...)               | S5         |
| E3  | Unicode Escape   | \uXXXX per character             | S5         |
| E4  | HTML Entity      | &#XX; per character              | S5         |
| E5  | ROT13            | Caesar cipher shift-13           | S5         |
| E6  | URL Encoding     | Percent-encoding (%XX)           | S5         |
| E7  | Binary           | 8-bit binary groups              | S5         |
| E8  | Octal            | \XXX octal escapes               | S5         |
| E9  | Nested Base64    | Double base64 (two layers)       | S5         |
| E10 | ROT13 + Base64   | ROT13 then base64                | S5         |
| E11 | Hex + Base64     | Hex bytes wrapped in base64      | S5         |

## Category 2: Structural (S1–S8)

Disguises payloads as legitimate document infrastructure.

| ID  | Name              | Container Format           | LPCI Stage |
|-----|-------------------|----------------------------|------------|
| S1  | JSON Embedding    | `{"config": "<payload>"}` | S2         |
| S2  | YAML Front Matter | `--- config: \| ...`      | S2         |
| S3  | Markdown Comment  | `[//]: # (payload)`       | S2         |
| S4  | HTML Meta Tag     | `<meta content="...">`    | S2         |
| S5  | Code Block        | ` ```config\n...``` `     | S2         |
| S6  | Split Payload     | Header + footer fragments  | S2         |
| S7  | XML Comment       | `<!-- config: ... -->`    | S2         |
| S8  | PDF Metadata      | `/Author (...)` field      | S2         |

## Category 3: Semantic (M1–M8)

Reframes injected instructions as legitimate system communications.

| ID  | Name                  | Reframe Strategy            | LPCI Stage |
|-----|-----------------------|-----------------------------|------------|
| M1  | Formatting Requirement| Presents as output format   | S3         |
| M2  | Compliance Directive  | GDPR/SOC2/NIST authority    | S3         |
| M3  | System Initialisation | Session bootstrap config    | S3         |
| M4  | Tool Metadata Schema  | Function/tool call format   | S3         |
| M5  | Authority Spoofing    | Admin/root token claim      | S3         |
| M6  | ISO Audit Directive   | ISO 42001/27001 compliance  | S3         |
| M7  | Gradual Trust Build   | Progressive trust escalation| S3         |
| M8  | Document Config Tag   | Hidden metadata field       | S3         |

## Category 4: Layered (L1–L5)

Stacks techniques multiplicatively: P(detect) = ∏ p_i.

| ID  | Chain                                  | Layers | LPCI Stage |
|-----|----------------------------------------|--------|------------|
| L1  | ROT13 → Base64 → JSON → Authority      | 4      | S5+S3      |
| L2  | Unicode → HTML Meta → Compliance       | 3      | S5+S3      |
| L3  | Nested Base64 → YAML → Authority Spoof | 3      | S5+S3      |
| L4  | Hex → Split Payload → Formatting       | 3      | S5+S3      |
| L5  | URL Encode → Code Block → ISO Audit    | 3      | S5+S3      |

## Category 5: Triggers (T1–T12)

Conditional activation — payload fires only when trigger condition is met.

| ID  | Name                    | Trigger Type               |
|-----|-------------------------|----------------------------|
| T1  | Keyword Trigger         | Single keyword             |
| T2  | Compound Keyword        | AND of two keywords        |
| T3  | Negation Trigger        | Fires when keyword absent  |
| T4  | Regex Pattern           | Regex match on input       |
| T5  | Temporal Trigger        | Time/date condition        |
| T6  | Semantic Similarity     | Meaning-based match        |
| T7  | Instruction Count       | After N interactions       |
| T8  | Role-Based              | Specific user role         |
| T9  | Tool-Call Trigger       | On specific tool invocation|
| T10 | Cross-Session           | Fires in future session    |
| T11 | Confidence-Based        | Only if model is confident |
| T12 | Steganographic          | Hidden via zero-width/encoding |

## Category 6: Exfiltration (EX1–EX5)

Channels injected instructions into data that exits the model boundary.

| ID  | Name                        | Exfiltration Method                      | LPCI Stage |
|-----|-----------------------------|------------------------------------------|------------|
| EX1 | URL Parameter Exfil         | Embeds secrets in outbound URL query     | S6         |
| EX2 | Markdown Image Exfil        | Encodes data in `![](url?data=...)` tag  | S6         |
| EX3 | JSON Field Exfil            | Leaks data in structured JSON responses  | S6         |
| EX4 | Steganographic Text Exfil   | Hides data via zero-width characters     | S6         |
| EX5 | Tool Call Argument Exfil    | Smuggles data in function call arguments | S6         |

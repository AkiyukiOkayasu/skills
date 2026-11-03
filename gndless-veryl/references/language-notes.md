# Veryl language notes

## Generic function

- component namespace 内の generic function へ、呼び出し元 module の parameter や導出 const を generic actual argument として渡せない場合がある (Veryl #3110)
- 再利用する generic helper は project-scope function として定義する
- dependency から公開する場合は `pub function` とし、`project_name::function_name::<...>` で呼び出す

## Boolean type

- `bbool` は `bit<1>` の2値 Boolean、`lbool` は `logic<1>` の4値 Boolean
- `bbool` は設計上 `0/1` を保証できる制御値に使う
- `lbool` は未初期化・CDC・external input の `x/z` を保持する値に使う
- `logic` は1bit encoding、waveform、protocol signal、または検証で `x/z` を観測する値に使う

## Types

- `logic<W>` は packed、`[N]` は unpacked
- `param` は外部から override する値、`const` は内部で導出する値

参照: https://doc.veryl-lang.org/book/05_language_reference/03_data_type/01_builtin_type.html

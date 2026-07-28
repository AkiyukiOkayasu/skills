# Veryl language notes

Veryl 固有の generic、型、Boolean、system function を扱う場合に参照する。

## Generic function

- component namespace 内の generic function へ、呼び出し元 module の parameter や導出 const を generic actual argument として渡せない場合がある
- parameterized module から使う再利用可能な generic helper は project-scope function として定義
- dependency から公開する場合は `pub function` とし、`project_name::function_name::<...>` で呼び出す
- 生成 SystemVerilog の可視性制約と Veryl #3110 を考慮

## 型

- `logic<W>` は packed、`[N]` は unpacked
- public port、module 契約、register・accumulator の width、signedness が重要な境界では型を明示
- `param` は外部から override する値、`const` は内部で導出する値
- enum の幅は原則として推論

## Boolean type

- `bbool` は `bit<1>` の2値 Boolean、`lbool` は `logic<1>` の4値 Boolean
- `bbool` は設計上 `0/1` を保証でき、`true`/`false` として読むのが自然な制御値に使用
- `lbool` は Boolean の意味を持ちながら未初期化・CDC・external input の `x/z` を保持する場合に使用
- `logic` は1bit encoding、waveform、protocol signal、または検証で `x/z` を観測する値に使用
- `logic` から `bbool` への変換では `x/z` が失われるため、2値化が仕様であることを確認

参照: https://doc.veryl-lang.org/book/05_language_reference/03_data_type/01_builtin_type.html

## System functions / tasks

- `$clog2(x)`: log2 の切り上げ
- `$size(x)`: array size
- `$bits(x)`: value の bit width
- `$signed(x)`: signed として扱う
- `$readmemh(path, mem)`: hex file を memory へ読み込み
- `$display(...)`: string output
- `$error(...)`: error output
- `$finish()`: simulation 終了

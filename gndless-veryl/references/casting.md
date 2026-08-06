# Cast

Veryl の cast、width 変更、signed/unsigned 変換を扱う場合に参照する。

cast を追加・変更する前に、source width、source signedness、target width、target signedness、truncation の有無を個別に確認する。

## Width manipulation primitives ($std)

拡張・切り詰めには `$std` 標準ライブラリの width manipulation primitives を優先する (Veryl 0.20.0 以降、dependency 追加不要)。

- `$std::zero_extend::<FROM_TYPE, TO_TYPE>(from)`: 上位に 0 を反復して拡張
- `$std::one_extend::<FROM_TYPE, TO_TYPE>(from)`: 上位に 1 を反復して拡張
- `$std::sign_extend::<FROM_TYPE, TO_TYPE>(from)`: FROM_TYPE の最上位 bit (MSB) を反復して拡張
- `$std::truncate::<FROM_TYPE, TO_TYPE>(from)`: 上位 bit を切り捨てて下位 bit を保持
- いずれも TO_WIDTH < FROM_WIDTH のときは拡張幅 0 になり truncate 相当の動作になるため、切り詰めの意図は `$std::truncate` で明示する
- `sign_extend` は source の signed/unsigned 属性ではなく bit pattern の MSB で拡張するため、`$signed()` の適用順による extension の違いを気にする必要がない
- generic 引数には type alias または fixed type を指定し、`logic<8>` などの型リテラルは直接書けない
- 同じ namespace に `$std::min`、`$std::max` (element-wise) もある

```veryl
type FROM_TYPE = logic<8>;
type TO_TYPE   = logic<16>;

let a: logic<16> = $std::zero_extend::<FROM_TYPE, TO_TYPE>(unsigned8); // 16'h0080
let b: logic<16> = $std::one_extend::<FROM_TYPE, TO_TYPE>(unsigned8);  // 16'hff80
let c: logic<16> = $std::sign_extend::<FROM_TYPE, TO_TYPE>(signed8);   // 16'hff80: MSB=1を反復
let d: logic<8>  = $std::truncate::<TO_TYPE, FROM_TYPE>(value16);      // value16[7:0]
```

## Width cast

- `value as WIDTH` は SystemVerilog の `WIDTH'(value)` に変換され、値の bit width だけを変更
- `WIDTH` には数値だけでなく width parameter や const も使用可能
- target width が広い場合、source が signed なら sign extension、unsigned なら zero extension
- target width が狭い場合、上位 bit を切り捨てて下位 `WIDTH` bit を保持
- width cast 自体は signed/unsigned 属性を変更しない
- `as logic<WIDTH>`、`as bit<WIDTH>`、`as signed logic<WIDTH>` は使用せず、width cast は `as WIDTH` と記載
- 拡張・切り詰めの意図が明確な箇所は `as WIDTH` よりも上記の `$std::*` primitives を使い、generated RTL の意図を明示

## Signedness

- `$signed(value)` と `$unsigned(value)` は bit width を変えず、式を signed/unsigned として解釈
- widening の前に `$signed()` を適用すると sign extension、前に `$unsigned()` を適用すると zero extension
- widening 後の `$signed()` / `$unsigned()` は既に拡張された bit pattern の属性だけを変更するため、cast の順序を明示
- sign extension が目的なら `$signed(value) as WIDTH` の順序トリックではなく `$std::sign_extend` を使う

`unsigned8 = 8'h80`、`signed8 = signed 8'h80` の場合:

```veryl
let a: logic<16>        = unsigned8 as 16;          // 16'h0080: zero extension
let b: signed logic<16> = signed8 as 16;            // 16'hff80: sign extension
let c: signed logic<16> = $signed(unsigned8) as 16; // 16'hff80: signed化してから拡張
let d: signed logic<16> = $signed(unsigned8 as 16); // 16'h0080: zero extension後にsigned化
let e: logic<16>        = $unsigned(signed8) as 16; // 16'h0080: unsigned化してから拡張
let f: logic<16>        = $unsigned(signed8 as 16); // 16'hff80: sign extension後にunsigned化
```

## Fixed and user-defined type cast

- `as u8/u16/u32/u64`、`as i8/i16/i32/i64` など fixed integer type への cast は target width と結果の signedness を指定
- fixed integer type cast でも widening 前の source signedness が extension を決めるため、unsigned source の `as i16` は source bit pattern を signed 8bit として sign extension しない
- unsigned bit pattern を signed として sign extension する場合は `$std::sign_extend` を使用
- enum など user-defined type への変換は `value as TypeName` を使用
- user-defined type cast では encoding の対応と illegal value の扱いを別途確認

```veryl
let a: logic<16>        = unsigned8 as u16;         // unsigned 16bit
let b: signed logic<16> = unsigned8 as i16;         // signed 16bitだが値は16'h0080
let c: signed logic<16> = $signed(unsigned8) as 16; // signed 8bitとして解釈して16'hff80へ拡張
let d: State            = raw_state as State;       // user-defined enumへcast
```

## Truncation

- narrowing は上位 bit を失うため、意図した modulo / slice 動作であることを確認
- signed value の narrowing でも下位 bit だけが残り、数値範囲や符号が保存されるとは限らない
- truncation が仕様なら `$std::truncate::<FROM_TYPE, TO_TYPE>` で意図を明示し、境界値、負値、MSB=1、all-ones を test

```veryl
type FROM_TYPE = logic<16>;
type TO_TYPE   = logic<8>;

let low: logic<8> = $std::truncate::<FROM_TYPE, TO_TYPE>(value16); // value16[7:0]を保持
```

## Verification

- cast を含む式は `veryl check` だけで終えず、生成 SystemVerilog の cast 順序を確認
- `$std::*` primitives は concatenation/repeat による拡張と `TO_TYPE'(...)` による cast に展開されることを生成 RTL で確認
- widening は source の MSB が1の値、narrowing は切り捨てられる上位 bit が1の値を test
- arithmetic の前後で cast する場合は、演算 width と signedness が変わる位置を確認

参照:

- https://doc.veryl-lang.org/book/05_language_reference/04_expression/10_type_cast.html
- https://doc.veryl-lang.org/book/07_appendix/01_formal_syntax.html
- https://veryl-lang.org/blog/announcing-veryl-0-20-0/

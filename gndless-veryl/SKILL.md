---
name: gndless-veryl
description: Use when editing Veryl RTL, including formatting, checking, building generated RTL, and choosing between veryl test and heavier simulation.
---

# Gndless Veryl

このスキルは、Veryl RTL 作業を扱う。

## 使う場面

- Veryl 生成物の更新
- `.veryl` の編集
- `veryl test` で済む軽い検証

## 基本方針

- 日常作業は `veryl` を直接使う
- 簡単な検証は `veryl test` で書く
- 複雑な検証や既存 SystemVerilog / C++ 資産を使う検証は別の simulation skill へ分ける
- 生成物だけ見て編集せず、元の `.veryl` を直す

## キャスト仕様

- `as 32` のように、`as` の後ろに幅を指定してキャストする
- `as logic<32>` や `as bit<32>` のように型名を書くのは誤り
- `as` で signed / unsigned の属性は変わらない
- 値を符号付きとして扱うときはシステム関数 `$signed()` を使う
- `$signed()` は「符号付きとして扱う」だけで、符号ビットを勝手に書き換えない

正誤例:

```veryl
let a: logic<32> = value as 32;          // correct
let b: logic<32> = value as logic<32>;   // wrong
let c: logic<32> = value as bit<32>;     // wrong
let d: i32       = $signed(value as 32); // signed として扱いたい場合
```

覚え方:

- `as` の右側には「型」ではなく「幅」を書く
- signed / unsigned を変えたいなら `as` ではなく `$signed()` を使う

## システム関数 / システムタスク

Veryl では SystemVerilog 標準のシステム関数 / システムタスクを使える。

- `$clog2(x)` は `x` の log2 の切り上げ
- `$size(x)` は配列サイズ
- `$bits(x)` は値のビット幅
- `$signed(x)` は値を符号付きとして扱う
- `$readmemh(path, mem)` は hex ファイルをメモリへ読み込む
- `$display(...)` は文字列出力
- `$error(...)` はエラー出力
- `$finish()` はシミュレーション終了

使用例:

```veryl
const w1: u32 = $clog2(32); // 5
const w2: u32 = $clog2(35); // 6

var array: logic<4, 8>;
const s1: u32 = $size(array); // 4
const s2: u32 = $bits(array); // 32

var uvalue: u32;
let svalue: i32 = $signed(uvalue) + 1;

initial {
    $readmemh("file.hex", array);
    $display("Hello World!");
    $error("Error!");
    $finish();
}
```

## ブーリアン型

- `bbool` は `bit<1>` のブーリアン型エイリアス
- `lbool` は `logic<1>` のブーリアン型エイリアス
- `true` と `false` も使える
- 型の本質的な差は、`bbool` が2値（`0/1`）、`lbool` が4値（`0/1/x/z`）であること
- `bbool` は、構成値に限らず、(1) 設計上0/1だけを保証でき、(2) 真偽値（`true`/`false`）として表現でき、(3) `bbool`にすることで意図の可読性が高まる信号・値に使う。`param`、`const`、入力、出力、内部レジスタ、関数戻り値、構造体フィールドを区別しない
- `lbool` は「意味は真偽値だが、未初期化・CDC・外部入力などによる`x/z`を保持して伝播させたい」場合に使う
- `logic` は、真偽値ではなく1bitの符号化・波形・プロトコル線として扱う値、または`x/z`を検証で観測したい値に使う。0/1しか現れない生のシリアルビットでも、`true`/`false`よりビット値として読む方が自然なら`logic`のままにする
- `enable`、`reset`、`copy_permitted`、`non_audio`、`original`、`invalid`、`locked`、`error`などは名前だけで決めず、設計上`x/z`が合法か、初期化後に必ず0/1になるかを確認して判断する
- `true` / `false` を使えることと、型を `bbool` / `lbool` にすることは別。信号名だけで型を変えない
- `logic` から `bbool` への変換は`x/z`を失うため、暗黙変換や一括置換を避け、2値化が仕様であることを確認する
- 公式stdの用例は参考にするが、SystemVerilog互換やstd内の採用箇所を型選択の上限にしない
- 参照: https://doc.veryl-lang.org/book/05_language_reference/03_data_type/01_builtin_type.html
- 参照: https://std.veryl-lang.org/async_fifo.html

## 通常使うコマンド

- `veryl fmt`
- `veryl fmt --check`
- `veryl check`
- `veryl build`
- `veryl test`

## `veryl publish`

- `veryl publish` の前に、まず `Veryl.toml` の version を更新する
- version 更新だけを一度コミットする
- その後に `veryl publish` を実行する
- publish 後は `Veryl.pub` に version と commit の対応が記録される
- `Veryl.pub` の更新を確認して、もう一度コミットする

推奨手順:

1. `Veryl.toml` の version を更新する
2. `git add Veryl.toml`
3. `git commit -m "update: Veryl package version を vX.Y.Z に上げる"`
4. `veryl publish`
5. `git add Veryl.pub`
6. `git commit -m "update: Veryl.pub を vX.Y.Z publish 結果で更新する"`

注意:

- version 更新前に `veryl publish` しない
- `Veryl.toml` と `Veryl.pub` を 1 コミットにまとめない
- publish 時点の commit が `Veryl.pub` に紐づくので、publish 前の状態を先に確定させる

## 変更後の確認

- `.veryl` を触ったら、まず対象ディレクトリで `veryl check`
- 小さいローカル検証なら `veryl test`
- 生成物更新が必要なら `veryl build`
- 合成やタイミングが絡む変更なら、下流フローでも確認する
- Rust や register map と契約がつながる変更なら、project 側 workflow も併用する

## アンチパターン

- `target/` 配下の生成物を手で直す
- Veryl 変更後に `veryl check` すら通さない
- ちょっとした性質確認なのに最初から重いテストベンチを増やす
- 契約信号を、相手側の更新なしに RTL だけ変える

## プロジェクト固有事項

- ディレクトリ構成、register map、reset 前提、Fmax 判定、統合 build コマンドはプロジェクト側の skill に置く

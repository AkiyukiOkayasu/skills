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
- 使えるときは積極的に `bbool` を使う
- `lbool` は `logic` の意味が必要な場合に使う

## 通常使うコマンド

- `veryl fmt`
- `veryl fmt --check`
- `veryl check`
- `veryl build`
- `veryl test`

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

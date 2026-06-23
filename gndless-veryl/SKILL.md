---
name: gndless-veryl
description: Use when editing Veryl RTL, including formatting, checking, building generated RTL, choosing between veryl test and heavier simulation, and deciding when a project task runner should remain outside the skill.
---

# Gndless Veryl

このスキルは、Veryl RTL 作業を扱う。

## 使う場面

- Veryl 生成物の更新
- `.veryl` の編集
- `veryl test` で済む軽い検証

## 基本方針

- 日常作業は `veryl` を直接使う
- task runner は複数工程を束ねるときだけ使う
- 簡単な検証は `veryl test` で書く
- 複雑な検証や既存 SystemVerilog / C++ 資産を使う検証は別の simulation skill へ分ける
- 生成物だけ見て編集せず、元の `.veryl` を直す

## キャスト仕様

- `as 32` のように、`as` の後ろに幅を指定してキャストする
- `as` で signed / unsigned の属性は変わらない
- 値を符号付きとして扱うときはシステム関数 `$signed()` を使う
- `$signed()` は「符号付きとして扱う」だけで、符号ビットを勝手に書き換えない

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

## task runner を使う場面

- Rust firmware 生成物も含めて統合確認したい
- Gowin 合成や Fmax 確認まで必要
- package 生成や書き込みも同時に行う
- 既存テストベンチを repo 標準の入口から実行したい

## 変更後の確認

- `.veryl` を触ったら、まず対象ディレクトリで `veryl check`
- 小さいローカル検証なら `veryl test`
- 生成物更新が必要なら `veryl build`
- project 標準の統合確認があるなら最後にそれも実行する
- Rust や register map と契約がつながる変更なら、project 側 workflow も併用する

## アンチパターン

- `target/` 配下の生成物を手で直す
- Veryl 変更後に `veryl check` すら通さない
- 単独で済む `veryl fmt` / `veryl check` まで task runner の新タスクにする
- ちょっとした性質確認なのに最初から重いテストベンチを増やす
- 契約信号を、相手側の更新なしに RTL だけ変える

## プロジェクト固有事項

- ディレクトリ構成、register map、reset 前提、Fmax 判定、統合 build コマンドはプロジェクト側の skill に置く

---
name: gndless-gowin
description: Use for Gowin EDA Tcl automation and device caveats, including import_files/gprj sync, syn_ramstyle, PnR options, and undocumented synthesis limits.
---

# Gndless Gowin

Gowin EDA の Tcl 自動化と、document に無い device / tool 挙動。

## Tcl script

- 先頭で `set script_path [file normalize [info script]]` と `set script_dir [file dirname $script_path]` を定義し、project path と file list は `file join` で `script_dir` から組み立てる
- `open_project` 後に `set_option` を明示する (gprj に残った設定に依存しない)
- `run all` は gprj を保存しない。`run close` まで実行する
- Gowin の絶対パス解決や `DYLD_LIBRARY_PATH` など環境依存は Tcl の外側 (wrapper script、just) で扱う

## import_files と gprj の同期

`import_files -fileList <f> -force` は file list のファイルを project の source directory へコピーし、gprj の file list を更新する。

- 新規ファイル: コピーされ gprj にも追加される
- 既存ファイル: コピーが上書きされる
- `.f` から消えたファイル: gprj からは削除されない。古いエントリが残り、次回も合成対象になる

削除に追従するには、`import_files` の前に生成 SV を `rm_file` で外す。vendor/IP の `.v` や `.cst` / `.sdc` を消さないよう拡張子を限定する。

```tcl
# 生成 SV だけを gprj から外し、最新の .f を import する
set generated_src_dir [file join $script_dir "myProject/src"]
foreach sv [glob -nocomplain -directory $generated_src_dir "*.sv"] {
    catch {rm_file [file join "src" [file tail $sv]]}
}
import_files -fileList $filelist_path -force
```

`rm_file` は gprj から外すだけでディスク上のファイルは残る。`..` を含む外部ファイルは `run close` 時に絶対パスで gprj へ保存されるため、相対パスを維持するなら `run close` 後に gprj の該当パスを文字列置換して戻す。

## Veryl の出力先

- `Veryl.toml` の `[build] target` を消さない。無いと `veryl build` は `.sv` を source directory (`src/`) に吐く
- `veryl build --out-dir <dir>` は `target` を上書きし、`.sv` と `.f` を `<dir>` 配下に出す。Gowin 用 staging には `--out-dir` を使い、`target` は直接 build したときの逃げ場として残す

## 合成制約

### syn_ramstyle

`syn_ramstyle` は RTL のコメント制約か GSC 制約ファイルで指定する。

- RTL: `object /* synthesis syn_ramstyle="value" */;`。Veryl では宣言直前のコメントが生成 SV にそのまま出る
- GSC: `INS "object" syn_ramstyle=value` / `GLOBAL syn_ramstyle=value`。優先度は GSC > RTL > IDE 設定
- 値: `block_ram` (default) / `distributed_ram` / `registers` / `rw_check` / `no_rw_check`
- GW5A は分散 RAM (SSRAM) 非対応。`distributed_ram` は WARN (IF0005) を出して registers へフォールバックする。FF 実装を狙うなら `registers` を指定する
- BSRAM 推論を避けたい小さなメモリ (例: PicoRV32 の cpuregs) は `registers` にする

### DSP乗算の推論

`MULTALU27X18` (1 DSP) と `MULT27X36` (2 DSP) の選択は、積のbit幅だけでは決まらない。GW5A-25A の実測では**符号拡張後のオペランド幅**で決まる。

- 27×18 DSPの入力は signed: A=27bit (magnitude 26 + sign)、B=18bit (magnitude 17 + sign)
- unsigned は正の signed として扱うため、A/B それぞれにゼロ拡張1bitが必要
- 27×18に収まる条件: unsigned A ≤26bit、unsigned B ≤17bit。signed なら A ≤27bit、B ≤18bit
- unsigned A=27bit または unsigned B=18bit は 27×36 になる
- signed 同士なら42〜45bit積でも 27×18 になる (実測: 25×18 signed、27×18 signed)
- `syn_dspstyle` は DSP / logic の選択だけ。27×18 / 27×36 を選ぶ属性は無い

例: `25×12 unsigned` は `26×13 signed` 相当で 27×18。`25×18 unsigned` は B が19bit必要になり 27×36。`25×18 signed` は 27×18。

実測表と実験方法は [references/dsp-multiplier-inference.md](references/dsp-multiplier-inference.md) を参照する。

### interface 配列の procedural for

Gowin Synthesis は `always_ff` / `always_comb` 内の `for` で interface (modport) 配列の変数インデックス選択ができない。

- エラー: `ERROR (EX3812) : 'i' is not a constant`
- 定数インデックス (`channels[0].raw`) は合成できる
- `veryl check` / `veryl test` では検出されず、Gowin 合成でのみ失敗する
- 回避: 入力 interface を generate assign で plain 配列へ展開し、procedural 内は plain 配列を扱う。出力も plain 配列から generate assign で接続する。testbench の `.raw` アクセスには不要

```veryl
var i_channels_raw: gndless_fixedpoint::Q1_23::Raw [8];
for i in 0..8 :g_ich {
    assign i_channels_raw[i] = i_channels[i].raw;
}

for i in 0..8 :g_out {
    assign o_channels[i].raw = o_channels_raw[i];
}
```

### 警告を RTL 側で減らす

GowinSyn に警告の抑制オプションは無い (SUG1220/SUG550 に該当なし)。

- ビット幅切り詰め (EX3791) は未サイズリテラルの演算で出る。`cnt = cnt + 1` を `cnt = cnt + 1'b1` にすると消える
- 1bit ポートへのタイオフは `0` ではなく `1'b0` にする (EX3670 の幅不一致が消える)
- Veryl は `16'd1` のようなサイズ付きリテラルを `1` に正規化するため、sized literal では EX3791 は消えない。`1'b1` は正規化されずに残る

## PnR オプション

タイミングマージンが足りないとき、合成オプションで改善しないなら配置・ルーティングアルゴリズムを試す。

- まず `-place_option 1` + `-route_option 2` を試す。3世代の実測で安定して上位
- `-place_option 1` + `-route_option 1` も安定候補。優劣は構成と測定環境で入れ替わる
- Fmax 最良の設定は構成依存で、世代ごとに `2/2`、`4/2`、`3/2` が最良だった。旧測定の `3` + `1` が常に最良ではない
- `-place_option 0` 系は速いが Fmax が大きく落ちる
- リリースごとに同一チェックアウト・同一環境で再スイープする

設定は `impl/pnr/cmd.do` に保存され、`set_option` の変更が反映されないことがある。option を変えたら `impl/pnr/cmd.do` を削除して再実行する。定義、実測値、測定の作法は [references/pnr-placement-options.md](references/pnr-placement-options.md)。

## no-op option

- `-retiming` / `-pipe` は headless `gw_sh` フローでは no-op (V1.9.12 で検証)。`saveto -all_options`、gprj、合成 `.prj`、SUG1220 のどこにも現れず、`set_option` しても合成ネットリストが変わらない。Tcl から削除してよい
- `-route_maxfan` は PnR の `cmd.do` に現れる実オプションなので残す
- 設定漏れの確認には `saveto -all_options project_config.tcl` を使う

## project の作成・合成

- 新規: [create_project_example.tcl](create_project_example.tcl) の `device` / `top` / `file list` / `pin option` を実プロジェクトに合わせる
- 既存: [run_gowin_example.tcl](run_gowin_example.tcl) の `project_path` / `filelist_path` / `top module` / `pin option` を合わせる
- GUI で gprj を作った場合も、`saveto -all_options` で設定を書き出して script のベースにする
- `create_project -name <prjName> -dir <path> -pn <pnName> [-device_version <arg>] [-force]`

新規 project では次を確認する。

- device、top module 名、`import_files` の file list
- `.f` から削除したファイルが gprj に残っていないか
- 外部ファイルが絶対パスで gprj に保存されていないか
- JTAG / READY / CPU / MSPI など Multi-purpose pin が実機の書き込み・起動経路と合っているか
- MultiBoot の address 幅と flash address (`-multi_boot` / `-mspi_jump`)
- `-bit_format` / `-bit_security` / `-bit_incl_bsram_init` / `-loading_rate`
- BSRAM / boot 周辺の reset delay、Background programming (`-bg_programming`)
- `saveto -all_options` で設定漏れが無いか

document に見当たらないからといって、実機で必要だった reset / boot 対策を消さない。

## 合成ログの警告チェック

Gowin の合成/PnR ログは無害な WARNING が多い。無害と確認済みの警告を「コード@ファイル + 理由」で列挙し、それ以外だけを要レビューとして扱う。

- 参照実装: FPGA_Oscillator の `Firmware/tools/synth-log-check` + 各プロジェクトの `ignored_warnings.txt` (`just synth-check` / `synth-warnings`)
- ERROR と、無害リストに無い警告で失敗する。無害リストの警告は件数表示のみ
- ファイル単位で判定する (行番号は設計変更でずれる)
- `just synth` / updater 合成の最後に自動実行し、新しい警告は内容を確認して無害なら理由付きで追加する

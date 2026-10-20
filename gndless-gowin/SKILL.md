---
name: gndless-gowin
description: Use when working on Gowin-specific project automation and device caveats, including Tcl scripts, gw_sh flows, generated RTL import, project bring-up, and board-specific behaviors not obvious from Gowin documentation.
---

# Gndless Gowin

Gowin EDA の Tcl スクリプト、project automation、device 依存の注意点。

## 基本方針

- Tcl は IDE のカレントディレクトリに依存させず、script 相対で書く
- 生成元は Veryl、合成入口は Gowin project、という責務分離を保つ
- 人手 GUI 操作だけに閉じた手順を残さない
- Gowin document に無い不安定要因や undocumented behavior は、再発防止のため skill に残す

## Tcl script の要点

- `set script_path [file normalize [info script]]` と `set script_dir [file dirname $script_path]` を先頭で定義する
- project path と file list は `file join` で `script_dir` から組み立てる
- `open_project` 後に `set_option` を明示する (gprj に残った設定に依存しない)
- `import_files -fileList ... -force` で最新の生成物を再投入する。新規ファイルは gprj に追加されるが、`.f` から消えたファイルは gprj に残る
- `run all` と `run close` まで含めて自動化する。`run close` で gprj に変更が保存される (`run all` だけでは保存されない)

## import_files と gprj の同期

`import_files -fileList <f> -force` は、file list に載っているファイルを project の source directory にコピーし、gprj の file list を更新する。挙動は次の通り。

- 新規ファイル: project の `src/` などへコピーされ、gprj にも追加される
- 既存ファイル: コピーが上書きされる
- `.f` から消えたファイル: **gprj からは削除されない**。古いエントリが残り、次回も合成対象になる

削除追従が必要な場合は、`import_files` の前に生成 SV を `rm_file` で外す。vendor/IP の `.v` や制約ファイル (`.cst` / `.sdc`) まで消さないよう、拡張子を限定する。

```tcl
# 生成 SV だけを gprj から外し、最新の .f を import する
set generated_src_dir [file join $script_dir "myProject/src"]
foreach sv [glob -nocomplain -directory $generated_src_dir "*.sv"] {
    catch {rm_file [file join "src" [file tail $sv]]}
}
import_files -fileList $filelist_path -force
```

- `rm_file` は gprj から外すだけで、ディスク上のファイルは残る。`import_files` が再度コピーする
- `..` を含む外部ファイルは、`run close` 時に gprj へ絶対パスで保存される。リポジトリ管理する gprj で相対パスを維持したい場合は、`run close` 後に gprj の該当パスを文字列置換して戻す

### Veryl の出力先

- `Veryl.toml` の `[build] target` は「未使用だから」と消さない。`target` が無いと `veryl build` は `.sv` を source directory (`src/`) に吐く
- `veryl build --out-dir <dir>` は `target` を上書きし、`.sv` と `.f` の両方を `<dir>` 配下に出す。Gowin 用の staging directory へ出す場合は `--out-dir` を使い、`target` は直接 `veryl build` したときの逃げ場として残す

## gw_sh の実行

- `./gw_sh run_gowin_example.tcl` のように Tcl script を渡して実行する
- Gowin IDE の絶対パス解決、`DYLD_LIBRARY_PATH` など実行環境の注入、project ごとの複合 build フローは Tcl の外側 (wrapper script、just など) で扱う
- Tcl 側は「project をどう開いて何を設定するか」に集中させ、`cd` 前提の相対パスや環境依存を持ち込まない

## RAM style 制約 (syn_ramstyle)

`syn_ramstyle` は環境変数やグローバル設定ではなく、RTL に埋め込むコメント制約か GSC 制約ファイルで指定する。

- RTL: `object /* synthesis syn_ramstyle="value" */;`。Veryl では宣言直前のコメントが生成 SV にそのまま出るため、`.veryl` にそのまま書ける
- GSC: `INS "object" syn_ramstyle=value` / `GLOBAL syn_ramstyle=value`。優先度は GSC > RTL > IDE 設定
- 値: `block_ram` (default) / `distributed_ram` / `registers` / `rw_check` / `no_rw_check`
- GW5A は分散 RAM (SSRAM) 非対応。`distributed_ram` は `WARN (IF0005) : Not support distributed RAM in current device` を出して registers へフォールバックする。FF 実装を狙うなら `registers` を指定する
- BSRAM 推論を避けたい小さなメモリ (例: PicoRV32 の cpuregs) は `registers` 指定で FF 実装にする

## 合成警告を発生源で減らす

GowinSyn に警告の抑制オプションは無い (SUG1220/SUG550 に該当なし)。警告は RTL 側で減らす。

- ビット幅切り詰め (EX3791) は未サイズリテラルの演算で出る。`cnt = cnt + 1` は `cnt = cnt + 1'b1` にすると警告が消える (どちらも同じ最大幅演算で、幅非依存)
- 1bit ポートへのタイオフは `0` ではなく `1'b0` にする (EX3670 の幅不一致が消える)
- Veryl は `16'd1` のようなサイズ付きリテラルを `1` に正規化するため、sized literal では EX3791 は消えない。`1'b1` は正規化されずに残る

## Gowin 合成の既知制約: interface 配列の procedural for

Gowin Synthesis は、`always_ff` / `always_comb` 内の `for` ループで interface (modport) 配列要素を変数インデックス選択できない (Veryl の interface が生成する SV の配列要素アクセスが定数展開されない)。

- エラー例: `ERROR (EX3812) : 'i' is not a constant`
- 定数インデックス (`channels[0].raw` など) は合成できる。問題になるのは変数 `i` を使うループだけ
- この制約は `veryl check` / `veryl test` では検出されず、Gowin 合成でのみ失敗する

回避パターン (Veryl): 入力 interface は generate assign で raw の plain 配列へ展開し、procedural 内は plain 配列を扱う。出力も plain 配列から generate assign で接続する。testbench (合成対象外) の `.raw` アクセスには適用不要。

```veryl
var i_channels_raw: gndless_fixedpoint::Q1_23::Raw [8];
for i in 0..8 :g_ich {
    assign i_channels_raw[i] = i_channels[i].raw;
}

for i in 0..8 :g_out {
    assign o_channels[i].raw = o_channels_raw[i];
}
```

## PnR 配置・ルーティングオプション

タイミングマージンが足りないとき、合成オプションで改善しない場合は、PnR の配置・ルーティングアルゴリズム選択を試す。

- `-place_option 2`: timing 優先の配置。単独で改善することが多い
- `-place_option 3` / `4`: 複数試行から最良を選択 (詳細は未公開)
- `-route_option 1`: timing に従うルーティング
- 実測では `-place_option 3` + `-route_option 1` が最良 (FPGA_Oscillator で Fmax 50.4 → 62.6 MHz)
- PnR 設定は `impl/pnr/cmd.do` に保存され、option 変更が反映されないことがある。`set_option` を変えたら `impl/pnr/cmd.do` を削除して再実行する

Option 定義、実測、測定の作法は [references/pnr-placement-options.md](references/pnr-placement-options.md)。

## 設定の確認と no-op option

現在の全設定を dump して、合成 script の `set_option` 漏れを洗い出すには `saveto -all_options` を使う。

```tcl
open_project myProject/myProject.gprj
saveto -all_options project_config.tcl
run close
```

- `-retiming` / `-pipe` は headless `gw_sh` フローでは no-op (V1.9.12 で検証)。`saveto -all_options`、gprj、合成 `.prj`、公式 Tcl ガイド (SUG1220) のどこにも現れず、`set_option` で設定しても合成ネットリストが変化しないため tcl から削除してよい
- `-route_maxfan` は PnR の `cmd.do` に現れる実オプションなので残す

## project の作成と合成

- 新規 project: [create_project_example.tcl](create_project_example.tcl) をテンプレートに `device` / `top` / `file list` / `pin option` を実プロジェクトへ合わせる
- 既存 project の合成: [run_gowin_example.tcl](run_gowin_example.tcl) をベースに `project_path` / `filelist_path` / `top module` / `pin option` を合わせる
- GUI で gprj を作った場合も、`saveto -all_options` で設定を書き出して script のベースにする
- `create_project` の構文: `create_project -name <prjName> -dir <path> -pn <pnName> [-device_version <arg>] [-force]`

## project 新設時の確認項目

- device が正しいか
- top module 名が一致しているか
- `import_files` の file list が最新の生成物を向いているか
- `.f` から削除したファイルが gprj に残っていないか
- 外部ファイルが絶対パスで gprj に保存されていないか
- `saveto -all_options` で設定漏れを確認したか

### JTAG / 特殊 pin

- JTAG / READY / CPU / MSPI など Multi-purpose pin option が用途に合っているか
- ベースは `create_project_example.tcl` の multi-purpose pins 節。実機の書き込み・起動経路と突き合わせる

### MultiBoot

- MultiBoot を使うなら address 幅と flash address が正しいか (`-multi_boot` / `-mspi_jump`)

### Bitstream

- `-bit_format` / `-bit_security` / `-bit_incl_bsram_init` / `-loading_rate` を用途に合わせる

### BSRAM / boot / reset

- BSRAM や boot 周辺の安定化に reset delay が必要か
- Background programming (`-bg_programming`) が必要か
- reset 方針を変えるなら、実機起動確認なしに削らない
- document に見当たらないからといって、実機で必要だった reset / boot 対策を消さない

## 合成ログの警告チェック

Gowin の合成/PnR ログは大半が無害な WARNING (カウンタの桁上がり切り捨て、最適化で消えたモジュール等) で、全件を追いかけるとノイズになる。無害と確認済みの警告を「コード@ファイル + 理由」で列挙し、それ以外だけを要レビューとして扱う。

- 参照実装: FPGA_Oscillator の `Firmware/tools/synth-log-check` (Rust) + 各プロジェクトの `ignored_warnings.txt` (`just synth-check` / `synth-warnings`)
- ERROR と、無害リストに無い警告で失敗する。無害リストの警告は件数表示のみ
- ファイル単位で判定する (行番号は設計変更で常にずれるため追わない)
- `just synth` / updater 合成の最後に自動実行する。新しく現れた警告は内容を確認し、無害なら理由付きで無害リストに追加する

## アンチパターン

- `cd` 前提の相対パスで script を書く
- GUI で設定しただけで Tcl に落とさない
- `impl/` 配下の成果物を入力ソースとして扱う
- `run all` で必要になる file list 更新を忘れる
- `import_files` だけで `.f` から消えたファイルの削除まで追従できると考える
- 外部ファイルの絶対パスを gprj にコミットする
- `Veryl.toml` の `target` を未使用と判断して消す
- device 固有 option を説明なしにコピペする
- document に見当たらない挙動だからといって、実機で必要だった reset / boot 対策を消す
- 合成ログの警告を目視確認だけに頼る (baseline チェックを build に組み込む)

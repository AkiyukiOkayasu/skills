# Gowin PnR 配置・ルーティングオプション

Gowin EDA の Place & Route には配置アルゴリズムとルーティングアルゴリズムの選択肢があり、
タイミングマージンに大きな影響を与える。Gowin の GUI 上の「Place Option」/「Route Option」に対応する。

## オプション定義 (IDE の設定定義から確認できる内容)

定義元: `GowinEDA/IDE/data/config/rtlplaceoptions.xml` / `rtlrouteoptions.xml`

### Place Option (`-place_option N`)

| 値 | 説明 (Gowin 定義) |
|---|---|
| 0 | default place algorithm、compilation speed 優先 |
| 1 | place algorithm 1、routability 優先 |
| 2 | place algorithm 2、**timing 優先** |
| 3 | place algorithm 3、select a number |
| 4 | place algorithm 4、select a number |

- 3 / 4 の「select a number」の具体的な意味はドキュメントに明記されていない
  (配置試行回数を選択する趣旨と推測されるが、詳細は未公開)
- GUI 上のデフォルトは 0

### Route Option (`-route_option N`)

| 値 | 説明 (Gowin 定義) |
|---|---|
| 0 | default route algorithm (混雑度に応じたデフォルト) |
| 1 | route algorithm 1、**timing に従う** |
| 2 | route algorithm 2、速度優先 (速い) |

## 実測の結論 (FPGA_Oscillator / GW5A-25 での事例)

旧測定では `-place_option 3` + `-route_option 1` が Fmax 50.4 → 62.6 MHz で最良だった。
しかし RTL が変わると優劣も入れ替わる。2026-10 に v0.6.1 / v0.7.0 / HEAD の3世代で
再スイープした結果は次の通り。

- バランス: `place 1` + `route 2`。3世代すべてで2番目に速く、Fmax は最良値より 5〜11% 低い
- 速度優先: `place 1` + `route 1`。3世代すべてで最速。Fmax は 1/2 より 4〜7% 低い
- Fmax 最大化は構成依存。8設定の比較では A=2/2 (66.1 MHz)、B=4/2 (76.0 MHz)、C=3/2 (76.7 MHz) が最良
- `place 2` + `route 2` が常に最良とは限らない。`place 4` は構成による振れが大きい
- 同じ構成Cでも環境で最良が入れ替わる (main は 2/2 78.3 MHz、worktree は 3/2 76.7 MHz)
- `place 2` + `route 1` はバージョンで結果が反転するため既定にしない
- `place 0` 系は最速だが Fmax が大きく落ちる (現行設計で 52 MHz)
- 合成時間は設定によらず約14〜17秒。差は PnR 側で出る
- 設定の優劣は RTL の変更で入れ替わるため、リリースごとに再スイープする

### 絶対 Fmax はチェックアウト環境でも変わる

同じ RTL・同じ設定でも、メインチェックアウトと `git worktree` で Fmax が変わった。

- HEAD / place3 / route1: メイン 68.984 MHz、worktree 72.778 MHz
- HEAD / place2 / route1: メイン 72.119 MHz、worktree 70.074 MHz
- HEAD / place2 / route2: メイン 78.291 MHz、worktree 75.317 MHz
- HEAD / place3 / route2: メイン 76.652 MHz、worktree 76.747 MHz
- HEAD / place1 / route2: メイン 72.394 MHz、worktree 72.666 MHz

プロジェクトの絶対パスや `impl` の状態が配置結果に影響すると考えられる。
設定同士の比較は同一チェックアウト・同一環境で行う。CI とローカルの Fmax を
そのまま比較しない。

## 重要な注意: cmd.do の設定永続化

Gowin は PnR 実行設定を `impl/pnr/cmd.do` に保存し、次回の PnR は**保存された設定を
そのまま使う**。合成 script の `set_option` を変更しただけでは反映されないことがある。

**オプションを変更したら `impl/pnr/cmd.do` を削除してから再実行する。**

```sh
rm impl/pnr/cmd.do   # PnR 前に必ず
```

- gprj にも設定が保存されるため、`set_option` を tcl から削除しただけでは元に戻らない
- 明示的に `set_option -place_option 0` のように指定すると確実に反映される
- 実行後の `cmd.do` の内容 (`-place_option N` / `-route_option N`) を確認してから
  タイミングレポートを読むと、どの設定で回ったのか誤認しない

## `-retiming` / `-pipe` は headless gw_sh フローでは no-op (V1.9.12)

- **GUI 設定には存在する**: `synthesisoptions.xml` の SYN13 Retiming / SYN12 Pipelining
  (GUI の「Retiming」/「Pipelining」。retiming のデフォルトは 1、pipe は 0)
- **ただし headless では影響しない**: `set_option` で 0/1 を変えても合成ネットリストは変化しない
  (タイムスタンプヘッダを除いた .vg の hash 比較で確認。retiming1/pipe1・retiming0/pipe1・
  retiming1/pipe0 の3組み合わせすべて同一)
- **記録もされない**: `saveto -all_options` にも gprj にも合成 `gwsynthesis/*.prj` にも現れない。
  公式 Tcl ガイド (SUG1220) にも記載がない
- **tcl から削除してよい**。`-route_maxfan` は PnR の `cmd.do` に現れる実オプションなので残す
- **測定の教訓**: .vg の hash 比較でオプション効果を検証する場合、先頭のタイムスタンプ
  コメント (4行) を除いてから比較すること (含めると全 run で hash が変わり誤検出する)

## 測定の作法

- 比較時は毎回 `cmd.do` を削除し、オプションを明示指定する
- 公平なフルビルド比較では `impl` ごと削除して合成からやり直す
- 同じ環境・同じ設計・同じオプションなら結果は決定的 (配置は同一解)。再実行しても同じ Fmax になる
- 環境 (パス、impl の状態、Gowin のバージョン) が変わると絶対 Fmax は変わりうる。比較は同一環境で行う
- macOS で連続実行するときは `caffeinate` でスリープを防ぎ、経過時間は単調時計で測る。
  壁時計だとスリープ中に数千秒の値が出ることがある
- Fmax は `fpgaOscillator_tr_content.html` の `Max Frequency Summary` の `Actual Fmax`、
  または `fpgaOscillator.timing_paths` の setup slack から確認できる
- setup / hold の TNS が 0 かも確認する。Fmax だけ見て hold 違反を見落とさない
- クリティカルパスが外部 IP (ソフトコア CPU など) 内部にある場合、合成オプション
  (`-retiming` / `-pipe` / `-route_maxfan`) では改善しないが、配置オプションの変更で
  ルーティング品質が変わり改善することがある (配置全体が変わるため)

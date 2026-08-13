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

- `-place_option 3` + `-route_option 1` の組み合わせが最も良い結果になることが多い
- `-place_option 2` (timing 優先) も単独で改善効果がある
- 合成・PnR の実行時間は配置オプションにより +10 秒程度増える (PnR 全体が 8s → 19s 程度)。
  フルビルド全体では誤差範囲
- 効果は設計依存。必ず対象設計でスイープして確認する

## 重要な注意: cmd.do の設定永続化

Gowin は PnR 実行設定を `impl/pnr/cmd.do` に保存し、次回の PnR は**保存された設定を
そのまま使う**。`run_gowin.tcl` の `set_option` を変更しただけでは反映されないことがある。

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

## 測定の作法

- 比較時は毎回 `cmd.do` を削除し、オプションを明示指定する
- 同じ設計・同じオプションなら結果は決定的 (配置は同一解)。再実行しても同じ Fmax になる
- Fmax は `fpgaOscillator.timing_paths` の setup slack から確認できる
- クリティカルパスが外部 IP (ソフトコア CPU など) 内部にある場合、合成オプション
  (`-retiming` / `-pipe` / `-route_maxfan`) では改善しないが、配置オプションの変更で
  ルーティング品質が変わり改善することがある (配置全体が変わるため)

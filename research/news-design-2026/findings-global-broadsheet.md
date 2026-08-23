# 欧米の総合・経済ニュース大手：情報設計の調査メモ

調査日: 2026-08-23（日本時間）
対象: BBC News、Reuters、The New York Times、Financial Times、The Guardian、Bloomberg
目的: AI/Appleニュースを大量表示するOHARU WATCHの次期情報設計へ移植できる原則を抽出する。

## 要約

1. 大手サイトは「トップ記事を1枚の巨大カードにする」より、サイト共通のヘッダー、ニュースの種類（速報・解説・意見・動画）、セクション見出し、記事リストを段階的に分け、読者が今どの層を見ているかを明示している。FT、Guardian、Bloombergのトップは、リード記事の後にテーマ別のセクションを連続させる構成だった。
2. BBCの公式GELは、カード最小幅266px、CSS Gridの自動折返し、body 15–18px、本文幅60–70字、相対単位、ソース順と表示順を一致させる方針を具体化している。大量記事を扱うOHARU WATCHには、この「固定の見た目」ではなく「意味順を壊さない可変グリッド」が最も移植しやすい。
3. OHARU WATCHでは、現在の丸角・影・ピル型ラベルを全廃する必要はないが、リード記事、AI国内／国外、Apple公式／リーク、更新時刻、媒体名を「罫線と文字階層」で先に読ませ、色や画像は補助へ下げるのが妥当。カードを小さく詰め込み過ぎず、媒体名と時刻を各見出しの直下に固定する。
4. 速報性のある大手は時刻、最新リスト、Most read/Most popular、Live、マーケット値などを別レイヤーにしている。OHARU WATCHでは「最新（時間順）」と「編集上の注目（重要度順）」を混ぜず、上部に時刻順、脇または下部に注目記事を置く方が、AI/Appleの大量表示に向く。

## 確度と確認方法

- **高**: 2026-08-23に公式ページ本文・ナビゲーション抽出を直接開いて確認したもの。または公式デザインシステムに明記された仕様。
- **中**: 公式ページの構造は直接確認したが、書体名・色・ピクセル寸法などはHTML本文に出ず、画面上の目視印象または公式説明からの推定を含むもの。
- **低／未確認**: robots制限等により消費者向けニューストップを直接開けず、公式の別ページで確認できる範囲だけを記録したもの。ニューストップの見た目については断定しない。

## 媒体別発見

### 1. BBC News / BBC GEL

確認URL（公式）:

- [BBC.comに掲載されるコンテンツの説明](https://help.bbc.com/hc/en-us/articles/39027623773331-What-types-of-news-content-will-be-available)（高。ニューストップそのものはrobots制限で本文取得できなかったため、BBCの公式ヘルプを確認）
- [BBC GEL Grid Demo](https://bbc.github.io/gel-grid/)（高）
- [BBC GEL Typography](https://bbc.github.io/gel/foundations/typography/)（高）
- [BBC GEL Grids](https://bbc.github.io/gel/foundations/grids/)（高）
- [BBC GEL Cards](https://bbc.github.io/gel/components/cards/)（高）

発見:

- BBC.comホームは「その時点の最大ニュース」と「編集部が選ぶ時宜にかなった記事・動画」を混在させる。トップナビにはCulture、Innovation（technology/health/science）、Earth、Sport、Business、Travelがあり、VideoとLiveも別フォーマットとして用意される。LiveはNewsとSportの進行中報道をタイムラインで追う場所、と公式説明にある。
- GELのグリッドは100%、50%、33.333%、25%、20%、12.5%を組み合わせる割合ベース。デモでは小さい画面から400px、600px、900px以上へ段階的に組み合わせを増やす例がある。
- カードは最小266px、`repeat(auto-fill, minmax(266px, 1fr))`で自動折返し、セル間隔は1rem（GELの一般グリッド指針では最低8px）という設計。カードを固定列数にせず、画面幅に応じて1列・2列・3列へ落とせる。
- タイポグラフィはReithを軸に、本文15–18pxを相対単位で設定し、本文幅は60–70文字程度、両端揃えを避け、行高は最低1.5を目安にする。小さ過ぎる文字を常用しない、ピンチズームを抑止しない、というアクセシビリティ方針も明記されている。
- Flexboxの`order`で見た目だけ順序を入れ替えると、スクリーンリーダーが読む順序と画面順がずれる。ソース順と重要度順をHTMLでも一致させるべき、とGELは警告する。カードでも見出しをソース順の先頭に置くことを求めている。

移植メモ: OHARU WATCHの大量記事リストは、固定の3列・4列ではなく、幅266px前後を下限にした自動グリッド（ただし本文付き記事は1列リストも併用）にする。モバイルで「重要度の高い記事をCSSだけで先頭へ移動」しない。HTML生成時点でリード→最新→カテゴリ順に並べる。

### 2. Reuters

確認URL（公式）:

- [Reuters Agency](https://reutersagency.com/)（中。消費者向けreuters.comではなく、同社の公式サービス説明）
- [Reuters Graphics](https://graphics.thomsonreuters.com/)（中。Reuters公式のグラフィック作品一覧）
- 消費者向け [Reutersトップ](https://www.reuters.com/)、[World](https://www.reuters.com/world/)、[Technology](https://www.reuters.com/technology/) は2026-08-23の取得環境でrobots／内部エラーとなり、ニューストップの画面構成は直接確認できなかった（未確認）。

確認できた範囲:

- Reuters Agencyは、リアルタイムのText wires（速報テキスト）、Pictures、Video、Graphicsを別のコンテンツ単位として説明している。Reuters Graphicsの公式一覧も、チャート・地図・インタラクティブ作品を独立した閲覧入口として扱う。
- したがって移植可能な原則は「速報の時間軸」と「深掘りのビジュアル／解説」を同じカード種別にしないこと。OHARU WATCHでは、通常記事（更新時刻順）と、特集・比較・解説（別セクション）を分けるのがよい。

注意: Reuters消費者向けサイトのヘッダー、罫線、書体、スマホ時の再配置については直接確認できていない。この節から色・グリッド寸法を推定しない。

### 3. The New York Times

確認URL:

- [NYTimesトップ](https://www.nytimes.com/)、[World section](https://www.nytimes.com/section/world) は2026-08-23の取得環境でrobots／内部エラーとなり、本文・画面を直接確認できなかった（未確認）。
- 検索結果には第三者によるNYTデザイン再現資料も出たが、一次資料ではないため採用しなかった。

結論: NYT固有の見出し書体、色、カード幅、トップのグリッド、スマホ再配置については、この調査メモでは断定しない。別環境で実ページを確認できる場合に追補する。

### 4. Financial Times

確認URL（公式）:

- [Financial Times Home](https://www.ft.com/)（高。2026-08-23に直接確認）

発見:

- ヘッダーにMarkets Dataへの入口、Sign In、Subscribe、サイドナビ開閉、検索を置く。大きなロゴと検索を同じヘッダー層に置き、課金導線をニュース本文の中へ埋め込まずヘッダーで処理している。
- トップ階層は、トピックラベル（例: Trump tariffs）、大見出し、補足文のリードから始まり、Editor’s picks、TOP STORIESへ続く。TOP STORIESはUS economy、Middle East war、War in Ukraine、German politicsなど、トピック名をラベルとして見出しの前に置く。
- 下層はMonetary Policy Radar、Spotlight、Best of FTWeekend、Most read、News、Opinion、Companies、Podcasts、Life & Arts、Video、Markets News、Technologyというセクションの連続。Opinionではコラム名や筆者名を見出しと分離し、Most readは順位付きリストにしている。
- 最下層のナビではWorld、Companies、Tech、Marketsなどの大分類と、AI、Semiconductors、Cyber Security、Equities、Bonds、Currencies等のサブ分類を折りたたみメニューで整理している。カテゴリが多くても、最初から全リンクを横一列に詰め込まない。
- 画面上は新聞的な文字階層と区切り線を中心とする編集面という印象だが、取得本文にはフォント名・色トークン・正確な余白値がないため、固有書体・色の断定は中確度に留める。

移植メモ: OHARU WATCHでは、カテゴリ名を見出しの前に置く「トピックラベル→見出し→要約→媒体・時刻」の順を採用する。`AI最新情報（国内）`等の4分類を、横並びピルだけでなく、罫線付きのセクション見出しとして再提示する。おすすめ記事と最新記事を同じリストへ混ぜない。

### 5. The Guardian

確認URL（公式）:

- [The Guardian International homepage](https://www.theguardian.com/international)（高。2026-08-23に直接確認）
- [International homepageのアクセシブル表示](https://www.theguardian.com/international?accessible=true)（中。本文構造の照合に使用）

発見:

- 最上部に版（International、UK、US、Australia、Europe）を切り替える入口があり、その下にNews、Opinion、Sport、Culture、Lifestyleの大分類。さらにWorld、US politics、UK、Climate crisis、Middle East、Ukraine、Environment、Science、Football、Tech、Business等が並ぶ。大分類とテーマ分類を二層に分けている。
- NewsはMiddle Eastのリード（画像・地域ラベル・見出し・説明）を先頭に、Ukraine war at a glance、Sweden、Television、Japan、Trade、Ebolaなど複数の小さな記事を続ける。1枚のリードを過度に大型化せず、同じグリッドの中で画像付き記事とテキスト中心の記事を混在させる。
- In focus、Features、UK news、World news、Culture、What to watch／listen／read／play、You may have missed、Newsletters、In pictures、Most popularという編集パッケージを順番に並べる。Most popularにはMost viewedとDeeply readを分け、「クリックされた記事」と「読む時間を使われた記事」を別指標で扱っている。
- 多くのカードで画像、テーマラベル、見出し、補足文、相対時刻（例: 1h ago、8h ago）の順が再現される。ニュースの鮮度を相対時刻で短く示しつつ、テーマラベルで一覧をスキャンできる。
- 書体名、色トークン、余白の厳密値は公式トップ本文からは確認できない。目視上の編集的な見出しと細い区切り線は参考になるが、固有フォントの採用は中確度の推定とする。

移植メモ: 「Most viewed」と「Deeply read」のように、OHARU WATCHでも「新着」と「注目（重要度）」を分ける。おすすめ枠は通常記事から除外する現行仕様を維持し、注目の理由を「重要度」だけでなく「更新時刻」「媒体」「カテゴリ」で追えるようにする。スマホでは画像→ラベル→見出し→要約→時刻の同じ順序を維持する。

### 6. Bloomberg

確認URL（公式）:

- [Bloomberg Home](https://www.bloomberg.com/)（中。検索結果の公式ページ本文を確認）
- [Bloomberg Latest](https://www.bloomberg.com/latest)（高。2026-08-23に直接確認）
- [Bloomberg Markets](https://www.bloomberg.com/markets)（高。2026-08-23に直接確認）
- [Bloomberg Technology](https://www.bloomberg.com/technology)（高。2026-08-23に直接確認）

発見:

- ヘッダーはLive TV、Markets、Economics、Industries、Tech、Politics、Businessweek、Opinion、Video、Moreというメディア入口を置き、その下にEdition、Menu、Subscribeを分ける。さらにMarketsページではTop Securities（S&P 500、Nasdaq、国債、原油、金、為替など）の横スクロール的な値表示をニュース本文より上に置く。
- Latestは「最も新しいnews、analysis、features、opinions」を一つの入口にしつつ、All Latest News、Most Popular、Most Active Stocksの3つの切替を用意する。新着と人気と市場活動をタブで切り分ける。
- MarketsページはDeals、Fixed Income、ETFs、FX Center、Alternative Investing、Markets Daily Newsletterのサブナビを持ち、記事の前後にStock Movers、Most Active、Crypto、Videos、Magazine、Odd Lots、Explainers、More Markets newsを配置する。TechnologyページもAI、Big Tech、Cybersecurity、Consumer Tech、Startups、Screentime、Tech In Depthを先に明示し、その下に画像付きリード、解説、AI等のサブセクション、時刻付きMore Technology newsを置く。
- ホーム検索結果では、Markets、Economics、Technology、Politics、Green、Crypto、AI、Work & Life、Market Data、Exploreが分類される。ニュースとデータを同じ見た目のカードにせず、データは専用のレイヤーとして扱う構造が明確。
- 見出し書体の固有名、カラーコード、グリッド寸法は本文抽出では確認できない。画面は白地・濃色文字・相場の上下を矢印や色で示す密度の高い金融ニュース面という印象だが、色については中確度の目視推定である。

移植メモ: OHARU WATCHに相場データは不要だが、Bloombergの「最新／人気／活動中」を参考に、記事一覧へ「新着」「注目」「Apple公式」などの表示切替を追加する余地がある。AIとAppleのサブカテゴリを、曖昧なタグ集ではなくカテゴリ下の専用セクションとして見せる。

## 横断原則（6媒体を比較して残す設計判断）

### 1. ヘッダーは「ブランド」「検索」「カテゴリ」「状態」を分離する

FTはロゴ、検索、Sign In、Subscribeをヘッダーで分離し、Bloombergはメディア入口、Edition、Menu、Subscribeを段階化し、Guardianは版切替と大分類を分ける。OHARU WATCHでは次の4層を一つの横並びに詰めない。

1. ブランド: OHARU WATCH
2. 状態: 最終更新日時、掲載件数
3. 導線: AI国内、AI国外、Apple公式、Appleリーク
4. 補助: 検索（将来）、カテゴリの開閉（スマホ）

根拠: [FTトップ](https://www.ft.com/)、[Guardianトップ](https://www.theguardian.com/international)、[Bloomberg Markets](https://www.bloomberg.com/markets)。確度: 高（構造）、中（色・寸法）。

### 2. 「リード→セクション→リスト」の3段階で大量表示する

リード記事は1件、または画像付き2–3件に限定し、その後にカテゴリごとの記事リストを置く。FTのTOP STORIES／News／Companies／Technology、GuardianのNews／In focus／World news／Most popular、BloombergのMarkets／Stock Movers／More newsが同型である。全記事を同じ大きさのカードにすると、重要度が読者に伝わらない。

根拠: [FTトップ](https://www.ft.com/)、[Guardianトップ](https://www.theguardian.com/international)、[Bloomberg Technology](https://www.bloomberg.com/technology)。確度: 高。

### 3. 最新性と注目度を別の軸で示す

GuardianはMost viewedとDeeply readを分け、Bloomberg LatestはAll Latest News／Most Popular／Most Active Stocksを分け、BBCはLiveを独立フォーマットにする。OHARU WATCHでは、時刻順の「新着」と重要度順の「注目」を同じソート結果として表現しない。各カードには相対時刻または日本時間の公開時刻を固定位置に置く。

根拠: [Guardianトップ](https://www.theguardian.com/international)、[Bloomberg Latest](https://www.bloomberg.com/latest)、[BBC公式ヘルプ](https://help.bbc.com/hc/en-us/articles/39027623773331-What-types-of-news-content-will-be-available)。確度: 高。

### 4. 罫線・余白・文字サイズを先に決め、色を補助にする

大手の本文抽出では、カテゴリ、見出し、補足、時刻、媒体という情報の順序が繰り返される。BBC GELは本文15–18px、60–70文字、相対単位、左揃え、行高1.5以上を具体化している。OHARU WATCHの現行の丸角・影・ピルを少し残す場合も、カテゴリを色だけで識別させず、文字と罫線を併用する。

根拠: [BBC GEL Typography](https://bbc.github.io/gel/foundations/typography/)、[Guardianトップ](https://www.theguardian.com/international)、[FTトップ](https://www.ft.com/)。確度: 高（可読性）、中（大手画面の見た目）。

### 5. スマホ再配置は「CSSで順番を変える」のではなく「意味順で折り返す」

BBC GELは`order`による視覚順と読み上げ順の不一致を明確に問題視している。カードの基本順は、テーマラベル→見出し→要約→媒体→時刻→画像（または画像→ラベル→見出し→要約→媒体→時刻）を決め、デスクトップで左右に置いてもソース順は保持する。Guardianの画像付き記事とテキスト中心記事の混在、BBCの自動カードグリッドはこの考え方と相性がよい。

根拠: [BBC GEL Grids](https://bbc.github.io/gel/foundations/grids/)、[BBC GEL Cards](https://bbc.github.io/gel/components/cards/)、[BBC GEL Cardsの自動グリッド](https://bbc.github.io/gel/components/cards/)。確度: 高。

## OHARU WATCHへの具体提案

### A. トップの骨格

```text
固定ヘッダー: OHARU WATCH | 最終更新 | AI国内 | AI国外 | Apple公式 | Appleリーク
  ↓
リード: 重要度と新しさを満たす1件（画像＋カテゴリラベル＋見出し＋要約＋媒体・時刻）
  ↓
新着タイムライン: 全カテゴリを時刻順で混在表示（媒体・時刻を必ず表示）
  ↓
カテゴリセクション: AI国内 / AI国外 / Apple公式 / Appleリーク
  ↓
注目: 重要度順。新着一覧との重複はしない
  ↓
補助: 媒体別・日付別・おすすめ理由（将来）
```

### B. グリッドとカード

- デスクトップは、リードを`2/3 + 1/3`または`1/2 + 1/2`、通常記事を1列の横長リストにする。画像付き3列カードは「短い見出しだけ」のサブ欄に限定する。
- カードの最小幅はBBC GELの266pxを目安にし、`minmax(266px, 1fr)`で自動折返しする。日本語の見出しは英語より行が増えるため、幅を狭くし過ぎない。
- 角丸は現行の18pxから8–12pxへ弱め、影は主要リードだけに限定する。通常リストは白地、1px罫線、十分な上下余白で区切る。これはFT／Guardian的な「情報の階層を線と余白で示す」方向の提案であり、固有サイトの完全再現ではない（確度: 中）。
- 見出しは本文より明確に大きく太くするが、カードごとに大見出しを乱発しない。リード1件、カテゴリ見出し、通常見出しの3段階に限定する。

### C. 色・書体・メタ情報

- 色はカテゴリの意味を伝えるアクセント1色＋中立色を基本にする。AI国内とAI国外を別々の派手な色にするより、同じAI系統色＋小さな地域ラベルの方が大量表示で落ち着く。
- 本文・要約は16px前後、行高1.6–1.8、最大幅65ch程度を目安にする。見出しが長い日本語では`line-clamp`で情報を切り過ぎない。
- カード内メタ情報は固定順で「カテゴリ（またはテーマ）／媒体名／公開時刻」。媒体名を省略記号だけにせず、`source-name`の幅を確保する。Guardianの相対時刻、FTのトピックラベル、Bloombergのサブセクション名が参考になる。
- 「重要度5段階」は星・赤色だけで強調せず、「注目」などの短い文字とツールチップ／記事詳細で説明する。速報、リーク、公式発表を重要度と混同しない。

### D. モバイル

- ヘッダーはブランド＋ハンバーガー（またはカテゴリ横スクロール）に縮小し、最終更新は2行目へ落とす。カテゴリは4つを無理に横一列へ詰めず、横スクロールまたは開閉メニューにする。
- リードは画像→カテゴリ→見出し→要約→媒体・時刻の1列。通常記事は画像を左、本文を右に固定せず、320px幅では画像を上、メタ・見出し・要約を下に積む。
- `order`で「おすすめだけを視覚的に先頭へ移動」しない。HTML上も重要度順／時刻順の意図が保たれるよう、Python側で並び順を決める。
- 画像のない記事は空白カードにせず、罫線と見出し階層で高さを揃える。BBC GELのカード最小幅と自動折返しを参考にする。

## コピーすべきでない点

- **金融端末級の密度**: BloombergのTop Securities、Stock Movers、Most Activeのような数値パネルを、そのままAI/Appleニュースに載せない。相場データと違い、記事の重要度を数値だけで説明できない。
- **巨大なカテゴリ網羅**: FT／Guardian／Bloombergの多数カテゴリをそのまま模倣しない。OHARU WATCHは4カテゴリが主目的であり、ナビを増やすほど見出しの視線が分散する。
- **購読・ログイン導線**: FT等のSubscribe／Sign Inは事業モデル上の要素。個人サイトに同じ導線や会員機能を足さない。
- **画像を主役にし過ぎる構成**: Guardianの写真中心の特集面は、写真編集部と大量の独自素材がある媒体だから成立する。RSS中心のOHARU WATCHで画像を大きくすると、デフォルト画像の反復が目立つ。
- **丸角・影・ピルの過剰使用**: 現行デザインの装飾を全廃する必要はないが、全セクションをカード化すると新聞的な優先順位が消える。罫線と余白を主役にする。
- **CSSだけの視覚順序変更**: BBC GELが警告するように、視覚順とスクリーンリーダー順がずれる。特にスマホで「重要度順に見せる」場合はHTML生成側で順番を決める。
- **固有ブランドの色・フォントの直輸入**: FTの背景色、GuardianやBloombergのブランド書体をコピーしても、OHARU WATCHの日本語RSSと目的には適合しない。色はアクセント1色、書体は日本語可読性を優先する。

## 見つからなかったこと／制約

- Reutersの消費者向け`reuters.com`、BBCの`bbc.com/news`、NYTの`nytimes.com`は、この調査環境ではrobots.txtまたは内部エラーで直接開けなかった。したがって、これら3媒体のニューストップの正確な色、CSS寸法、フォント名、モバイル画面は未確認。
- 公式ページ本文は、ページの情報構造や見出し順は返すが、すべてのCSSトークン、ブレークポイント、画面幅別スクリーンショットを返すわけではない。FT、Guardian、Bloombergの「書体名・色・罫線の細さ」は、明記のないものを推定として扱った。
- Bloombergの取得ページには更新時点のニュース見出し・株価が含まれるが、これはデザイン観察用の動的データであり、内容の事実確認やOHARU WATCHへの転載対象ではない。
- Reuters AgencyとReuters GraphicsはReutersの一次資料だが、消費者向けニューストップとは情報設計の目的が異なる。Reutersトップの視覚比較としては使わず、速報／写真／動画／グラフィックを分ける編集単位の根拠に限定した。

## 検索クエリ一覧

実施した異なる検索クエリ（2026-08-23）:

1. `site:bbc.com/news BBC News homepage latest world business technology`
2. `Reuters homepage world business technology latest news site navigation`
3. `site:nytimes.com NYT homepage latest news sections design typography layout`
4. `site:theguardian.com/international The Guardian homepage news sections layout latest`
5. `site:ft.com Financial Times homepage markets latest news layout sections`
6. `site:bloomberg.com Bloomberg homepage markets technology latest news navigation design`
7. `New York Times homepage site:nytimes.com/section/world top stories latest 2026`
8. `site:bbc.github.io/gel BBC GEL design system typography spacing grid`

検索結果のうち、実際に本文まで読んだ有望ページ: BBC Help／BBC GEL Grid・Typography・Grids・Cards、Reuters Agency／Reuters Graphics、FT Home、Guardian International、Bloomberg Latest／Markets／Technology。未確認ページは本文で明記した。

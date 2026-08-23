# テクノロジー系ニュースサイトの視覚表現調査

確認日: 2026-08-23（日本時間）
対象: The Verge、WIRED、TechCrunch、Ars Technica、Axios、Rest of World、Apple Newsroom
目的: AI/Appleニュースを大量表示するOHARU WATCHの次期デザインに転用できる、画像に依存しすぎない原則を抽出する。

## 要約

7媒体を実ページと媒体自身のデザイン説明で比較すると、長期運用に効く共通点は「重要度をレイアウトで示す」「短いメタデータと本文の役割を分ける」「画像がなくても見出しとタグだけで読める」ことである。The Vergeのストリーム、Ars Technicaの表示モード切替、Axiosの短い要点、Rest of Worldのテーマ別ブロックは、大量の記事を一列に積むだけではなく、スクロール中の判断単位を作っている。派手な色・大画像・無限スクロールはブランドを作れる一方、情報密度・可読性・通信量・認知負荷と交換になるため、OHARU WATCHでは固定比率の控えめな画像と本文中心のリストを基本にするのが妥当である。最も再現性の高い案は、現在のカード構造を維持しながら「1色のアクセント」「短い見出し上限」「カテゴリごとの明確な区切り」「先読みしない遅延画像」を足す方式である。

## 媒体別発見

### The Verge

- 実ページ: [The Vergeトップ](https://www.theverge.com/)（2026-08-23確認）。上部に Tech / Reviews / Science / Entertainment / AI / Policy のナビゲーションがあり、表示モードとして `Top Stories / Latest / Following` がある。先頭は画像付きの大きな記事、その後に `Quick Posts`、テーマ別のまとまり、`Most Popular` の順位リストが続く。直接のHTMLテキスト上でも、画像付きストーリーと画像なしの短文フィードが混在していることを確認できた。確度: **高**。
- 2022年の公式説明に近い報道では、StoryStreamを「編集者が外部の投稿・動画・Redditスレッドなども含めてまとめるフィード」とし、より多くの更新を無限スクロールで見せる構想だった。[Axiosによるリデザイン報道](https://www.axios.com/2022/09/13/verge-goes-after-twitter-new-redesign)（2022-09-13）。現在のトップにも、記事の本文カード、短いQuick Post、テーマ別フィード、Popular順位表という同系統の構造が残っている。確度: **高**（現在ページの構造）／**中**（2022年からの継続性）。
- 色・タイポグラフィは、公式説明で「よりカラフルで現代的なフォントとグラフィック」「新しい明るいカラーパレット」とされ、本文にはセリフ体も採用された。[同Axios記事](https://www.axios.com/2022/09/13/verge-goes-after-twitter-new-redesign)。ライブページのテキスト取得では色コードやCSSは確定できず、現行の正確なアクセント色は断定しない。確度: **中**。
- 2026年のリニューアル紹介（第三者の転載ページ）には、大きな注目記事と時系列フィードを左右に分け、明るいアクセントを置く構成の説明がある。[The next evolution of The Verge's homepage](https://www.webnuz.com/article/2026-04-21/The%20next%20evolution%20of%20The%20Verges%20homepage%20is%20here)。第三者情報なので、視覚の細部は参考扱いにする。確度: **低〜中**。
- 応用: 画像がカテゴリの意味を担えない場合でも、`Latest`（時系列）と`Top Stories`（編集上位）を分け、短文フィードには時刻・媒体・カテゴリを必ず添える。StoryStream風の混在をそのまま採用すると、AIとAppleが同じ流れに見えるため、OHARU WATCHではカテゴリ境界を残す。
- モバイル: 2026年の紹介画像はラップトップとスマートフォンの左右分割を示すが、公式のCSSや実機幅は未確認であるため、OHARU WATCHでそのまま再現しない。確度: **低〜中**（[紹介ページ](https://www.webnuz.com/article/2026-04-21/The%20next%20evolution%20of%20The%20Verges%20homepage%20is%20here)の画像説明）。

### WIRED

- 実ページ: [WIREDトップ](https://www.wired.com/homepage/)（2026-08-23確認）。Security / Politics / The Big Story / Business / Science / Culture / Reviewsという上部ナビゲーションを持ち、本文テキストでは `Today's Picks`、`Subscriber Exclusives`、`The Big Story`、`Special Editions` など編集上のまとまりが確認できる。確度: **高**。
- WIRED自身のリデザイン説明は、スマートフォンを起点にカードの仕組みを設計し、他画面へ拡張したこと、カードによりホームとセクションがスキャンしやすくなったこと、Retina対応画像と専用フォントを使ったことを記す。[Welcome to the New WIRED](https://www.wired.com/2015/03/our-new-site/)。確度: **高**。
- その後の改善説明では、著者を目立たせ、本文幅を広げ、読み込みを速くし、ADA準拠、フォントをスキャンしやすく、ナビを整理したと明記している。[Why WIRED.com Looks Different Today](https://www.wired.com/story/why-wiredcom-looks-different-today/)。派手なカードの採用後も、可読性とアクセシビリティを逆方向の評価軸にしている点が重要である。確度: **高**。
- 視覚的には、カードや大画像を使うが、記事のまとまり・見出し・著者・本文幅で密度を制御するタイプ。現在ページのテキスト取得では画像の正確なアスペクト比は分からないため、比率は固定値として採用しない。確度: **中**。
- 応用: 画像の有無を問わず、記事タイトル、媒体、公開時刻、本文抜粋を一定の順序にし、作者名／媒体名を「信頼のメタデータ」として残す。画像を大きくする前に本文幅と見出しの行数を整える。

### TechCrunch

- 実ページ: [TechCrunchトップ](https://techcrunch.com/)（2026-08-23確認）。上部に Latest / Startups / Venture / Apple / Security / AI / Apps / Events / Podcasts / Newsletters のナビゲーションと検索がある。先頭は画像付きの主要記事群、`Top Headlines` の短いリスト、`Featured`、`Latest News`、`In Brief`、カテゴリ別の長い一覧、`Most Popular`、動画・ポッドキャストへ続く。統一カードだけでなく、画像付き記事、画像なし見出しリスト、カテゴリモジュールを使い分けている。確度: **高**。
- 現在のトップのカテゴリタグは記事の上に置かれ、画像の有無にかかわらず `AI`、`Climate`、`Government & Policy` などを識別できる。`In Brief` は他媒体の記事を短く案内する枠で、元記事の所在を隠さない設計に転用しやすい。確度: **高**。
- 2024年の公式リデザイン説明は、以前の「実用一点張り」から、より滑らかで速く、ナビが改善され、色・モダンさを更新し、大きなニュースの経過を届ける機能を追加したと説明する。[TechCrunch reimagined](https://techcrunch.com/2024/10/02/techcrunch-reimagined-welcome-to-our-new-design/)。確度: **高**。
- 長期の公式リデザイン記事は、レスポンシブな単一コードベース、記事内の大きな画像、可読性・散らかりの改善を説明している。[TechCrunch Has Redesigned, Again](https://techcrunch.com/2013/10/15/techcrunch-has-redesigned-again/)。現在の色コードは公式記事に記載されないため、従来からの緑を正確な値として固定しない。確度: **中**。
- 応用: `Top Headlines` 型の画像なし短冊を設けると、デフォルト画像が連続しても視覚が単調にならない。AI/Appleの記事を「画像付きカード」と「テキスト速報」の2種類で扱い、記事が実際に速報なのか解説なのかをラベルで示す。
- モバイル: TechCrunchの公式リデザイン記録は、27インチからiPhoneまで同一コードベースで表示を調整し、小画面では補助要素を外すレスポンシブ設計を記す。[TechCrunch Has Redesigned, Again](https://techcrunch.com/2013/10/15/techcrunch-has-redesigned-again/)。確度: **高**（ただし2013年の説明であり、現行CSSの保証ではない）。

### Ars Technica

- 実ページ: [Ars Technicaトップ](https://arstechnica.com/)（2026-08-23確認）。検索経由の公式ページ表示では、`Classic / Grid / List / Neutron Star` の表示モード、`Featured` の大きな記事、記事ごとの著者・日付・コメント数、`Most Read` の順位リストを確認できた。確度: **高**（公式ページの検索取得）。
- 画面説明では、Grid表示に大きな注目記事と小さな一覧を併置し、List表示ではテキスト密度を上げられる。これは単一の「正解のカード比率」を押し付けず、読者の目的（眺める／大量に読む）に表示を合わせる設計である。確度: **中**（画面画像の第三者説明を含む）。
- 直接の再取得は403だったため、現行CSSの色・フォント・厳密な画像比率は確認できなかった。検索結果上は、画像、見出し、著者、時刻、コメント数を近接配置している。確度: **高**（取得制約）／**中**（視覚細部）。
- 応用: OHARU WATCHに複雑なテーマ切替を持ち込む必要はないが、PCでは現在の画像付き行、スマホでは画像を小さくした`一覧モード`を用意すると、大量表示と可読性を両立しやすい。モード追加は将来機能とし、まずは同じDOM順序でCSSだけを切り替えられるようにする。
- モバイル: `List`表示は小画面で画像を省略・縮小する設計の参照になるが、Arsの現行ブレークポイントは未確認。確度: **中**。

### Axios

- 実ページ: [Axiosトップ](https://www.axios.com/)（2026-08-23確認）。`Politics & Policy / Business / Technology / Health / Energy & Climate` のカテゴリナビ、`Catch up quick` の短いヘッドライン群、`TOP STORIES / MOST POPULAR` の切替、画像付きの主要記事、`Go deeper (1–2 min. read)`、`THE LATEST` の小さなリストがある。短い要点と読了目安を先に出す構成で、画像がなくても意味が通る。確度: **高**。
- Axiosの公式Smart Brevity説明は、先に「何が新しいか」「なぜ重要か」を伝え、短い見出し・白スペース・太字・箇条書き・画像を組み合わせると説明する。[Smart Brevity](https://www.axioshq.com/smart-brevity)。これは視覚デザインというより編集フォーマットだが、大量ニュース一覧のスキャンに直結する。確度: **高**。
- 色・フォント・カードの詳細は、ライブページの本文取得では確定できなかった。第三者のライブ採取に基づくデザインシステム説明では、ほぼ白〜薄灰の背景、黒系文字、単一の濃紺アクセント、サンセリフ見出し／セリフ本文、丸いカテゴリチップ、正方形に近い画像セルとされる。[Axios Design System（第三者採取）](https://www.shadcn.io/design/axios)。確度: **中**（コードの公式仕様ではない）。
- 応用: カテゴリごとに色を増やすより、アクセント1色＋文字の太さ＋`新着 / 重要 / 公式 / リーク`の短いタグで情報を分ける。タイトルの上限（日本語なら2〜3行）と「何が重要か」の一文を固定する。
- モバイル: AxiosのSmart Brevity教材は、見出しを10語または60文字程度にするとスマートフォンで約2行に収まりやすいと説明する。[Smart Brevity 101](https://www.axioshq.com/hubfs/Marketing%20Research%20and%20Tools/Smart%20Brevity%20101%20-%20How%20to%20optimize%20an%20essential%20communication.pdf)。英語の目安なので、日本語タイトルは表示実測で上限を決める。確度: **中**。

### Rest of World

- 実ページ: [Rest of Worldトップ](https://restofworld.org/)（2026-08-23確認）。上部のテーマナビ（Tech Giants / EV Revolution / China Outside China / Innovation）、`Latest Stories` の読了分数付きリスト、画像付きの主要記事、テーマ別のまとまり、`Editor's picks` の年切替、`Charts` が連続する。大画像だけにせず、読了時間・地域・テーマ・著者を明示している。確度: **高**。
- 公式Style Guideは、ブランド色をCobalt `#242EF7`、UIラベルをInput Mono、見出し等をModerat、本文をGeorgiaと定義し、インラインリンクは原則下線、丸角モジュールを使うと記す。[Rest of World Style Guide](https://restofworld.org/style-guide/)（最終更新 2026-01-12）。確度: **高**。
- 2025年の公式色刷新記事は、7色をランダムに回す方式から単一のCobalt Blue＋白背景へ移行した理由を、訪問ごとの不統一、読者の混乱、写真チームの認知負荷、写真を目立たせる必要として説明する。[One bold blue to rule them all](https://restofworld.org/inside/design-color-refresh/)。これは「派手さを減らすことがブランド弱体化ではない」という実例である。確度: **高**。
- 2021年の公式ホームページ刷新記事は、モバイル画面も含む柔軟なコンテンツブロック、Big Story / Spotlight / Curated Collection / Recent Storiesを使い分け、編集者が保守しやすい構造にしたと説明する。[New year, new look](https://restofworld.org/inside/homepage-redesign/)。当日の直接取得は429だったため、本文は検索スニペットと公式ページの引用に基づく。確度: **中**。
- 同記事は、高解像度画像とリッチなフォントを採用する代わりに、画像容量・通信速度とのトレードオフを意図的に受け入れたと説明する。画像を真似る場合は、OHARU WATCHの無料RSS運用やデフォルト画像とは条件が異なることに注意する。確度: **高**。
- 応用: 色は1つの主アクセントに絞り、カテゴリ色は背景全面ではなく小さなタグ・左罫線に留める。テーマブロックの考え方は、AI国内／AI国外／Apple公式／Appleリークの4分類と相性がよい。

### Apple Newsroom

- 実ページ: [Apple Newsroomトップ](https://www.apple.com/newsroom/) と [All Topics Archive](https://www.apple.com/newsroom/archive/)（2026-08-23確認）。アーカイブには`All Topics / All Years / All Months`のフィルタ、月単位の見出し、`PRESS RELEASE`と`UPDATE`の種別ラベル、日付、記事タイトルがあり、画像なしでも検索・時系列確認ができる。確度: **高**。
- 個別記事例では、`PRESS RELEASE`、日付、タイトル、短いリード、横長の大画像、本文中の複数画像、前後移動、`Media in this article / Download all media`が確認できる。[Apple accelerates app development with new intelligence frameworks and advanced tools](https://www.apple.com/newsroom/2026/06/apple-aids-app-development-with-new-intelligence-frameworks-and-advanced-tools/)。確度: **高**。
- トップの本文はクライアント側描画のためテキスト取得が少なく、現行トップの厳密なカード比率・フォントCSSは確定できない。Apple公式のデザインリソースはSF Pro / SF Compact / SF Mono / New Yorkを提供しているため、Apple系の雰囲気を参考にする場合も、OSフォントを無断転載せずシステムフォントへフォールバックするのが安全である。[Apple Design Resources](https://developer.apple.com/design/resources/)。確度: **中**（Newsroomへの適用は未確認）。
- 画像中心の見栄えは強いが、二次資料では通常トップは画像重視で情報密度が低く、記者向けにArchiveのコンパクトリストが存在すると報告されている。[Apple transitions to Newsroom portal](https://9to5mac.com/2017/05/25/apple-newsroom-new-design-bios/)。一次アーカイブでも、実際に画像なしの種別・日付・タイトル一覧が確認できた。確度: **中**。
- 応用: Apple公式の「更新種別＋日付＋タイトル」の情報設計を、OHARU WATCHの`公式`／`リーク`や`新着`ラベルへ転用する。画像のダウンロードを前提にせず、記事一覧では種別と本文抜粋を主役にする。

## 横断原則

1. **カードの形ではなく、判断の単位を設計する。** 7媒体とも、画像付き主役、短い見出しリスト、テーマ別ブロック、ランキングまたはアーカイブを組み合わせている。全記事を同じカードにするより、重要度・速報性・読了時間の違いを構造で示す方が、画像が似ていても意味を保てる。確度: **高**。
2. **アクセント色は1色を主役にする。** Rest of Worldは複数パレットが読者と制作側の混乱を招いたとしてCobalt＋白へ整理し、Axiosも単一アクセントという方向で採取されている。カテゴリごとの色分けを残す場合も、タグや罫線など小面積に限定する。確度: **高**（Rest of World）／**中**（Axios）。
3. **見出し・メタデータ・本文抜粋を別レイヤーにする。** 媒体名、時刻、著者、読了分数、コメント数、記事種別は、画像がない時にも信頼・新しさ・内容を伝える。見出しを装飾で埋めず、メタデータは短く固定幅で揃える。確度: **高**。
4. **画像は固定比率で“穴”をなくす。** 実ページは横長の主画像、正方形に近いセル、小さなサムネイルなど複数比率を使うが、OHARU WATCHで毎回比率を変えると一覧が跳ねる。`aspect-ratio`（例: 16:10または16:9）と`object-fit: cover`を使い、未取得・デフォルト画像でも同じ矩形を確保する。実媒体の比率を厳密に測定できなかったため、これは実装提案であり媒体横断の事実ではない。確度: **中**（設計提案）。
5. **スマホは「1列化」だけでなく、密度モードを下げる。** WIREDはスマホ起点のカード設計、Rest of Worldはモバイルを含むブロック設計、ArsはList表示を持つ。OHARU WATCHでは横長画像を小さくし、タイトル→カテゴリ→媒体→抜粋の順で1列にする。横スクロールのカテゴリナビは短く保ち、記事カード自体を横スワイプにしない。確度: **高**（方針）／**中**（各媒体の細部）。
6. **無限スクロールは“便利”と同時に状態を失わせる。** The Vergeはフィードと無限スクロールで再訪・広告機会を狙えるが、OHARU WATCHは記事数が多い個人ダッシュボードで、現在位置・未読・カテゴリ境界を見失いやすい。既存の「最初30件＋20件追加」ボタンは、表示量と通信量を利用者が制御できる点で合理的である。確度: **高**（The Vergeの目的）／**中**（OHARU WATCHへのリスク）。
7. **アクセシビリティはデザイン後の検査ではなく、レイアウトの材料にする。** WIREDはリデザイン後にADA準拠、本文幅、読みやすいフォント、速度を改善した。OHARU WATCHでも、色だけでカテゴリを区別せず、文字ラベル・見出し階層・キーボードフォーカス・`alt`・`prefers-reduced-motion`を維持する。確度: **高**。

## OHARU WATCHへの提案

### 次期トップの構造（変更量が少ない順）

1. **現在の白・ネイビー基調は維持し、主アクセントを青1色に整理する。** AI国外やAppleリークの紫・赤は、タグの文字色または左罫線だけにし、背景全面には使わない。Rest of Worldの単一Cobalt化が、派手さを保ちつつ運用と認知負荷を下げた根拠になる。
2. **先頭は「今日の注目」1件＋“速報リスト”に分ける。** 先頭記事だけ16:10程度の固定画像枠を与え、次の5〜8件は画像を小さくした横長行にする。デフォルト画像が連続しても、先頭以外は文字の階層が主役になる。
3. **カテゴリごとに「見出し→タグ→媒体・時刻→本文抜粋」の順を統一する。** タイトルは原則2〜3行で切り、抜粋は2行まで。タグは`AI国内`、`AI国外`、`Apple公式`、`Appleリーク`とし、色がなくても読めるようにする。
4. **画像は遅延読み込みし、失敗時も同じ比率を保つ。** 既存のデフォルト画像フォールバックを残し、カードの高さを画像取得結果に依存させない。外部OGP取得を通常運用で有効化しない現行方針は速度面で妥当。
5. **「おすすめ」と通常一覧の役割を分ける。** The VergeのTop Stories／Latest、AxiosのTop Stories／Most Popularのように、注目と時系列を別枠にする。ただし同一記事を二重表示しない現在のルールは維持する。
6. **ボタン追加を維持し、無限スクロールは採用しない。** 追加件数（20件）を明記し、残り件数をボタンに表示する。これにより無料RSS運用でも画面が急に長くならず、読み位置を失いにくい。
7. **CSSだけで“高密度モード”を将来追加できるようにする。** `.article-card`の画像幅をPC 176px／スマホ 96px程度へ切り替えるだけで、ArsのList表示に近い読み方を提供できる。DOM・アクセシビリティ順序は変えない。

### 画像がデフォルト中心でも成立する理由

- 視線誘導の主役を写真から「見出しの行数、タグの位置、メタデータ、罫線、余白」へ移す。Axiosの短い要点、Apple Archiveの種別・日付・タイトル、Arsのコメント数付きリストが参考になる。
- デフォルト画像はカテゴリの“意味”を表す主役ではなく、一覧の矩形を埋める背景として扱う。画像上に白文字を重ねる、画像の色でカテゴリを伝える、といった依存を避ける。
- 画像の縦横比が記事ごとに異なるとスクロールが不安定になるので、取得元が違っても同じ比率・同じ余白で表示する。画像の美しさより、見出しを読み飛ばさないことを優先する。

## 反証・リスク

- **派手なダークテーマをそのまま採用する反証:** The Vergeのような高コントラストの暗色＋鮮色はブランド化に有効だが、画像の上に文字を置く設計や大きな装飾は、タイトルの折返し・色覚差・明るい場所の画面での読みやすさを損ねやすい。現行OHARU WATCHの白地は、長い日本語タイトルとデフォルト画像の組合せでは安全側である。The Vergeは視覚の参考にするが、色面・巨大ロゴ・縦書き風装飾は部分採用に留める。確度: **中**（一般的なUIリスク。ページ固有のユーザーテスト結果ではない）。
- **大画像中心の反証:** Rest of Worldは高解像度画像と豊かなフォントを意図的に選んだが、同時に画像容量・通信速度とのトレードオフを認めている。Apple Newsroomも画像中心のトップは見栄えがよい一方、二次資料では情報密度が低いと評され、Archiveのコンパクトリストが補完している。無料RSSとGitHub PagesのOHARU WATCHでは、大画像を既定にすると速度と更新安定性が悪化する。確度: **高**（Rest of World）／**中**（Appleの二次資料）。
- **無限スクロールの反証:** The Vergeは再訪と広告機会、編集者の集約効率を狙えるが、個人のニュース確認では「どこまで読んだか」「カテゴリをまたいだか」が不明瞭になる。記事を大量表示するほど、追加ボタン・件数表示・カテゴリ境界の方が検証可能である。確度: **高**（The Vergeの目的）／**中**（ユーザー行動の推定）。
- **タグ色増加の反証:** 色をカテゴリごとに増やすと一見わかりやすいが、Rest of World自身がランダムな複数色の不統一と認知負荷を問題にして単色化した。色覚に依存する情報設計を避けるため、タグ文字を必須にする。確度: **高**。
- **角丸カードの反証:** 現行OHARU WATCHは角丸と影を使うが、全要素がカード化するとページが“UIの箱”に見え、ニュースの優先順位が均一になる。WIREDやTechCrunchのように、罫線・余白・見出しサイズだけで区切るセクションを混ぜる方が、デフォルト画像でも紙面らしい密度を作れる。確度: **中**。
- **フォント変更の反証:** WIREDやRest of Worldはブランドフォントを持つが、外部フォントの追加は通信量と日本語グリフの欠落を招きやすい。OHARU WATCHでは既存のシステム日本語フォントを維持し、ウェイト・行間・字間で階層を作る方が費用と速度の面で現実的である。確度: **高**（実装リスク）。

## 見つからなかったこと／調査上の制約

- 2026-08-23時点の各サイトで、全カードの正確な画像アスペクト比、ブレークポイント、CSSフォントファイル、Lighthouse値を一次情報だけで揃えることはできなかった。したがって本稿は「16:9が標準」といった断定をしていない。
- in-app Browserは接続できず、直接ページの視覚スクリーンショットを操作取得できなかった。Webの実ページテキスト、公式デザイン記事、画像検索が返したスクリーンショット説明を照合し、画面の色・比率は確度を下げて記録した。画像検索結果や第三者のデザインシステムは、媒体の公式仕様ではない。
- Ars Technicaは公式トップの検索結果を読めたが、直接の再取得は403 Forbiddenだった。そのため現行ページの正確な色・フォント・画像比率は未確認である。
- Rest of Worldのホームページ刷新記事は、公式ページへの直接アクセス時に429 Too Many Requestsになった。検索スニペットと同媒体の現行Style Guide／色刷新記事で補完したが、2021年当時のモバイル画面の細部は未確認である。
- Apple Newsroomトップはクライアント側描画が多く、Webテキストでは記事カードの全順序を再現できなかった。アーカイブと個別記事ページは確認できた。
- The Vergeの2026年リニューアルの細部は、公式トップの現在構造は確認できたが、公式のまとまったデザイン仕様ページは検索で特定できなかった。第三者の2026年紹介は参考止まりとした。
- 媒体別のモバイル挙動を同一端末・同一幅で実測比較することはできなかった。次の工程でOHARU WATCH自身を375px／768px／1280pxで確認し、横はみ出し、見出し行数、画像遅延を検査する必要がある。

## 検索クエリ一覧（すべて2026-08-23）

1. `The Verge homepage technology news design layout typography cards`
2. `Wired homepage technology news design layout typography cards`
3. `TechCrunch homepage news design cards list typography`
4. `Ars Technica homepage current layout article cards typography 2026`
5. `Axios homepage news design typography cards list current`
6. `Rest of World homepage design layout typography news`
7. `Apple Newsroom homepage current design layout typography images press releases`
8. `The Verge 2026 homepage feed layout redesign official`
9. `digital news site homepage mobile design cards default thumbnails performance accessibility`
10. `The Verge homepage black yellow color typography screenshots current site visual design`
11. `The Verge website redesign color palette font 2022 official`
12. `TechCrunch 2024 redesign color palette typography official design`
13. `TechCrunch homepage screenshot green logo card layout current site`
14. `Axios homepage design Smart Brevity typography cards official 2026`
15. `Axios design system homepage fonts color card layout current site`
16. `Ars Technica homepage screenshot 2026`
17. `Apple Newsroom homepage screenshot 2026`

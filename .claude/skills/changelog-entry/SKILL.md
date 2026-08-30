---
name: changelog-entry
description: "给「远征尼朋 / Nippon Expedition」更新记录站点加一条版本更新记录：从 mod 仓库的 version.md 取料、写中文正文、查术语对照表译成英文、构建并肉眼验证。触发词：加一条更新记录、写 changelog、更新记录、新版本、发版记录、release notes、v1.0.2、把这次改动记到站点上、更新 changelog、补一条 log"
---

# 加一条更新记录

本 skill 只服务 `nippon-expedition-site` 这一个仓库。所有相对路径都相对**本仓库根目录**，且只在维护者本机成立（原料在同级的私有仓库里）。

## 第 1 步：取料

唯一权威原料是 [`../nippon_expedition/_docs/backlog/version.md`](../nippon_expedition/_docs/backlog/version.md)——mod 仓库那边按「一条改动 = 一行、只写玩家看得懂的功能变化」维护的流水账，粒度正好。

```bash
sed -n '/^---$/,$p' ../nippon_expedition/_docs/backlog/version.md | head -60
```

注意版本号后面的标记：`(未发布)` 表示还没上工坊。

那边有个和版本小节**同级、不参与版本号进位**的「## 追加兼容子 mod」小节，每接入一个第三方 mod 追加一行。它排在版本小节之上，所以从 `## <数字>` 开始截会整段漏掉——上面的命令从分隔线起截就是为了带上它。这类条目进站点的**子 mod** 页签，写法见第 2 步。

**绝对不要**从 `../nippon_expedition/_docs/log.md` 取料。那是开发流水账，写的是表名、字段、key、根因排查，属于开发者视角，不上公开站。

其他可选参考：工坊描述双语成稿 `../nippon_expedition/steam_description_{zh,en}.txt`（大段介绍已有现成译文，首发条目就是从这里提炼的）；子 mod 说明 `../nippon_expedition_{nrs,cathay,yinyin}_compat/README_{zh,en}.md`（都是作者定稿的双语成文，直接搬）。

## 第 2 步：建文件、写中文

`content/releases/<日期>-v<版本>.md`：

```markdown
---
version: 1.0.2
date: 2026-09-15
type: content
tags: main
---

<!-- lang: zh -->

### 新增
- ……

### 修复
- ……

<!-- lang: en -->

### Added
- ...

### Fixed
- ...
```

front matter 规则：

- `version` 必填。排序按数字段比较，`1.10.0` 排在 `1.9.0` 之上。**子 mod 条目例外，见下。**
- `date` 可选。**还没上工坊就留空**——该条会排在所有有日期的之上，页面上不显示日期。别编一个假日期。真发布了再补。
- `type`：`release` / `content` / `balance` / `hotfix`，默认 `release`。
- `tags`：`main` / `stronger-ai` / `nrs-compat` / `cathay-compat` / `yinyin-compat`，逗号分隔。
- `channel`：`main`（默认）/ `submod`，决定进哪个页签。

新增 `type` 或 `tags` 取值时同时改 `content/i18n.json` 的 `TYPE`/`TAGS`（中英各一份）和 `scripts/build.py` 的 `KNOWN_TYPES`，漏了会构建报错。

### 子 mod：一个包一个文件，日期落在每条改动上

子 mod 没有版本号，组织方式和本体不同——**一个子 mod 一个文件**，标题用 `title`，每条改动自己带日期，倒序追加。和 `version.md` 的「子 mod 更新记录」小节一一对应，那边加一行，这边也加一行。

文件是 `content/releases/submod-<短名>.md`，**文件名不带日期**：

```markdown
---
title.zh: 震旦机制兼容包
title.en: Cathay Mechanics Compatibility Patch
channel: submod
url: https://steamcommunity.com/sharedfiles/filedetails/?id=3792252212
tags: cathay-compat
---

<!-- lang: zh -->

一句话说明这个包干什么、谁需要装。

- 2026-08-30 接入 **[某某 mod](链接)**：……
    - 补充说明写成缩进子条目，不带日期。
- 2026-08-30 上线，首个接入 **[某某 mod](链接)**：……
```

- **加新一条就是在已有文件顶部加一行**，不要为一次更新新建文件，也别把两个包混进一个文件。
- **不写 `date`**：排序日期从正文里最新的日期算出来，没有第二处要同步。
- `url` 是这个包自己的工坊页，标题会渲染成带 ↗ 的链接。**正文里别再自链一次**，导语直接说「这个 mod」/「this mod」。
- 默认不显示 `type` 徽章——一个文件横跨多次改动，标一个「版本发布」是假的。
- 正文按时间倒序，不按「新增 / 修复」分组；日期就是分组。
- `key.zh` / `key.en` 两行写一个双语字段。`version` 和 `title` 至少要有一个。
- 子 mod 的中英文案，隔壁 `../nippon_expedition_<包名>/README_{zh,en}.md` 通常已经是作者定稿的双语成文，**直接沿用，别重译**（查表顺序里的第 4 档）。

正文按「新增 / 修复 / 调整」分组，用 `###` 起（`#`/`##` 留给页面本身）。写玩家视角的「加了什么、修了什么」，判据是**读者不打开 pack 能不能看懂**——不写表名、key、字段、力量类型。

### 列表里绝对不能有空行

Python-Markdown 会在列表项内部的空行处**结束整个列表**，后面的 `- ` 会被折进段落变成裸横线。补充说明写成缩进 4 空格的嵌套子条目：

```markdown
- 新增可选子 mod「XX 兼容包」。
    - ⚠️ 装上后旧存档会失效。
- 下一条正常继续
```

构建脚本对此有护栏（检出段落内裸 `- ` 直接报错并指出文件与语种），但别依赖它——写对更省事。

## 第 3 步：译英文——专名查表，不许现编

**这是最容易出错的一步。** mod 里的专名早已定案，凭语感另译会和游戏内文本对不上，玩家看不懂。

按顺序查：

| 顺序 | 查什么 | 路径 | 例 |
| --- | --- | --- | --- |
| 1 | 本项目自造专名 | `../nippon_expedition/_docs/translation/术语对照_自造专名.tsv` | 沈长风 = Shen Changfeng、武者屋形 = Warrior's Manor、伊瑟拉玛银战车 = Ithilmar Chariot |
| 2 | 原版官方译名 | `../nippon_expedition/_docs/translation/术语对照_原版专名.tsv` | 黎山 = Mount Li、尚武造诣 = Martial Prowess、长牙之路 = The Ivory Road |
| 3 | IEE 地名 | `../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md` | 龙舰海港 = Dragon Fleet Port、橙色神華大社 = Temple of the Orange Simca |
| 4 | 工坊描述成稿 | `../nippon_expedition/steam_description_en.txt` | 大段功能介绍的现成表述 |

一次查多个词：

```bash
grep -h "沈长风\|武者屋形\|尚武造诣\|长牙之路" ../nippon_expedition/_docs/translation/术语对照_*.tsv | cut -f1-3
grep "神華\|龙舰海港" ../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md
```

两张 TSV 的列：自造专名是 `类别 / 中文 / 建议英文 / 依据 / 确定度 / loc key 示例`；原版专名是 `中文 / 官方英文 / 置信度 / 出现次数 / 涉及文件数 / 原版出处key / 出现在`。

### 中文专名也要留神：玩家看到的名字 ≠ 项目文档里的名字

有些地名，IEE 官方中文和本项目文档写法不一致。更新记录是**给玩家看的引导文案**，必须用**玩家在游戏地图上看到的那个名字**，不是项目内部惯用写法。

| 玩家在地图上看到 | 项目文档惯用 | key |
| --- | --- | --- |
| **竜舰海港** | 龙舰海港 / 龙舰港口 | `cr_combi_region_nippon_2_1` |

这类冲突在 IEE 清单里以「译名冲突提醒」引用块标出，写到地名时顺手 `grep 译名冲突` 扫一遍。`version.md` 的原文通常已经用了对的那个，**照抄原文比自己换词安全**。

**四处都查不到才可以自己拟**，并且拟完要把这条回填进 `术语对照_自造专名.tsv`（`确定度` 填 `待确认`），别让下次再拟一遍、拟出第二个译名。定名政策见同目录 `术语对照_自造专名_说明.md`。

英文块可以先不写——缺了英文页会自动回落中文正文并显示「尚未翻译」提示，支持先发中文后补译。中文块必填。

大段正文的精翻可以配合 `translate-polisher` skill；几条 bullet 按上面流程直接译即可。

## 第 4 步：构建并肉眼验证

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory site/_dist
```

打开 <http://localhost:8000/changelog/>（英文 `/en/changelog/`；`/` 是简介页，不是更新记录）。**要真的看页面**，不能只看构建没报错——列表被截断、专名译错这类问题构建都不会拦。

逐项确认：

- 新条目排在最上面，版本号 / 日期 / 徽章 / 标签都对
- 列表没有被截断（数一下 bullet 条数对不对）
- 中英两页都正常，语言切换不 404

改动了链接、模板或资源路径时，额外跑一次带子路径的构建（项目站点最容易翻车的一环）：

```bash
SITE_BASE_PATH=/nippon-expedition-site SITE_ORIGIN=https://camtrik.github.io python3 scripts/build.py
grep -oE '(href|src|content)="/[^"]*"' site/_dist/en/changelog/index.html | sort -u   # 应全部带前缀
python3 scripts/build.py   # 记得改回来
```

## 第 5 步：提交

只提交 `content/` 下的改动（以及必要时的 `i18n.json` / `build.py`）。**`site/_dist/` 不入库**，已在 `.gitignore`，由 Actions 现场构建。

推到 `main` 后 GitHub Actions 自动构建部署到 <https://camtrik.github.io/nippon-expedition-site/>。

```bash
gh run watch --repo camtrik/nippon-expedition-site --exit-status
curl -s -o /dev/null -w '%{http_code}\n' https://camtrik.github.io/nippon-expedition-site/
```

## 顺带一提

如果这一版在工坊真发布了，记得回 mod 仓库把 `version.md` 里那一版的 `(未发布)` 换成发布日期——但**「已发布」这个动作只有用户能宣布**，agent 不得自行标记。同时把本仓库对应条目的 `date` 补上。

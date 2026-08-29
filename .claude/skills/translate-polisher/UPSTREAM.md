# 来源与同步

这个 skill 是**外部 vendored 内容，不要就地改**。要改行为请在项目自己的 skill 里包一层，
或者先在上游提 PR，改完重新同步——否则下次同步会把本地改动冲掉。

| 项 | 值 |
| --- | --- |
| 上游 | https://github.com/rookie-ricardo/erduo-skills |
| 路径 | `skills/translate-polisher` |
| 固定提交 | `52efddaf1cc49c0104a481327059d27ddca01280`（2026-04-06） |
| 装入日期 | 2026-08-23 |
| 许可证 | MIT（见同目录 `LICENSE`，Copyright (c) 2026 Erduo） |

## 装在哪几处

| 用途 | 路径 |
| --- | --- |
| Claude Code + Codex（共享目录，两个 symlink 都指这里） | `/d/ModsProjects/.agents/skills/translate-polisher/` |
| zcode（仓库级） | `warhammer_3/nippon_expedition/.zcode/skills/translate-polisher/` |

两份是**同一提交的副本**。重新同步时两处都要更新。

```bash
gh api repos/rookie-ricardo/erduo-skills/contents/skills/translate-polisher/SKILL.md --jq '.content' | base64 -d
```

## 用在本项目时的注意事项

这个 skill 是给**连续散文**（文章、书籍章节）做精翻的，不是给 loc 条目表做的。用于
「远征尼朋英文版」时有三条要自己补，skill 本身不管：

1. **富文本标记必须原样保留**——`\\n`（两个反斜杠）、`[[col:…]][[/col]]`、`[[img:…]]`、
   `%s`/`%d`、`||`、`{{tr:…}}`。全库计数见
   [`_docs/translation/英文化待译内容清单.md`](../../../_docs/translation/英文化待译内容清单.md) 第五节第 2 条，
   翻译后必须逐条对齐。upstream 没有 protected-span 机制。
2. **术语走项目自己的基线**，不要让它自由发挥。已定死的 15 条译名在同一份文档第六节；
   战锤原版专有名词一律用原版英文原名，不回译。可以把这些喂给它的 `--glossary` 参数。
3. **`scripts/fix_punctuation.py` 不要用**。它是把英文标点转成中文全角标点的，服务于
   *英译中*方向。我们是中译英，跑它只会把结果弄坏。

另外它的四步流程（分析→初译→审校→终稿）里，「分析原文口吻」这一步对孤立的
tooltip 条目意义不大，成本却照付——短条目建议直接用它的初译+审校两步。

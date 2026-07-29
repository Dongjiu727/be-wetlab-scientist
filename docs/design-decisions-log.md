# 项目设计决策记录 / Design Decision Log

> **用途 / Purpose**: 这份文档记录项目架构演进过程中的每一个关键决策——为什么这样设计、考虑过哪些替代方案、为什么放弃它们。用于：(1) 面试/介绍时的话术练习 (2) README撰写素材 (3) 未来维护/迭代时回顾"当初为什么这么设计"，避免推倒重来。
>
> 格式参考业界的 **ADR (Architecture Decision Record)** 惯例。每次做重大设计决策，就在后面加一条，不要回头改旧记录——错误的决策也留着，标注"后续修正"，这本身就是成长轨迹的证据。

---

## 项目定位 / Project Positioning

**中文**：这是一个把十几年wet lab troubleshooting经验结构化、产品化的诊断工具，覆盖Western Blot和qPCR（未来可扩展到肿瘤免疫相关的其他湿实验），面向实验室学生和博后。核心差异化：市面上现有资源（Bio-Rad Western Blot Doctor、各厂商troubleshooting guide、westernblot.cc）都是静态的症状-原因对照表或用教学模拟图构建的决策树，不基于真实实验案例，也不是可编程/可扩展的工具。这个项目基于真实案例、支持交互式鉴别诊断、且用可复用决策子树的图结构组织知识库，避免了传统对照表的冗余。

**English**: This is a diagnostic tool that structures over a decade of hands-on wet-lab troubleshooting experience (Western Blot & qPCR, with tumor immunology as the primary application context) into an interactive assistant for graduate students and postdocs. Existing resources (vendor guides like Bio-Rad's Western Blot Doctor, or decision-tree sites built on teaching simulations) are either static symptom-cause tables or not grounded in real experimental cases. This project is differentiated by being (1) built from real, verified lab cases, (2) structured as an interactive diagnostic graph rather than a flat table, and (3) designed with reusable decision subtrees to keep the knowledge base maintainable as it scales.

**面试一句话电梯陈述 / Elevator pitch for interviews**:
> "I turned my own troubleshooting intuition — the mental checklist I run through every time a Western Blot fails — into a structured, queryable diagnostic tool, using a decision-graph architecture with reusable subtrees so the knowledge base scales without duplicating logic across symptoms."

---

## ADR-001: 单一Repo + 模块化多助手架构，而非每个assay一个repo

**问题 / Context**: 项目要发布到已有其他项目（单细胞分析学习项目）的GitHub账号上，且未来会扩展到多种实验类型（WB、qPCR，未来可能是流式细胞、IHC等）。

**决策 / Decision**: 用一个repo（`be-wetlab-scientist`），内部按模块组织（`app/modules/`, `knowledge_base/`），而不是每种实验类型单开一个repo。

**理由 / Rationale**: 保持GitHub主页整洁、可发现性好；核心诊断引擎（`engine/`）与具体案例数据（`knowledge_base/`）分离，未来加新assay类型只需加一个新数据文件+一个新UI模块，引擎代码不用改。

**面试话术 / Interview soundbite**: "I designed it as a single extensible framework rather than one-off scripts per assay — adding a new assay type means adding a data file and a thin UI module, not touching the core engine."

---

## ADR-002: 诊断逻辑用图结构（决策树+可复用子树），而非扁平表格

**问题 / Context**: 最初设想的"症状-猜测-鉴别问题-确认实验"表格，是扁平的一行一个原因。但实际排查时，"抗体排查""表达量检查"这类子流程会在多个不同症状之间重复出现（比如"完全无信号"和"信号弱"都需要走一遍抗体排查）。

**决策 / Decision**: 改用节点图（node graph）结构：每个诊断节点有唯一ID，case只需指定"入口节点"+ 自己独有的分支，通用子树（如`node_antibody_problem`）被多个case引用，不重复定义。

**理由 / Rationale**: 避免知识库随case数量增长而线性膨胀冗余内容；新case填写成本降低；共享节点的更新（比如厂商新出的一个抗体保存建议）只需改一处，所有引用它的case自动生效。

**面试话术 / Interview soundbite**: "Instead of a flat lookup table, I modeled the diagnostic logic as a graph with shared subtrees — common checks like antibody troubleshooting are defined once and referenced by every symptom that needs them, similar to how you'd factor out a shared function instead of copy-pasting code."

**修正记录（来自WB-002案例验证） / Correction (found while validating with WB-002)**: 填第二个案例（"信号弱"）时发现，`node_antibody_problem`不能是纯静态复用——同一套排查逻辑既要能用于目标蛋白抗体，也要能用于reference蛋白抗体（如GAPDH的一抗二抗也可能变质）。因此共享子树需要支持**参数化**（如 `node_antibody_problem(antibody_role: "reference" | "target")`），而不只是无参数的节点引用。这跟软件工程里"把函数写成带参数的可配置版本，而不是复制粘贴改一个变量名"是同一个道理，是个不错的类比可以在面试时用。

**面试话术补充 / Additional soundbite**: "When I validated the reusable-subtree design with a second case, I found the shared node needed a parameter — the antibody-troubleshooting subtree had to work for both the target antibody and the reference antibody. So I parameterized it rather than duplicating it, which is the same instinct as turning a copy-pasted function into one with an argument."

---

## ADR-003: 输入分两阶段——「既定事实清单」vs「需要新做实验的鉴别问题」

**问题 / Context**: 用户提到，像"是否设置了阳性/阴性对照""转膜后有没有做丽春红染色""上样量多少"这些问题，答案是用户已经知道的既定事实（做实验时留下的记录/图片），不需要重新做实验才能回答。而"提高一抗浓度后重复一次"这类问题，需要真正花时间做新实验才能得到答案。这两类问题混在一个线性问答流程里，会让用户体验很差（该一次性说完的信息被拆成来回跳转的多轮问答）。

**决策 / Decision**: 拆成两阶段——第一阶段是`intake_checklist`（一次性表单，问已知事实），第二阶段才是真正的`decision tree`（鉴别问题，可能需要新实验）。

**理由 / Rationale**: 更贴近真实诊断思维过程（先盘点已知信息排除一批可能性，再决定要不要做新实验）；减少用户来回点击的疲劳感；UI上可以用一次性表单（`st.form`）而不是逐题弹出。

**面试话术 / Interview soundbite**: "I separated 'facts the user already knows' from 'questions that require running a new experiment' — this mirrors how an expert actually troubleshoots: triage with existing evidence first, only recommend new bench work when necessary."

---

## ADR-004: 加入Routing Rules层——基于已知事实组合直接跳转诊断，而非逐题走决策树

**问题 / Context**: intake checklist收集完的信息，如果只是逐条走决策树来处理，效率不如"一眼看几个信息组合就能排除一半可能性"的专家思维。

**决策 / Decision**: 在intake checklist和decision tree之间加一层`routing_rules`——根据多个已知事实的组合，直接匹配/排除大类原因，只有信息不足以判断时才进入需要新实验的决策树细节。

**理由 / Rationale**: 更贴近专家的真实推理过程；减少不必要的鉴别问题（如果阳性对照也无信号，直接跳到抗体排查子树，不用再问转膜相关问题）。

**面试话术 / Interview soundbite**: "I added a rule-matching layer between the intake form and the decision tree, so the tool can immediately narrow down likely causes from a combination of known facts — the same shortcut an experienced scientist takes instead of asking every question in a strict sequence."

---

## ADR-005: 引入`experiment_context`层——assay级别的通用参数，与症状无关，贯穿全流程

**问题 / Context**: 用户提出：有没有可能在描述问题之后，直接让用户填一次上样量、转膜条件、目标蛋白大小、抗体信息等，这样不仅能帮助排除原因，还能让最后的优化建议更具体（比如"提高到40μg"而不是泛泛的"增加上样量"）。

**决策 / Decision**: 新增`experiment_context_schema`（每种assay类型定义一次，如WB的上样量/抗体信息/转膜方式/膜类型），在诊断会话开始时收集一次，同时输入给routing rules（用于排除）和最终输出模板（用于生成个性化建议文本）。

**理由 / Rationale**: 同一份数据两处复用，避免重复收集；输出建议从"通用建议"升级为"结合具体数值的可执行建议"，这是产品价值的核心提升点。

**面试话术 / Interview soundbite**: "The same experiment parameters feed two different consumers — the rule engine (for exclusion logic) and the output generator (for personalized, numeric recommendations) — so I modeled it as a single shared context object rather than collecting it twice."

---

## ADR-006: 必填字段 vs 可选字段的划分，及降级策略

**问题 / Context**: `experiment_context`表单如果全部必填，会提高使用门槛（尤其对赶时间的学生）；但字段太随意可选，又会影响诊断质量和建议的具体程度。

**决策 / Decision**: 关键字段（直接影响能否给出具体建议的，如目标蛋白分子量、上样量）设为必填；次要字段（如具体转膜buffer配方）设为可选，放在"展开更多"里。可选字段留空时，输出建议自动降级为通用建议，而不是报错阻断流程。

**理由 / Rationale**: 平衡"诊断质量"与"使用门槛"；graceful degradation（优雅降级）而非硬性报错，保证工具在信息不全时依然可用。

**面试话术 / Interview soundbite**: "I designed the form with required-vs-optional fields and a graceful-degradation fallback — missing optional data just means less specific advice, not a broken tool. This is a common pattern in production systems that I applied here deliberately."

---

## ADR-007: 知识来源分级与人机协作验证流程

**问题 / Context**: 用户自己的真实案例覆盖不了所有可能性（比如学生常犯的"低级错误"，专家凭记忆容易漏掉）。需要补充外部知识，但要避免直接抓取论坛内容（版权/可靠性风险，见此前讨论）。

**决策 / Decision**: 建立"AI搜索候选内容 → 呈现来源和可信度评估 → 人（领域专家）判断是否采纳"的协作流程。AI搜索时区分两类结果：(1) 单一叙事型案例（如论坛帖子里的具体故事，可信度需要人工核实）(2) 多个独立权威来源交叉验证的机制性知识（可信度天然更高，可作为checklist条目直接收录，附带`source_refs`标注来源类型而非具体案例)。知识库条目最终由人决定是否收录，AI不自动写入。

**理由 / Rationale**: 保持知识库的权威性和专家把关的核心价值，同时用AI覆盖专家个人经验的盲点（比如新手常见错误，专家自己不会犯所以容易忘记提及）。

**面试话术 / Interview soundbite**: "I used AI as a research assistant to surface candidate content and flag its confidence level based on source convergence — but a domain expert (myself) remains the gatekeeper for what actually enters the knowledge base. This kept the tool's core value (verified expertise) intact while still catching blind spots in my own experience."

**分层补充 / Refinement — 三级知识来源体系**:
1. **专家验证的真实案例**（最高权重）——你自己经历并确认过的case。
2. **多源交叉验证的机制性知识**（高权重）——多个独立权威来源（如不同厂商的troubleshooting指南）都一致提到的原因，可直接收录为checklist条目。
3. **社区/论坛的单一来源实操经验**（如丁香园上关于具体仪器、试剂品牌的使用心得）——这类内容信息密度高、覆盖官方指南没有的实操细节，但本质是单一个人经验，**只能作为"候选建议"呈现给专家复核，不能直接当作已验证事实收录**，且引用时只能转述要点、标注来源类型（"社区反馈"），不能逐字复制论坛原文（版权与可靠性考量）。

**面试话术补充 / Additional soundbite**: "I treat community forum knowledge as a distinct, lower-confidence tier — valuable for surfacing specific, practical details that vendor documentation never covers, but it's single-source anecdote rather than verified fact, so it always routes through human review before entering the knowledge base."

**可信度评估方法论 / Credibility assessment method（来自作者的实际判断流程）**: 面对论坛/社区里"可能是真的"但无法直接验证的说法，专家实际采用的判断路径是：(1) 对照自己已有的知识/经验是否合理 (2) 查阅文献或数据库交叉验证 (3) 找同行/PI讨论 (4) 如果以上都不能确定，设计一个成本较低的确认性小实验去实际测试这个假说是否成立。这个判断流程本身值得沉淀为文档（如`CONTRIBUTING.md`里的"内容评审标准"），因为项目未来计划邀请其他资深实验人员共同补充知识库，这套标准就是协作时的内容审核准则，不只是作者一个人用。

---

## ADR-008: 双支柱产品结构——反应式诊断 + 预防式设计指南

**问题 / Context**: 最初设计只考虑"实验已经失败，帮用户排查原因"（反应式）。但用户指出，很多有价值的经验（引物设计原则、对照/重复设计规范、reference gene稀释策略、ΔCt计算方法）本质是"预防性最佳实践"，不属于"排除症状原因"的决策树逻辑，如果硬塞进决策树会让结构混乱，但完全不放又会丢失这部分经验的价值。

**决策 / Decision**: 产品设为两个平级入口——「实验出问题了」（走交互式诊断决策树）和「准备设计新实验」（查阅按assay类型+设计阶段组织的结构化最佳实践checklist，非交互式决策树，是可浏览的参考文档）。两者共享同一个repo和知识库目录，只是内容组织形式不同。

**理由 / Rationale**: 决策树适合"症状→排除原因"这种条件分支推理；实验设计知识是"一次性讲清楚原则，用户自行套用"，更适合结构化文档形式，强行做成交互问答反而繁琐。两个模块并列，产品价值从"救火"扩展到"预防"，覆盖用户完整的实验生命周期。

**面试话术 / Interview soundbite**: "I realized troubleshooting and experiment design are different knowledge shapes — one is conditional branching logic, the other is a checklist of principles you apply upfront. Rather than forcing both into the same decision-tree format, I gave them equal billing as two entry points sharing the same knowledge base, so the tool covers the full experiment lifecycle, not just the failure recovery part."

**衔接模式补充 / Bridging pattern**: 两个模块不是完全割裂的——决策树里保留轻量的"闸门节点"（如"这条引物是否做过设计验证？"），只做是/否判断来指明问题方向；具体"怎么验证"的详细步骤只在设计指南里写一份，避免同一内容在两个模块里重复维护。闸门节点回答"否"时，直接引用设计指南对应章节作为confirm_experiment的内容。

---

## 待办 / Next Steps（持续更新区）

- [ ] 用WB「信号弱」案例验证 ADR-002 的子树复用设计是否真的成立（`node_antibody_problem`、`check_expression_level` 能否直接复用，只新增1-2个独有节点）
- [ ] 用qPCR案例验证跨assay的schema设计是否通用，还是需要为qPCR单独设计一套结构
- [ ] 补充：如果intake信息与routing rule冲突（如用户提到的"丽春红有条带但考马斯显示胶上有残留"矛盾信号）如何处理——目前只是提示"需要复核"，后续要不要做得更细？

---

## 英语自我介绍练习稿 / English Self-Intro Draft (for interview practice)

> "During my PhD/postdoc, I spent years troubleshooting Western Blots and qPCR experiments — and I noticed that expert troubleshooting is really just a decision tree that lives in an experienced scientist's head. So I built a tool that externalizes that reasoning: users answer a short intake form about their experiment and symptoms, the tool runs that through a rule-matching layer to narrow down likely causes, and if it's still ambiguous, walks them through differential questions — the same way I would if a student came to my bench with a bad blot. The interesting engineering problem was making the knowledge base scale: instead of one giant lookup table, I structured it as a graph with reusable subtrees, so common checks like antibody troubleshooting aren't duplicated across every symptom that needs them."

（这段可以直接背，或者根据面试官追问调整细节，比如被问到"为什么不用表格"时，直接引用上面ADR-002的话术。）

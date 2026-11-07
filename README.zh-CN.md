# gstack-codex-auto

[English](README.md) | **简体中文** · [验证记录](docs/validation.md) · [安全边界](SECURITY.md)

v0.1.1 完成了[两轮对抗检查](docs/adversarial-review.md)，修复恢复、提交一致性、进程清理和发布边界问题。

把产品需求交给 **Codex CLI**，自动串联规划、质疑、实现、审查、QA、修复、文档和候选选择，输出可审阅的 Git 分支。参考 [gstack-auto](https://github.com/loperanger7/gstack-auto) 的流程设计，使用独立编写的 Python 控制器，不依赖 Claude 运行时。

**当前是实验性 v0.1.1。** 控制器离线测试和模拟 CLI 集成测试已覆盖主要流程；发布准备时的真实 Codex 请求返回 HTTP 401。因此尚未完成真实模型的全流程验收，不能把离线测试当成真实项目成功率的证据。

## 能做什么

- 13 个阶段角色：CEO 规划 → 质疑 → 工程规划 → 质疑 → 设计规划 → 质疑 → 统合方案 → 质疑 → 实现 → 文档 → 审查与 QA → 评分。阶段编号兼容概念顺序，文档实际在最终审查、QA 和测试之前执行。
- 每阶段启动独立 Codex 会话；每个候选使用独立 Git worktree。支持多个候选并行、多轮迭代，下一轮从上一轮胜出的提交继续。
- 审查、QA 和配置的客观测试命令必须全部通过，才有资格参与评分选优；失败会进入有次数限制的修复循环。
- 支持断点续跑、调用次数预算、超时、STOP 文件、结构化报告和产物完整性检查。
- 默认读取本机安装的 gstack Codex skills；缺失时明确报错。显式选择 `builtin` 才会使用本项目的基础角色说明。
- `publish` 命令可推送最终候选并创建 GitHub 草稿 PR，不会自动合并或部署。

范围是开发主流程。v0.1.1 不包含交互式需求访谈、Web 控制台、邮件通知、生产部署，也不声称遍历 gstack 的全部辅助技能。同一 Codex 模型的新会话不等于跨模型独立审查；评分选优也不等于训练模型。

## 安装

需要 Python 3.11+、Git、已安装且能正常调用的 Codex CLI，以及 Linux、macOS 或 WSL。原生 Windows 暂不支持。发布 PR 额外需要 GitHub CLI。Python 包没有运行时第三方依赖。

```bash
pipx install 'git+https://github.com/f-tiger/gstack-codex-auto.git@v0.1.1'
gstack-codex-auto --help
```

如果没有 pipx，可以按 [英文 README](README.md#install) 使用虚拟环境。默认 gstack 模式需要先按[上游文档](https://github.com/garrytan/gstack)执行 `./setup --host codex`。本项目不附带上游 skills 或二进制文件。

## 使用

在已有 Git 项目中编写 `SPEC.md`，写清楚目标、验收条件、限制和必须验证的实际行为，再创建 `gca.json`：

```json
{
  "repo": ".",
  "spec": "SPEC.md",
  "skill_mode": "gstack",
  "candidates": 2,
  "parallel": 2,
  "rounds": 1,
  "max_fixes": 2,
  "max_calls": 60,
  "timeout": 1200,
  "gate_timeout": 300,
  "gates": [["npm", "test", "--", "--runInBand"]]
}
```

把 `gates` 换成该项目真实的测试命令。不能填入一条恒成功命令后把结果当成有效验收。配置中的命令必须使用参数数组，不会进行 shell 展开。

提交或暂存当前修改，确保源码仓库干净且至少有一个提交；然后运行：

```bash
gstack-codex-auto doctor --config gca.json
gstack-codex-auto plan --config gca.json
gstack-codex-auto run --config gca.json --run-dir ../gca-runs/feature-001
gstack-codex-auto report ../gca-runs/feature-001
```

运行目录必须是源码仓库外的新目录。`doctor` 不调用模型，不能证明登录、浏览器或模型服务可用。一个无修复的候选需要 13 次 Codex 调用；`max_calls` 是所有轮次和候选共享的调用次数上限，不是 token 或金额上限。

Git worktree 不会复制 `.venv`、`node_modules` 等被忽略的依赖目录。请预先准备可复用的外部环境或缓存；控制器不自动安装依赖。测试命令不能修改源码，生成物应被 Git 忽略。默认规划、审查、QA 和评分使用只读沙箱，写代码和修复使用工作区写权限。必须依赖浏览器等证据但当前环境无法提供时，应阻塞并说明原因。

```bash
gstack-codex-auto resume ../gca-runs/feature-001
touch ../gca-runs/feature-001/STOP
```

STOP 在下一阶段/检查边界生效，不会立即中止正在执行的子进程。移除 STOP 后可以继续。调用预算不会因续跑而重置。中断的写入阶段可能保留部分修改，续跑会看到这些内容；请勿手动修改进行中或中断的候选工作区。

Ctrl+C 会向活动的 Codex/测试进程传递取消信号。命令结束后会清理其原进程组，持久运行的服务应在外部单独启动。中断后的 HEAD/分支必须保持不变；控制器提交过程中断可能需要新建运行。v0.1.1 使用第 2 版检查点，不自动兼容旧运行目录。不支持子模块、稀疏检出或隐藏文件变化的 Git 索引标记。

审阅结果后，可以显式发布草稿 PR：

```bash
gstack-codex-auto publish ../gca-runs/feature-001 \
  --github-repo OWNER/REPO --base main --title "实现需求"
```

目标必须匹配源码仓库的 `origin`，最终候选分支必须仍指向已验证的提交。发布前检查生成的内容是否包含秘密，并在 PR 中重新运行 CI。

发布还会核对全部实际推送地址，获取运行锁并重新校验审查、QA、评分和测试记录。请保留候选工作区及产物直到发布完成。所有控制器发起的 Git 操作均禁用 hooks，推送不会隐式附带标签。

## 边界与验证

worktree 分离代码修改，但不提供安全隔离；配置的测试命令由当前系统用户直接执行。只用于可信仓库和可信测试命令。模型评分是判断，不是质量证明；测试覆盖不足仍会漏掉问题。

运行目录包含私有代码、提示和日志，默认权限为 `0700`，不应公开上传。顶层 skill 文件会记录哈希，但它们引用的文档、二进制和主机配置不会被完整冻结。上游 gstack 在 Codex 上的兼容性也会随版本变化。

完整参数、断点恢复和权限边界见 [README](README.md)、[SECURITY.md](SECURITY.md)；离线测试方法见 [CONTRIBUTING.md](CONTRIBUTING.md)。

本项目原创代码采用 MIT 协议。流程灵感归功于 gstack-auto 和 gstack；未复制或重新分发它们的源码、提示文件或二进制。本项目不是 OpenAI 或 gstack 官方版本。

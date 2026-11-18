# 监管通告条款与内部义务适用确认

本地文本工作区用于保存义务与期限抽取相关的合成记录，并提供基础规范化和词项查看能力。

## 环境

需要 Python 3.11 或更新版本。运行程序仅使用 Python 标准库。测试依赖固定为 pytest 8.3.4，可执行 `python -m pip install -r requirements-dev.txt` 安装。

## 运行

运行 `PYTHONPATH=src python -m nlp_regulatory_obligation_tracker.desk_cli` 按正式通告的已登记条款核查申报材料。受理日期取受理处签发回执；培训材料和征求意见稿可查看，但不参与正式办理。

从项目根目录执行 `PYTHONPATH=src python -m nlp_regulatory_obligation_tracker.cli ingest fixtures/records.json` 导入样例，随后执行 `PYTHONPATH=src python -m nlp_regulatory_obligation_tracker.cli list` 查看记录。工作数据写入 `var/records.json`。业务查询使用 fixtures/business.json 中的初始资料，约定见 fixtures/business-contract.md。执行 PYTHONPATH=src python -m nlp_regulatory_obligation_tracker.cli business 可查看当前业务目录结果。

样例为本地合成文本。记录包含来源、修订号和原文，当前工作区对空白做统一处理，并提供字符及英文词项切分。

## 测试

执行 `python -m pytest -q` 检查规范化、记录持久化和来源筛选。

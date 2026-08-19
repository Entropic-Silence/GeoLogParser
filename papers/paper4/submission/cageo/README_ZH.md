# Paper 4 中文导师审阅稿

中文稿文件：

- manuscript_zh.md：中文 Markdown 正文，供修改和批注。
- manuscript_zh.html：Pandoc 生成的单文件 HTML，已内嵌四张图，可直接在浏览器打开。
- manuscript_zh.pdf：由单文件 HTML 打印生成的中文审阅 PDF，共 14 页。

本稿由 papers/paper4/manuscript.md 转换而来，不覆盖英文科学 source-of-truth。模型名称、代码标识、引用键、公式和冻结数值保留原形式，以便与证据包逐项核对。正式投稿仍以英文 C&G 稿件、官方要求和作者最终声明为准。

生成 HTML 的命令：

    pandoc manuscript_zh.md --from markdown+tex_math_dollars+raw_tex --to html5 --standalone --embed-resources --resource-path ..\.. -o manuscript_zh.html

PDF 使用 Microsoft Edge 的无头打印从 manuscript_zh.html 生成，仅供导师审阅。

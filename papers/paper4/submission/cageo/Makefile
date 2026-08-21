SHELL := powershell.exe

.PHONY: review clean

review:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File build.ps1

clean:
	Get-ChildItem -LiteralPath . -File -Include body_pandoc.tex,manuscript.aux,manuscript.bbl,manuscript.blg,manuscript.fdb_latexmk,manuscript.fls,manuscript.synctex.gz,manuscript.toc | Remove-Item -Force -ErrorAction SilentlyContinue

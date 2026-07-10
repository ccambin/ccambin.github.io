# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: onedir 모드 (1GB 모델을 onefile로 묶으면 실행 시마다
# 임시폴더에 풀어야 해서 시작이 매우 느려짐)
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

PROJ = os.path.abspath(os.path.join(SPECPATH, '..'))

llama_datas, llama_binaries, llama_hidden = collect_all('llama_cpp')

datas = [
    (os.path.join(PROJ, 'templates'), 'templates'),
    (os.path.join(PROJ, 'models'), 'models'),
]
datas += collect_data_files('jieba')
datas += collect_data_files('pypinyin')
datas += llama_datas

a = Analysis(
    [os.path.join(PROJ, 'app.py')],
    pathex=[PROJ],
    binaries=llama_binaries,
    datas=datas,
    hiddenimports=['jieba', 'pypinyin', 'openpyxl'] + llama_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'pandas', 'scipy', 'PIL'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChineseMailVocab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ChineseMailVocab',
)

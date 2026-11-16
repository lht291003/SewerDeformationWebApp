import os as OS, sys as Sys, streamlit as App

Sys.dont_write_bytecode = True

Path = OS.path.join(OS.path.dirname(OS.path.abspath(__file__)), "WebApp.py")

if OS.path.exists(Path):
    WebProgram = App.App(Path)
    if __name__ == "__main__":
        WebProgram.run()
else:
    print(f"Không thể khởi chạy, vui lòng kiểm tra lại đường dẫn tới dự án")
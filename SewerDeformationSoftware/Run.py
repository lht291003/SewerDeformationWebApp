import os, sys, subprocess

def GetCommand(Filename):
    AppPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), Filename)
    if not os.path.exists(AppPath):
        print(f"Không thể chạy {Filename}, vui lòng kiểm tra lại tên ứng dụng")
        sys.exit(0)
    AppStartCommand = [sys.executable, "-B", "-m", "streamlit", "run", AppPath]

    return AppStartCommand

if __name__ == "__main__":
    subprocess.run(GetCommand("WebApp.py"), check=True)
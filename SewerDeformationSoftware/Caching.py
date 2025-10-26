from Library import App, Torch, Hashlib, OS, YOLO

@App.cache_resource(show_spinner=False)
def BuildModel(Content, Extension, Dir):
    if Extension.upper() == ".ENGINE" and not Torch.cuda.is_available():
        App.toast("TensorRT chỉ chạy trên phần cứng NVIDIA", icon="❌")
        return None
    ModelName = f"{Hashlib.md5(Content).hexdigest().upper()}"
    ModelPath = OS.path.join(Dir, f"{ModelName}{Extension}")
    with open(ModelPath, "wb") as Fl:
        Fl.write(Content)
    NewM = YOLO(ModelPath, "segment")
    GetSample = (1, 3, 640, 640)
    NewM(Torch.zeros(GetSample))
    return NewM
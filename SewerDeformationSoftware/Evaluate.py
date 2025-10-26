from Library import OS, Shutil, Zip, CV2, NP, App, DataFrame
from Analysis import GetIoU

def SaveFiles(Dir, Datas):
    Only = {File.name: File for File in Datas}
    ZipsQueue = []
    for DataName, Data in Only.items():
        GetPath = OS.path.join(Dir, DataName)
        with open(GetPath, "wb") as F:
            F.write(Data.getbuffer())
        if Data.name.upper().endswith(".ZIP"):
            ZipsQueue.append(GetPath)
    while ZipsQueue:
        GetZipPath = ZipsQueue.pop(0)
        ZipDir, _ = OS.path.splitext(GetZipPath)
        with Zip.ZipFile(GetZipPath, "r") as ZF:
            ZF.extractall(ZipDir)
        for (Root, _, Files) in OS.walk(ZipDir):
            for File in Files:
                if File.upper().endswith(".ZIP"):
                    ZipsQueue.append(OS.path.join(Root, File))
        OS.remove(GetZipPath)
    return sum(len(Files) for Root, _, Files in OS.walk(Dir))

def VisualDatas(ImagePaths, LabelPaths, ISet, USet, NumFile):
    with App.expander("Thông tin về dữ liệu", expanded=True):
        C1, C2, C3 = App.columns(3)
        C1.metric("Tổng số tệp tin đã tải lên", NumFile, border=True)
        C2.metric("Tổng số cặp [Ảnh - Nhãn]", len(ISet), border=True)
        C3.metric("Tệp khác", (NumFile - len(ISet) * 2), border=True)
        DataTable = []
        for Name in USet: DataTable.append({
                "Name": Name,
                "Image": Name in ImagePaths,
                "Label": Name in LabelPaths,
        })    
        App.dataframe(
            DataTable, column_config={
                "Name": App.column_config.TextColumn("Tên đối tượng"),
                "Image": App.column_config.CheckboxColumn("Hình ảnh"),
                "Label": App.column_config.CheckboxColumn("Nhãn TXT"),
            }
        )

def IoUAtThresholds(IoUList, Name):
    IoUResultDict = {"Name": Name}
    Total = len(IoUList)
    Thresholds = {
        "IoU90": 0.90, "IoU93": 0.93,
        "IoU95": 0.95, "IoU98": 0.98,
    }
    for Name, Threshold in Thresholds.items():
        Count = sum(IoU >= Threshold for IoU in IoUList)
        IoUResultDict.update({Name: f"{Count}/{Total}"})
    return IoUResultDict

def VisualIoUEvals(ResultList):
    with App.expander("Đánh giá và so sánh hiệu suất", expanded=True):
        C1, C2 = App.columns(2)
        YSModelIoUs = [I["YSModel"] for I in ResultList]
        SEModelIoUs = [I["SEModel"] for I in ResultList]
        YSMLabel = "Mô hình ban đầu"
        SEMLabel = "Mô hình so sánh"
        GetNumItem = len(ResultList)
        AvgYSModel = sum(YSModelIoUs) / GetNumItem
        AvgSEModel = sum(SEModelIoUs) / GetNumItem
        C1.metric(YSMLabel, f"Avg IoU: {AvgYSModel:.4f}", border=True)
        C2.metric(SEMLabel, f"Avg IoU: {AvgSEModel:.4f}", border=True)
        App.dataframe([
            IoUAtThresholds(YSModelIoUs, YSMLabel),
            IoUAtThresholds(SEModelIoUs, SEMLabel),
        ])
        StylerList = DataFrame(ResultList).style.highlight_max(["YSModel", "SEModel"], "#EC6A2C", 1)
        App.dataframe(
            StylerList, column_order=("Name", "YSModel", "SEModel"),
            column_config={
                "Name": App.column_config.TextColumn("Tên dữ liệu"),
                "YSModel": App.column_config.NumberColumn(YSMLabel),
                "SEModel": App.column_config.NumberColumn(SEMLabel),
            }
        )

def CreateBinaryMaskFromTXTLabel(Name, ImagePath, LabelPath, MaskDir):
    ImgSize = CV2.imread(ImagePath).shape[:2]
    Height, Width = ImgSize
    CreateMask = NP.zeros(ImgSize, NP.uint8)
    with open(LabelPath, "r") as File:
        GetTXTLines = File.readlines()
        for Line in GetTXTLines:
            Parts = Line.strip().split()[1:]
            Crds = [float(C) for C in Parts]
            Points = []
            for I in range(0, len(Crds), 2):
                Points.append([Crds[I] * Width, Crds[I + 1] * Height])
            Points = NP.array([Points], NP.int32)
            CV2.fillPoly(CreateMask, Points, 255)
    BMPath = OS.path.join(MaskDir, f"{Name}.PNG")
    CV2.imwrite(BMPath, CreateMask)
    OS.remove(LabelPath)

def ShowException(Error):
    App.exception(Error)
    App.stop()

def ValidImage(ImagePath):
    GetBaseName = OS.path.basename(ImagePath)
    if CV2.imread(ImagePath) is None:
        ShowException(ValueError(f"Tệp '{GetBaseName}' không phải là một hình ảnh hợp lệ hoặc đã bị hỏng"))

def ValidLabel(LabelPath):
    GetBaseName = OS.path.basename(LabelPath)
    with open(LabelPath, "r") as File:
        GetTXTLines = File.readlines()
        if not GetTXTLines:
            ShowException(ValueError(f"Không tìm thấy bất kỳ dòng chú thích nào trong tệp {GetBaseName}"))
        for I, Line in enumerate(GetTXTLines):
            Nums = Line.strip()
            Nums = Nums.split()
            if len(Nums) < 7:
                ShowException(ValueError(f"Tệp {GetBaseName}(Dòng {I+1}): Không có đủ phần tử tối thiểu"))
            GetClassID = Nums[0]
            if not GetClassID.isdigit():
                ShowException(ValueError(f"Tệp {GetBaseName}(Dòng {I+1}): ID phải là số nguyên không âm"))
            if (len(Nums) - 1) % 2 != 0:
                ShowException(ValueError(f"Tệp {GetBaseName}(Dòng {I+1}): Số các tọa độ phải là số chẵn"))
            for Num in Nums[1:]:
                if not Num.replace('.', '', 1).replace('-', '', 1).isdigit():
                    ShowException(ValueError(f"Tệp {GetBaseName}(Dòng {I+1}): Chứa giá trị '{Num}' không phải một số thực hợp lệ"))
                Crd = float(Num)
                if not 0.0 <= Crd <= 1.0:
                    ShowException(ValueError(f"Tệp {GetBaseName}(Dòng {I+1}): Chứa giá trị '{Crd}' nằm ngoài phạm vi 0 <= X <= 1"))

def CreateDirectoryTree(Dir):
    TempDir = OS.path.join(Dir, "Temp")
    EvalDir = OS.path.join(Dir, "Eval")
    ImageDir = OS.path.join(EvalDir, "Images")
    BMaskDir = OS.path.join(EvalDir, "BMasks")
    for Path in (EvalDir, TempDir):
        if OS.path.exists(Path):
            Shutil.rmtree(Path)
        OS.makedirs(Path)
    OS.makedirs(ImageDir)
    OS.makedirs(BMaskDir)
    return EvalDir, ImageDir, BMaskDir, TempDir

def ExploreFiles(Dir, ImgExts):
    ImgPaths = {}
    TXTPaths = {}
    ImgExts = [E.upper() for E in ImgExts]
    for Root, Dirs, Files in OS.walk(Dir):
        for File in Files:
            Base, Ext = OS.path.splitext(File)
            Ext = Ext.upper().replace(".", "")
            if Ext in ImgExts:
                ImgPaths[Base] = OS.path.join(Root, File)
            elif Ext == "TXT":
                TXTPaths[Base] = OS.path.join(Root, File)
    return ImgPaths, TXTPaths

def IsPNGAndMove(ImagePath, Dest, ImageExt):
    Base, Ext = OS.path.splitext(ImagePath)
    if Ext.upper() != ImageExt.upper():
        NewImagePath = Base + ImageExt
        CV2.imwrite(NewImagePath, CV2.imread(ImagePath))
        OS.remove(ImagePath)
        ImagePath = NewImagePath
    Shutil.move(ImagePath, Dest)

def ProcessPairs(ImagePaths, LabelPaths, ImageDir, MaskDir, Names):
    for Name in Names:
        ValidImage(ImagePaths[Name])
        ValidLabel(LabelPaths[Name])
        ImagePath = ImagePaths[Name]
        LabelPath = LabelPaths[Name]
        OnlyImgName = OS.path.basename(ImagePath)
        Dst = OS.path.join(ImageDir, OnlyImgName)
        IsPNGAndMove(ImagePath, Dst, ".PNG")
        CreateBinaryMaskFromTXTLabel(Name, Dst, LabelPath, MaskDir)

def PrepareDatas(Datas, Types, Dir):
    EvalDir, ImageDir, BMaskDir, TempDir = CreateDirectoryTree(Dir)
    Sum = SaveFiles(TempDir, Datas)
    ImageExtensions = [T for T in Types if T not in ["ZIP", "TXT"]]
    ImagePaths, LabelPaths = ExploreFiles(TempDir, ImageExtensions)
    IList = sorted(set(ImagePaths.keys()) & set(LabelPaths.keys()))
    UList = sorted(set(ImagePaths.keys()) | set(LabelPaths.keys()))
    ProcessPairs(ImagePaths, LabelPaths, ImageDir, BMaskDir, IList)
    Shutil.rmtree(TempDir)
    VisualDatas(ImagePaths, LabelPaths, IList, UList, Sum)
    return (ImageDir, BMaskDir) if len(IList) > 0 else (None, None)

def EvaluateModels(ImageDir, BMaskDir, YSModel, SeModel):
    DictYModel = {"YSModel": YSModel, "SEModel": SeModel}.items()
    ImageList = sorted([Image for Image in OS.listdir(ImageDir)])
    BMaskList = sorted([Image for Image in OS.listdir(BMaskDir)])
    ImageDataDict = {}
    IoUResultList = []
    for (Image, BMask) in zip(ImageList, BMaskList):
        GetImagePath = OS.path.join(ImageDir, Image)
        GetBMaskPath = OS.path.join(BMaskDir, BMask)
        LoadBMask = (CV2.imread(GetBMaskPath, CV2.IMREAD_GRAYSCALE) // 255).astype(NP.uint8)
        LoadImage = CV2.imread(GetImagePath)
        Base, Tail = OS.path.splitext(Image)
        ImageDataDict[Base] = [LoadImage, LoadBMask]
    ImageDataDict = ImageDataDict.items()
    for ObjectName, (Image, BMask) in ImageDataDict:
        Row = {}
        for Key, Model in DictYModel:
            Result = Model(Image)[0]
            if Result.masks is None:
                YOLOSegBMask = NP.zeros_like(BMask)
            else:
                YOLOSegBMask = (Result.masks.data[0].cpu().numpy() * 255).astype(NP.uint8)
            Row[Key] = GetIoU(YOLOSegBMask, BMask)
        Row["Name"] = ObjectName
        IoUResultList.append(Row)
    VisualIoUEvals(IoUResultList)
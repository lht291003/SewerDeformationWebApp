from Analysis import AnalyzePicture, ComparePictures, ShowMask
from Library import App, Temp, Shutil, PDF, OS, CV2 
from Caching import BuildModel
from Export import GetResults
from Visualize import ShowVisuals
from Evaluate import PrepareDatas, EvaluateModels

App.set_page_config("Pipes Inspection", "Assets/PIIcon.ico")
App.title("DỰ ĐOÁN BIẾN DẠNG HÌNH HỌC TIẾT DIỆN ĐƯỜNG CỐNG")
if "WorkDir" not in App.session_state:
    Work = OS.path.join(Temp.gettempdir(), "StreamlitSewer")
    if OS.path.exists(Work):
        Shutil.rmtree(Work)
    App.session_state['YSModel'] = None
    App.session_state['SeModel'] = None
    App.session_state['WorkDir'] = Work
    OS.makedirs(App.session_state['WorkDir'])
    App.session_state['VideoSegLog'] = list()
ConfTab, EvalTab, PhotoTab, VideoTab, InfoTab = App.tabs(["CẤU HÌNH MÔ HÌNH", "ĐÁNH GIÁ VÀ SO SÁNH MÔ HÌNH", "PHÂN TÍCH HÌNH ẢNH", "PHÂN TÍCH VIDEO", "THÔNG TIN DỰ ÁN"])
with ConfTab:
    LoadModelFile = App.file_uploader("Tải lên mô hình YOLO", ["PT", "ONNX", "ENGINE"])
    if LoadModelFile is not None:
        BuildingButton = App.button("Xác nhận xây dựng mô hình YOLO", width="stretch")
        if BuildingButton:
            (Basename, Tail), Data = OS.path.splitext(LoadModelFile.name), LoadModelFile.read()
            App.session_state['YSModel'] = BuildModel(Data, Tail, App.session_state['WorkDir'])
with PhotoTab:
    UploadedPicture = App.empty()
    LoadPhotoFile = App.file_uploader("Tải ảnh lên:", ["PNG", "JPG", "WEBP", "JPEG"])
    if LoadPhotoFile is not None:
        GetPhotoPath = OS.path.join(App.session_state['WorkDir'], LoadPhotoFile.name)
        with open(GetPhotoPath, "wb") as PicFile: PicFile.write(LoadPhotoFile.read())
        UploadedPicture.image(GetPhotoPath, width="stretch")
        SegButton = App.button("Phân Đoạn", width="stretch")
        if SegButton:
            if App.session_state['YSModel'] is not None:
                Result = App.session_state['YSModel'](GetPhotoPath)[0]
                (PlotImage, MaskImage, Ellipse), GetResult = AnalyzePicture(Result)
                MaskImage = ShowMask(MaskImage, Ellipse, GetResult.get("Shape")[0])
                App.header("PHÂN ĐOẠN HÌNH ẢNH", divider=True)
                App.image(PlotImage, "Ảnh phân đoạn", width="stretch")
                App.header("PHÂN TÍCH HÌNH ẢNH", divider=True)
                App.image(MaskImage, "Mặt nạ đầu ra", width="stretch")
                App.table(GetResult)
with VideoTab:
    LoadVideoFile = App.file_uploader("Tải video lên:", ["MP4", "MOV", "AVI", "WMV"])
    if LoadVideoFile is not None:
        GetVideoPath = OS.path.join(App.session_state['WorkDir'], LoadVideoFile.name)
        with open(GetVideoPath, "wb") as VidFile: VidFile.write(LoadVideoFile.read())
        FmSpacing = App.slider("Khoảng cách hai khung hình", value=30, max_value=100)
        SegButton = App.button("Chạy phân đoạn", width="stretch")
        if SegButton:
            App.header("PHÂN TÍCH VIDEO TRỰC QUAN", divider=True)
            with App.expander("Dự đoán với khung hình hiện tại"):
                L1, R1 = App.columns(2)
                L1NowFrame = L1.empty()
                R1NowFrame = R1.empty()
                ParamTbl1 = App.empty()
            with App.expander("So sánh với khung hình trước đó"):
                L2, R2 = App.columns(2)
                L2NowFrame = L2.empty()
                R2PreFrame = R2.empty()
                ParamTbl2 = App.empty()
            Count = 0
            if App.session_state['YSModel'] is not None:
                Capture = CV2.VideoCapture(GetVideoPath)
                App.session_state['VideoSegLog'].clear()
                while Capture.isOpened():
                    (CanRead, Frame) = Capture.read()
                    if not CanRead: break
                    Result = App.session_state['YSModel'](Frame)[0]
                    GetImgLikes, GetResult = AnalyzePicture(Result)
                    Plot, Mask, Ellipse = GetImgLikes
                    Count += 1
                    Record = {
                        "AspectRatio": GetResult["AspectRatio"][0],
                        "Orientation": GetResult["Orientation"][0],
                        "Deformation": GetResult["Deformation"][0],
                        "Plot": Plot,
                        "Mask": Mask,
                        "Shape": GetResult["Shape"][0]
                    }
                    Draw = ShowMask(Mask, Ellipse, Record["Shape"])
                    Record["Draw"] = Draw
                    App.session_state['VideoSegLog'].append(Record)
                    L1NowFrame.image(Plot, "Ảnh phân đoạn", width="stretch")
                    R1NowFrame.image(Draw, "Mặt nạ đầu ra", width="stretch")
                    ParamTbl1.table(GetResult)
                    if not Count <= FmSpacing:
                        PreFrm = App.session_state['VideoSegLog'][Count - FmSpacing - 1]
                        Prev = PreFrm["Plot"]
                        L2NowFrame.image(Prev, "Ảnh phân đoạn trước đó", width="stretch")
                        R2PreFrame.image(Plot, "Ảnh phân đoạn hiện tại", width="stretch")
                        ParamTbl2.table(ComparePictures(PreFrm, App.session_state['VideoSegLog'][-1]))
                Capture.release()
                App.header("TRỰC QUAN DỮ LIỆU", divider=True)
                ShowVisuals(App.session_state['VideoSegLog'])
                App.header("NHẬT KÝ PHÂN ĐOẠN", divider=True)
                with App.spinner("Đang xử lý tập tin"):
                    GetZFile = GetResults(App.session_state['VideoSegLog'])
                Label = "⬇️ Lưu kết quả"
                Mime = "Application/Zip"
                Filename = "Results.zip"
                Save = App.download_button(Label, GetZFile, Filename, Mime)
            else:
                App.toast("Mô hình phân đoạn chưa được tải lên", icon="❌")
with EvalTab:
    Types = ["ZIP", "TXT", "PNG", "JPG", "WEBP", "JPEG"]
    LoadFiles = App.file_uploader("Tải lên dữ liệu đánh giá", Types, True)
    if len(LoadFiles) >= 1:
        InfoSeModelFile = "Tải thêm mô hình YOLO khác để so sánh hiệu suất"
        LoadSeModelFile = App.file_uploader(InfoSeModelFile, ["PT", "ONNX", "ENGINE"])
        if LoadSeModelFile is not None:
            EvalButton = App.button("Đánh giá và so sánh", width="stretch")
            if EvalButton:
                if App.session_state['YSModel'] is not None:
                    (Tail, Data) = OS.path.splitext(LoadSeModelFile.name)[1], LoadSeModelFile.read()
                    LoadSeModel = BuildModel(Data, Tail, App.session_state['WorkDir'])
                    App.session_state['SeModel'] = LoadSeModel
                    ImageDir, MaskDir = PrepareDatas(LoadFiles, Types, App.session_state['WorkDir'])
                    if ImageDir and MaskDir:
                        YSModel = App.session_state['YSModel']
                        SeModel = App.session_state['SeModel']
                        EvaluateModels(ImageDir, MaskDir, YSModel, SeModel)
                    else:
                        App.toast("Không tìm thấy cặp ảnh và nhãn TXT nào để thực hiện", icon="❌")
                else:
                    App.toast("Mô hình YOLO-Seg ban đầu hiện tại vẫn chưa được tải lên", icon="❌")
with InfoTab:
    C1, C2 = App.columns(2)
    with C1:
        ShowPDF1 = App.button("Thông tin chung", width="stretch")
    with C2:
        ShowPDF2 = App.button("Thông tin dự án", width="stretch")
    if ShowPDF1:
        PDF("Assets/Doc1.pdf", pages_vertical_spacing=10, render_text=True)
    if ShowPDF2:
        PDF("Assets/Doc2.pdf", pages_vertical_spacing=10, render_text=True)
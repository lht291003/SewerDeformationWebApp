from Library import Image, ImageIO, NP, CV2, Zip, XLImage, BIO, Workbook, Alignment, Table, TableStyleInfo
from Analysis import Conclude
from Visualize import SpChart, DEChart

def GetVideo(Data, PadBot=40, PadColor=(0, 0, 0), TxtColor=(255, 255, 255), Scale=1, Thick=2):
    def AddCaption2Frame(Img, Caption):
        Font = CV2.FONT_HERSHEY_SIMPLEX
        Size = CV2.getTextSize(Caption, Font, Scale, Thick)[0]
        GetPaddedImg = CV2.copyMakeBorder(Img, 0, PadBot, 0, 0, CV2.BORDER_CONSTANT, PadColor)
        Coord = (GetPaddedImg.shape[1] - Size[0]) // 2, Img.shape[0] + (PadBot + Size[1]) // 2
        (X, Y) = Coord
        CV2.putText(GetPaddedImg, Caption, (X, Y), Font, Scale, TxtColor, Thick, CV2.LINE_AA)
        return GetPaddedImg
    VideoBuffer = BIO()
    StandardSize = None
    VideoWriter = ImageIO.get_writer(VideoBuffer, "MP4", fps=3)
    for OrdNum, Dict in enumerate(Data, 1):
        PlotImg = Dict["Plot"]
        MaskImg = Dict["Draw"]
        if PlotImg.ndim == 2:
            PlotImg = CV2.cvtColor(PlotImg, CV2.COLOR_GRAY2RGB)
        if MaskImg.ndim == 2:
            MaskImg = CV2.cvtColor(MaskImg, CV2.COLOR_GRAY2RGB)
        if StandardSize is None:
            StandardSize = (MaskImg.shape[1], MaskImg.shape[0])
        PlotImg = CV2.resize(PlotImg, StandardSize)
        MaskImg = CV2.resize(MaskImg, StandardSize)
        Combination = NP.hstack((PlotImg, MaskImg))
        Cation = f"Frame:{OrdNum}  Conclude:{Conclude(Dict['Shape'])}" 
        VideoWriter.append_data(AddCaption2Frame(Combination, Cation))
    VideoWriter.close()
    VideoBuffer.seek(0)
    return VideoBuffer

def GetExcel(Data, ImageHeight=150):
    def GetResizeImage(Img, Height):
        W, H = Img.size
        Size = (int(W * (Height / H)), Height)
        return Img.resize(Size, Image.LANCZOS)
    def PXToColW(Pixel): return (Pixel - 5) / 7
    def PXToRowH(Pixel): return (Pixel * 0.750)
    def AddChart2Excel(Sheet, Img, Row, Col, Height=525):
        ChartRI = GetResizeImage(Image.open(Img), Height)
        XLByteIO = BIO()
        ChartRI.save(XLByteIO, "JPEG")
        XLByteIO.seek(0)
        Sheet.add_image(XLImage(XLByteIO), f"{Col}{Row}")
        (Height, Width) = (ChartRI.height, ChartRI.width)
        Sheet.row_dimensions[Row].height, Sheet.column_dimensions[Col].width = PXToRowH(Height), PXToColW(Width)
    XBuffer = BIO()
    WB = Workbook()
    WS = WB.active
    WS.append(["SegmentedImage", "SegmentedMask", "Frame", "Shape", "AspectRatio", "Orientation", "Deformation"])
    ImgCol = { "A": 0, "B": 0 }
    for OrdNum, Dict in enumerate(Data, 1):
        RowIdx = WS.max_row + 1
        WS.append(["", "", OrdNum, Dict["Shape"], Dict["AspectRatio"], Dict["Orientation"], Dict["Deformation"]])
        for (Name, Key) in zip(ImgCol.keys(), ["Plot", "Draw"]):
            LoadImg = Image.fromarray(Dict[Key])
            ResizedImage = GetResizeImage(LoadImg, ImageHeight)
            ImageBytes = BIO()
            ResizedImage.save(ImageBytes, "JPEG")
            if ResizedImage.width > ImgCol[Name]:
                ImgCol[Name] = ResizedImage.width
            ImageBytes.seek(0)
            WS.add_image(XLImage(ImageBytes), f"{Name}{RowIdx}")
        WS.row_dimensions[RowIdx].height = PXToRowH(ImageHeight)
        for Cell in WS[RowIdx]:
            if Cell.column_letter not in ImgCol.keys(): Cell.alignment = Alignment(None, "CENTER".lower())
    for Each in WS.columns:
        Name = Each[0].column_letter
        if Name not in ImgCol.keys():
            MaxLg = 0
            for Cell in Each:
                if Cell.value:
                    MaxLg = max(MaxLg, len(str(Cell.value)))
            WS.column_dimensions[Name].width = (MaxLg + 3.3)
        else:
            Wid = ImgCol[Name]
            WS.column_dimensions[Name].width = PXToColW(Wid)
    NewSegmentResultTable = Table(1, "ResultTable", f"A1:{WS.cell(WS.max_row, WS.max_column).coordinate}")
    NewSegmentResultTable.tableStyleInfo = TableStyleInfo("TableStyleMedium23", False, False, True, False)
    WS.add_table(NewSegmentResultTable)
    WS.title = "DANH SÁCH ĐÃ PHÂN ĐOẠN"
    ChartSheet = WB.create_sheet("THỐNG KÊ PHÂN ĐOẠN VIDEO")
    AddChart2Excel(ChartSheet, SpChart(Data, False), 1, "A")
    AddChart2Excel(ChartSheet, DEChart(Data, False), 3, "A")
    WB.save(XBuffer)
    XBuffer.seek(0)
    return XBuffer

def GetResults(Data):
    OutputZip = BIO()
    ZipBuffer = Zip.ZipFile(OutputZip, "w", Zip.ZIP_DEFLATED)
    ZipBuffer.writestr("SegLogs.xlsx", GetExcel(Data).read())
    ZipBuffer.writestr("SegVideo.mp4", GetVideo(Data).read())
    ZipBuffer.close()
    OutputZip.seek(0)
    return OutputZip
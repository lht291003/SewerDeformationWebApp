from Library import NP, CV2

def PredictOrientation(A):
    RoundAgl = round(A, 2)
    return f"Vertical {RoundAgl}" if 80 <= A <= 110 else f"Horizontal {RoundAgl}"

def GetIoU(Mask1, Mask2):
    if Mask1.ndim > 2:
        Mask1 = NP.squeeze(Mask1)
    if Mask2.ndim > 2:
        Mask2 = NP.squeeze(Mask2)
    if Mask1.shape != Mask2.shape:
        (H1, W1) = Mask1.shape[:2]
        (H2, W2) = Mask2.shape[:2]
        if (H1 * W1) <= (H2 * W2):
            Mask1 = CV2.resize(Mask1, (W2, H2), None, 0.0, 0.0, CV2.INTER_NEAREST)
        else:
            Mask2 = CV2.resize(Mask2, (W1, H1), None, 0.0, 0.0, CV2.INTER_NEAREST)
    if not NP.any(Mask1) or not NP.any(Mask2):
        return 0
    return NP.logical_and(Mask1, Mask2).sum() / NP.logical_or(Mask1, Mask2).sum()

def GetCnt(Mask):
    FindCnts = CV2.findContours(Mask, CV2.RETR_EXTERNAL, CV2.CHAIN_APPROX_SIMPLE)
    FindCnts = FindCnts[0]
    if len(FindCnts) >= 1:
        MaxCnt = max(FindCnts, key=CV2.contourArea)
        return MaxCnt if len(MaxCnt) >= 5 else None
    return None

def GetRealAngle(Ax, Angle):
    Major, Minor = Ax
    if Major < Minor:
        return (Angle - 90) if (Angle > 90) else (Angle + 90)
    return Angle

def GetDictData(Shape, AspectRatio, Orientation, Deformation):
    FormattedResults = {
        "Shape": [Shape],
        "AspectRatio": [AspectRatio],
        "Orientation": [Orientation],
        "Deformation": [Deformation],
    }
    FormattedResults.update({"Conclusion": [Conclude(Shape)]})
    return FormattedResults

def GetEMask(Mask, Contour):
    EM = NP.zeros_like(Mask)
    Ellipse = CV2.fitEllipse(Contour)
    CV2.ellipse(EM, Ellipse, 255, -1)
    return Ellipse, EM

def ShowMask(Mask, Ellipse, Shape):
    if Mask.ndim == 2:
        Mask = CV2.cvtColor(Mask, CV2.COLOR_GRAY2RGB)
        if Shape not in ["Undefined", None]:
            CV2.ellipse(Mask, Ellipse, (0, 99, 0), 2)
            (GetCenter, GetAxes, GetAngle) = Ellipse
            (XC, YC), (D1, D2) = (GetCenter, GetAxes)
            SA = (D1 / 2)
            SB = (D2 / 2)
            if Shape == "Ellipse":
                Theta = NP.radians(GetAngle)
                DXMajor = SA * NP.cos(Theta)
                DYMajor = SA * NP.sin(Theta)
                DXMinor = SB * NP.cos(Theta + NP.pi / 2)
                DYMinor = SB * NP.sin(Theta + NP.pi / 2)
            elif Shape == "Circle":
                DXMajor, DYMajor = (SA, 0)
                DXMinor, DYMinor = (0, SB)
            PT1Major = (int(XC - DXMajor), int(YC - DYMajor))
            PT2Major = (int(XC + DXMajor), int(YC + DYMajor))
            PT1Minor = (int(XC - DXMinor), int(YC - DYMinor))
            PT2Minor = (int(XC + DXMinor), int(YC + DYMinor))
            CV2.line(Mask, PT1Major, PT2Major, (0, 0, 255), 2)
            CV2.line(Mask, PT1Minor, PT2Minor, (255, 0, 0), 2)
            H, W = Mask.shape[:2]
            CV2.line(Mask, (0, int(YC)), (W, int(YC)), (0, 255, 0), 1)
            CV2.line(Mask, (int(XC), 0), (int(XC), H), (0, 255, 0), 1)
        return Mask
    else:
        return Mask

def Conclude(Shape):
    if not Shape:
        return None
    return "Normal" if Shape == "Circle" else "Deformed"

def GetDeltaOrientation(OldOrientation, NowOrientation):
    def ExtractAngleinOrientation(Orientation):
        if not Orientation: return 0
        return float(Orientation.split(" ")[1])
    OldAngle = ExtractAngleinOrientation(OldOrientation)
    NowAngle = ExtractAngleinOrientation(NowOrientation)
    Delta = round(abs(NowAngle - OldAngle), 2)
    if Delta == 0:
        return "Unchanged Angle"
    else:
        if NowAngle > OldAngle:
            return f"Increased Angle {Delta}"
        else:
            return f"Decreased Angle {Delta}"

def AnalizeMask(Mask):
    AspectRatio = None
    Deformation = None
    Orientation = None
    Shape = None
    Angle = None
    Contour = GetCnt(Mask)
    if Contour is not None:
        Ellipse, EMask = GetEMask(Mask, Contour)
        (GetCenter, GetAxes, GetAngle) = Ellipse
        MMask = CV2.bitwise_and(Mask, EMask)
        IsEllipse = GetIoU(MMask, EMask) >= 0.99
        if IsEllipse:
            AspectRatio = (min(GetAxes) / max(GetAxes))
            if AspectRatio < 0.99:
                Angle = GetRealAngle(GetAxes, GetAngle)
                Deformation = (1 - AspectRatio)
                Orientation = PredictOrientation(Angle)
                Shape = "Ellipse"
            else:
                Shape = "Circle"
        else:
            Shape = "Undefined"
        return (MMask, Ellipse, Shape, AspectRatio, Orientation, Deformation)
    else:
        return None

def ComparePictures(OldFrame, NowFrame):
    IoU = GetIoU(OldFrame["Mask"], NowFrame["Mask"])
    Shape = "Deformed" if (IoU < 0.99) else "Normal"
    Deformation = (1 - IoU)
    DeltaOrientation = None
    OldShapeCond = OldFrame["Shape"] != "Undefined"
    NowShapeCond = NowFrame["Shape"] != "Undefined"
    if OldShapeCond and NowShapeCond:
        OldOrientation = OldFrame["Orientation"]
        NowOrientation = NowFrame["Orientation"]
        DeltaOrientation = GetDeltaOrientation(OldOrientation, NowOrientation)
    FormattedResults = {
        "IoU (MaskA & MaskB)": [IoU],
        "Deformation": [Deformation],
        "ΔAngle": [DeltaOrientation],
        "Conclusion": [Shape]
    }
    return FormattedResults

def AnalyzePicture(Result):
    GetPlot = Result.plot()
    Mask, TbDict, Ellipse = (NP.zeros_like(GetPlot), GetDictData(None, None, None, None), None)
    if Result.masks:
        GetBMask = (Result.masks.data[0].cpu().numpy() * 255).astype(NP.uint8)
        Info = AnalizeMask(GetBMask)
        if Info:
            Mask, Ellipse, Shape, AspectRatio, Orientation, Deformation = Info
            TbDict = GetDictData(Shape, AspectRatio, Orientation, Deformation)
    return (CV2.cvtColor(GetPlot, 4), Mask, Ellipse), TbDict
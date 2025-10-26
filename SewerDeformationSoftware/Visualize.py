from Library import NP, App, Chart, Plt, BIO, Series, cut

def DEChart(Data, IsShow):
    DeformationSeries = Series([Item['Deformation'] for Item in Data if Item['Deformation'] != None])
    Bins = NP.arange(0, 1.0 + 0.05, 0.05)
    Labels = [f"{round(Bins[Index], 2)}-{round(Bins[Index+1], 2)}" for Index in range(len(Bins) - 1)]
    RangeSeries = cut(DeformationSeries, Bins, True, Labels, False, 3, True)
    BinCounts = RangeSeries.value_counts().reset_index()
    BinCounts.columns = ["Range", "Frame"]
    if not IsShow:
        (Figure, Axes) = Plt.subplots(figsize=(11, 6.5))
        Axes.bar(BinCounts["Range"], BinCounts["Frame"])
        Axes.set_title("Biểu đồ phân bố phạm vi biến dạng của đường cống")
        Axes.set_xlabel("Range")
        Axes.set_ylabel("Frame")
        Plt.xticks(rotation=90)
        Plt.tight_layout()
        ChartBytes = BIO()
        Plt.savefig(ChartBytes, format="JPG")
        ChartBytes.seek(0)
        Plt.close(Figure)
        return ChartBytes
    with App.expander("Biểu đồ phân bố phạm vi biến dạng của đường cống"):
        App.plotly_chart(Chart.bar(BinCounts, "Range", "Frame", "Range"))

def SpChart(Data, IsShow):
    ShapeSeries = Series([Item['Shape'] for Item in Data])
    ShapeCounts = ShapeSeries.value_counts().reset_index()
    ShapeCounts.columns = ["Shape", "Frame"]
    if not IsShow:
        (Figure, Axes) = Plt.subplots(figsize=(11.00, 6.50))
        Axes.bar(ShapeCounts["Shape"], ShapeCounts["Frame"])
        Axes.set_title("Biểu đồ phân bố hình dạng hình học của đường cống")
        Axes.set_xlabel("Shape")
        Axes.set_ylabel("Frame")
        Plt.tight_layout()
        ChartBytes = BIO()
        Plt.savefig(ChartBytes, format="JPG")
        ChartBytes.seek(0)
        Plt.close(Figure)
        return ChartBytes
    with App.expander("Biểu đồ phân bố hình dạng hình học của đường cống"):
        App.plotly_chart(Chart.bar(ShapeCounts, "Shape", "Frame", "Shape"))

def ShowVisuals(Data):
    SpChart(Data, True)
    DEChart(Data, True)
heatmap = wiz.model("struct").zenly.heatmap(
    region=wiz.request.query("region", wiz.request.query("location", "")),
    limit=wiz.request.query("limit", 12)
)
wiz.response.status(200, heatmap=heatmap)

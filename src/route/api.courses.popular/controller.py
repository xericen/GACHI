limit = wiz.request.query("limit", 4)
rows = wiz.model("struct").course.popular(limit)
wiz.response.status(200, rows=rows)

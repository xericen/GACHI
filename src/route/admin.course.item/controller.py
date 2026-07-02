segment = wiz.request.match("/admin/courses/<string(length=32):id>")
wiz.model("admin_route").course_item(segment.id)

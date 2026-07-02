segment = wiz.request.match("/admin/courses/<string(length=32):id>/tags")
wiz.model("admin_route").course_tags(segment.id)

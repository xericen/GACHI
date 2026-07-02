segment = wiz.request.match("/admin/courses/<string(length=32):id>/featured")
wiz.model("admin_route").course_featured(segment.id)

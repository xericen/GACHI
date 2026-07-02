segment = wiz.request.match("/admin/curation/featured/<id>")
wiz.model("admin_route").featured_item(segment.id)

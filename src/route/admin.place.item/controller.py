segment = wiz.request.match("/admin/places/<id>")
wiz.model("admin_route").place_item(segment.id)

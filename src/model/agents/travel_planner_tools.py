Types = wiz.model("ai_harness/types")


class AiToolAdapter:
    def __init__(self, implementation, name):
        self.implementation = implementation
        self.name = name
        self.schema = self._schema(name)

    def execute(self, arguments):
        if self.name == "place_search":
            data = self.implementation.execute_place_search(arguments)
        elif self.name == "directions_lookup":
            data = self.implementation.execute_directions_lookup(arguments)
        else:
            data = {"status": "error", "message": f"지원하지 않는 함수입니다: {self.name}"}
        return Types.ToolResult(
            status=str(data.get("status") or "ok"),
            data=data,
            retryable=False,
        )

    def _schema(self, name):
        for item in self.implementation.function_declarations() or []:
            if item.get("name") == name:
                return dict(item)
        return {"type": "function", "name": name, "parameters": {"type": "object"}}


class TravelPlannerTools:
    @staticmethod
    def build(implementation):
        return [
            AiToolAdapter(implementation, "place_search"),
            AiToolAdapter(implementation, "directions_lookup"),
        ]


Model = TravelPlannerTools

class Tool:
    name = ""
    schema = {}

    def execute(self, arguments):
        raise NotImplementedError


Model = Tool

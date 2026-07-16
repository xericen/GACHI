Types = wiz.model("ai_harness/types")


class ModelProvider:
    def generate(self, messages, tools, system_prompt, stream=False):
        raise NotImplementedError


class ProviderTypes:
    ModelProvider = ModelProvider
    ProviderError = Types.ProviderError


Model = ProviderTypes

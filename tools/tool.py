class Tool:
    def __init__(
        self,
        name,
        description,
        parameters,
        callback
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.callback = callback

from .KonanZerroSyntheticProvider import KonanZerroSyntheticProvider


class KonanNotInitializedObjectSyntheticProvider(KonanZerroSyntheticProvider):
    def __init__(self, valobj):
        super(KonanNotInitializedObjectSyntheticProvider, self).__init__(valobj)

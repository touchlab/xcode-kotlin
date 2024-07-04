from .KonanZerroSyntheticProvider import KonanZerroSyntheticProvider


class KonanNullSyntheticProvider(KonanZerroSyntheticProvider):
    def __init__(self, valobj):
        super(KonanNullSyntheticProvider, self).__init__(valobj)

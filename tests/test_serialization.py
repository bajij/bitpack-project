from bitpack.crossing import BitPackingCrossing
from bitpack.aligned import BitPackingAligned
from bitpack.overflow import BitPackingOverflow
from bitpack.header import PackedData

def roundtrip(packer, arr):
    data = packer.compress(arr)
    blob = data.to_bytes()
    data2 = PackedData.from_bytes(blob)
    out = [0]*len(arr)
    packer.decompress(out, data2)
    assert out == arr

def test_roundtrip_crossing():
    roundtrip(BitPackingCrossing(), [1,2,3,4095,4,5])

def test_roundtrip_aligned():
    roundtrip(BitPackingAligned(), [1,2,3,4095,4,5])

def test_roundtrip_overflow():
    roundtrip(BitPackingOverflow(), [1,2,3,1024,4,5,2048])

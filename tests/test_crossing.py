from bitpack.crossing import BitPackingCrossing
from bitpack.header import PackedData, KIND_CROSSING

def test_crossing_basic_k12():
    arr = [1, 2, 3, 4095, 4, 5]  # k=12 (max=4095)
    packer = BitPackingCrossing()
    data = packer.compress(arr)
    assert data.kind == KIND_CROSSING
    assert data.k == 12
    # get direct
    for i, v in enumerate(arr):
        assert packer.get(i, data) == v
    # decompress
    out = [0]*len(arr)
    packer.decompress(out, data)
    assert out == arr

def test_crossing_zeroes_k0():
    arr = [0,0,0]
    packer = BitPackingCrossing()
    data = packer.compress(arr)
    assert data.k == 0
    out = [0]*3
    packer.decompress(out, data)
    assert out == arr

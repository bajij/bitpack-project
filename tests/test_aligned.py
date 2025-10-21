from bitpack.aligned import BitPackingAligned
from bitpack.header import KIND_ALIGNED

def test_aligned_basic_k12():
    arr = [1, 2, 3, 4095, 4, 5]
    p = BitPackingAligned()
    data = p.compress(arr)
    assert data.kind == KIND_ALIGNED
    assert data.k == 12
    # cap doit être floor(32/12)=2
    assert data.cap == 2
    # get + decompress
    for i, v in enumerate(arr):
        assert p.get(i, data) == v
    out = [0]*len(arr)
    p.decompress(out, data)
    assert out == arr

def test_aligned_k32_cap1():
    # valeurs proches de 2^32-1 => k=32 => cap=1
    arr = [0xFFFFFFFF, 0x12345678, 0]
    p = BitPackingAligned()
    data = p.compress(arr)
    assert data.k == 32 and data.cap == 1
    out = [0]*len(arr)
    p.decompress(out, data)
    assert out == arr

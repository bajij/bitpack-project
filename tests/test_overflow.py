from bitpack.overflow import BitPackingOverflow
from bitpack.header import KIND_OVERFLOW

def test_overflow_example_from_statement():
    # 1,2,3,1024,4,5,2048  -> k'=3, m=2, p=1 attendu
    arr = [1,2,3,1024,4,5,2048]
    p = BitPackingOverflow(auto_select=True)
    data = p.compress(arr)
    assert data.kind == KIND_OVERFLOW
    assert data.k_prime == 3
    assert data.p in (0,1)  # 2 éléments overflow => p=1
    # get + decompress
    for i, v in enumerate(arr):
        assert p.get(i, data) == v
    out = [0]*len(arr)
    p.decompress(out, data)
    assert out == arr

def test_overflow_no_overflow_case():
    arr = [0, 1, 2, 3, 4]
    # On force un k' assez grand pour que TOUT tienne inline
    p = BitPackingOverflow(auto_select=False, k_prime=3)
    data = p.compress(arr)
    assert data.k_prime == 3
    assert data.k_over == 0  # aucun overflow attendu
    out = [0] * len(arr)
    p.decompress(out, data)
    assert out == arr


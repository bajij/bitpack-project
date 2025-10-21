from bitpack.core import write_bits, read_bits, ceil_div

def test_read_write_bits_crossing():
    words = [0, 0]
    # écrire 20 bits à partir du bit 28 => chevauche deux mots (4 + 16)
    write_bits(words, 28, 20, 0xABCDE)
    val = read_bits(words, 28, 20)
    assert val == 0xABCDE

def test_ceil_div():
    assert ceil_div(0, 32) == 0
    assert ceil_div(1, 32) == 1
    assert ceil_div(32, 32) == 1
    assert ceil_div(33, 32) == 2

with open("tiny_u32.bin","wb") as f:
    for x in [1,2,3,4095,4,5]:
        f.write((x & 0xFFFFFFFF).to_bytes(4,"little"))
print("OK: tiny_u32.bin créé")

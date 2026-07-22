BN = repr(chr(92) + chr(110))
print(f"BN variable = {BN}")
print(f"BN length = {len(eval(BN))}")
print(f"Raw: {[ord(c) for c in eval(BN)]}")

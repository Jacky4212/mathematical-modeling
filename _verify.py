import os
os.chdir(r'D:\code\cherry studio\数学建模')

with open('ai-chat.js', 'rb') as f:
    raw = f.read()

idx = raw.find(b'var SYS_BASE')
end = raw.find(b'var SYS = SYS_BASE', idx)
chunk = raw[idx:end]

# Count \n'+ (backslash-n-quote-plus = bytes 92,110,39,43)
pattern = bytes([92, 110, 39, 43])
count = 0
for i in range(len(chunk) - 3):
    if chunk[i:i+4] == pattern:
        count += 1

print(f'Backslash-n lines: {count} (expected 15-16)')

# Show first 200 chars
text = chunk.decode('utf-8', errors='replace')
for i, line in enumerate(text.split('\n')[:5]):
    print(f'  Line {i}: {line[:80]}...' if len(line) > 80 else f'  Line {i}: {line}')

if count >= 14:
    print('OK - SYS_BASE block looks correct')
else:
    print('FAIL - not enough backslash-n escapes')

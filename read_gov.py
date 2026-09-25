path = r'c:\Users\LENOVO\OneDrive\Desktop\sih\frontend\src\pages\government\GovernmentPortal.jsx'
content = open(path, 'rb').read().decode('utf-8')
# find the broken area around line 46
lines = content.split('\n')
for i, line in enumerate(lines[40:60], start=41):
    open(r'c:\Users\LENOVO\OneDrive\Desktop\sih\gov_lines.txt', 'a', encoding='utf-8').write(f"{i}: {line}\n")

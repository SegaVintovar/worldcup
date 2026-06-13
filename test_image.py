from PIL import Image

path = "/home/sbonevel/worldcup/src/assets/sidequest_logo.png"

img = Image.open(path)

print("mode:", img.mode)
print("bands:", img.getbands())
print("format:", img.format)

# check real alpha presence
if "A" in img.getbands():
    print("✅ HAS TRANSPARENCY (alpha channel exists)")
else:
    print("❌ NO TRANSPARENCY (this is your issue)")
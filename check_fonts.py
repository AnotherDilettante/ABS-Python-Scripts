import matplotlib.font_manager

# Get all installed fonts
font_names = sorted(set([f.name for f in matplotlib.font_manager.fontManager.ttflist]))

# Print them
print("--- AVAILABLE FONTS ---")
for font in font_names:
    print(font)
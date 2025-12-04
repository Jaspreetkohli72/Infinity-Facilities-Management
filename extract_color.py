from PIL import Image
import collections

def get_dominant_blue(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = img.getdata()
    
    # Filter for vibrant blue pixels
    # Blue must be significantly greater than Red and Green to be "blue"
    # And Red/Green shouldn't be too high (to avoid white/light gray)
    blue_pixels = []
    for r, g, b in pixels:
        if b > r + 20 and b > g + 20 and (r < 200 or g < 200):
            blue_pixels.append((r, g, b))
            
    if not blue_pixels:
        return "No vibrant blue pixels found"
    
    # Get most common blue pixel
    counter = collections.Counter(blue_pixels)
    most_common = counter.most_common(5) # Get top 5 to see range
    
    return most_common

image_path = r"C:/Users/Jaspreet/.gemini/antigravity/brain/1fcdf59c-858c-4d69-a778-6d76303a24cd/uploaded_image_1764786596156.png"
results = get_dominant_blue(image_path)
print("Top 5 Blues:")
for color, count in results:
    print(f"#{color[0]:02x}{color[1]:02x}{color[2]:02x} (Count: {count})")

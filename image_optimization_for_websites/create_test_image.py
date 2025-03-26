#!/usr/bin/env python3

from PIL import Image, ImageDraw
import os

def create_test_image(filename, size=(1200, 800), color=(255, 255, 255)):
    # Create a new image with the given size and color
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes to make the image more interesting
    # Draw a gradient
    for i in range(0, size[0], 2):
        r = int(255 * (i / size[0]))
        g = int(255 * (1 - i / size[0]))
        b = 100
        draw.line([(i, 0), (i, size[1])], fill=(r, g, b), width=2)
    
    # Draw some circles
    for i in range(0, size[0], 200):
        for j in range(0, size[1], 200):
            radius = 50 + (i + j) % 50
            draw.ellipse((i-radius, j-radius, i+radius, j+radius), 
                         fill=(i % 255, j % 255, (i+j) % 255))
    
    # Save the image
    img.save(filename, 'JPEG', quality=95)
    print(f"Created test image: {filename} ({os.path.getsize(filename) / 1024:.2f} KB)")

def main():
    # Create test directory if it doesn't exist
    os.makedirs('test_images', exist_ok=True)
    
    # Create a small image
    create_test_image('test_images/small_image.jpg', (800, 600))
    
    # Create a large image
    create_test_image('test_images/large_image.jpg', (3000, 2000))

if __name__ == "__main__":
    main()
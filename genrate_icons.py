#!/usr/bin/env python3
"""
Quick PWA Icon Generator
Run this script to generate all required icon files for your attendance PWA
"""

import os
from PIL import Image, ImageDraw, ImageFont


def create_gradient_background(size, start_color, end_color):
    """Create gradient background"""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)

    for i in range(size):
        # Linear gradient
        ratio = i / size
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)

        draw.line([(0, i), (size, i)], fill=(r, g, b))

    return img, draw


def create_attendance_icon(size):
    """Create professional attendance icon"""

    # Colors matching your theme
    start_color = (102, 126, 234)  # #667eea
    end_color = (118, 75, 162)  # #764ba2

    img, draw = create_gradient_background(size, start_color, end_color)

    center = size // 2

    # Draw main clock circle (white background)
    clock_radius = int(size * 0.35)
    draw.ellipse([
        center - clock_radius, center - clock_radius,
        center + clock_radius, center + clock_radius
    ], fill='white', outline='white', width=3)

    # Draw clock border
    border_width = max(2, size // 100)
    draw.ellipse([
        center - clock_radius, center - clock_radius,
        center + clock_radius, center + clock_radius
    ], fill=None, outline=(50, 50, 100), width=border_width)

    # Draw hour markers
    import math
    for hour in range(12):
        angle = hour * 30 - 90  # Start from top (12 o'clock)
        outer_radius = clock_radius * 0.9
        inner_radius = clock_radius * 0.8

        outer_x = center + outer_radius * math.cos(math.radians(angle))
        outer_y = center + outer_radius * math.sin(math.radians(angle))
        inner_x = center + inner_radius * math.cos(math.radians(angle))
        inner_y = center + inner_radius * math.sin(math.radians(angle))

        line_width = 3 if hour % 3 == 0 else 1  # Bold for 12, 3, 6, 9
        draw.line([inner_x, inner_y, outer_x, outer_y],
                  fill=(50, 50, 100), width=line_width)

    # Draw clock hands (9:00 - typical work start time)
    hand_color = (50, 50, 100)

    # Hour hand (pointing to 9)
    hour_length = clock_radius * 0.5
    hour_x = center - hour_length
    hour_y = center
    draw.line([center, center, hour_x, hour_y],
              fill=hand_color, width=max(3, size // 50))

    # Minute hand (pointing to 12)
    minute_length = clock_radius * 0.7
    minute_x = center
    minute_y = center - minute_length
    draw.line([center, center, minute_x, minute_y],
              fill=hand_color, width=max(2, size // 70))

    # Center dot
    dot_radius = max(3, size // 50)
    draw.ellipse([
        center - dot_radius, center - dot_radius,
        center + dot_radius, center + dot_radius
    ], fill=hand_color)

    # Add decorative elements for larger icons
    if size >= 128:
        # Add small person icons around the clock
        person_positions = [
            (center - clock_radius - 20, center - 10),  # Left
            (center + clock_radius + 20, center - 10),  # Right
            (center - 10, center - clock_radius - 20),  # Top
            (center - 10, center + clock_radius + 20)  # Bottom
        ]

        for x, y in person_positions:
            # Simple person icon
            head_radius = 4
            body_height = 12

            # Head
            draw.ellipse([x, y, x + head_radius * 2, y + head_radius * 2],
                         fill='white', outline=(50, 50, 100), width=1)

            # Body
            draw.rectangle([x + head_radius // 2, y + head_radius * 2,
                            x + head_radius * 1.5, y + head_radius * 2 + body_height],
                           fill='white', outline=(50, 50, 100), width=1)

    return img


def generate_all_icons():
    """Generate all required PWA icon sizes"""

    sizes = [72, 96, 128, 192, 512]
    static_dir = 'static'

    # Create static directory if it doesn't exist
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"✅ Created directory: {static_dir}")

    print("🎨 Generating PWA Icons...")
    print("=" * 40)

    success_count = 0

    for size in sizes:
        try:
            icon = create_attendance_icon(size)
            filename = f'icon-{size}.png'
            filepath = os.path.join(static_dir, filename)

            icon.save(filepath, 'PNG', optimize=True)
            print(f"✅ Created: {filename} ({size}x{size})")
            success_count += 1

        except Exception as e:
            print(f"❌ Failed to create icon-{size}.png: {e}")

    print("=" * 40)
    print(f"🎉 Generated {success_count}/{len(sizes)} icons successfully!")

    if success_count == len(sizes):
        print("\n📋 All PWA icons are ready!")
        print(f"📁 Location: {os.path.abspath(static_dir)}")
        return True
    else:
        print("\n⚠️  Some icons failed to generate. Check the errors above.")
        return False


def verify_files():
    """Verify all required files exist"""

    required_files = [
        'static/manifest.json',
        'static/sw.js',
        'static/icon-72.png',
        'static/icon-96.png',
        'static/icon-128.png',
        'static/icon-192.png',
        'static/icon-512.png'
    ]

    print("\n🔍 Verifying PWA files...")
    all_good = True

    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - MISSING")
            all_good = False

    return all_good


def main():
    """Main function"""
    print("🚀 PWA Icon Generator for Company Attendance System")
    print("=" * 55)

    try:
        # Check if PIL is available
        from PIL import Image, ImageDraw

        # Generate icons
        success = generate_all_icons()

        if success:
            # Verify all files
            if verify_files():
                print("\n" + "=" * 55)
                print("🎉 SUCCESS! Your PWA is ready!")
                print("\n📋 Next Steps:")
                print("1. Make sure your updated attendance.py is in place")
                print("2. Run: streamlit run attendance.py")
                print("3. Access via mobile browser")
                print("4. Look for 'Add to Home Screen' option")
                print("5. Test offline functionality")

                print(f"\n📱 Test your PWA at: http://localhost:8501")
            else:
                print("\n⚠️  Some files are missing. Please check the errors above.")

    except ImportError:
        print("❌ PIL (Pillow) library is required!")
        print("Install it with: pip install Pillow")
        print("\nOr create icons manually:")
        print("- Use any image editor to create square PNG images")
        print("- Required sizes: 72x72, 96x96, 128x128, 192x192, 512x512")
        print("- Save as icon-{size}.png in the static folder")


if __name__ == "__main__":
    main()
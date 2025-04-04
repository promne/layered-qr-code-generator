import qrcode
import random
import os
import math
from PIL import Image, ImageDraw

# --- Helper Functions ---

def get_alignment_pattern_locations(version):
    """
    Calculate the center coordinates of alignment patterns for a given QR version.
    Args:
        version: The QR code version number (1 to 40).
    Returns:
        A list of (row, col) tuples for the center coordinates. Returns empty list for version 1.
    """
    # Alignment pattern positions are specified by the standard.
    # This is a lookup table based on common versions.
    # Source: e.g., https://www.thonky.com/qr-code-tutorial/alignment-pattern-locations
    if version < 2:
        return []
    # Formula-based calculation is complex. Using a lookup for common versions.
    # Pattern: First is always 6. Last is always matrix_size - 7. Others are spaced approx evenly.
    positions = [
        [], # Version 0 - Invalid
        [], # Version 1 - No alignment patterns
        [6, 18], # Version 2 (25x25)
        [6, 22], # Version 3 (29x29)
        [6, 26], # Version 4 (33x33)
        [6, 30], # Version 5 (37x37)
        [6, 34], # Version 6 (41x41)
        # Version 7 (45x45) introduces multiple alignment patterns
        [6, 22, 38],
        [6, 24, 42], # V8 (49x49)
        [6, 26, 46], # V9 (53x53)
        [6, 28, 50], # V10 (57x57)
        [6, 30, 54], # V11 (61x61)
        [6, 32, 58], # V12 (65x65)
        [6, 34, 62], # V13 (69x69)
        # And so on... Add more as needed, or implement the formula.
        # For higher versions, the number and spacing increase.
        # Let's stop at V13 for this example lookup.
    ]
    if version >= len(positions):
        # Approximation for higher versions (less accurate)
        # A proper implementation would use the formula from the spec.
        size = 4 * version + 17
        num_patterns = math.ceil((version - 1) / 7) + 2 # Rough estimate
        step = (size - 7 - 6) / (num_patterns - 1) if num_patterns > 1 else 0
        coords = [6 + round(i * step) for i in range(num_patterns)]
        print(f"Warning: Using estimated alignment pattern locations for version {version}. Accuracy not guaranteed.")
        # Exclude potential overlaps with finder patterns (approximate check)
        return [(r, c) for r in coords for c in coords if not ((r < 9 and c < 9) or (r < 9 and c > size - 10) or (r > size - 10 and c < 9))]
    else:
        coords = positions[version]
        # Generate all pairs, excluding those overlapping finder patterns (approx)
        size = 4 * version + 17
        return [(r, c) for r in coords for c in coords if not ((r < 9 and c < 9) or (r < 9 and c > size - 10) or (r > size - 10 and c < 9))]


def is_structural(row, col, size, version):
    """
    Approximates if a module is part of common structural elements.
    Includes improved checks for alignment patterns based on version.
    WARNING: Still a heuristic, especially for high versions or unusual masks.
    Args:
        row, col: Module coordinates (0-indexed relative to the code matrix).
        size: The width/height of the QR code matrix (e.g., 21 for version 1).
        version: The QR code version number.
    Returns:
        True if likely structural, False otherwise.
    """
    # 1. Finder Patterns (Top-left, Top-right, Bottom-left) - 7x7 core + 1 separator
    # Check 8x8 area to be safe and include separators
    if (row < 8 and col < 8) or \
       (row < 8 and col >= size - 8) or \
       (row >= size - 8 and col < 8):
        return True

    # 2. Timing Patterns (Row 6 and Column 6, between finder patterns)
    if (row == 6 and col >= 8 and col < size - 8) or \
       (col == 6 and row >= 8 and row < size - 8):
        return True

    # 3. Alignment Patterns (Depend on version >= 2)
    # Each alignment pattern is a 5x5 area. Check a slightly larger box (e.g., +/- 2) around center.
    alignment_centers = get_alignment_pattern_locations(version)
    for center_r, center_c in alignment_centers:
        if abs(row - center_r) <= 2 and abs(col - center_c) <= 2:
            return True

    # 4. Format Information (Adjacent to finder patterns)
    # Fixed positions relative to finder patterns. Size 15 modules total.
    format_coords = set()
    # Around top-left finder
    for i in range(9): format_coords.add((8, i)) # Row 8, cols 0-8 (excluding timing pattern col 6)
    for i in range(8): format_coords.add((i, 8)) # Col 8, rows 0-7 (excluding timing pattern row 6)
    format_coords.discard((8,6)) # Discard timing pattern intersection safely
    format_coords.discard((6,8)) # Discard timing pattern intersection safely

    # Around top-right finder
    for i in range(8): format_coords.add((8, size - 1 - i)) # Row 8, near top-right
    # Around bottom-left finder
    for i in range(8): format_coords.add((size - 1 - i, 8)) # Col 8, near bottom-left

    if (row, col) in format_coords:
        return True

    # 5. Version Information (Only for version >= 7)
    # Two 3x6 blocks near top-right and bottom-left corners.
    if version >= 7:
        # Top-right block: rows 0-5, cols size-11 to size-9
        if (row < 6 and col >= size - 11 and col < size - 8):
            return True
        # Bottom-left block: cols 0-5, rows size-11 to size-9
        if (col < 6 and row >= size - 11 and row < size - 8):
            return True

    return False # Assume data/ECC otherwise

# --- Layer Generation ---

def generate_visual_layered_qrs(data: str, n: int, k: int, output_dir: str, filename_prefix: str, box_size: int, border: int):
    """
    Generates n image layers that, when k are stacked, form a QR code.
    Args:
        data: The string data to encode.
        n: Total number of image layers.
        k: Number of layers required for reconstruction.
        output_dir: Directory to save the layer images.
        filename_prefix: Prefix for output filenames.
        box_size: Size of each QR module in pixels.
        border: Width of the quiet zone border (in modules).
    """
    if k > n or k < 1:
        raise ValueError("k must be between 1 and n")

    # 1. Generate the target QR code
    qr = qrcode.QRCode(
        version=None, # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_L, # Lower ECC might be sufficient, reduces density
        box_size=box_size,
        border=border # Let qrcode library handle the border initially
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_version = qr.version
    print(f"Target QR Code Version: {qr_version}")

    # Get the module matrix *without* the border for logic.
    # qr.modules gives a list of lists (rows) of booleans (True=black).
    if not hasattr(qr, 'modules') or qr.modules is None:
         raise RuntimeError("Could not access QR code modules directly from the library. Check qrcode library version or implementation.")
    matrix = qr.modules
    matrix_size = len(matrix) # This is the size of the code area (e.g., 21 for v1)

    if matrix_size == 0:
        raise ValueError("Generated QR matrix is empty. Input data might be too large or invalid.")

    print(f"Generated target QR matrix of size: {matrix_size}x{matrix_size} (Version: {qr_version}) used for logic.")


    # 2. Calculate final image dimensions (including border)
    img_size = (matrix_size + 2 * border) * box_size

    # 3. Create n transparent layer images
    layers = []
    for i in range(n):
        layer_img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0)) # Transparent background
        layers.append((layer_img, ImageDraw.Draw(layer_img))) # Store image and its drawing context

    # 4. Determine how many layers a black data module needs to be on
    black_count_for_data = n - k + 1
    print(f"Each black data module will be drawn on {black_count_for_data} out of {n} layers.")

    # 5. Iterate through target matrix (core modules) and distribute onto layers
    all_layer_indices = list(range(n))
    structural_module_count = 0
    data_module_count = 0

    for r_idx, row in enumerate(matrix):
        for c_idx, module_is_black in enumerate(row):
            # Determine if the module is structural (using 0-based index relative to matrix start)
            # Pass the determined version to the structural check function
            is_structural_module = is_structural(r_idx, c_idx, matrix_size, qr_version)

            # Calculate pixel coordinates for the top-left of this module in the final image
            # (including the border offset)
            px_y = (border + r_idx) * box_size
            px_x = (border + c_idx) * box_size

            if module_is_black: # Target module is black
                if is_structural_module:
                    structural_module_count += 1
                    # Structural & Black: Must be black on ALL n layers
                    for _, draw_context in layers:
                        draw_context.rectangle(
                            [px_x, px_y, px_x + box_size -1 , px_y + box_size - 1], # Use -1 for exact box size pixels
                            fill=(0, 0, 0, 255) # Black, fully opaque
                        )
                else:
                    data_module_count += 1
                    # Data & Black: Must be black on exactly `black_count_for_data` layers
                    # Choose a random subset of layers for this module
                    chosen_layer_indices = random.sample(all_layer_indices, black_count_for_data)
                    for layer_idx in chosen_layer_indices:
                        _, draw_context = layers[layer_idx]
                        draw_context.rectangle(
                            [px_x, px_y, px_x + box_size - 1, px_y + box_size - 1],
                            fill=(0, 0, 0, 255) # Black, fully opaque
                        )
            else: # Target module is White (False)
                # Structural & White: Must be white (transparent) on ALL layers.
                # Data & White: Must be white (transparent) on ALL layers.
                # Since layers start transparent, we do nothing here.
                pass

    print(f"Processed {structural_module_count} structural modules and {data_module_count} data/ECC modules.")
    if structural_module_count == 0 and matrix_size > 0:
         print("Warning: No structural modules were identified. The `is_structural` function might need refinement for this QR version/layout.")


    # 6. Save the layer images
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating output directory {output_dir}: {e}")
            return # Cannot save images

    for i, (layer_img, _) in enumerate(layers):
        filename = f"{filename_prefix}{i+1}_of_{n}.png"
        filepath = os.path.join(output_dir, filename)
        try:
            layer_img.save(filepath, "PNG")
            print(f"Saved: {filepath}")
        except Exception as e:
            print(f"Error saving image {filepath}: {e}")

# Example Usage (Optional - can be run if the script is executed directly)
if __name__ == '__main__':
    # Define parameters
    data_to_encode = "https://google.com"
    num_layers = 5 # Total layers (n)
    required_layers = 3 # Layers needed for reconstruction (k)
    output_directory = "output_layers"
    file_prefix = "layer_"
    module_pixel_size = 10 # Size of each black/white square
    quiet_zone_size = 4 # Standard quiet zone border width

    # Create a dummy QR code just to estimate version needed
    qr_check = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr_check.add_data(data_to_encode)
    qr_check.make(fit=True)
    estimated_version = qr_check.version
    print(f"Estimated QR version needed for '{data_to_encode}': {estimated_version}")

    # Generate the layers
    generate_visual_layered_qrs(
        data=data_to_encode,
        n=num_layers,
        k=required_layers,
        output_dir=output_directory,
        filename_prefix=file_prefix,
        box_size=module_pixel_size,
        border=quiet_zone_size
    )
    print("\\nLayer generation complete.")
    print(f"Check the '{output_directory}' folder for the generated PNG images.")

